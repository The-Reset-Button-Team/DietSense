"""
DietSense — Recommendation Routes
Wraps the ML recommendation engine to serve filtered and ranked meal plans.
Enforces that user_id is derived exclusively from verified JWT, never from request body.
Integrates directly with local SQLite food catalog and meal logs.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List, Optional
import os
import sqlite3
import json
import math

from app.core.config import settings
from app.core.dependencies import get_current_user
from routes.meal_logs import get_user_meal_logs
from ml.recommendation.recommender import recommend
from ml.scoring.safety_gate import audit_safe, filter_safe
from db.database import get_db_cursor
from app.services.pricing_service import calculate_recipe_cost, evaluate_meal_budget_status

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

# ---------------------------------------------------------------------------
# SAMPLE_CANDIDATES — kept as emergency fallback if the SQLite DB is missing
# or unreadable. The primary source is the full foods catalog (load_candidate_foods).
# Enriched with realistic recipe ingredients linking to verified Indian food prices.
# ---------------------------------------------------------------------------
SAMPLE_CANDIDATES = [
    {
        "id": 1,
        "name": "Vegetable Poha with Peanuts",
        "tags": ["veg", "breakfast", "quick", "indian", "light"],
        "allergens": ["peanuts"],
        "cuisine": "indian",
        "cost_estimate": 40,
        "prep_time": 15,
        "calories": 350,
        "protein_g": 8.5,
        "carbs_g": 55.0,
        "fat_g": 9.0,
        "fiber_g": 3.5,
        "sodium_mg": 260.0,
        "calcium_mg": 45.0,
        "iron_mg": 2.1,
        "food_category": "Cereals and Millets",
        "data_source": "ICMR_NIN",
        "ingredients": [
            {"food_id": 12, "food_name": "Rice (Poha)", "quantity": 80.0, "unit": "g"},
            {"food_id": 263, "food_name": "Peanuts", "quantity": 25.0, "unit": "g"},
            {"food_id": 205, "food_name": "Potato", "quantity": 50.0, "unit": "g"},
            {"food_id": 235, "food_name": "Onion", "quantity": 40.0, "unit": "g"},
        ],
    },
    {
        "id": 2,
        "name": "Moong Dal & Oats Chilla",
        "tags": ["veg", "breakfast", "quick", "high-protein", "indian"],
        "allergens": [],
        "cuisine": "indian",
        "cost_estimate": 50,
        "prep_time": 12,
        "calories": 380,
        "protein_g": 18.0,
        "carbs_g": 48.0,
        "fat_g": 7.0,
        "fiber_g": 5.0,
        "sodium_mg": 180.0,
        "calcium_mg": 68.0,
        "iron_mg": 3.4,
        "food_category": "Grain Legumes and Pulses",
        "data_source": "ICMR_NIN",
        "ingredients": [
            {"food_id": 31, "food_name": "Green Gram (Moong Dal)", "quantity": 60.0, "unit": "g"},
            {"food_id": 16, "food_name": "Wheat Flour / Oats", "quantity": 30.0, "unit": "g"},
            {"food_id": 282, "food_name": "Cow Milk / Curd", "quantity": 100.0, "unit": "ml"},
            {"food_id": 235, "food_name": "Onion", "quantity": 30.0, "unit": "g"},
        ],
    },
    {
        "id": 3,
        "name": "Brown Rice & Palak Dal Tadka",
        "tags": ["veg", "lunch", "indian", "comfort", "high-fiber"],
        "allergens": [],
        "cuisine": "indian",
        "cost_estimate": 80,
        "prep_time": 25,
        "calories": 520,
        "protein_g": 22.0,
        "carbs_g": 78.0,
        "fat_g": 11.0,
        "fiber_g": 7.2,
        "sodium_mg": 340.0,
        "calcium_mg": 140.0,
        "iron_mg": 4.8,
        "food_category": "Cereals and Millets",
        "data_source": "ICMR_NIN",
        "ingredients": [
            {"food_id": 10, "food_name": "Brown Rice", "quantity": 90.0, "unit": "g"},
            {"food_id": 69, "food_name": "Spinach (Palak)", "quantity": 120.0, "unit": "g"},
            {"food_id": 34, "food_name": "Lentil Dal", "quantity": 50.0, "unit": "g"},
            {"food_id": 131, "food_name": "Tomato", "quantity": 50.0, "unit": "g"},
            {"food_id": 235, "food_name": "Onion", "quantity": 40.0, "unit": "g"},
        ],
    },
    {
        "id": 4,
        "name": "Grilled Chicken Breast with Quinoa & Veggies",
        "tags": ["non-veg", "lunch", "western", "high-protein", "long-prep-time", "expensive"],
        "allergens": [],
        "cuisine": "western",
        "cost_estimate": 160,
        "prep_time": 30,
        "calories": 550,
        "protein_g": 45.0,
        "carbs_g": 42.0,
        "fat_g": 12.0,
        "fiber_g": 2.5,
        "sodium_mg": 390.0,
        "calcium_mg": 52.0,
        "iron_mg": 2.6,
        "food_category": "Poultry",
        "data_source": "USDA",
        "ingredients": [
            {"food_id": 301, "food_name": "Chicken Breast", "quantity": 180.0, "unit": "g"},
            {"food_id": 3, "food_name": "Barley Grain", "quantity": 60.0, "unit": "g"},
            {"food_id": 94, "food_name": "Cauliflower & Veggies", "quantity": 100.0, "unit": "g"},
        ],
    },
    {
        "id": 5,
        "name": "Foxtail Millet & Moong Dal Khichdi",
        "tags": ["veg", "dinner", "indian", "light", "gluten-free", "quick"],
        "allergens": [],
        "cuisine": "indian",
        "cost_estimate": 60,
        "prep_time": 20,
        "calories": 420,
        "protein_g": 16.0,
        "carbs_g": 65.0,
        "fat_g": 8.0,
        "fiber_g": 6.0,
        "sodium_mg": 210.0,
        "calcium_mg": 85.0,
        "iron_mg": 3.8,
        "food_category": "Cereals and Millets",
        "data_source": "ICMR_NIN",
        "ingredients": [
            {"food_id": 2, "food_name": "Bajra / Millet", "quantity": 80.0, "unit": "g"},
            {"food_id": 31, "food_name": "Green Gram (Moong Dal)", "quantity": 50.0, "unit": "g"},
            {"food_id": 131, "food_name": "Tomato", "quantity": 40.0, "unit": "g"},
        ],
    },
    {
        "id": 6,
        "name": "Roasted Spiced Makhana",
        "tags": ["veg", "snack", "indian", "quick", "light"],
        "allergens": [],
        "cuisine": "indian",
        "cost_estimate": 45,
        "prep_time": 7,
        "calories": 180,
        "protein_g": 4.5,
        "carbs_g": 24.0,
        "fat_g": 6.0,
        "fiber_g": 4.0,
        "sodium_mg": 120.0,
        "calcium_mg": 38.0,
        "iron_mg": 1.4,
        "food_category": "Nuts and Oilseeds",
        "data_source": "ICMR_NIN",
        "ingredients": [
            {"food_id": 99991, "food_name": "Foxnuts (Makhana)", "quantity": 40.0, "unit": "g"},
            {"food_id": 251, "food_name": "Turmeric Powder", "quantity": 5.0, "unit": "g"},
        ],
    },
    {
        "id": 7,
        "name": "Masala Paneer Bhurji with Whole Wheat Toast",
        "tags": ["veg", "breakfast", "quick", "high-protein", "indian", "dairy", "bread"],
        "allergens": ["dairy", "gluten"],
        "cuisine": "indian",
        "cost_estimate": 65,
        "prep_time": 10,
        "calories": 390,
        "protein_g": 22.0,
        "carbs_g": 38.0,
        "fat_g": 14.0,
        "fiber_g": 2.8,
        "sodium_mg": 320.0,
        "calcium_mg": 280.0,
        "iron_mg": 2.2,
        "food_category": "Milk and Milk Products",
        "data_source": "ICMR_NIN",
        "ingredients": [
            {"food_id": 283, "food_name": "Paneer", "quantity": 120.0, "unit": "g"},
            {"food_id": 16, "food_name": "Wheat Flour / Toast", "quantity": 60.0, "unit": "g"},
            {"food_id": 131, "food_name": "Tomato", "quantity": 40.0, "unit": "g"},
            {"food_id": 235, "food_name": "Onion", "quantity": 40.0, "unit": "g"},
        ],
    },
    {
        "id": 8,
        "name": "Fresh Palak Paneer & Brown Rice with Dahi Bowl",
        "tags": ["veg", "lunch", "dinner", "high-protein", "indian", "iron-rich", "dairy"],
        "allergens": ["dairy"],
        "cuisine": "indian",
        "cost_estimate": 95,
        "prep_time": 20,
        "calories": 480,
        "protein_g": 24.0,
        "carbs_g": 52.0,
        "fat_g": 16.0,
        "fiber_g": 6.5,
        "food_category": "Milk and Milk Products",
        "data_source": "ICMR_NIN",
        "ingredients": [
            {"food_id": 283, "food_name": "Paneer", "quantity": 100.0, "unit": "g"},
            {"food_id": 69, "food_name": "Spinach", "quantity": 120.0, "unit": "g"},
            {"food_id": 10, "food_name": "Brown Rice", "quantity": 80.0, "unit": "g"},
            {"food_id": 282, "food_name": "Cow Milk / Curd", "quantity": 100.0, "unit": "ml"},
        ],
    },
]

# ---------------------------------------------------------------------------
# Slot → food-category keyword mapping
# Maps each meal slot to the SQLite LIKE patterns used to filter candidate rows.
# A None value means "accept all categories" (e.g. lunch, dinner).
# ---------------------------------------------------------------------------
SLOT_CATEGORY_KEYWORDS: Dict[str, Optional[List[str]]] = {
    "early_morning": ["beverage", "nut", "seed", "fruit"],
    "breakfast": ["cereal", "grain", "legume", "pulse", "dairy", "milk", "egg", "fruit"],
    "lunch": None,  # All categories except pure beverage (handled in SQL)
    "evening_snack": ["nut", "seed", "fruit", "snack", "legume", "pulse", "vegetable"],
    "dinner": None,  # All categories except pure beverage (handled in SQL)
}

# Slots that exclude pure-beverage categories
_BEVERAGE_EXCLUDED_SLOTS = {"lunch", "dinner", "early_morning", "breakfast", "evening_snack"}

# Slots that also exclude heavy-meat categories (breakfast)
_HEAVY_MEAT_CATEGORIES = ["poultry", "animal meat", "marine fish", "fresh water fish",
                           "crustacean", "mollusk"]


SLOT_CALORIE_WEIGHTS: Dict[str, float] = {
    "early_morning": 0.05,
    "breakfast": 0.25,
    "lunch": 0.35,
    "evening_snack": 0.10,
    "dinner": 0.25,
}


def _build_slot_query(slot_id: str, limit: Optional[int] = None, shuffle: bool = False) -> tuple:
    """
    Build a parameterised SQLite query string and params tuple for a given slot_id.
    Returns (query_string, params_tuple).
    Supports optional ORDER BY RANDOM() when shuffle=True.
    """
    base_select = """
        SELECT id, name, food_category, calories_kcal, protein_g, carbohydrates_g, fat_g,
               fiber_g, sodium_mg, calcium_mg, iron_mg,
               is_vegetarian, is_vegan, is_gluten_free, allergen_flags, data_source
        FROM foods
        WHERE calories_kcal > 50
    """
    params: list = []

    keywords = SLOT_CATEGORY_KEYWORDS.get(slot_id, "UNKNOWN")

    if keywords == "UNKNOWN":
        # slot_id not recognised — return nothing (caller handles 400)
        return None, None

    if slot_id == "breakfast":
        # Include specific categories; exclude heavy meat categories
        include_clauses = " OR ".join(
            ["LOWER(food_category) LIKE ?"] * len(keywords)
        )
        for kw in keywords:
            params.append(f"%{kw}%")
        # Exclude heavy meat
        exclude_clauses = " AND ".join(
            ["LOWER(food_category) NOT LIKE ?"] * len(_HEAVY_MEAT_CATEGORIES)
        )
        for kw in _HEAVY_MEAT_CATEGORIES:
            params.append(f"%{kw}%")
        query = f"{base_select} AND ({include_clauses}) AND {exclude_clauses}"

    elif keywords is None:
        # lunch or dinner: all categories except pure beverage
        query = f"{base_select} AND LOWER(food_category) NOT LIKE ?"
        params.append("%beverage%")

    else:
        # early_morning, evening_snack: keyword-based include list
        include_clauses = " OR ".join(
            ["LOWER(food_category) LIKE ?"] * len(keywords)
        )
        for kw in keywords:
            params.append(f"%{kw}%")
        query = f"{base_select} AND ({include_clauses})"

    if shuffle:
        query += " ORDER BY RANDOM()"

    if limit:
        query += f" LIMIT {int(limit)}"

    return query, tuple(params)


def _row_to_candidate(r: sqlite3.Row, offset: int = 1000) -> Dict[str, Any]:
    """
    Convert a SQLite foods row into a candidate dict suitable for the recommender.
    offset is added to the DB id to avoid collisions with SAMPLE_CANDIDATES ids.
    """
    cat = str(r["food_category"] or "").lower()
    tags = [cat] + [w.strip() for w in cat.replace("&", " ").replace("and", " ").split() if len(w.strip()) > 2]
    if "milk" in cat or "dairy" in cat:
        tags.extend(["dairy", "milk"])
    if "egg" in cat:
        tags.extend(["egg", "eggs"])
    if any(m in cat for m in ["meat", "poultry", "beef", "pork", "chicken"]):
        tags.append("meat")
    if any(f in cat for f in ["fish", "crustacean", "mollusk", "seafood"]):
        tags.extend(["fish", "seafood"])

    if r["is_vegetarian"]:
        tags.append("veg")
    else:
        tags.append("non-veg")

    if "is_vegan" in r.keys() and not r["is_vegan"]:
        tags.append("non-vegan")

    if r["is_gluten_free"]:
        tags.append("gluten-free")

    # Derive prep time and cost estimate from category heuristics (documented thresholds)
    is_meat = any(w in cat for w in ["poultry", "meat", "fish", "beef", "pork", "seafood",
                                      "crustacean", "mollusk"])
    prep = 30 if is_meat else (20 if "legume" in cat or "pulse" in cat else 15)
    cost = 150 if is_meat else (80 if "nut" in cat or "dairy" in cat or "milk" in cat else 50)

    # Derive penalty tags with documented thresholds
    if prep > 25:
        tags.append("long-prep-time")
    else:
        tags.append("quick")

    if cost > 100:
        tags.append("expensive")

    allergens = [a.strip().lower() for a in (r["allergen_flags"] or "").split(",") if a.strip()]
    if "nuts" in allergens and "peanuts" not in allergens:
        allergens.append("peanuts")
    if "peanuts" in allergens and "nuts" not in allergens:
        allergens.append("nuts")

    def _extract_nutrient(col: str) -> Optional[float]:
        """Extract float from row, returning None for missing data and preserving 0.0."""
        if col in r.keys() and r[col] is not None:
            try:
                val = float(r[col])
                if not (math.isnan(val) or math.isinf(val)):
                    return round(val, 2)
            except (ValueError, TypeError):
                pass
        return None

    fiber_val = _extract_nutrient("fiber_g")
    sodium_val = _extract_nutrient("sodium_mg")
    calcium_val = _extract_nutrient("calcium_mg")
    iron_val = _extract_nutrient("iron_mg")

    is_egg = "egg" in cat
    is_banana = "banana" in str(r["name"] or "").lower()
    is_liquid = "milk" in cat or "beverage" in cat
    unit = "piece" if (is_egg or is_banana) else ("ml" if is_liquid else "g")
    quantity = 1.0 if (is_egg or is_banana) else 100.0

    ingredients = [
        {
            "food_id": r["id"],
            "food_name": r["name"],
            "quantity": quantity,
            "unit": unit,
        }
    ]

    return {
        "id": offset + r["id"],
        "name": r["name"],
        "tags": list(set(tags)),
        "allergens": list(set(allergens)),
        "cuisine": "indian" if "ICMR" in str(r["data_source"] or "") else "general",
        "cost_estimate": cost,
        "prep_time": prep,
        "calories": float(r["calories_kcal"]),
        "protein_g": float(r["protein_g"]),
        "carbs_g": float(r["carbohydrates_g"]),
        "fat_g": float(r["fat_g"]),
        "fiber_g": fiber_val if fiber_val is not None else 0.0,
        "sodium_mg": sodium_val,
        "calcium_mg": calcium_val,
        "iron_mg": iron_val,
        "micronutrients": {
            "fiber_g": fiber_val,
            "sodium_mg": sodium_val,
            "calcium_mg": calcium_val,
            "iron_mg": iron_val,
        },
        "food_category": r["food_category"],
        "data_source": str(r["data_source"]) if "data_source" in r.keys() and r["data_source"] else "USDA",
        "ingredients": ingredients,
    }


def load_candidate_foods(slot_id: Optional[str] = None, shuffle: bool = False) -> List[Dict[str, Any]]:
    """
    Loads candidate items from the full local SQLite foods catalog (all records
    with calories_kcal > 50, up to 14,099 rows), falling back to SAMPLE_CANDIDATES
    only if the database is missing or unreadable.

    When slot_id is provided the query is filtered to categories relevant to that
    meal slot (see SLOT_CATEGORY_KEYWORDS). When slot_id is None all non-trivial
    foods are returned (full-day planning).
    When shuffle is True, candidates are sampled randomly from SQLite.
    """
    db_path = settings.sqlite_db_path
    if not os.path.exists(db_path):
        # Emergency fallback: DB not found
        return list(SAMPLE_CANDIDATES)

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        if slot_id is not None:
            query, params = _build_slot_query(slot_id, limit=60, shuffle=shuffle)
            if query is None:
                # Unknown slot — return empty list; caller raises 400
                conn.close()
                return []
            cur.execute(query, params)
        else:
            # Full catalog — balanced sample for full-day planning
            order_clause = "ORDER BY RANDOM()" if shuffle else ""
            cur.execute(f"""
                SELECT id, name, food_category, calories_kcal, protein_g, carbohydrates_g, fat_g,
                       fiber_g, sodium_mg, calcium_mg, iron_mg,
                       is_vegetarian, is_vegan, is_gluten_free, allergen_flags, data_source
                FROM foods
                WHERE calories_kcal > 50
                {order_clause}
                LIMIT 40
            """)

        db_foods = cur.fetchall()
        conn.close()

        # Combine curated meal candidates matching slot with SQLite foods catalog
        if slot_id is not None:
            sample_matching = [
                s for s in SAMPLE_CANDIDATES
                if slot_id in s.get("tags", []) or (slot_id == "evening_snack" and "snack" in s.get("tags", []))
            ]
        else:
            sample_matching = list(SAMPLE_CANDIDATES)

        candidates = sample_matching + [_row_to_candidate(r) for r in db_foods]
        return candidates

    except Exception:
        # Emergency fallback: DB error — use sample candidates
        return list(SAMPLE_CANDIDATES)


def _get_pantry_items(user_id: str) -> List[str]:
    """Load in-stock pantry items for the given user from SQLite."""
    pantry_items = []
    try:
        with get_db_cursor() as cur:
            cur.execute(
                "SELECT name FROM pantry_items WHERE user_id = ? AND in_stock = 1",
                (user_id,),
            )
            pantry_items = [row["name"].lower() for row in cur.fetchall()]
    except Exception:
        pass
    return pantry_items


def _normalize_profile(user_profile: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize aliases (dietary_preference -> dietary_pref, calorie_target -> target_calories)."""
    prof = dict(user_profile)
    if "dietary_preference" in prof and "dietary_pref" not in prof:
        prof["dietary_pref"] = prof["dietary_preference"]
    if "calorie_target" in prof and "target_calories" not in prof:
        prof["target_calories"] = prof["calorie_target"]
    if "dietary_pref" not in prof:
        prof["dietary_pref"] = "vegetarian"
    if "target_calories" not in prof:
        prof["target_calories"] = 2000
    if "budget_per_meal" not in prof:
        prof["budget_per_meal"] = 100
    if "prep_time_limit" not in prof:
        prof["prep_time_limit"] = 30
    if "allergies" not in prof:
        prof["allergies"] = []
    return prof


