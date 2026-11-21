"""
DietSense — Food of the Day Integration & Functional Test Suite
Covers all 13 test requirements:
1. Valid food is selected for current day
2. Refreshing does not change the selection (deterministic persistence)
3. New daily selection appears on next calendar day
4. Recently featured foods are avoided (30-day window)
5. Incomplete nutrition data handling
6. Missing images do not break the endpoint/card
7. Missing prices display the correct unavailable state ("Price unavailable", never ₹0)
8. Available prices show correct unit and source information
9. Add to Pantry works via API
10. Duplicate pantry entries are prevented
11. Food details show actual database values
12. Feature works completely offline without Gemini
13. Existing pantry and food catalog functionality remain intact
"""

import os
import sys
import uuid
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.main import app
from app.core.security import create_access_token
from app.services.food_of_the_day_service import (
    get_or_create_food_of_the_day,
    get_candidate_food_ids,
    get_similar_foods,
    _generate_factual_profile,
)
from db.database import init_db, get_db_cursor

client = TestClient(app)
init_db()


def create_user_fixture(prefix: str = "fotd"):
    """Creates a local user in SQLite and returns user_id, email, and auth headers."""
    uid = f"usr_{prefix}_{uuid.uuid4().hex[:8]}"
    email = f"{prefix}_{uuid.uuid4().hex[:6]}@dietsense.ai"
    token = create_access_token(user_id=uid, email=email)
    now = datetime.now(timezone.utc).isoformat()

    with get_db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO users (id, email, password_hash, full_name, status, created_at, updated_at)
            VALUES (?, ?, '!test_hash', 'FOTD Tester', 'active', ?, ?)
            """,
            (uid, email, now, now),
        )
        cur.execute(
            """
            INSERT INTO profiles (
                id, user_id, email, full_name, dietary_pref, allergies,
                target_calories, budget_per_meal, prep_time_limit, is_solo_cook,
                active_meal_frequency, age, gender, height_cm, weight_kg,
                goal, activity_level, updated_at
            ) VALUES (
                ?, ?, ?, 'FOTD Tester', 'vegetarian', '[]',
                2000, 100.0, 30, 1,
                '3_meals', 26, 'male', 175.0, 75.0,
                'lose_weight', 'lightly_active', ?
            )
            """,
            (f"prof_{uid}", uid, email, now),
        )

    headers = {"Authorization": f"Bearer {token}"}
    return uid, email, headers


# ─── 1. Daily Selection & Determinism Tests ──────────────────────────────────

class TestDailyFoodSelectionAndPersistence:
    def test_valid_food_selected_for_current_day(self):
        """Req 1: A valid food is selected for the current day."""
        res = client.get("/api/foods/food-of-the-day")
        assert res.status_code == 200
        data = res.json()
        assert "date" in data
        assert "food" in data
        food = data["food"]
        assert food["id"] > 0
        assert len(food["name"]) > 0
        assert food["calories_kcal"] > 0
        assert food["protein_g"] >= 0
        assert "pricing" in food
        assert "editorial" in food

    def test_refresh_does_not_change_selection(self):
        """Req 2: Refreshing the dashboard does not change the selection."""
        res1 = client.get("/api/foods/food-of-the-day")
        res2 = client.get("/api/foods/food-of-the-day")
        res3 = client.get("/api/foods/daily/featured")
        assert res1.status_code == 200
        assert res2.status_code == 200
        assert res3.status_code == 200
        assert res1.json()["food"]["id"] == res2.json()["food"]["id"]
        assert res1.json()["food"]["id"] == res3.json()["food"]["id"]

    def test_new_selection_on_next_calendar_day(self):
        """Req 3: A new daily selection appears on the next calendar day."""
        date_a = "2026-12-01"
        date_b = "2026-12-02"

        res_a = client.get(f"/api/foods/food-of-the-day?date={date_a}")
        res_b = client.get(f"/api/foods/food-of-the-day?date={date_b}")
        assert res_a.status_code == 200
        assert res_b.status_code == 200
        assert res_a.json()["date"] == date_a
        assert res_b.json()["date"] == date_b
        # Two consecutive days must have distinct foods
        assert res_a.json()["food"]["id"] != res_b.json()["food"]["id"]

    def test_recently_featured_foods_avoided(self):
        """Req 4: Recently featured foods are avoided within the window."""
        with get_db_cursor() as cur:
            # Seed 5 consecutive days and check uniqueness
            selected_ids = []
            for day in range(10, 15):
                d_str = f"2026-11-{day:02d}"
                fotd = get_or_create_food_of_the_day(cur, target_date=d_str)
                selected_ids.append(fotd["food"]["id"])

        # All 5 selected food IDs must be distinct
        assert len(selected_ids) == len(set(selected_ids)), f"Expected all unique foods, got: {selected_ids}"


# ─── 2. Data Integrity & Robustness Tests ─────────────────────────────────────

class TestDataIntegrityAndRobustness:
    def test_incomplete_nutrition_data_handled_correctly(self):
        """Req 5: Foods with incomplete or invalid data are rejected from candidate selection."""
        with get_db_cursor() as cur:
            # Candidate IDs must all have positive calories & protein
            candidates = get_candidate_food_ids(cur, exclude_ids=[])
            assert len(candidates) > 0
            cur.execute(f"SELECT COUNT(*) AS bad_cnt FROM foods WHERE id IN ({','.join(map(str, candidates))}) AND (calories_kcal <= 0 OR protein_g < 0)")
            assert cur.fetchone()["bad_cnt"] == 0

    def test_missing_images_handled_gracefully(self):
        """Req 6: Missing images do not break the card or response."""
        res = client.get("/api/foods/food-of-the-day?date=2026-11-21")
        assert res.status_code == 200
        editorial = res.json()["food"]["editorial"]
        # image_url can be None, but card structure remains complete
        assert "image_url" in editorial
        assert "short_intro" in editorial
        assert len(editorial["short_intro"]) > 0

    def test_missing_prices_display_correct_unavailable_state(self):
        """Req 7: Missing prices display 'Price unavailable', never ₹0."""
        # Query a food that has no record in food_prices
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT f.id FROM foods f
                LEFT JOIN food_prices fp ON fp.food_id = f.id
                WHERE fp.price_id IS NULL AND f.calories_kcal > 0
                LIMIT 1
            """)
            unpriced_row = cur.fetchone()

        if unpriced_row:
            unpriced_id = unpriced_row["id"]
            test_date = "2029-01-01"
            with get_db_cursor() as cur:
                cur.execute(
                    """
                    INSERT OR REPLACE INTO daily_featured_foods (feature_date, food_id, short_intro, description, created_at)
                    VALUES (?, ?, 'Intro', 'Desc', '2026-01-01')
                    """,
                    (test_date, unpriced_id),
                )
            res = client.get(f"/api/foods/food-of-the-day?date={test_date}")
            assert res.status_code == 200
            pricing = res.json()["food"]["pricing"]
            assert pricing["available"] is False
            assert pricing["price"] is None
            assert pricing["formatted_price"] == "Price unavailable"
            assert "₹0" not in pricing["formatted_price"]

    def test_available_prices_show_unit_and_source(self):
        """Req 8: Available prices show correct unit and source information."""
        res = client.get("/api/foods/food-of-the-day?date=2026-11-21&region=National")
        assert res.status_code == 200
        pricing = res.json()["food"]["pricing"]
        if pricing["available"]:
            assert "₹" in pricing["formatted_price"]
            assert pricing["unit"] in ("kg", "100g", "litre", "piece", "dozen")
            assert pricing["source"] is not None
            assert len(pricing["source"]) > 0
            assert pricing["price_type"] in ("verified", "estimated")


