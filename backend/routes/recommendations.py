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
        "fiber_g": 3.5,
        "food_category": "Cereals and Millets",
        "data_source": "ICMR_NIN",
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
        "food_category": "Grain Legumes and Pulses",
        "data_source": "ICMR_NIN",
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
        "food_category": "Cereals and Millets",
        "data_source": "ICMR_NIN",
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
        "food_category": "Poultry",
        "data_source": "USDA",
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
        "food_category": "Cereals and Millets",
        "data_source": "ICMR_NIN",
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
        "food_category": "Nuts and Oilseeds",
        "data_source": "ICMR_NIN",
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
        "food_category": "Milk and Milk Products",
        "data_source": "ICMR_NIN",
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
               fiber_g, is_vegetarian, is_vegan, is_gluten_free, allergen_flags, data_source
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

    fiber_val = 0.0
    if "fiber_g" in r.keys() and r["fiber_g"] is not None:
        try:
            fiber_val = float(r["fiber_g"])
        except (ValueError, TypeError):
            fiber_val = 0.0

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
        "fiber_g": fiber_val,
        "food_category": r["food_category"],
        "data_source": str(r["data_source"]) if "data_source" in r.keys() and r["data_source"] else "USDA",
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
                       fiber_g, is_vegetarian, is_vegan, is_gluten_free, allergen_flags, data_source
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

    user_profile = _normalize_profile(user_profile)
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
    shuffle: bool = False,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Single-slot regeneration endpoint. Returns 3 to 5 alternative foods
    ranked by the full ML pipeline (safety gate → TF-IDF → scoring →
    adaptive penalties → pantry bonus → explainability).

    Path parameter ``slot_id`` must be one of:
        early_morning, breakfast, lunch, evening_snack, dinner

    Request body is the same ``user_profile`` dict as ``POST /recommendations/``.
    Supports optional ``shuffle: bool`` in query or body to re-sample candidates from SQLite.
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

    is_shuffle = shuffle or bool(user_profile.get("shuffle", False))
    user_profile = _normalize_profile(user_profile)

    top_n = int(user_profile.get("top_n", 5))
    if top_n < 3:
        top_n = 3
    elif top_n > 5:
        top_n = 5

    user_id = current_user["id"]
    meal_logs = get_user_meal_logs(user_id)
    pantry_items = _get_pantry_items(user_id)

    candidates = load_candidate_foods(slot_id=slot_id, shuffle=is_shuffle)
    if not candidates:
        # Fallback: slot filtered everything — return empty list gracefully
        return []

    results = recommend(
        user_profile=user_profile,
        candidates=candidates,
        meal_logs=meal_logs,
        top_n=top_n,
        pantry_items=pantry_items,
    )
    return results


@router.post("/daily")
async def generate_daily_recommendations(
    payload: Dict[str, Any],
    shuffle: bool = False,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Generate evidence-based daily meal plan recommendations from the SQLite food catalog.
    Returns 3 to 5 alternative recommendations for each active meal slot,
    filtered by safety gate (dietary restrictions & declared allergens),
    scored with respect to calorie and macro targets, and calculated daily nutrition totals.
    Supports per-slot shuffle or whole-plan shuffle.
    """
    user_profile = payload.get("user_profile", payload)
    if "user_profile" in user_profile and isinstance(user_profile["user_profile"], dict):
        user_profile = user_profile["user_profile"]

    user_profile = _normalize_profile(user_profile)
    user_id = current_user["id"]
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
    if top_n < 3:
        top_n = 3
    elif top_n > 5:
        top_n = 5

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

    for slot_id in ["early_morning", "breakfast", "lunch", "evening_snack", "dinner"]:
        if not active_slots.get(slot_id):
            continue

        weight = SLOT_CALORIE_WEIGHTS.get(slot_id, 0.25)
        norm_ratio = weight / total_active_weight
        slot_target_cals = total_target_cals * norm_ratio

        slot_profile = dict(user_profile)
        slot_profile["target_calories"] = total_target_cals
        slot_profile["slot_target_calories"] = slot_target_cals

        slot_shuffle = is_shuffle or (shuffle_slot == slot_id)
        candidates = load_candidate_foods(slot_id=slot_id, shuffle=slot_shuffle)

        recs = recommend(
            user_profile=slot_profile,
            candidates=candidates,
            meal_logs=meal_logs,
            top_n=top_n,
            pantry_items=pantry_items,
        )

        slot_results[slot_id] = recs

        if recs:
            first_item = recs[0]["item"]
            total_cals += float(first_item.get("calories", 0))
            total_prot += float(first_item.get("protein_g", 0))
            total_carbs += float(first_item.get("carbs_g", 0))
            total_fat += float(first_item.get("fat_g", 0))
            total_fiber += float(first_item.get("fiber_g", 0))

    return {
        "slots": slot_results,
        "totals": {
            "calories": round(total_cals),
            "protein_g": round(total_prot, 1),
            "carbs_g": round(total_carbs, 1),
            "fat_g": round(total_fat, 1),
            "fiber_g": round(total_fiber, 1),
        },
    }