def _merge_with_db_profile(user_id: str, user_profile: Dict[str, Any]) -> Dict[str, Any]:
    """Merges caller profile with user's persisted SQLite profile for missing fields."""
    prof = dict(user_profile)
    try:
        with get_db_cursor() as cur:
            cur.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,))
            db_row = cur.fetchone()
            if db_row:
                db_data = dict(db_row)
                if "dietary_pref" not in prof and "dietary_preference" not in prof and "dietary_pref" in db_data:
                    prof["dietary_pref"] = db_data["dietary_pref"]
                if "allergies" not in prof and "allergies" in db_data:
                    raw_a = db_data["allergies"]
                    if raw_a:
                        try:
                            prof["allergies"] = json.loads(raw_a) if isinstance(raw_a, str) else raw_a
                        except Exception:
                            prof["allergies"] = []
                if "target_calories" not in prof and "calorie_target" not in prof and "target_calories" in db_data:
                    prof["target_calories"] = int(db_data["target_calories"])
                if "budget_per_meal" not in prof and "budget_per_meal" in db_data:
                    prof["budget_per_meal"] = float(db_data["budget_per_meal"])
                if "prep_time_limit" not in prof and "prep_time_limit" in db_data:
                    prof["prep_time_limit"] = int(db_data["prep_time_limit"])
                if "goal" not in prof and db_data.get("goal"):
                    prof["goal"] = db_data["goal"]
    except Exception:
        pass
    return _normalize_profile(prof)


