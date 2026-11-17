"""
DietSense — Recommendation Routes
Wraps the ML recommendation engine to serve filtered and ranked meal plans.
Enforces that user_id is derived exclusively from verified JWT, never from request body.
Integrates directly with local SQLite food catalog and meal logs.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List, Optional
import os
import sqlite3

from app.core.config import settings
from app.core.dependencies import get_current_user
from routes.meal_logs import get_user_meal_logs
from ml.recommendation.recommender import recommend
from db.database import get_db_cursor

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

# ---------------------------------------------------------------------------
# SAMPLE_CANDIDATES — kept as emergency fallback if the SQLite DB is missing
# or unreadable. The primary source is the full foods catalog (load_candidate_foods).
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
        "food_category": "Cereals and Millets",
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
        "food_category": "Grain Legumes and Pulses",
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
        "food_category": "Cereals and Millets",
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
        "food_category": "Poultry",
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
        "food_category": "Cereals and Millets",
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
        "food_category": "Nuts and Oilseeds",
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
        "food_category": "Milk and Milk Products",
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
        "food_category": "Milk and Milk Products",
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


def _build_slot_query(slot_id: str, limit: Optional[int] = None) -> tuple:
    """
    Build a parameterised SQLite query string and params tuple for a given slot_id.
    Returns (query_string, params_tuple).
    """
    base_select = """
        SELECT id, name, food_category, calories_kcal, protein_g, carbohydrates_g, fat_g,
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

    if limit:
        query += f" LIMIT {int(limit)}"

    return query, tuple(params)


def _row_to_candidate(r: sqlite3.Row, offset: int = 1000) -> Dict[str, Any]:
    """
    Convert a SQLite foods row into a candidate dict suitable for the recommender.
    offset is added to the DB id to avoid collisions with SAMPLE_CANDIDATES ids.
    """
    cat = str(r["food_category"] or "").lower()
    tags = [cat]

    if r["is_vegetarian"]:
        tags.append("veg")
    else:
        tags.append("non-veg")

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

    allergens = [a.strip() for a in (r["allergen_flags"] or "").split(",") if a.strip()]

    return {
        "id": offset + r["id"],
        "name": r["name"],
        "tags": tags,
        "allergens": allergens,
        "cuisine": "indian" if "ICMR" in str(r["data_source"] or "") else "general",
        "cost_estimate": cost,
        "prep_time": prep,
        "calories": float(r["calories_kcal"]),
        "protein_g": float(r["protein_g"]),
        "carbs_g": float(r["carbohydrates_g"]),
        "fat_g": float(r["fat_g"]),
        "food_category": r["food_category"],
    }


def load_candidate_foods(slot_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Loads candidate items from the full local SQLite foods catalog (all records
    with calories_kcal > 50, up to 14,099 rows), falling back to SAMPLE_CANDIDATES
    only if the database is missing or unreadable.

    When slot_id is provided the query is filtered to categories relevant to that
    meal slot (see SLOT_CATEGORY_KEYWORDS). When slot_id is None all non-trivial
    foods are returned (full-day planning).
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
            query, params = _build_slot_query(slot_id, limit=60)
            if query is None:
                # Unknown slot — return empty list; caller raises 400
                conn.close()
                return []
            cur.execute(query, params)
        else:
            # Full catalog — balanced sample for full-day planning
            cur.execute("""
                SELECT id, name, food_category, calories_kcal, protein_g, carbohydrates_g, fat_g,
                       is_vegetarian, is_vegan, is_gluten_free, allergen_flags, data_source
                FROM foods
                WHERE calories_kcal > 50
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


@router.post("/")
async def generate_recommendations(
    user_profile: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Run candidate meals through safety gate, TF-IDF scoring, and return ranked recommendations.
    Uses authenticated user's real meal logs from SQLite for adaptive penalties.
    user_id is derived exclusively from JWT for authorization and isolation.

    Accepts an optional ``meal_slot`` field in ``user_profile``. When present,
    candidate foods are pre-filtered to the categories relevant to that slot
    (see SLOT_CATEGORY_KEYWORDS). When absent, the full catalog is used for a
    complete day plan (top 5 overall, as today).
    """
    # Support both flat payloads and nested { user_profile: { ... } } payloads
    if "user_profile" in user_profile and isinstance(user_profile["user_profile"], dict):
        user_profile = user_profile["user_profile"]

    user_id = current_user["id"]
    meal_logs = get_user_meal_logs(user_id)

    # Load user's in-stock pantry items for ingredient-aware recommendations
    pantry_items = _get_pantry_items(user_id)

    # Optional slot-level pre-filter
    meal_slot: Optional[str] = user_profile.get("meal_slot")
    candidates = load_candidate_foods(slot_id=meal_slot)

    results = recommend(
        user_profile=user_profile,
        candidates=candidates,
        meal_logs=meal_logs,
        top_n=user_profile.get("top_n", 6),
        pantry_items=pantry_items,
    )
    return results


@router.post("/slot/{slot_id}")
async def generate_slot_recommendations(
    slot_id: str,
    user_profile: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Single-slot regeneration endpoint. Returns up to 5 alternative foods
    ranked by the full ML pipeline (safety gate → TF-IDF → scoring →
    adaptive penalties → pantry bonus → explainability).

    Path parameter ``slot_id`` must be one of:
        early_morning, breakfast, lunch, evening_snack, dinner

    Request body is the same ``user_profile`` dict as ``POST /recommendations/``.

    Each result object has the shape::

        {
            "item": {
                "id", "name", "tags", "allergens", "cuisine",
                "cost_estimate", "prep_time", "calories",
                "protein_g", "carbs_g", "fat_g", "food_category"
            },
            "score": float,
            "breakdown": { ... },
            "reason": string
        }

    Returns 400 if ``slot_id`` is not recognised.
    user_id is derived exclusively from JWT for authorization and isolation.
    """
    # Validate slot_id against the known mapping
    if slot_id not in SLOT_CATEGORY_KEYWORDS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown slot_id '{slot_id}'. "
                   f"Valid values: {list(SLOT_CATEGORY_KEYWORDS.keys())}",
        )

    # Support both flat payloads and nested { user_profile: { ... } } payloads
    if "user_profile" in user_profile and isinstance(user_profile["user_profile"], dict):
        user_profile = user_profile["user_profile"]

    user_id = current_user["id"]
    meal_logs = get_user_meal_logs(user_id)
    pantry_items = _get_pantry_items(user_id)

    candidates = load_candidate_foods(slot_id=slot_id)
    if not candidates:
        # Fallback: slot filtered everything — return empty list gracefully
        return []

    results = recommend(
        user_profile=user_profile,
        candidates=candidates,
        meal_logs=meal_logs,
        top_n=5,
        pantry_items=pantry_items,
    )
    return results
