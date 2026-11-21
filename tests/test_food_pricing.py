"""
DietSense — Indian Food Pricing & Unit Conversion Test Suite
Tests:
1. Food with a verified price (DoCA / NECC / Agmarknet)
2. Food with an estimated price (Retail Market Index)
3. Food with no available price ('Price unavailable', never ₹0)
4. Multiple regional prices for one food (Delhi, Mumbai, Bengaluru, National)
5. Price per kg conversion (to gram and 100g)
6. Price per 100g conversion (to gram)
7. Price per litre conversion (to ml)
8. Price per dozen conversion (to piece, and piece to dozen)
9. Unsupported unit conversions (cross-dimension weight <-> volume <-> count returns None)
10. Recipe with all ingredient prices available (is_complete=True, total_cost, cost_per_serving)
11. Recipe with one or more missing ingredient prices (is_complete=False, total_cost=None, missing_ingredients list)
12. Price updates without modifying nutrition records (foods table untouched)
13. Food catalog endpoints (list_foods and get_food_detail) returning enriched pricing metadata
14. Backward compatibility with existing pantry and food catalog functionality
"""

import os
import sys
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
from app.services.pricing_service import (
    convert_units,
    convert_price,
    format_inr,
    get_unit_dimension,
)
from db.database import init_db, get_db_cursor

client = TestClient(app)
init_db()


# ─── Unit Conversion & Formatting Unit Tests ──────────────────────────────────

class TestUnitConversionsAndFormatting:
    def test_price_per_kg_conversions(self):
        """Price per kg correctly converts to price per gram and price per 100g."""
        # ₹40/kg:
        # 1g should cost ₹0.04
        # 100g should cost ₹4.00
        p_per_g = convert_price(40.0, "kg", "g")
        assert p_per_g is not None
        assert pytest.approx(p_per_g, 0.0001) == 0.04

        p_per_100g = convert_price(40.0, "kg", "100g")
        assert p_per_100g is not None
        assert pytest.approx(p_per_100g, 0.01) == 4.0

    def test_price_per_100g_conversions(self):
        """Price per 100g correctly converts to price per gram and price per kg."""
        # ₹25/100g:
        # 1g should cost ₹0.25
        # 1kg should cost ₹250.00
        p_per_g = convert_price(25.0, "100g", "g")
        assert p_per_g is not None
        assert pytest.approx(p_per_g, 0.001) == 0.25

        p_per_kg = convert_price(25.0, "100g", "kg")
        assert p_per_kg is not None
        assert pytest.approx(p_per_kg, 0.01) == 250.0

    def test_price_per_litre_conversions(self):
        """Price per litre correctly converts to price per ml."""
        # ₹60/litre:
        # 1ml should cost ₹0.06
        p_per_ml = convert_price(60.0, "litre", "ml")
        assert p_per_ml is not None
        assert pytest.approx(p_per_ml, 0.0001) == 0.06

        # 250ml should cost 250 * 0.06 = ₹15.00
        qty_in_l = convert_units(250.0, "ml", "litre")
        assert qty_in_l is not None
        assert pytest.approx(qty_in_l, 0.001) == 0.25

    def test_price_per_dozen_conversions(self):
        """Price per dozen correctly converts to price per piece, and piece to dozen."""
        # ₹84/dozen:
        # 1 piece should cost ₹7.00
        p_per_pc = convert_price(84.0, "dozen", "piece")
        assert p_per_pc is not None
        assert pytest.approx(p_per_pc, 0.01) == 7.0

        # ₹7/piece to dozen:
        p_per_doz = convert_price(7.0, "piece", "dozen")
        assert p_per_doz is not None
        assert pytest.approx(p_per_doz, 0.01) == 84.0

    def test_unsupported_cross_dimension_conversions(self):
        """Cross-dimensional conversions without verified density must return None."""
        # Weight to Volume: kg to litre
        assert convert_units(1.0, "kg", "litre") is None
        assert convert_price(40.0, "kg", "litre") is None

        # Count to Weight: dozen to kg
        assert convert_units(1.0, "dozen", "kg") is None
        assert convert_price(84.0, "dozen", "kg") is None

        # Volume to Weight: ml to grams
        assert convert_units(500.0, "ml", "g") is None
        assert convert_price(60.0, "litre", "g") is None

    def test_inr_formatting_rules(self):
        """INR currency formatting follows DietSense rules: clean values, never ₹0 for missing."""
        assert format_inr(40.0, "kg") == "₹40/kg"
        assert format_inr(25.50, "100g") == "₹25.50/100g"
        assert format_inr(60.0, "litre") == "₹60/litre"
        assert format_inr(7.0, "piece") == "₹7/piece"
        assert format_inr(84.0, "dozen") == "₹84/dozen"
        assert format_inr(None, "kg") == "Price unavailable"
        assert format_inr(0.0, "kg") == "Price unavailable"
        assert format_inr(-10.0, "kg") == "Price unavailable"


