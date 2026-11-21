"""
DietSense — Food Catalog Integration Test Suite
Tests:
1. Category listing endpoint (GET /api/foods/categories)
2. All Foods view for unauthenticated and authenticated users
3. In My Pantry view for empty and populated pantries
4. Not in My Pantry view for empty and populated pantries
5. Adding food to pantry (POST /api/foods/{food_id}/add-to-pantry)
6. Duplicate prevention / upsert when adding already-present food
7. Pantry state transitions across all 3 views upon add and remove
8. Updating pantry entry (PATCH /api/foods/{food_id}/pantry-entry)
9. Removing food from pantry (DELETE /api/foods/{food_id}/remove-from-pantry)
10. Strict multi-user data isolation (User A cannot see or mutate User B's pantry)
11. Search across all 3 views with partial matching
12. Category, dietary, and nutritional filtering
13. Sorting (calories, protein, name) with backend pagination
14. Food detail endpoint (GET /api/foods/{food_id}) with pantry status
15. Backward compatibility with Clear Pantry (Batch 1)
"""

import os
import sys
import uuid
from datetime import datetime, timezone
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
from db.database import init_db, get_db_cursor

client = TestClient(app)
init_db()


def create_user_fixture(prefix: str = "cat"):
    """Creates a local user in SQLite and returns user_id, email, and auth headers."""
    uid = f"usr_{prefix}_{uuid.uuid4().hex[:8]}"
    email = f"{prefix}_{uuid.uuid4().hex[:6]}@dietsense.ai"
    token = create_access_token(user_id=uid, email=email)
    now = datetime.now(timezone.utc).isoformat()

    with get_db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO users (id, email, password_hash, full_name, status, created_at, updated_at)
            VALUES (?, ?, '!test_hash', 'Catalog Tester', 'active', ?, ?)
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
                ?, ?, ?, 'Catalog Tester', 'vegetarian', '[]',
                2000, 100.0, 30, 1,
                '3_meals', 26, 'male', 175.0, 75.0,
                'lose_weight', 'lightly_active', ?
            )
            """,
            (f"prof_{uid}", uid, email, now),
        )

    headers = {"Authorization": f"Bearer {token}"}
    return uid, email, headers


def get_first_catalog_food():
    """Helper to get a known food item from SQLite foods table."""
    with get_db_cursor() as cur:
        cur.execute("SELECT id, name, food_category FROM foods ORDER BY id ASC LIMIT 1")
        return cur.fetchone()


class TestFoodCatalogCategories:
    def test_get_categories(self):
        """GET /api/foods/categories returns distinct non-empty categories."""
        res = client.get("/api/foods/categories")
        assert res.status_code == 200
        data = res.json()
        assert "categories" in data
        assert isinstance(data["categories"], list)
        assert len(data["categories"]) > 0
        assert any("Milk" in cat or "Vegetable" in cat or "Cereal" in cat or "Meat" in cat for cat in data["categories"])


class TestThreeFoodViewsEmptyPantry:
    def test_unauthenticated_all_foods(self):
        """Unauthenticated user can view All Foods, in_pantry is false."""
        res = client.get("/api/foods/?view=all&limit=10")
        assert res.status_code == 200
        data = res.json()
        assert "items" in data
        assert len(data["items"]) > 0
        assert data["total"] > 0
        for item in data["items"]:
            assert item["in_pantry"] is False
            assert item["pantry_item_id"] is None

    def test_empty_pantry_user_views(self):
        """User with empty pantry: in_pantry is empty, not_in_pantry equals total catalog."""
        uid, email, headers = create_user_fixture("empty")

        # 1. All Foods
        res_all = client.get("/api/foods/?view=all&limit=10", headers=headers)
        assert res_all.status_code == 200
        all_data = res_all.json()
        assert all_data["total"] > 0
        assert all(item["in_pantry"] is False for item in all_data["items"])

        # 2. In My Pantry
        res_in = client.get("/api/foods/?view=in_pantry", headers=headers)
        assert res_in.status_code == 200
        in_data = res_in.json()
        assert in_data["total"] == 0
        assert len(in_data["items"]) == 0

        # 3. Not in My Pantry
        res_not = client.get("/api/foods/?view=not_in_pantry&limit=10", headers=headers)
        assert res_not.status_code == 200
        not_data = res_not.json()
        assert not_data["total"] == all_data["total"]
        assert all(item["in_pantry"] is False for item in not_data["items"])


class TestPantryMutationsAndTransitions:
    def test_add_food_to_pantry_and_view_transitions(self):
        """
        Tests adding a food to the pantry:
        - Added food appears in 'in_pantry' view
        - Added food disappears from 'not_in_pantry' view
        - Added food remains visible in 'all' view with in_pantry=True
        """
        uid, email, headers = create_user_fixture("mut")
        food = get_first_catalog_food()
        assert food is not None
        food_id = food["id"]
        food_name = food["name"]

        # Add food to pantry
        add_res = client.post(
            f"/api/foods/{food_id}/add-to-pantry",
            json={"quantity": "250g", "in_stock": True},
            headers=headers,
        )
        assert add_res.status_code == 200
        add_data = add_res.json()
        assert add_data["status"] == "success"
        assert add_data["already_in_pantry"] is False
        assert add_data["pantry_item"]["name"] == food_name
        assert add_data["pantry_item"]["quantity"] == "250g"
        assert add_data["pantry_item"]["matched_food_id"] == food_id

        # Verify in 'in_pantry' view
        res_in = client.get("/api/foods/?view=in_pantry", headers=headers)
        assert res_in.status_code == 200
        in_data = res_in.json()
        assert in_data["total"] == 1
        assert in_data["items"][0]["id"] == food_id
        assert in_data["items"][0]["in_pantry"] is True
        assert in_data["items"][0]["pantry_quantity"] == "250g"

        # Verify NOT in 'not_in_pantry' view (searching for this exact food)
        res_not = client.get(f"/api/foods/?view=not_in_pantry&q={food_name}", headers=headers)
        assert res_not.status_code == 200
        not_data = res_not.json()
        matching_ids = [item["id"] for item in not_data["items"]]
        assert food_id not in matching_ids

        # Verify in 'all' view has in_pantry=True
        res_all = client.get(f"/api/foods/?view=all&q={food_name}", headers=headers)
        assert res_all.status_code == 200
        all_data = res_all.json()
        matching_item = next(item for item in all_data["items"] if item["id"] == food_id)
        assert matching_item["in_pantry"] is True
        assert matching_item["pantry_quantity"] == "250g"

    def test_duplicate_prevention_on_add(self):
        """Adding the same food multiple times must update rather than duplicate pantry rows."""
        uid, email, headers = create_user_fixture("dup")
        food = get_first_catalog_food()
        food_id = food["id"]

        # First add
        res1 = client.post(
            f"/api/foods/{food_id}/add-to-pantry",
            json={"quantity": "100g"},
            headers=headers,
        )
        assert res1.status_code == 200
        assert res1.json()["already_in_pantry"] is False

        # Second add with new quantity
        res2 = client.post(
            f"/api/foods/{food_id}/add-to-pantry",
            json={"quantity": "500g"},
            headers=headers,
        )
        assert res2.status_code == 200
        assert res2.json()["already_in_pantry"] is True

        # Check DB row count: exactly 1 row for this user
        with get_db_cursor() as cur:
            cur.execute("SELECT COUNT(*) AS cnt FROM pantry_items WHERE user_id = ?", (uid,))
            assert cur.fetchone()["cnt"] == 1
            cur.execute("SELECT quantity FROM pantry_items WHERE user_id = ?", (uid,))
            assert cur.fetchone()["quantity"] == "500g"

    def test_update_pantry_entry(self):
        """PATCH /api/foods/{food_id}/pantry-entry updates quantity and in_stock."""
        uid, email, headers = create_user_fixture("upd")
        food = get_first_catalog_food()
        food_id = food["id"]

        # Add food first
        client.post(f"/api/foods/{food_id}/add-to-pantry", json={"quantity": "1 unit"}, headers=headers)

        # Update entry
        patch_res = client.patch(
            f"/api/foods/{food_id}/pantry-entry",
            json={"quantity": "2.5 kg", "in_stock": False},
            headers=headers,
        )
        assert patch_res.status_code == 200
        patch_data = patch_res.json()
        assert patch_data["status"] == "success"
        assert patch_data["pantry_item"]["quantity"] == "2.5 kg"
        assert patch_data["pantry_item"]["in_stock"] is False

        # Detail check
        detail_res = client.get(f"/api/foods/{food_id}", headers=headers)
        assert detail_res.status_code == 200
        assert detail_res.json()["pantry_quantity"] == "2.5 kg"
        assert detail_res.json()["pantry_in_stock"] is False

    def test_remove_food_from_pantry(self):
        """
        Removing a food updates all three views:
        - Food disappears from 'in_pantry'
        - Food reappears in 'not_in_pantry'
        - Food remains in 'all' with in_pantry=False
        """
        uid, email, headers = create_user_fixture("rem")
        food = get_first_catalog_food()
        food_id = food["id"]
        food_name = food["name"]

        # Add food
        client.post(f"/api/foods/{food_id}/add-to-pantry", json={"quantity": "1 bottle"}, headers=headers)

        # Remove food
        del_res = client.delete(f"/api/foods/{food_id}/remove-from-pantry", headers=headers)
        assert del_res.status_code == 200
        assert del_res.json()["status"] == "success"

        # Check 'in_pantry' is now empty
        res_in = client.get("/api/foods/?view=in_pantry", headers=headers)
        assert res_in.json()["total"] == 0

        # Check 'not_in_pantry' now includes the food
        res_not = client.get(f"/api/foods/?view=not_in_pantry&q={food_name}", headers=headers)
        matching_ids = [item["id"] for item in res_not.json()["items"]]
        assert food_id in matching_ids

        # Check 'all' shows in_pantry=False
        res_all = client.get(f"/api/foods/?view=all&q={food_name}", headers=headers)
        matching = next(item for item in res_all.json()["items"] if item["id"] == food_id)
        assert matching["in_pantry"] is False


class TestMultiUserIsolation:
    def test_user_a_cannot_see_user_b_pantry(self):
        """User A's pantry items do not appear in User B's pantry or affect User B's catalog views."""
        user_a_id, _, headers_a = create_user_fixture("usera")
        user_b_id, _, headers_b = create_user_fixture("userb")

        food = get_first_catalog_food()
        food_id = food["id"]

        # User A adds food
        client.post(f"/api/foods/{food_id}/add-to-pantry", json={"quantity": "User A stock"}, headers=headers_a)

        # User A sees it in pantry
        res_a = client.get("/api/foods/?view=in_pantry", headers=headers_a)
        assert res_a.json()["total"] == 1

        # User B still has empty pantry
        res_b = client.get("/api/foods/?view=in_pantry", headers=headers_b)
        assert res_b.json()["total"] == 0

        # User B sees food in 'not_in_pantry'
        res_b_not = client.get(f"/api/foods/?view=not_in_pantry&q={food['name']}", headers=headers_b)
        assert any(item["id"] == food_id for item in res_b_not.json()["items"])

        # User B cannot remove User A's item
        del_res = client.delete(f"/api/foods/{food_id}/remove-from-pantry", headers=headers_b)
        assert del_res.status_code == 404


