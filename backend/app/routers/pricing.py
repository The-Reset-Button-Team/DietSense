"""
DietSense — Pricing Router (API prefix /api/pricing)
Provides endpoints for Indian food pricing, regional price lookups, unit conversions,
ingredient cost estimation, and recipe meal cost foundations.
"""

from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Query, Path, HTTPException, Body
from pydantic import BaseModel, Field

from db.database import get_db_cursor
from app.services.pricing_service import (
    get_food_price,
    get_all_food_prices,
    get_available_regions,
    calculate_ingredient_cost,
    calculate_recipe_cost,
    convert_price,
    convert_units,
    format_inr,
)

router = APIRouter(prefix="/api/pricing", tags=["Food Pricing"])


# ─── Pydantic Schemas ─────────────────────────────────────────────────────────

class IngredientItemSchema(BaseModel):
    food_id: int = Field(..., ge=1, description="Catalog Food ID")
    quantity: float = Field(..., gt=0, description="Quantity of ingredient")
    unit: str = Field(..., description="Unit (e.g. g, kg, 100g, ml, litre, piece, dozen)")
    food_name: Optional[str] = Field(default=None, description="Optional food name override")


class CalculateIngredientsRequest(BaseModel):
    ingredients: List[IngredientItemSchema] = Field(..., min_length=1)
    region: Optional[str] = Field(default="National", description="Target pricing region")


class RecipeCostRequest(BaseModel):
    recipe_name: str = Field(..., min_length=1)
    servings: int = Field(default=1, ge=1)
    ingredients: List[IngredientItemSchema] = Field(..., min_length=1)
    region: Optional[str] = Field(default="National", description="Target pricing region")


class PriceRecordInputSchema(BaseModel):
    food_id: int = Field(..., ge=1)
    price: float = Field(..., gt=0)
    currency: str = Field(default="INR")
    unit: str = Field(..., min_length=1)
    region: str = Field(default="National")
    source: str = Field(..., min_length=1)
    price_type: str = Field(..., pattern="^(verified|estimated)$")
    last_updated: Optional[str] = None


class BulkImportPricesRequest(BaseModel):
    prices: List[PriceRecordInputSchema] = Field(..., min_length=1)


class UnitConversionCheckRequest(BaseModel):
    quantity: float = Field(..., gt=0)
    from_unit: str
    to_unit: str


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.get("/regions")
async def list_pricing_regions() -> Dict[str, List[str]]:
    """Returns a list of all distinct geographic regions with pricing data."""
    with get_db_cursor() as cur:
        regions = get_available_regions(cur)
    return {"regions": regions}


@router.get("/food/{food_id}")
async def get_price_for_food(
    food_id: int = Path(..., ge=1),
    region: Optional[str] = Query("National"),
) -> Dict[str, Any]:
    """
    Fetches the price for a specific food item.
    Prioritizes requested region; falls back to 'National' or available benchmark.
    Returns 404 if food does not exist in catalog.
    If food exists but has no price record, returns available=False with 'Price unavailable'.
    """
    with get_db_cursor() as cur:
        cur.execute("SELECT id, name FROM foods WHERE id = ?", (food_id,))
        food = cur.fetchone()
        if not food:
            raise HTTPException(status_code=404, detail="Food item not found in catalog")

        price_data = get_food_price(cur, food_id, region=region)
        all_prices = get_all_food_prices(cur, food_id)

    if not price_data:
        return {
            "food_id": food_id,
            "food_name": food["name"],
            "available": False,
            "price": None,
            "price_formatted": "Price unavailable",
            "unit": None,
            "region": region,
            "source": None,
            "price_type": None,
            "last_updated": None,
            "regional_options": [],
        }

    return {
        "food_id": food_id,
        "food_name": food["name"],
        "available": True,
        "price": price_data["price"],
        "price_formatted": price_data["formatted_price"],
        "unit": price_data["unit"],
        "currency": price_data["currency"],
        "region": price_data["region"],
        "source": price_data["source"],
        "price_type": price_data["price_type"],
        "last_updated": price_data["last_updated"],
        "regional_options": all_prices,
    }


@router.get("/food/{food_id}/all")
async def get_all_prices_for_food(food_id: int = Path(..., ge=1)) -> Dict[str, Any]:
    """Returns all regional and historical price records available for a specific food."""
    with get_db_cursor() as cur:
        cur.execute("SELECT id, name FROM foods WHERE id = ?", (food_id,))
        food = cur.fetchone()
        if not food:
            raise HTTPException(status_code=404, detail="Food item not found in catalog")

        prices = get_all_food_prices(cur, food_id)

    return {
        "food_id": food_id,
        "food_name": food["name"],
        "count": len(prices),
        "prices": prices,
    }