# ─── Food Price Record Verification ──────────────────────────────────────────

class TestFoodPriceRecords:
    def test_food_with_verified_price(self):
        """Wheat flour (Atta, id: 16) has a verified price from DoCA."""
        res = client.get("/api/pricing/food/16?region=National")
        assert res.status_code == 200
        data = res.json()
        assert data["available"] is True
        assert data["price"] == 36.0
        assert data["unit"] == "kg"
        assert data["currency"] == "INR"
        assert data["price_type"] == "verified"
        assert "DoCA" in data["source"] or "Department of Consumer Affairs" in data["source"]
        assert data["price_formatted"] == "₹36/kg"

    def test_food_with_estimated_price(self):
        """Paneer (id: 283) has an estimated price labeled accurately."""
        res = client.get("/api/pricing/food/283?region=National")
        assert res.status_code == 200
        data = res.json()
        assert data["available"] is True
        assert data["price_type"] == "estimated"
        assert data["price"] == 420.0
        assert data["unit"] == "kg"
        assert data["price_formatted"] == "₹420/kg"
        assert "Retail" in data["source"]

    def test_food_with_no_available_price(self):
        """Foods without pricing data return available=False and 'Price unavailable', not ₹0."""
        # Find a USDA food without seeded price (e.g. exotic seafood or seal oil, id: 587)
        res = client.get("/api/pricing/food/587")
        assert res.status_code == 200
        data = res.json()
        assert data["available"] is False
        assert data["price"] is None
        assert data["price_formatted"] == "Price unavailable"

    def test_multiple_regional_prices(self):
        """Food with multiple regional prices returns distinct prices per region and lists options."""
        # Atta (id: 16) has Delhi, Mumbai, Bengaluru, Kolkata, and National prices
        res_del = client.get("/api/pricing/food/16?region=Delhi")
        res_mum = client.get("/api/pricing/food/16?region=Mumbai")
        res_blr = client.get("/api/pricing/food/16?region=Bengaluru")

        assert res_del.status_code == 200
        assert res_mum.status_code == 200
        assert res_blr.status_code == 200

        data_del = res_del.json()
        data_mum = res_mum.json()
        data_blr = res_blr.json()

        assert data_del["region"] == "Delhi"
        assert data_del["price"] == 35.0

        assert data_mum["region"] == "Mumbai"
        assert data_mum["price"] == 38.0

        assert data_blr["region"] == "Bengaluru"
        assert data_blr["price"] == 40.0

        # Check regional_options list
        assert len(data_del["regional_options"]) >= 4
        regions = [r["region"] for r in data_del["regional_options"]]
        assert "Delhi" in regions
        assert "Mumbai" in regions
        assert "National" in regions

    def test_list_pricing_regions(self):
        """GET /api/pricing/regions returns all distinct regions with National listed first."""
        res = client.get("/api/pricing/regions")
        assert res.status_code == 200
        data = res.json()
        assert "regions" in data
        assert "National" in data["regions"]
        assert "Delhi" in data["regions"]
        assert "Mumbai" in data["regions"]
        assert data["regions"][0] == "National"


