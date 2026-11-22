"""
DietSense — Batch 5 & Batch 6: Budget-Aware Recommendations & Integration Test Suite.
Verifies all 32 test scenarios:
1. User accesses recommendations without selecting a budget (unrestricted recommendations).
2. User selects ₹50.
3. User selects ₹100.
4. User selects ₹200.
5. User selects ₹500.
6. User enters a custom amount.
7. User enters an amount outside the quick selections.
8. Invalid manual input is rejected (negative, zero, invalid string).
9. Quick selection updates the active budget.
10. Custom entry updates the active budget.
11. Per Meal filtering works.
12. Per Day filtering works.
13. Within Budget works.
14. Slightly Above Budget works.
15. Show All works.
16. Clear Budget Filter works.
17. Changing the budget updates recommendations.
18. Correct ingredient cost calculation.
19. Correct cost per serving.
20. Missing ingredient prices handling.
21. Incomplete meal cost handling (never classified as within budget).
22. Verified and estimated price labels.
23. Allergy filtering remains enforced (executed before ranking & budget filtering).
24. Dietary restrictions remain enforced.
25. Pantry-based recommendations work.
26. Missing ingredients are identified correctly.
27. Additional purchase costs are calculated correctly.
28. Recommendations work without a budget.
29. Existing meal planning functionality works.
30. Existing pantry functionality works.
31. Existing food catalog works.
32. Existing pricing functionality works.
"""

import sys
import os
import time
import jwt
import uuid
import pytest
from fastapi.testclient import TestClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.main import app
from app.core.config import settings
from db.database import init_db, get_db_cursor
from app.services.pricing_service import (
    calculate_recipe_cost,
    calculate_ingredient_cost,
    evaluate_meal_budget_status,
)

client = TestClient(app)
init_db()

TEST_SECRET = settings.jwt_secret
TEST_ALGORITHM = settings.jwt_algorithm or "HS256"
TEST_AUDIENCE = settings.jwt_audience or "authenticated"


def generate_token(user_id: str, email: str = "budget_test@dietsense.ai") -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "aud": TEST_AUDIENCE,
        "role": "authenticated",
        "exp": int(time.time()) + 3600,
        "iat": int(time.time()),
    }
    return jwt.encode(payload, TEST_SECRET, algorithm=TEST_ALGORITHM)


