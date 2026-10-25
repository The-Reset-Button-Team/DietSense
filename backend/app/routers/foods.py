"""
DietSense — Foods Router (API prefix /api/foods)
Queries candidate food items from the local SQLite database.
"""

from fastapi import APIRouter, Query
from typing import List, Optional
from pydantic import BaseModel
import os
import sqlite3
from app.core.config import settings

router = APIRouter()


class FoodItemSummary(BaseModel):
    id: int
    name: str
    data_source: str
    calories_kcal: float
    protein_g: float
    carbs_g: float
    fat_g: float
    category: str
    is_vegetarian: bool
    is_gluten_free: bool


SAMPLE_FOODS = [
    {"id": 1, "name": "Rolled Oats (Avena sativa)", "data_source": "USDA", "calories_kcal": 389.0, "protein_g": 16.9, "carbs_g": 66.3, "fat_g": 6.9, "category": "cereals", "is_vegetarian": True, "is_gluten_free": False},
    {"id": 2, "name": "Moong Dal (Vigna radiata)", "data_source": "ICMR_NIN", "calories_kcal": 348.0, "protein_g": 24.0, "carbs_g": 59.8, "fat_g": 1.2, "category": "legumes", "is_vegetarian": True, "is_gluten_free": True},
    {"id": 3, "name": "Paneer / Cottage Cheese", "data_source": "ICMR_NIN", "calories_kcal": 265.0, "protein_g": 18.3, "carbs_g": 2.1, "fat_g": 20.8, "category": "dairy", "is_vegetarian": True, "is_gluten_free": True},
    {"id": 4, "name": "Curd / Dahi (Whole Milk)", "data_source": "ICMR_NIN", "calories_kcal": 60.0, "protein_g": 3.1, "carbs_g": 4.4, "fat_g": 3.2, "category": "dairy", "is_vegetarian": True, "is_gluten_free": True},
    {"id": 5, "name": "Chicken Breast (Boneless)", "data_source": "USDA", "calories_kcal": 165.0, "protein_g": 31.0, "carbs_g": 0.0, "fat_g": 3.6, "category": "poultry", "is_vegetarian": False, "is_gluten_free": True},
]


@router.get("/", response_model=List[FoodItemSummary])
async def search_foods(q: Optional[str] = None, category: Optional[str] = None, limit: int = 50):
    db_path = settings.sqlite_db_path
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            query = "SELECT id, name, data_source, food_category as category, calories_kcal, protein_g, carbohydrates_g as carbs_g, fat_g, is_vegetarian, is_gluten_free FROM foods WHERE 1=1"
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
            if rows:
                return rows
        except Exception:
            pass

    results = SAMPLE_FOODS
    if q:
        results = [f for f in results if q.lower() in f["name"].lower()]
    if category:
        results = [f for f in results if f["category"].lower() == category.lower()]
    return results[:limit]