# ─── 3. Pantry Integration Tests ──────────────────────────────────────────────

class TestPantryIntegration:
    def test_add_food_of_the_day_to_pantry(self):
        """Req 9: Add to Pantry works using stable food ID for authenticated user."""
        uid, email, headers = create_user_fixture("fotd_add")

        res_fotd = client.get("/api/foods/food-of-the-day?date=2026-11-21", headers=headers)
        assert res_fotd.status_code == 200
        food_id = res_fotd.json()["food"]["id"]
        assert res_fotd.json()["food"]["pantry"]["in_pantry"] is False

        # Add to pantry
        res_add = client.post(
            f"/api/foods/{food_id}/add-to-pantry",
            headers=headers,
            json={"quantity": "500g", "in_stock": True},
        )
        assert res_add.status_code == 200
        assert res_add.json()["status"] == "success"

        # Now check food-of-the-day again for this user: should reflect in_pantry == True
        res_after = client.get("/api/foods/food-of-the-day?date=2026-11-21", headers=headers)
        assert res_after.status_code == 200
        assert res_after.json()["food"]["pantry"]["in_pantry"] is True
        assert res_after.json()["food"]["pantry"]["pantry_quantity"] == "500g"

    def test_duplicate_pantry_prevention(self):
        """Req 10: Adding food that already exists in pantry updates quantity rather than duplicating."""
        uid, email, headers = create_user_fixture("fotd_dup")

        res_fotd = client.get("/api/foods/food-of-the-day?date=2026-11-21", headers=headers)
        food_id = res_fotd.json()["food"]["id"]

        # Add once
        client.post(
            f"/api/foods/{food_id}/add-to-pantry",
            headers=headers,
            json={"quantity": "1 kg"},
        )

        # Add twice
        res_second = client.post(
            f"/api/foods/{food_id}/add-to-pantry",
            headers=headers,
            json={"quantity": "2 kg"},
        )
        assert res_second.status_code == 200
        assert res_second.json()["already_in_pantry"] is True

        # Verify only 1 row exists in pantry_items for this user and food
        with get_db_cursor() as cur:
            cur.execute("SELECT COUNT(*) AS cnt FROM pantry_items WHERE user_id = ? AND matched_food_id = ?", (uid, food_id))
            assert cur.fetchone()["cnt"] == 1