def enrich_and_filter_candidates(
    candidates: List[Dict[str, Any]],
    user_profile: Dict[str, Any],
    pantry_items: Optional[List[str]] = None,
    budget_amount: Optional[float] = None,
    budget_mode: str = "within_budget",
    tolerance_pct: float = 0.20,
    region: str = "National",
) -> List[Dict[str, Any]]:
    """
    Enriches candidates with Indian Food Pricing calculations from SQLite food_prices,
    identifies pantry match and missing ingredient costs, attaches structured budget status,
    and filters candidates according to the active budget mode:
    - 'within_budget': requires complete pricing AND cost <= budget_amount
    - 'slightly_above': requires complete pricing AND cost <= budget_amount * (1 + tolerance_pct)
    - 'show_all': unrestricted; displays all safe candidates with visible cost & status
    If budget_amount is None or <= 0, no budget filtering is applied.
    """
    clean_mode = (budget_mode or "within_budget").strip().lower()
    if clean_mode not in ("within_budget", "slightly_above", "show_all"):
        clean_mode = "within_budget"

    clean_region = (region or "National").strip()

    try:
        with get_db_cursor() as cur:
            for c in candidates:
                ings = c.get("ingredients")
                if not ings:
                    f_id = c.get("id", 1)
                    actual_food_id = f_id if f_id < 1000 else (f_id - 1000)
                    ings = [{
                        "food_id": actual_food_id,
                        "food_name": c.get("name"),
                        "quantity": 100.0,
                        "unit": "g",
                    }]
                    c["ingredients"] = ings

                cost_res = calculate_recipe_cost(
                    cur=cur,
                    ingredients=ings,
                    servings=1,
                    region=clean_region,
                    recipe_name=c.get("name"),
                    pantry_item_names=pantry_items,
                )

                if cost_res["is_complete"] and cost_res["total_cost"] is not None:
                    c["cost_estimate"] = cost_res["total_cost"]
                    c["cost_per_serving"] = cost_res["cost_per_serving"]
                else:
                    c["cost_estimate"] = None
                    c["cost_per_serving"] = None

                status_info = evaluate_meal_budget_status(
                    cost=c["cost_estimate"],
                    is_complete=cost_res["is_complete"],
                    budget=budget_amount,
                    tolerance_pct=tolerance_pct,
                )

                c["cost_breakdown"] = cost_res
                c["budget_status"] = status_info["status"]
                c["budget_status_label"] = status_info["status_label"]
                c["cost_difference"] = status_info["cost_difference"]
                c["cost_difference_formatted"] = status_info["cost_difference_formatted"]
                c["is_affordable"] = status_info["is_affordable"]
                c["fits_within_budget"] = status_info["fits_within_budget"]
                c["fits_slightly_above"] = status_info["fits_slightly_above"]
                c["pantry_coverage_pct"] = cost_res.get("pantry_coverage_pct", 0)
                c["pantry_matched_ingredients"] = cost_res.get("pantry_matched_ingredients", [])
                c["pantry_missing_ingredients"] = cost_res.get("pantry_missing_ingredients", [])
                c["missing_ingredients_cost"] = cost_res.get("missing_ingredients_cost")
                c["missing_ingredients_cost_formatted"] = cost_res.get("missing_ingredients_cost_formatted")
    except Exception:
        for c in candidates:
            if "cost_breakdown" not in c:
                c["budget_status"] = "cost_unavailable"
                c["budget_status_label"] = "Cost Unavailable"
                c["cost_difference"] = 0.0
                c["cost_difference_formatted"] = ""
                c["is_affordable"] = False
                c["fits_within_budget"] = False
                c["fits_slightly_above"] = False

    # Apply budget filtering mode if budget_amount is specified and > 0
    if budget_amount is not None and budget_amount > 0:
        if clean_mode == "within_budget":
            filtered = [c for c in candidates if c.get("fits_within_budget")]
        elif clean_mode == "slightly_above":
            filtered = [c for c in candidates if c.get("fits_slightly_above")]
        else:  # show_all
            filtered = candidates
        return filtered

    return candidates