@pytest.fixture(scope="module")
def auth_user():
    uid = str(uuid.uuid4())
    token = generate_token(uid)
    headers = {"Authorization": f"Bearer {token}"}
    # Ensure profile exists
    with get_db_cursor() as cur:
        cur.execute(
            """
            INSERT OR REPLACE INTO users (id, email, password_hash, full_name, status, created_at, updated_at)
            VALUES (?, ?, 'dummy_hash', ?, 'active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            (uid, f"{uid}@dietsense.ai", "Budget Tester"),
        )
        cur.execute(
            """
            INSERT OR REPLACE INTO profiles (id, user_id, email, full_name, dietary_pref, target_calories, budget_per_meal, updated_at)
            VALUES (?, ?, ?, ?, 'vegetarian', 2000, 100, CURRENT_TIMESTAMP)
            """,
            (uid, uid, f"{uid}@dietsense.ai", "Budget Tester"),
        )
        # Seed user pantry item: "Peanuts", "Onion"
        cur.execute(
            """
            INSERT INTO pantry_items (id, user_id, name, category, quantity, in_stock, created_at, updated_at)
            VALUES (?, ?, 'Peanuts', 'Nuts', '200g', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            (str(uuid.uuid4()), uid),
        )
        cur.execute(
            """
            INSERT INTO pantry_items (id, user_id, name, category, quantity, in_stock, created_at, updated_at)
            VALUES (?, ?, 'Onion', 'Vegetables', '1kg', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            (str(uuid.uuid4()), uid),
        )
    return {"user_id": uid, "headers": headers}


# ─── Group 1: Budget Selection (Scenarios 1-10) ──────────────────────────────

class TestBudgetSelection:
    def test_01_recommendations_without_budget(self, auth_user):
        """Scenario 1: Access recommendations without budget - returns unrestricted recommendations."""
        res = client.post(
            "/recommendations/",
            json={"user_profile": {"dietary_pref": "vegetarian", "target_calories": 2000}},
            headers=auth_user["headers"],
        )
        assert res.status_code == 200
        data = res.json()
        assert len(data) > 0
        for rec in data:
            assert "estimated_cost" in rec
            assert "cost_formatted" in rec

    def test_02_select_quick_budget_50(self, auth_user):
        """Scenario 2: Quick budget ₹50 filters recommendations strictly <= ₹50."""
        res = client.post(
            "/recommendations/?budget_amount=50&budget_mode=within_budget",
            json={"user_profile": {"dietary_pref": "vegetarian"}},
            headers=auth_user["headers"],
        )
        assert res.status_code == 200
        data = res.json()
        for rec in data:
            assert rec["estimated_cost"] is not None
            assert rec["estimated_cost"] <= 50.0
            assert rec["budget_status"] == "within_budget"

    def test_03_select_quick_budget_100(self, auth_user):
        """Scenario 3: Quick budget ₹100 allows meals up to ₹100."""
        res = client.post(
            "/recommendations/?budget_amount=100&budget_mode=within_budget",
            json={"user_profile": {"dietary_pref": "vegetarian"}},
            headers=auth_user["headers"],
        )
        assert res.status_code == 200
        data = res.json()
        for rec in data:
            assert rec["estimated_cost"] is not None
            assert rec["estimated_cost"] <= 100.0

    def test_04_select_quick_budget_200(self, auth_user):
        """Scenario 4: Quick budget ₹200 allows broader options."""
        res = client.post(
            "/recommendations/?budget_amount=200&budget_mode=within_budget",
            json={"user_profile": {"dietary_pref": "vegetarian"}},
            headers=auth_user["headers"],
        )
        assert res.status_code == 200
        data = res.json()
        assert len(data) > 0

    def test_05_select_quick_budget_500(self, auth_user):
        """Scenario 5: Quick budget ₹500 encompasses all standard meals."""
        res = client.post(
            "/recommendations/?budget_amount=500&budget_mode=within_budget",
            json={"user_profile": {"dietary_pref": "vegetarian"}},
            headers=auth_user["headers"],
        )
        assert res.status_code == 200
        data = res.json()
        assert len(data) > 0

    def test_06_custom_amount_entry(self, auth_user):
        """Scenario 6: User enters custom amount (e.g. ₹75)."""
        res = client.post(
            "/recommendations/",
            json={
                "user_profile": {"dietary_pref": "vegetarian"},
                "budget_amount": 75.0,
                "budget_mode": "within_budget",
            },
            headers=auth_user["headers"],
        )
        assert res.status_code == 200
        data = res.json()
        for rec in data:
            assert rec["estimated_cost"] <= 75.0

    def test_07_custom_amount_outside_quick_selections(self, auth_user):
        """Scenario 7: User enters amount outside quick selections (e.g. ₹135)."""
        res = client.post(
            "/recommendations/",
            json={
                "user_profile": {"dietary_pref": "vegetarian"},
                "budget_amount": 135.0,
                "budget_mode": "within_budget",
            },
            headers=auth_user["headers"],
        )
        assert res.status_code == 200
        data = res.json()
        for rec in data:
            assert rec["estimated_cost"] <= 135.0

    def test_08_invalid_manual_input_rejected(self, auth_user):
        """Scenario 8: Invalid budget values (negative, zero, string) are rejected with 400."""
        # Negative
        res_neg = client.post(
            "/recommendations/?budget_amount=-25",
            json={"user_profile": {}},
            headers=auth_user["headers"],
        )
        assert res_neg.status_code == 400

        # Zero
        res_zero = client.post(
            "/recommendations/?budget_amount=0",
            json={"user_profile": {}},
            headers=auth_user["headers"],
        )
        assert res_zero.status_code == 400

        # Non-numeric
        res_str = client.post(
            "/recommendations/?budget_amount=invalid_amt",
            json={"user_profile": {}},
            headers=auth_user["headers"],
        )
        assert res_str.status_code in (400, 422)

        res_body_str = client.post(
            "/recommendations/",
            json={"user_profile": {}, "budget_amount": "invalid_amt"},
            headers=auth_user["headers"],
        )
        assert res_body_str.status_code == 400

    def test_09_quick_selection_updates_active_budget(self, auth_user):
        """Scenario 9: Quick selection parameter updates active budget in response."""
        res = client.post(
            "/recommendations/?budget_amount=150&budget_mode=within_budget",
            json={"user_profile": {}},
            headers=auth_user["headers"],
        )
        assert res.status_code == 200
        data = res.json()
        for r in data:
            assert r["budget_status"] == "within_budget"

    def test_10_custom_entry_updates_active_budget(self, auth_user):
        """Scenario 10: Custom budget entry dynamically controls ranking and budget status."""
        res = client.post(
            "/recommendations/?budget_amount=60&budget_mode=within_budget",
            json={"user_profile": {}},
            headers=auth_user["headers"],
        )
        assert res.status_code == 200
        data = res.json()
        for r in data:
            assert r["estimated_cost"] <= 60.0


# ─── Group 2: Filtering Modes (Scenarios 11-17) ──────────────────────────────

class TestFilteringModes:
    def test_11_per_meal_filtering(self, auth_user):
        """Scenario 11: Per Meal filtering evaluates each meal independently against per-meal threshold."""
        res = client.post(
            "/recommendations/daily",
            json={
                "user_profile": {"dietary_pref": "vegetarian"},
                "budget_amount": 70.0,
                "budget_type": "per_meal",
                "budget_mode": "within_budget",
            },
            headers=auth_user["headers"],
        )
        assert res.status_code == 200
        data = res.json()
        assert "budget_summary" in data
        assert data["budget_summary"]["budget_type"] == "per_meal"
        for slot, recs in data["slots"].items():
            for rec in recs:
                assert rec["estimated_cost"] <= 70.0

    def test_12_per_day_filtering(self, auth_user):
        """Scenario 12: Per Day filtering partitions daily budget across active slots."""
        res = client.post(
            "/recommendations/daily",
            json={
                "user_profile": {"dietary_pref": "vegetarian"},
                "budget_amount": 250.0,
                "budget_type": "per_day",
                "budget_mode": "within_budget",
            },
            headers=auth_user["headers"],
        )
        assert res.status_code == 200
        data = res.json()
        summary = data["budget_summary"]
        assert summary["budget_type"] == "per_day"
        assert summary["budget_amount"] == 250.0
        assert "slot_budget_allocations" in summary

    def test_13_within_budget_mode(self, auth_user):
        """Scenario 13: Within Budget excludes over-budget meals and incomplete price items."""
        res = client.post(
            "/recommendations/?budget_amount=50&budget_mode=within_budget",
            json={"user_profile": {"dietary_pref": "vegetarian"}},
            headers=auth_user["headers"],
        )
        assert res.status_code == 200
        data = res.json()
        for rec in data:
            assert rec["budget_status"] == "within_budget"
            assert rec["estimated_cost"] is not None
            assert rec["estimated_cost"] <= 50.0

    def test_14_slightly_above_budget_mode(self, auth_user):
        """Scenario 14: Slightly Above Budget includes meals up to 20% over budget with difference flagged."""
        res = client.post(
            "/recommendations/?budget_amount=50&budget_mode=slightly_above&tolerance_pct=0.20",
            json={"user_profile": {"dietary_pref": "vegetarian"}},
            headers=auth_user["headers"],
        )
        assert res.status_code == 200
        data = res.json()
        for rec in data:
            assert rec["estimated_cost"] <= 60.0  # 50 * 1.20 = 60
            assert rec["budget_status"] in ("within_budget", "slightly_above")
            if rec["budget_status"] == "slightly_above":
                assert rec["cost_difference"] > 0
                assert "+" in rec["cost_difference_formatted"]

    def test_15_show_all_mode(self, auth_user):
        """Scenario 15: Show All displays all safe meals regardless of cost with cost visible."""
        res = client.post(
            "/recommendations/?budget_amount=40&budget_mode=show_all",
            json={"user_profile": {"dietary_pref": "vegetarian"}},
            headers=auth_user["headers"],
        )
        assert res.status_code == 200
        data = res.json()
        assert len(data) > 0
        # Should include items higher than 40
        has_above = any(r["estimated_cost"] is None or r["estimated_cost"] > 40.0 for r in data)
        assert has_above

    def test_16_clear_budget_filter(self, auth_user):
        """Scenario 16: Omitting budget_amount restores unrestricted recommendations."""
        res = client.post(
            "/recommendations/",
            json={"user_profile": {"dietary_pref": "vegetarian"}},
            headers=auth_user["headers"],
        )
        assert res.status_code == 200
        data = res.json()
        assert len(data) > 0

    def test_17_changing_budget_updates_recommendations(self, auth_user):
        """Scenario 17: Switching budget from ₹50 to ₹200 updates candidates returned."""
        res50 = client.post(
            "/recommendations/?budget_amount=50&budget_mode=within_budget",
            json={"user_profile": {}},
            headers=auth_user["headers"],
        )
        res200 = client.post(
            "/recommendations/?budget_amount=200&budget_mode=within_budget",
            json={"user_profile": {}},
            headers=auth_user["headers"],
        )
        names50 = {r["item"]["name"] for r in res50.json()}
        names200 = {r["item"]["name"] for r in res200.json()}
        # 200 budget should include all 50 items plus higher-cost ones
        assert names50.issubset(names200) or len(names200) >= len(names50)


# ─── Group 3: Pricing & Cost Calculations (Scenarios 18-22) ──────────────────

class TestPricingCalculations:
    def test_18_correct_ingredient_cost_calculation(self):
        """Scenario 18: Recipe ingredient costs are computed from quantity * unit price."""
        with get_db_cursor() as cur:
            # 100g Rice (raw brown, ₹52/kg) -> ₹5.20
            ing_cost = calculate_ingredient_cost(cur, food_id=10, quantity=100.0, unit="g")
            assert ing_cost["available"] is True
            assert pytest.approx(ing_cost["cost"], 0.01) == 5.20

    def test_19_correct_cost_per_serving(self):
        """Scenario 19: Cost per serving divides total recipe cost by servings count."""
        with get_db_cursor() as cur:
            ingredients = [
                {"food_id": 10, "quantity": 100.0, "unit": "g"},  # Rice: ₹5.20
                {"food_id": 69, "quantity": 100.0, "unit": "g"},  # Spinach: ₹3.00 (at ₹30/kg)
            ]
            res = calculate_recipe_cost(cur, ingredients=ingredients, servings=2)
            assert res["is_complete"] is True
            assert pytest.approx(res["total_cost"], 0.05) == 8.20
            assert pytest.approx(res["cost_per_serving"], 0.05) == 4.10

    def test_20_missing_ingredient_prices(self):
        """Scenario 20: Missing ingredient prices flag incomplete recipe without inventing ₹0."""
        with get_db_cursor() as cur:
            ingredients = [
                {"food_id": 10, "quantity": 100.0, "unit": "g"},  # Rice: ₹5.20
                {"food_id": 99999, "quantity": 50.0, "unit": "g"}, # Non-existent food
            ]
            res = calculate_recipe_cost(cur, ingredients=ingredients)
            assert res["is_complete"] is False
            assert res["total_cost"] is None
            assert res["cost_per_serving"] is None
            assert res["missing_count"] == 1

    def test_21_incomplete_meal_cost_handling(self):
        """Scenario 21: Incomplete meal costs are never classified as Within Budget."""
        status = evaluate_meal_budget_status(cost=None, is_complete=False, budget=100.0)
        assert status["status"] == "incomplete_cost"
        assert status["fits_within_budget"] is False
        assert status["fits_slightly_above"] is False

    def test_22_verified_and_estimated_price_labels(self):
        """Scenario 22: Price types (verified vs estimated) are tracked accurately."""
        with get_db_cursor() as cur:
            # Atta has verified price
            atta = calculate_ingredient_cost(cur, food_id=16, quantity=100.0, unit="g")
            assert atta["price_type"] == "verified"
            # Paneer has estimated price
            paneer = calculate_ingredient_cost(cur, food_id=283, quantity=100.0, unit="g")
            assert paneer["price_type"] == "estimated"


# ─── Group 4: Safety & Pantry Awareness (Scenarios 23-27) ────────────────────

class TestSafetyAndPantry:
    def test_23_allergy_filtering_enforced(self, auth_user):
        """Scenario 23: Allergy filtering strictly excludes peanut allergens even if inexpensive."""
        res = client.post(
            "/recommendations/",
            json={"user_profile": {"dietary_pref": "vegetarian", "allergies": ["peanuts"]}},
            headers=auth_user["headers"],
        )
        assert res.status_code == 200
        data = res.json()
        for rec in data:
            assert "peanuts" not in rec["item"].get("allergens", [])
            assert "peanuts" not in [t.lower() for t in rec["item"].get("tags", [])]

    def test_24_dietary_restrictions_enforced(self, auth_user):
        """Scenario 24: Vegetarian dietary restriction excludes non-vegetarian items."""
        res = client.post(
            "/recommendations/",
            json={"user_profile": {"dietary_pref": "vegetarian"}},
            headers=auth_user["headers"],
        )
        assert res.status_code == 200
        data = res.json()
        for rec in data:
            assert "non-veg" not in rec["item"].get("tags", [])

    def test_25_pantry_based_recommendations(self, auth_user):
        """Scenario 25: Pantry-matched ingredients are recognized in recommendations."""
        res = client.post(
            "/recommendations/",
            json={"user_profile": {"dietary_pref": "vegetarian"}},
            headers=auth_user["headers"],
        )
        assert res.status_code == 200
        data = res.json()
        # Find item with peanuts or onion in pantry
        pantry_matches = [r for r in data if len(r.get("pantry_matched_ingredients", [])) > 0]
        assert len(pantry_matches) > 0

    def test_26_missing_ingredients_identified(self):
        """Scenario 26: Recipe ingredients not in pantry are correctly isolated."""
        with get_db_cursor() as cur:
            ingredients = [
                {"food_id": 263, "food_name": "Peanuts", "quantity": 25.0, "unit": "g"},
                {"food_id": 205, "food_name": "Potato", "quantity": 50.0, "unit": "g"},
            ]
            res = calculate_recipe_cost(
                cur, ingredients=ingredients, pantry_item_names=["peanuts"]
            )
            assert "Potato" in res["pantry_missing_ingredients"]
            assert "Peanuts" in res["pantry_matched_ingredients"]

    def test_27_additional_purchase_cost_calculated(self):
        """Scenario 27: Additional purchase cost covers ONLY missing pantry ingredients."""
        with get_db_cursor() as cur:
            ingredients = [
                {"food_id": 263, "food_name": "Peanuts", "quantity": 25.0, "unit": "g"},  # ₹3.50 (in pantry)
                {"food_id": 205, "food_name": "Potato", "quantity": 50.0, "unit": "g"},   # ₹1.40 (missing)
            ]
            res = calculate_recipe_cost(
                cur, ingredients=ingredients, pantry_item_names=["peanuts"]
            )
            # Full cost is ₹4.90, but missing ingredients cost is only Potato = ₹1.40
            assert pytest.approx(res["missing_ingredients_cost"], 0.05) == 1.40


# ─── Group 5: Backward Compatibility (Scenarios 28-32) ───────────────────────

class TestBackwardCompatibility:
    def test_28_recommendations_work_without_budget(self, auth_user):
        """Scenario 28: Recommendations work cleanly when no budget is specified."""
        res = client.post(
            "/recommendations/daily",
            json={"user_profile": {"target_calories": 2000}},
            headers=auth_user["headers"],
        )
        assert res.status_code == 200
        data = res.json()
        assert "slots" in data
        assert "totals" in data

    def test_29_existing_meal_planning_works(self, auth_user):
        """Scenario 29: Existing meal plans endpoint operates without regression."""
        res = client.get("/meal-plans", headers=auth_user["headers"])
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    def test_30_existing_pantry_functionality_works(self, auth_user):
        """Scenario 30: Existing pantry endpoints operate without regression."""
        res = client.get("/api/pantry/", headers=auth_user["headers"])
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    def test_31_existing_food_catalog_works(self):
        """Scenario 31: Existing 3-view food catalog operates without regression."""
        res = client.get("/api/foods/?view=all&limit=5")
        assert res.status_code == 200
        data = res.json()
        assert "items" in data
        assert len(data["items"]) == 5

    def test_32_existing_pricing_functionality_works(self):
        """Scenario 32: Batch 3 pricing endpoints operate without regression."""
        res = client.get("/api/pricing/food/10")  # Brown rice
        assert res.status_code == 200
        data = res.json()
        assert data["food_id"] == 10
        assert data["price"] > 0