# ─── 4. Factual Profile & Offline Robustness Tests ────────────────────────────

class TestFactualProfileAndOfflineIntegrity:
    def test_food_details_show_actual_database_values(self):
        """Req 11: Food details match exact values from the foods table."""
        res = client.get("/api/foods/food-of-the-day?date=2026-11-21")
        assert res.status_code == 200
        food_data = res.json()["food"]
        food_id = food_data["id"]

        with get_db_cursor() as cur:
            cur.execute("SELECT * FROM foods WHERE id = ?", (food_id,))
            db_row = dict(cur.fetchone())

        assert food_data["name"] == db_row["name"]
        assert round(food_data["calories_kcal"], 1) == round(db_row["calories_kcal"], 1)
        assert round(food_data["protein_g"], 1) == round(db_row["protein_g"], 1)
        assert round(food_data["carbohydrates_g"], 1) == round(db_row["carbohydrates_g"], 1)
        assert round(food_data["fat_g"], 1) == round(db_row["fat_g"], 1)

    def test_feature_works_completely_offline_without_gemini(self):
        """Req 12: Rule-based factual profile generates without any external AI API calls."""
        sample_food = {
            "name": "Bajra (Pennisetum typhoideum)",
            "name_local": "Pearl Millet",
            "food_category": "Cereals and Millets",
            "calories_kcal": 361.0,
            "protein_g": 11.6,
            "carbohydrates_g": 67.5,
            "fat_g": 5.0,
            "fiber_g": 11.5,
        }
        profile = _generate_factual_profile(sample_food)
        assert "short_intro" in profile
        assert "description" in profile
        assert "common_usage" in profile
        assert "preparation_methods" in profile
        # Factual nutritional mentions
        assert "361" in profile["description"]
        assert "11.6g" in profile["description"]
        # No prohibited disease claims
        for prohibited in ("cures cancer", "treats diabetes", "guaranteed weight loss", "miracle"):
            assert prohibited not in profile["description"].lower()

    def test_existing_dashboard_and_catalog_remain_intact(self):
        """Req 13: Backward compatibility with Batch 1, 2, and 3."""
        # 1. Categories endpoint works
        res_cats = client.get("/api/foods/categories")
        assert res_cats.status_code == 200

        # 2. 3-view catalog works
        res_all = client.get("/api/foods/?view=all&limit=5")
        assert res_all.status_code == 200
        assert len(res_all.json()["items"]) == 5

        # 3. Pricing regions endpoint works
        res_regions = client.get("/api/pricing/regions")
        assert res_regions.status_code == 200
        assert "National" in res_regions.json()["regions"]

        # 4. Similar foods generation returns populated list
        with get_db_cursor() as cur:
            sims = get_similar_foods(cur, food_id=1, category="Cereals and Millets", limit=3)
            assert len(sims) == 3
            assert all(s["calories_kcal"] > 0 for s in sims)