def attach_recommendation_pricing(
    recs: List[Dict[str, Any]],
    budget_amount: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """Enriches the top-level recommendation result objects with pricing & budget fields."""
    for rec in recs:
        item = rec.get("item", {})
        cost_bd = item.get("cost_breakdown", {})
        total_cost = item.get("cost_estimate")
        rec["estimated_cost"] = total_cost
        rec["cost_per_serving"] = item.get("cost_per_serving")
        rec["cost_formatted"] = (
            cost_bd.get("total_cost_formatted")
            if cost_bd
            else ("Price unavailable" if total_cost is None else f"₹{total_cost:.2f}")
        )
        rec["cost_per_serving_formatted"] = cost_bd.get("cost_per_serving_formatted")
        rec["budget_status"] = item.get("budget_status", "cost_unavailable")
        rec["budget_status_label"] = item.get("budget_status_label", "Cost Unavailable")
        rec["cost_difference"] = item.get("cost_difference", 0.0)
        rec["cost_difference_formatted"] = item.get("cost_difference_formatted", "")
        rec["is_affordable"] = item.get("is_affordable", False)
        rec["price_type"] = cost_bd.get("price_type")
        rec["cost_breakdown"] = cost_bd
        rec["pantry_matched_ingredients"] = item.get("pantry_matched_ingredients", [])
        rec["pantry_missing_ingredients"] = item.get("pantry_missing_ingredients", [])
        rec["missing_ingredients_cost"] = item.get("missing_ingredients_cost")
        rec["missing_ingredients_cost_formatted"] = item.get("missing_ingredients_cost_formatted")

        # Clinical explainability augmentation
        if budget_amount is not None and item.get("budget_status") == "within_budget":
            if "budget" not in rec.get("reason", "").lower():
                rec["reason"] = (rec.get("reason", "").rstrip(".") + ", and fits your selected budget.")
    return recs


@router.post("/")
async def generate_recommendations(
    user_profile: Dict[str, Any],
    budget_amount: Optional[float] = Query(None, description="Active session budget in INR"),
    budget_type: Optional[str] = Query(None, description="per_meal or per_day"),
    budget_mode: Optional[str] = Query(None, description="within_budget, slightly_above, show_all"),
    tolerance_pct: Optional[float] = Query(None, description="Tolerance for slightly_above mode"),
    region: Optional[str] = Query(None, description="Indian pricing region"),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Run candidate meals through safety gate, Indian food pricing calculations,
    user-controlled budget filtering, TF-IDF scoring, and return ranked recommendations.
    Uses authenticated user's real meal logs from SQLite for adaptive penalties.
    user_id is derived exclusively from JWT for authorization and isolation.
    """
    # Support both flat payloads and nested { user_profile: { ... } } payloads
    payload = user_profile if isinstance(user_profile, dict) else {}
    if "user_profile" in payload and isinstance(payload["user_profile"], dict):
        body_profile = payload["user_profile"]
    else:
        body_profile = payload

    # Extract budget params from query or body
    eff_budget = budget_amount if budget_amount is not None else payload.get("budget_amount")
    if eff_budget is None and "budget_amount" in body_profile:
        eff_budget = body_profile["budget_amount"]
    if eff_budget is not None:
        try:
            eff_budget = float(eff_budget)
            if eff_budget <= 0:
                raise HTTPException(status_code=400, detail="Budget amount must be a positive number greater than 0.")
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Budget amount must be a valid positive number.")

    eff_type = str(
        budget_type or payload.get("budget_type") or body_profile.get("budget_type") or "per_meal"
    ).strip().lower()
    if eff_type not in ("per_meal", "per_day"):
        raise HTTPException(status_code=400, detail="Invalid budget_type. Must be 'per_meal' or 'per_day'.")

    eff_mode = str(
        budget_mode or payload.get("budget_mode") or body_profile.get("budget_mode") or "within_budget"
    ).strip().lower()
    if eff_mode not in ("within_budget", "slightly_above", "show_all"):
        raise HTTPException(status_code=400, detail="Invalid budget_mode. Must be 'within_budget', 'slightly_above', or 'show_all'.")

    eff_tolerance_raw = tolerance_pct if tolerance_pct is not None else (
        payload.get("tolerance_pct") if payload.get("tolerance_pct") is not None else body_profile.get("tolerance_pct", 0.20)
    )
    eff_tolerance = float(eff_tolerance_raw)
    eff_region = str(region or payload.get("region") or body_profile.get("region") or "National").strip()

    user_id = current_user["id"]
    merged_profile = _merge_with_db_profile(user_id, body_profile)
    if eff_budget is not None:
        merged_profile["budget_per_meal"] = eff_budget

    meal_logs = get_user_meal_logs(user_id)
    pantry_items = _get_pantry_items(user_id)

    # Optional slot-level pre-filter
    meal_slot: Optional[str] = merged_profile.get("meal_slot")
    candidates = load_candidate_foods(slot_id=meal_slot)

    # 1. Safety Gate executed FIRST
    safe_candidates = filter_safe(candidates, merged_profile)
    if not safe_candidates:
        return []

    # 2. Pricing Enrichment & Budget Filtering
    budget_filtered = enrich_and_filter_candidates(
        candidates=safe_candidates,
        user_profile=merged_profile,
        pantry_items=pantry_items,
        budget_amount=eff_budget,
        budget_mode=eff_mode,
        tolerance_pct=eff_tolerance,
        region=eff_region,
    )
    if not budget_filtered:
        return []

    results = recommend(
        user_profile=merged_profile,
        candidates=budget_filtered,
        meal_logs=meal_logs,
        top_n=merged_profile.get("top_n", 6),
        pantry_items=pantry_items,
    )

    return attach_recommendation_pricing(results, budget_amount=eff_budget)


@router.post("/slot/{slot_id}")
async def generate_slot_recommendations(
    slot_id: str,
    user_profile: Dict[str, Any],
    shuffle: bool = False,
    budget_amount: Optional[float] = Query(None),
    budget_type: Optional[str] = Query(None),
    budget_mode: Optional[str] = Query(None),
    tolerance_pct: Optional[float] = Query(None),
    region: Optional[str] = Query(None),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Single-slot regeneration endpoint with budget-aware filtering and Indian food pricing.
    Returns 3 to 5 alternative foods ranked by the full ML pipeline.
    """
    if slot_id not in SLOT_CATEGORY_KEYWORDS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown slot_id '{slot_id}'. Valid values: {list(SLOT_CATEGORY_KEYWORDS.keys())}",
        )

    payload = user_profile if isinstance(user_profile, dict) else {}
    if "user_profile" in payload and isinstance(payload["user_profile"], dict):
        body_profile = payload["user_profile"]
    else:
        body_profile = payload

    eff_budget = budget_amount if budget_amount is not None else payload.get("budget_amount")
    if eff_budget is None and "budget_amount" in body_profile:
        eff_budget = body_profile["budget_amount"]
    if eff_budget is not None:
        try:
            eff_budget = float(eff_budget)
            if eff_budget <= 0:
                raise HTTPException(status_code=400, detail="Budget amount must be a positive number greater than 0.")
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Budget amount must be a valid positive number.")

    eff_type = str(
        budget_type or payload.get("budget_type") or body_profile.get("budget_type") or "per_meal"
    ).strip().lower()
    if eff_type not in ("per_meal", "per_day"):
        raise HTTPException(status_code=400, detail="Invalid budget_type. Must be 'per_meal' or 'per_day'.")

    eff_mode = str(
        budget_mode or payload.get("budget_mode") or body_profile.get("budget_mode") or "within_budget"
    ).strip().lower()
    if eff_mode not in ("within_budget", "slightly_above", "show_all"):
        raise HTTPException(status_code=400, detail="Invalid budget_mode. Must be 'within_budget', 'slightly_above', or 'show_all'.")

    eff_tolerance_raw = tolerance_pct if tolerance_pct is not None else (
        payload.get("tolerance_pct") if payload.get("tolerance_pct") is not None else body_profile.get("tolerance_pct", 0.20)
    )
    eff_tolerance = float(eff_tolerance_raw)
    eff_region = str(region or payload.get("region") or body_profile.get("region") or "National").strip()

    is_shuffle = shuffle or bool(body_profile.get("shuffle", False))
    user_id = current_user["id"]
    merged_profile = _merge_with_db_profile(user_id, body_profile)

    # For per_day budget, allocate slot budget based on slot calorie weight
    slot_budget = eff_budget
    if eff_budget is not None and eff_type == "per_day":
        w = SLOT_CALORIE_WEIGHTS.get(slot_id, 0.25)
        # standard 3 main meals total active weight ~0.85
        slot_budget = round(eff_budget * (w / 0.85), 2)

    if slot_budget is not None:
        merged_profile["budget_per_meal"] = slot_budget

    top_n = int(body_profile.get("top_n", 5))
    top_n = max(3, min(5, top_n))

    meal_logs = get_user_meal_logs(user_id)
    pantry_items = _get_pantry_items(user_id)

    candidates = load_candidate_foods(slot_id=slot_id, shuffle=is_shuffle)
    if not candidates:
        return []

    # 1. Safety Gate FIRST
    safe_candidates = filter_safe(candidates, merged_profile)
    if not safe_candidates:
        return []

    # 2. Pricing & Budget Filtering
    budget_filtered = enrich_and_filter_candidates(
        candidates=safe_candidates,
        user_profile=merged_profile,
        pantry_items=pantry_items,
        budget_amount=slot_budget,
        budget_mode=eff_mode,
        tolerance_pct=eff_tolerance,
        region=eff_region,
    )
    if not budget_filtered:
        return []

    results = recommend(
        user_profile=merged_profile,
        candidates=budget_filtered,
        meal_logs=meal_logs,
        top_n=top_n,
        pantry_items=pantry_items,
    )

    return attach_recommendation_pricing(results, budget_amount=slot_budget)


@router.post("/daily")
async def generate_daily_recommendations(
    payload: Dict[str, Any],
    shuffle: bool = False,
    budget_amount: Optional[float] = Query(None),
    budget_type: Optional[str] = Query(None),
    budget_mode: Optional[str] = Query(None),
    tolerance_pct: Optional[float] = Query(None),
    region: Optional[str] = Query(None),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Generate evidence-based daily meal plan recommendations with Indian Food Pricing,
    user-controlled budget filtering (Per Meal vs Per Day, Within Budget vs Slightly Above vs Show All),
    and comprehensive Daily Meal Plan Budget Summary.
    """
    user_profile = payload.get("user_profile", payload)
    if "user_profile" in user_profile and isinstance(user_profile["user_profile"], dict):
        user_profile = user_profile["user_profile"]

    eff_budget = budget_amount if budget_amount is not None else payload.get("budget_amount")
    if eff_budget is None and "budget_amount" in user_profile:
        eff_budget = user_profile["budget_amount"]
    if eff_budget is not None:
        try:
            eff_budget = float(eff_budget)
            if eff_budget <= 0:
                raise HTTPException(status_code=400, detail="Budget amount must be a positive number greater than 0.")
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Budget amount must be a valid positive number.")

    eff_type = str(budget_type or payload.get("budget_type") or user_profile.get("budget_type") or "per_meal").strip().lower()
    if eff_type not in ("per_meal", "per_day"):
        raise HTTPException(status_code=400, detail="Invalid budget_type. Must be 'per_meal' or 'per_day'.")

    eff_mode = str(budget_mode or payload.get("budget_mode") or user_profile.get("budget_mode") or "within_budget").strip().lower()
    if eff_mode not in ("within_budget", "slightly_above", "show_all"):
        raise HTTPException(status_code=400, detail="Invalid budget_mode. Must be 'within_budget', 'slightly_above', or 'show_all'.")

    eff_tolerance = float(
        tolerance_pct
        if tolerance_pct is not None
        else payload.get("tolerance_pct", user_profile.get("tolerance_pct", 0.20))
    )
    eff_region = str(region or payload.get("region") or user_profile.get("region") or "National").strip()

    user_id = current_user["id"]
    user_profile = _merge_with_db_profile(user_id, user_profile)
    meal_logs = get_user_meal_logs(user_id)
    pantry_items = _get_pantry_items(user_id)

    raw_active_slots = payload.get("active_slots", {
        "early_morning": False,
        "breakfast": True,
        "lunch": True,
        "evening_snack": False,
        "dinner": True,
    })
    active_slots = {
        s: bool(raw_active_slots.get(s, False))
        for s in ["early_morning", "breakfast", "lunch", "evening_snack", "dinner"]
    }
    if not any(active_slots.values()):
        active_slots["breakfast"] = True
        active_slots["lunch"] = True
        active_slots["dinner"] = True

    is_shuffle = shuffle or bool(payload.get("shuffle", False))
    shuffle_slot = payload.get("shuffle_slot")

    top_n = int(payload.get("top_n", 5))
    top_n = max(3, min(5, top_n))

    total_target_cals = float(user_profile.get("target_calories", 2000.0))
    if total_target_cals <= 0:
        total_target_cals = 2000.0

    total_active_weight = sum(SLOT_CALORIE_WEIGHTS[s] for s, active in active_slots.items() if active)
    if total_active_weight <= 0:
        total_active_weight = 1.0

    slot_results: Dict[str, List[Dict[str, Any]]] = {}
    total_cals = 0.0
    total_prot = 0.0
    total_carbs = 0.0
    total_fat = 0.0
    total_fiber = 0.0
    total_sodium = 0.0
    total_calcium = 0.0
    total_iron = 0.0
    has_fiber = False
    has_sodium = False
    has_calcium = False
    has_iron = False

    slot_costs: Dict[str, Optional[float]] = {}
    slot_budget_allocations: Dict[str, Optional[float]] = {}
    daily_cost_sum = 0.0
    daily_is_complete = True
    incomplete_slots: List[str] = []

    for slot_id in ["early_morning", "breakfast", "lunch", "evening_snack", "dinner"]:
        if not active_slots.get(slot_id):
            continue

        weight = SLOT_CALORIE_WEIGHTS.get(slot_id, 0.25)
        norm_ratio = weight / total_active_weight
        slot_target_cals = total_target_cals * norm_ratio

        # Determine slot budget
        if eff_budget is not None:
            if eff_type == "per_day":
                slot_budget = round(eff_budget * norm_ratio, 2)
            else:
                slot_budget = eff_budget
            slot_budget_allocations[slot_id] = slot_budget
        else:
            slot_budget = None
            slot_budget_allocations[slot_id] = None

        slot_profile = dict(user_profile)
        slot_profile["target_calories"] = total_target_cals
        slot_profile["slot_target_calories"] = slot_target_cals
        if slot_budget is not None:
            slot_profile["budget_per_meal"] = slot_budget

        slot_shuffle = is_shuffle or (shuffle_slot == slot_id)
        candidates = load_candidate_foods(slot_id=slot_id, shuffle=slot_shuffle)

        # 1. Safety Gate FIRST
        safe_candidates = filter_safe(candidates, slot_profile)

        # 2. Pricing & Budget Filtering
        budget_filtered = enrich_and_filter_candidates(
            candidates=safe_candidates,
            user_profile=slot_profile,
            pantry_items=pantry_items,
            budget_amount=slot_budget,
            budget_mode=eff_mode,
            tolerance_pct=eff_tolerance,
            region=eff_region,
        )

        recs = recommend(
            user_profile=slot_profile,
            candidates=budget_filtered,
            meal_logs=meal_logs,
            top_n=top_n,
            pantry_items=pantry_items,
        )
        recs = attach_recommendation_pricing(recs, budget_amount=slot_budget)
        slot_results[slot_id] = recs

        if recs:
            first_item = recs[0]["item"]
            total_cals += float(first_item.get("calories", 0))
            total_prot += float(first_item.get("protein_g", 0))
            total_carbs += float(first_item.get("carbs_g", 0))
            total_fat += float(first_item.get("fat_g", 0))

            micros = first_item.get("micronutrients") or {}
            fib = micros.get("fiber_g") if micros.get("fiber_g") is not None else first_item.get("fiber_g")
            if fib is not None:
                total_fiber += float(fib)
                has_fiber = True

            sod = micros.get("sodium_mg") if micros.get("sodium_mg") is not None else first_item.get("sodium_mg")
            if sod is not None:
                total_sodium += float(sod)
                has_sodium = True

            cal = micros.get("calcium_mg") if micros.get("calcium_mg") is not None else first_item.get("calcium_mg")
            if cal is not None:
                total_calcium += float(cal)
                has_calcium = True

            irn = micros.get("iron_mg") if micros.get("iron_mg") is not None else first_item.get("iron_mg")
            if irn is not None:
                total_iron += float(irn)
                has_iron = True

            # Track slot costs
            cost_val = recs[0].get("estimated_cost")
            if cost_val is not None:
                slot_costs[slot_id] = round(float(cost_val), 2)
                daily_cost_sum += float(cost_val)
            else:
                slot_costs[slot_id] = None
                daily_is_complete = False
                incomplete_slots.append(slot_id)
        else:
            slot_costs[slot_id] = None

    # Calculate Budget Summary
    if daily_is_complete and any(active_slots.values()) and all(slot_costs.get(s) is not None for s in active_slots if active_slots[s]):
        daily_total_cost = round(daily_cost_sum, 2)
        daily_total_formatted = f"₹{daily_total_cost:.2f}"
        if eff_budget is not None and eff_type == "per_day":
            rem = round(eff_budget - daily_total_cost, 2)
            is_over = daily_total_cost > eff_budget
            overage = round(daily_total_cost - eff_budget, 2) if is_over else 0.0
            remaining_budget = rem
            remaining_budget_formatted = f"+₹{overage:.2f} over budget" if is_over else f"₹{rem:.2f} remaining"
        elif eff_budget is not None and eff_type == "per_meal":
            remaining_budget = None
            is_over = False
            overage = 0.0
            remaining_budget_formatted = "Per-meal budget active"
        else:
            remaining_budget = None
            is_over = False
            overage = 0.0
            remaining_budget_formatted = "No budget configured"
    else:
        daily_total_cost = None
        daily_total_formatted = "Estimate incomplete (missing ingredient prices)"
        remaining_budget = None
        remaining_budget_formatted = "Cannot calculate (incomplete meal pricing)"
        is_over = False
        overage = 0.0

    budget_summary = {
        "budget_type": eff_type,
        "budget_amount": eff_budget,
        "budget_mode": eff_mode,
        "region": eff_region,
        "slot_costs": slot_costs,
        "slot_budget_allocations": slot_budget_allocations,
        "daily_total_cost": daily_total_cost,
        "daily_total_formatted": daily_total_formatted,
        "partial_cost": round(daily_cost_sum, 2),
        "partial_cost_formatted": f"₹{round(daily_cost_sum, 2):.2f}",
        "is_complete": daily_is_complete and len(incomplete_slots) == 0,
        "remaining_budget": remaining_budget,
        "remaining_budget_formatted": remaining_budget_formatted,
        "is_over_budget": is_over,
        "overage_amount": overage,
        "incomplete_slots": incomplete_slots,
    }

    return {
        "slots": slot_results,
        "totals": {
            "calories": round(total_cals),
            "protein_g": round(total_prot, 1),
            "carbs_g": round(total_carbs, 1),
            "fat_g": round(total_fat, 1),
            "fiber_g": round(total_fiber, 1) if has_fiber else 0.0,
            "sodium_mg": round(total_sodium, 1) if has_sodium else None,
            "calcium_mg": round(total_calcium, 1) if has_calcium else None,
            "iron_mg": round(total_iron, 1) if has_iron else None,
        },
        "micronutrients": {
            "fiber_g": round(total_fiber, 1) if has_fiber else None,
            "sodium_mg": round(total_sodium, 1) if has_sodium else None,
            "calcium_mg": round(total_calcium, 1) if has_calcium else None,
            "iron_mg": round(total_iron, 1) if has_iron else None,
            "data_completeness": {
                "fiber_tracked": has_fiber,
                "sodium_tracked": has_sodium,
                "calcium_tracked": has_calcium,
                "iron_tracked": has_iron,
            },
        },
        "budget_summary": budget_summary,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 8B ─ SWAP & SAFETY SHIELD ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════


def _describe_active_rules(user_profile: Dict[str, Any]) -> List[Dict[str, str]]:
    """Return human-readable list of active safety rules for the user."""
    diet = str(user_profile.get("dietary_pref") or user_profile.get("dietary_preference") or "").strip().lower()
    allergies: List[str] = [
        str(a).strip().lower()
        for a in (user_profile.get("allergies") or [])
        if str(a).strip()
    ]

    rules: List[Dict[str, str]] = []

    DIET_LABELS = {
        "vegetarian": "Vegetarian — no meat, poultry, fish or seafood",
        "lacto-vegetarian": "Lacto-vegetarian — no meat or eggs",
        "vegan": "Vegan — no animal products whatsoever",
        "eggetarian": "Eggetarian — eggs allowed; no meat or fish",
        "ovo-vegetarian": "Ovo-vegetarian — eggs allowed; no dairy or meat",
        "pescatarian": "Pescatarian — fish/seafood allowed; no red meat or poultry",
    }
    if diet in DIET_LABELS:
        rules.append({"rule": "diet", "label": DIET_LABELS[diet], "value": diet})

    for allergy in allergies:
        rules.append({
            "rule": "allergen",
            "label": f"Allergen exclusion: {allergy.title()}",
            "value": allergy,
        })

    if not rules:
        rules.append({
            "rule": "none",
            "label": "No dietary restrictions configured — all foods eligible",
            "value": "",
        })

    return rules


def _macro_delta(current: Dict[str, Any], candidate: Dict[str, Any]) -> Dict[str, Any]:
    """Compute signed macro and micronutrient deltas: candidate − current."""
    deltas: Dict[str, Any] = {
        "delta_calories": round(float(candidate.get("calories", 0)) - float(current.get("calories", 0)), 1),
        "delta_protein_g": round(float(candidate.get("protein_g", 0)) - float(current.get("protein_g", 0)), 1),
        "delta_carbs_g": round(float(candidate.get("carbs_g", 0)) - float(current.get("carbs_g", 0)), 1),
        "delta_fat_g": round(float(candidate.get("fat_g", 0)) - float(current.get("fat_g", 0)), 1),
        "delta_fiber_g": round(float(candidate.get("fiber_g", 0)) - float(current.get("fiber_g", 0)), 1),
    }

    cand_sod = candidate.get("sodium_mg")
    cur_sod = current.get("sodium_mg")
    if cand_sod is not None and cur_sod is not None:
        deltas["delta_sodium_mg"] = round(float(cand_sod) - float(cur_sod), 1)

    cand_calc = candidate.get("calcium_mg")
    cur_calc = current.get("calcium_mg")
    if cand_calc is not None and cur_calc is not None:
        deltas["delta_calcium_mg"] = round(float(cand_calc) - float(cur_calc), 1)

    cand_iron = candidate.get("iron_mg")
    cur_iron = current.get("iron_mg")
    if cand_iron is not None and cur_iron is not None:
        deltas["delta_iron_mg"] = round(float(cand_iron) - float(cur_iron), 1)

    return deltas


def _macro_match_pct(current: Dict[str, Any], candidate: Dict[str, Any]) -> int:
    """Compute a 0–100 macro similarity score between two food items."""
    cur_cal = float(current.get("calories", 1)) or 1
    cand_cal = float(candidate.get("calories", 0))
    cal_diff = abs(cur_cal - cand_cal) / cur_cal

    cur_prot = float(current.get("protein_g", 1)) or 1
    cand_prot = float(candidate.get("protein_g", 0))
    prot_diff = abs(cur_prot - cand_prot) / cur_prot

    # Weight calories 60%, protein 40%
    score = max(0.0, 1.0 - (0.6 * cal_diff + 0.4 * prot_diff))
    return round(score * 100)


@router.post("/swap")
async def generate_swap_alternatives(
    payload: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Generate backend-scored swap alternatives for a specific meal slot.

    Request body:
        current_meal: { name, calories, protein_g, carbs_g, fat_g, fiber_g, ... }
        slot_id: one of early_morning | breakfast | lunch | evening_snack | dinner
        target_calories: int (optional, overrides profile)
        top_n: 3–5 (optional)

    Returns:
        {
          current_meal: {...},
          swap_alternatives: [
            { item: {...}, macro_match_pct: int, delta_calories, delta_protein_g,
              delta_carbs_g, delta_fat_g, delta_fiber_g, reason, score }
          ]
        }

    Safety gate is applied BEFORE scoring. Unsafe items are excluded and never
    returned to the client regardless of macro similarity.
    """
    slot_id: Optional[str] = payload.get("slot_id")
    if slot_id and slot_id not in SLOT_CATEGORY_KEYWORDS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown slot_id '{slot_id}'. Valid: {list(SLOT_CATEGORY_KEYWORDS.keys())}",
        )

    current_meal: Dict[str, Any] = payload.get("current_meal", {})
    top_n = max(3, min(5, int(payload.get("top_n", 5))))
    target_calories_override = payload.get("target_calories")

    user_id = current_user["id"]
    user_profile = _merge_with_db_profile(user_id, {})

    if target_calories_override:
        user_profile["target_calories"] = float(target_calories_override)

    meal_logs = get_user_meal_logs(user_id)
    pantry_items = _get_pantry_items(user_id)

    # Load slot-specific candidates (shuffle=True for variety on swap)
    candidates = load_candidate_foods(slot_id=slot_id, shuffle=True)
    if not candidates:
        return {"current_meal": current_meal, "swap_alternatives": []}

    # Apply safety gate FIRST — non-negotiable before scoring
    safe_candidates = filter_safe(candidates, user_profile)

    # Exclude the current meal itself from alternatives
    current_name = (current_meal.get("name") or "").strip().lower()
    safe_candidates = [c for c in safe_candidates if c.get("name", "").strip().lower() != current_name]

    if not safe_candidates:
        return {"current_meal": current_meal, "swap_alternatives": []}

    # Enrich candidates with pricing & budget status
    budget_amount = payload.get("budget_amount")
    budget_mode = payload.get("budget_mode", "within_budget")
    tolerance_pct = float(payload.get("tolerance_pct", 0.20))
    region = payload.get("region", "National")

    enriched_candidates = enrich_and_filter_candidates(
        candidates=safe_candidates,
        user_profile=user_profile,
        pantry_items=pantry_items,
        budget_amount=budget_amount,
        budget_mode=budget_mode,
        tolerance_pct=tolerance_pct,
        region=region,
    )
    if not enriched_candidates:
        return {"current_meal": current_meal, "swap_alternatives": []}

    # Score with ML engine
    ranked = recommend(
        user_profile=user_profile,
        candidates=enriched_candidates,
        meal_logs=meal_logs,
        top_n=top_n,
        pantry_items=pantry_items,
    )
    ranked = attach_recommendation_pricing(ranked, budget_amount=budget_amount)

    swap_alternatives = []
    for rec in ranked:
        item = rec.get("item", rec)
        deltas = _macro_delta(current_meal, item)
        swap_alternatives.append({
            "item": item,
            "macro_match_pct": _macro_match_pct(current_meal, item),
            **deltas,
            "reason": rec.get("reason", ""),
            "score": rec.get("score", 0),
            "estimated_cost": rec.get("estimated_cost"),
            "cost_formatted": rec.get("cost_formatted"),
            "budget_status": rec.get("budget_status"),
            "budget_status_label": rec.get("budget_status_label"),
            "cost_difference": rec.get("cost_difference"),
            "cost_difference_formatted": rec.get("cost_difference_formatted"),
            "price_type": rec.get("price_type"),
            "missing_ingredients_cost": rec.get("missing_ingredients_cost"),
            "missing_ingredients_cost_formatted": rec.get("missing_ingredients_cost_formatted"),
        })

    return {
        "current_meal": current_meal,
        "swap_alternatives": swap_alternatives,
    }


@router.post("/swap/validate")
async def validate_swap_candidate(
    payload: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Validate a single swap candidate against the user's safety profile.
    Returns 200 { safe: true } if safe, or 400 with blocked reason if unsafe.

    Request body:
        candidate: { name, tags: [...], allergens: [...], ... }
    """
    candidate = payload.get("candidate")
    if not candidate:
        raise HTTPException(status_code=422, detail="'candidate' field is required")

    user_id = current_user["id"]
    user_profile = _merge_with_db_profile(user_id, {})

    audit = audit_safe([candidate], user_profile)

    if audit["blocked"]:
        block = audit["blocked"][0]
        raise HTTPException(
            status_code=400,
            detail={
                "safe": False,
                "reason": block["reason"],
                "rule": block["rule"],
                "conflict": block["conflict"],
            },
        )

    return {"safe": True, "candidate": candidate}


@router.get("/safety-shield")
async def get_safety_shield(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Audit the food catalog against the authenticated user's dietary rules and allergens.

    Returns:
        {
          active_rules: [ { rule, label, value } ],
          safe_count: int,
          blocked_count: int,
          total_audited: int,
          blocked_candidates: [ { item: {...}, reason, rule, conflict } ]
        }

    Safety logic is sourced exclusively from ml.scoring.safety_gate.audit_safe.
    Gemini AI is never involved in safety decisions.
    """
    user_id = current_user["id"]
    user_profile = _merge_with_db_profile(user_id, {})

    # Load a representative 100-item sample from the full catalog
    candidates = load_candidate_foods(slot_id=None, shuffle=False)
    # Cap at 100 for performance; ensure stable ordering for reproducible counts
    candidates = candidates[:100]

    audit = audit_safe(candidates, user_profile)

    blocked_summary = [
        {
            "item": {
                "id": b["item"].get("id"),
                "name": b["item"].get("name"),
                "calories": b["item"].get("calories"),
                "tags": b["item"].get("tags", []),
                "allergens": b["item"].get("allergens", []),
            },
            "reason": b["reason"],
            "rule": b["rule"],
            "conflict": b["conflict"],
        }
        for b in audit["blocked"]
    ]

    return {
        "active_rules": _describe_active_rules(user_profile),
        "safe_count": len(audit["safe"]),
        "blocked_count": len(audit["blocked"]),
        "total_audited": len(candidates),
        "blocked_candidates": blocked_summary,
    }