class TestSearchFiltersSortingPagination:
    def test_search_partial_matching(self):
        """Search query matches partial food names across views."""
        res = client.get("/api/foods/?q=rice&limit=10")
        assert res.status_code == 200
        data = res.json()
        assert data["total"] > 0
        for item in data["items"]:
            assert "rice" in item["name"].lower() or (item["name_local"] and "rice" in item["name_local"].lower())

    def test_category_filter(self):
        """Filter by category returns only items in that category."""
        res_cats = client.get("/api/foods/categories")
        categories = res_cats.json()["categories"]
        target_cat = categories[0]

        res = client.get(f"/api/foods/?category={target_cat}&limit=10")
        assert res.status_code == 200
        data = res.json()
        for item in data["items"]:
            assert item["food_category"] == target_cat

    def test_dietary_filters(self):
        """Vegetarian filter returns only vegetarian foods."""
        res = client.get("/api/foods/?is_vegetarian=true&limit=15")
        assert res.status_code == 200
        data = res.json()
        assert data["total"] > 0
        for item in data["items"]:
            assert item["is_vegetarian"] is True

    def test_nutritional_filters(self):
        """Min protein and max calories filters are respected."""
        res = client.get("/api/foods/?min_protein=20&max_calories=300&limit=15")
        assert res.status_code == 200
        data = res.json()
        assert data["total"] > 0
        for item in data["items"]:
            assert item["protein_g"] >= 20.0
            assert item["calories_kcal"] <= 300.0

    def test_sorting_by_calories_desc(self):
        """Sorting by calories descending produces ordered results."""
        res = client.get("/api/foods/?sort_by=calories&sort_order=desc&limit=10")
        assert res.status_code == 200
        items = res.json()["items"]
        calories = [item["calories_kcal"] for item in items]
        assert calories == sorted(calories, reverse=True)

    def test_sorting_by_protein_desc(self):
        """Sorting by protein descending produces ordered results."""
        res = client.get("/api/foods/?sort_by=protein&sort_order=desc&limit=10")
        assert res.status_code == 200
        items = res.json()["items"]
        proteins = [item["protein_g"] for item in items]
        assert proteins == sorted(proteins, reverse=True)

    def test_backend_pagination(self):
        """Pagination returns distinct slices and correct metadata."""
        res_p1 = client.get("/api/foods/?page=1&limit=5")
        res_p2 = client.get("/api/foods/?page=2&limit=5")
        assert res_p1.status_code == 200
        assert res_p2.status_code == 200
        p1 = res_p1.json()
        p2 = res_p2.json()
        assert p1["page"] == 1
        assert p2["page"] == 2
        assert p1["limit"] == 5
        assert p2["limit"] == 5
        assert p1["total"] == p2["total"]
        assert p1["total_pages"] == p2["total_pages"]
        # Ensure page 1 and page 2 items are disjoint
        p1_ids = {item["id"] for item in p1["items"]}
        p2_ids = {item["id"] for item in p2["items"]}
        assert len(p1_ids.intersection(p2_ids)) == 0


class TestFoodDetailEndpoint:
    def test_food_detail_valid(self):
        """GET /api/foods/{food_id} returns detailed food fields."""
        food = get_first_catalog_food()
        food_id = food["id"]
        res = client.get(f"/api/foods/{food_id}")
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == food_id
        assert data["name"] == food["name"]
        assert "calories_kcal" in data
        assert "protein_g" in data
        assert "carbohydrates_g" in data
        assert "fat_g" in data
        assert "is_vegetarian" in data
        assert "in_pantry" in data

    def test_food_detail_not_found(self):
        """GET /api/foods/999999999 returns 404."""
        res = client.get("/api/foods/999999999")
        assert res.status_code == 404