@router.post("/calculate-ingredients")
async def calculate_ingredients_pricing(payload: CalculateIngredientsRequest) -> Dict[str, Any]:
    """
    Calculates cost per ingredient for a list of items based on Indian food unit prices.
    Accurately converts units (e.g. g -> kg, dozen -> piece, ml -> litre).
    If an ingredient has no price or conversion is unavailable, clearly indicates unavailable.
    """
    with get_db_cursor() as cur:
        items_in = [item.model_dump() for item in payload.ingredients]
        results = [
            calculate_ingredient_cost(
                cur,
                food_id=i["food_id"],
                quantity=i["quantity"],
                unit=i["unit"],
                region=payload.region,
                food_name=i.get("food_name"),
            )
            for i in items_in
        ]

    available_costs = [r["cost"] for r in results if r["available"] and r["cost"] is not None]
    all_available = len(available_costs) == len(results)

    return {
        "region": payload.region or "National",
        "currency": "INR",
        "total_items": len(results),
        "available_items_count": len(available_costs),
        "missing_items_count": len(results) - len(available_costs),
        "is_complete": all_available,
        "total_cost": round(sum(available_costs), 2) if all_available else None,
        "partial_cost": round(sum(available_costs), 2),
        "ingredients": results,
    }


@router.post("/recipe-cost")
async def calculate_recipe_pricing(payload: RecipeCostRequest) -> Dict[str, Any]:
    """
    Calculates estimated recipe cost and cost per serving.
    - If all required ingredient prices exist: returns complete cost and cost per serving.
    - If any ingredient price is missing: returns is_complete=False and total_cost=None
      with clear missing_ingredients list to avoid misleading financial estimates.
    """
    with get_db_cursor() as cur:
        items_in = [item.model_dump() for item in payload.ingredients]
        cost_report = calculate_recipe_cost(
            cur,
            ingredients=items_in,
            servings=payload.servings,
            region=payload.region,
            recipe_name=payload.recipe_name,
        )

    return cost_report


@router.post("/convert")
async def test_unit_conversion(payload: UnitConversionCheckRequest) -> Dict[str, Any]:
    """
    Helper utility to test unit conversions. Returns converted quantity or error if incompatible.
    """
    converted = convert_units(payload.quantity, payload.from_unit, payload.to_unit)
    if converted is None:
        return {
            "supported": False,
            "quantity": payload.quantity,
            "from_unit": payload.from_unit,
            "to_unit": payload.to_unit,
            "message": f"Conversion from '{payload.from_unit}' to '{payload.to_unit}' is cross-dimensional and unsupported without food density.",
        }

    return {
        "supported": True,
        "quantity": payload.quantity,
        "from_unit": payload.from_unit,
        "to_unit": payload.to_unit,
        "converted_quantity": round(converted, 5),
    }


@router.post("/record")
async def create_or_update_price_record(payload: PriceRecordInputSchema) -> Dict[str, Any]:
    """
    Controlled mechanism to add or update a food price record.
    Ensures that food nutrition data in foods table is NEVER modified.
    """
    now = datetime.now(timezone.utc).isoformat()
    date_str = payload.last_updated or now[:10]
    pid = f"prc_{payload.food_id}_{payload.region.lower()[:3]}_{uuid.uuid4().hex[:6]}"

    with get_db_cursor() as cur:
        # Check food exists
        cur.execute("SELECT id, name FROM foods WHERE id = ?", (payload.food_id,))
        food = cur.fetchone()
        if not food:
            raise HTTPException(status_code=404, detail="Food item does not exist in catalog")

        cur.execute(
            """
            INSERT INTO food_prices (
                price_id, food_id, price, currency, unit, region, source, price_type, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                pid,
                payload.food_id,
                payload.price,
                payload.currency,
                payload.unit,
                payload.region,
                payload.source,
                payload.price_type,
                date_str,
            ),
        )

    return {
        "status": "success",
        "message": f"Price record created for '{food['name']}' in region '{payload.region}'",
        "price_record": {
            "price_id": pid,
            "food_id": payload.food_id,
            "food_name": food["name"],
            "price": payload.price,
            "formatted_price": format_inr(payload.price, payload.unit),
            "unit": payload.unit,
            "currency": payload.currency,
            "region": payload.region,
            "source": payload.source,
            "price_type": payload.price_type,
            "last_updated": date_str,
        },
    }


@router.post("/import")
async def bulk_import_prices(payload: BulkImportPricesRequest) -> Dict[str, Any]:
    """
    Controlled bulk import endpoint for verified government or retail price datasets.
    """
    imported_count = 0
    now = datetime.now(timezone.utc).isoformat()

    with get_db_cursor() as cur:
        for p in payload.prices:
            cur.execute("SELECT id FROM foods WHERE id = ?", (p.food_id,))
            if not cur.fetchone():
                continue

            pid = f"prc_{p.food_id}_{p.region.lower()[:3]}_{uuid.uuid4().hex[:6]}"
            date_str = p.last_updated or now[:10]
            cur.execute(
                """
                INSERT INTO food_prices (
                    price_id, food_id, price, currency, unit, region, source, price_type, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (pid, p.food_id, p.price, p.currency, p.unit, p.region, p.source, p.price_type, date_str),
            )
            imported_count += 1

    return {
        "status": "success",
        "imported_count": imported_count,
        "total_submitted": len(payload.prices),
    }
