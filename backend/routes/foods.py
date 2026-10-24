"""
DietSense - Foods & Recipes Routes Stub
Provides food catalog search, allergen metadata, and recipe lookups.
"""

from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional, Dict, Any
import os
import sqlite3

router = APIRouter(prefix="/foods", tags=["Foods"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "database", "dietsense.db")

SAMPLE_FOODS = [
    {"id": 1, "name": "Rolled Oats (Avena sativa)", "data_source": "USDA", "food_category": "cereals", "calories_kcal": 389.0, "protein_g": 16.9, "carbohydrates_g": 66.3, "fat_g": 6.9, "is_vegetarian": True, "is_gluten_free": False, "allergen_flags": ""},
    {"id": 2, "name": "Moong Dal (Vigna radiata)", "data_source": "ICMR_NIN", "food_category": "legumes", "calories_kcal": 348.0, "protein_g": 24.0, "carbohydrates_g": 59.8, "fat_g": 1.2, "is_vegetarian": True, "is_gluten_free": True, "allergen_flags": ""},
    {"id": 3, "name": "Paneer / Cottage Cheese", "data_source": "ICMR_NIN", "food_category": "dairy", "calories_kcal": 265.0, "protein_g": 18.3, "carbohydrates_g": 2.1, "fat_g": 20.8, "is_vegetarian": True, "is_gluten_free": True, "allergen_flags": "dairy"},
    {"id": 4, "name": "Curd / Dahi (Whole Milk)", "data_source": "ICMR_NIN", "food_category": "dairy", "calories_kcal": 60.0, "protein_g": 3.1, "carbohydrates_g": 4.4, "fat_g": 3.2, "is_vegetarian": True, "is_gluten_free": True, "allergen_flags": "dairy"},
    {"id": 5, "name": "Chicken Breast (Boneless)", "data_source": "USDA", "food_category": "poultry", "calories_kcal": 165.0, "protein_g": 31.0, "carbohydrates_g": 0.0, "fat_g": 3.6, "is_vegetarian": False, "is_gluten_free": True, "allergen_flags": ""},
]


@router.get("/")
async def list_foods(q: Optional[str] = None, category: Optional[str] = None, limit: int = 50):
    """
    Query candidate food items and recipes from database with filters.
    """
    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            
            query = "SELECT id, name, name_local, data_source, food_category, calories_kcal, protein_g, carbohydrates_g, fat_g, is_vegetarian, is_vegan, is_gluten_free, allergen_flags FROM foods WHERE 1=1"
            params = []
            
            if q:
                query += " AND name LIKE ?"
                params.append(f"%{q}%")
            if category:
                query += " AND food_category LIKE ?"
                params.append(f"%{category}%")
                
            query += " LIMIT ?"
            params.append(limit)
            
            cur.execute(query, params)
            rows = [dict(row) for row in cur.fetchall()]
            conn.close()
            return rows
        except Exception:
            pass

    # Fallback to SAMPLE_FOODS
    results = SAMPLE_FOODS
    if q:
        results = [f for f in results if q.lower() in f["name"].lower()]
    if category:
        results = [f for f in results if f["food_category"].lower() == category.lower()]
    return results[:limit]


@router.get("/{food_id}")
async def get_food_detail(food_id: int):
    """
    Get detailed nutritional breakdown and allergen info for a specific item.
    """
    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM foods WHERE id = ?", (food_id,))
            row = cur.fetchone()
            conn.close()
            if row:
                return dict(row)
        except Exception:
            pass

    for f in SAMPLE_FOODS:
        if f["id"] == food_id:
            return f
    raise HTTPException(status_code=404, detail="Food item not found")

