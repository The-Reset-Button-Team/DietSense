from fastapi import APIRouter, Query
from typing import List, Optional
from pydantic import BaseModel

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
async def search_foods(q: Optional[str] = None, category: Optional[str] = None):
    results = SAMPLE_FOODS
    if q:
        results = [f for f in results if q.lower() in f["name"].lower()]
    if category:
        results = [f for f in results if f["category"].lower() == category.lower()]
    return results
