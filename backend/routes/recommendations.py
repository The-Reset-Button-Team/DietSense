"""
DietSense — Recommendation Routes
Wraps the ML recommendation engine to serve filtered and ranked meal plans.
Enforces that user_id is derived exclusively from verified JWT, never from request body.
Integrates directly with local SQLite food catalog and meal logs.
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any, List
import os
import sqlite3

from app.core.config import settings
from app.core.dependencies import get_current_user
from routes.meal_logs import get_user_meal_logs
from ml.recommendation.recommender import recommend
from db.database import get_db_cursor

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

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
    },
]


def load_candidate_foods() -> List[Dict[str, Any]]:
    """Loads candidate items from local SQLite foods catalog, falling back to rich candidates."""
    candidates = list(SAMPLE_CANDIDATES)
    db_path = settings.sqlite_db_path
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("""
                SELECT id, name, food_category, calories_kcal, protein_g, carbohydrates_g, fat_g,
                       is_vegetarian, is_vegan, is_gluten_free, allergen_flags, data_source
                FROM foods
                WHERE calories_kcal > 50
                LIMIT 40
            """)
            db_foods = cur.fetchall()
            conn.close()
            for r in db_foods:
                cat = str(r["food_category"]).lower()
                tags = [cat]
                if r["is_vegetarian"]:
                    tags.append("veg")
                else:
                    tags.append("non-veg")
                if r["is_gluten_free"]:
                    tags.append("gluten-free")

                # Derive prep time and cost estimate from category
                is_meat = any(w in cat for w in ["poultry", "meat", "fish", "beef", "pork", "seafood"])
                prep = 30 if is_meat else (20 if "legume" in cat or "pulse" in cat else 15)
                cost = 150 if is_meat else (80 if "nut" in cat or "dairy" in cat else 50)

                # Derive penalty tags with documented thresholds
                if prep > 25:
                    tags.append("long-prep-time")
                else:
                    tags.append("quick")

                if cost > 100:
                    tags.append("expensive")

                allergens = [a.strip() for a in (r["allergen_flags"] or "").split(",") if a.strip()]

                candidates.append({
                    "id": 1000 + r["id"],
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
                })
        except Exception:
            pass
    return candidates


@router.post("/")
async def generate_recommendations(
    user_profile: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Run candidate meals through safety gate, TF-IDF scoring, and return ranked recommendations.
    Uses authenticated user's real meal logs from SQLite for adaptive penalties.
    user_id is derived exclusively from JWT for authorization and isolation.
    """
    user_id = current_user["id"]
    meal_logs = get_user_meal_logs(user_id)

    # Load user's in-stock pantry items for ingredient-aware recommendations
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

    candidates = load_candidate_foods()
    results = recommend(
        user_profile=user_profile,
        candidates=candidates,
        meal_logs=meal_logs,
        top_n=user_profile.get("top_n", 6),
        pantry_items=pantry_items,
    )
    return results