# ─── Ingredient & Recipe Cost Foundation ──────────────────────────────────────

class TestRecipeAndIngredientCostFoundation:
    def test_ingredient_cost_calculation(self):
        """Ingredient cost calculated accurately with unit conversion."""
        # 500g of Atta (food_id: 16, ₹36/kg in National):
        # 500g = 0.5kg -> 0.5 * 36 = ₹18.00
        payload = {
            "ingredients": [
                {"food_id": 16, "quantity": 500, "unit": "g"},
                {"food_id": 282, "quantity": 250, "unit": "ml"},  # Cow milk (₹58/l -> 250ml = ₹14.50)
                {"food_id": 284, "quantity": 2, "unit": "piece"},  # Eggs (₹7/pc -> 2 pcs = ₹14.00)
            ],
            "region": "National",
        }
        res = client.post("/api/pricing/calculate-ingredients", json=payload)
        assert res.status_code == 200
        data = res.json()

        assert data["is_complete"] is True
        assert data["available_items_count"] == 3
        assert data["missing_items_count"] == 0

        atta_res = data["ingredients"][0]
        assert atta_res["available"] is True
        assert atta_res["cost"] == 18.0

        milk_res = data["ingredients"][1]
        assert milk_res["available"] is True
        assert milk_res["cost"] == 14.5

        egg_res = data["ingredients"][2]
        assert egg_res["available"] is True
        assert egg_res["cost"] == 14.0

        # Total = 18.0 + 14.5 + 14.0 = ₹46.50
        assert data["total_cost"] == 46.50

    def test_recipe_with_all_ingredient_prices_available(self):
        """Recipe with all valid prices returns is_complete=True, total_cost, and cost_per_serving."""
        payload = {
            "recipe_name": "Paneer Bhurji with Roti",
            "servings": 2,
            "region": "National",
            "ingredients": [
                {"food_id": 283, "quantity": 200, "unit": "g"},  # Paneer (₹420/kg -> 200g = ₹84.00)
                {"food_id": 235, "quantity": 100, "unit": "g"},  # Onion (₹32/kg -> 100g = ₹3.20)
                {"food_id": 131, "quantity": 100, "unit": "g"},  # Tomato (₹38/kg -> 100g = ₹3.80)
                {"food_id": 16, "quantity": 150, "unit": "g"},   # Atta (₹36/kg -> 150g = ₹5.40)
            ],
        }
        res = client.post("/api/pricing/recipe-cost", json=payload)
        assert res.status_code == 200
        data = res.json()

        assert data["is_complete"] is True
        assert data["missing_count"] == 0
        assert len(data["missing_ingredients"]) == 0

        # Expected total: 84.0 + 3.20 + 3.80 + 5.40 = 96.40
        assert data["total_cost"] == 96.40
        assert data["total_cost_formatted"] == "₹96.40"
        # 2 servings -> 96.40 / 2 = 48.20 per serving
        assert data["cost_per_serving"] == 48.20
        assert data["cost_per_serving_formatted"] == "₹48.20"

    def test_recipe_with_missing_ingredient_price(self):
        """Recipe with missing ingredient price returns is_complete=False and does NOT output misleading total."""
        payload = {
            "recipe_name": "Seafood Special with Unknown Herb",
            "servings": 1,
            "region": "National",
            "ingredients": [
                {"food_id": 16, "quantity": 100, "unit": "g"},     # Atta: ₹3.60
                {"food_id": 587, "quantity": 50, "unit": "g"},      # Seal oil: NO PRICE
            ],
        }
        res = client.post("/api/pricing/recipe-cost", json=payload)
        assert res.status_code == 200
        data = res.json()

        assert data["is_complete"] is False
        assert data["total_cost"] is None  # Total is strictly None to prevent misleading financial totals!
        assert "incomplete" in data["total_cost_formatted"].lower()
        assert data["cost_per_serving"] is None
        assert data["missing_count"] == 1
        assert len(data["missing_ingredients"]) == 1
        assert data["partial_cost"] == 3.60

    def test_recipe_with_unsupported_unit_conversion(self):
        """Recipe with incompatible unit conversion (e.g. litres of atta) flags as missing."""
        payload = {
            "recipe_name": "Incompatible Units Test",
            "servings": 1,
            "region": "National",
            "ingredients": [
                {"food_id": 16, "quantity": 2, "unit": "litre"},  # Atta is priced in kg, litre is incompatible!
            ],
        }
        res = client.post("/api/pricing/recipe-cost", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["is_complete"] is False
        assert data["ingredients"][0]["available"] is False
        assert "cannot convert" in data["ingredients"][0]["reason"].lower()


# ─── Price Mutations & Catalog Integrity ──────────────────────────────────────

class TestPriceMutationsAndCatalogIntegrity:
    def test_price_record_addition_does_not_modify_nutrition(self):
        """Adding or updating price records must NEVER modify the foods table nutrition data."""
        target_food_id = 16  # Atta

        # 1. Fetch nutrition baseline
        with get_db_cursor() as cur:
            cur.execute("SELECT calories_kcal, protein_g, carbohydrates_g, fat_g FROM foods WHERE id = ?", (target_food_id,))
            baseline_nutrition = dict(cur.fetchone())

        # 2. Add a new custom regional price record
        post_res = client.post(
            "/api/pricing/record",
            json={
                "food_id": target_food_id,
                "price": 45.0,
                "currency": "INR",
                "unit": "kg",
                "region": "Jaipur",
                "source": "Rajasthan State Mandi Board",
                "price_type": "verified",
                "last_updated": "2026-05-18",
            },
        )
        assert post_res.status_code == 200

        # 3. Verify price appears for Jaipur
        check_res = client.get(f"/api/pricing/food/{target_food_id}?region=Jaipur")
        assert check_res.status_code == 200
        assert check_res.json()["price"] == 45.0
        assert check_res.json()["region"] == "Jaipur"

        # 4. Verify nutrition record in foods table is 100% IDENTICAL
        with get_db_cursor() as cur:
            cur.execute("SELECT calories_kcal, protein_g, carbohydrates_g, fat_g FROM foods WHERE id = ?", (target_food_id,))
            after_nutrition = dict(cur.fetchone())

        assert baseline_nutrition == after_nutrition


# ─── Food Catalog Pricing Integration ─────────────────────────────────────────

class TestCatalogViewsPricingIntegration:
    def test_all_foods_view_includes_pricing(self):
        """GET /api/foods/?view=all returns items annotated with pricing."""
        res = client.get("/api/foods/?view=all&limit=24")
        assert res.status_code == 200
        data = res.json()
        assert len(data["items"]) > 0

        # At least some items (like Atta, Rice, Milk, Egg) have prices
        priced_items = [i for i in data["items"] if i["price"] is not None]
        assert len(priced_items) > 0

        for item in data["items"]:
            assert "price" in item
            assert "price_formatted" in item
            assert "price_type" in item
            if item["price"] is not None:
                assert item["price"] > 0
                assert "₹" in item["price_formatted"]
                assert item["price_type"] in ("verified", "estimated")
            else:
                assert item["price_formatted"] == "Price unavailable"

    def test_food_detail_endpoint_pricing(self):
        """GET /api/foods/{food_id} returns primary price and all regional prices."""
        res = client.get("/api/foods/16")
        assert res.status_code == 200
        data = res.json()
        assert data["price"] == 36.0
        assert data["price_formatted"] == "₹36/kg"
        assert data["price_type"] == "verified"
        assert "prices" in data
        assert len(data["prices"]) >= 4

    def test_direct_food_price_endpoints(self):
        """GET /api/foods/{food_id}/price and /prices return correct records."""
        res_price = client.get("/api/foods/16/price?region=Delhi")
        assert res_price.status_code == 200
        assert res_price.json()["price"] == 35.0
        assert res_price.json()["region"] == "Delhi"

        res_prices = client.get("/api/foods/16/prices")
        assert res_prices.status_code == 200
        assert res_prices.json()["count"] >= 4
