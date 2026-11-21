"""
DietSense — Foods Router (API prefix /api/foods)
Provides comprehensive food catalog queries, full-text search, filters, sorting,
pagination, and seamless pantry integration across three views:
1. All Foods (annotated with pantry presence)
2. In My Pantry (scoped to authenticated user's active pantry)
3. Not in My Pantry (catalog foods not present in authenticated user's pantry)
"""

import math
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Query, Path, HTTPException, Depends, status
from pydantic import BaseModel

from app.core.config import settings
from app.core.dependencies import get_current_user, get_optional_current_user
from app.core.sync_service import enqueue_sync_operation
from app.services.pricing_service import (
    format_inr,
    get_food_price,
    get_all_food_prices,
)
from app.services.food_of_the_day_service import get_or_create_food_of_the_day
from db.database import get_db_cursor

router = APIRouter()


class AddToPantryRequest(BaseModel):
    quantity: Optional[str] = "1 unit"
    expiry_date: Optional[str] = None
    in_stock: Optional[bool] = True


class UpdatePantryEntryRequest(BaseModel):
    quantity: Optional[str] = None
    in_stock: Optional[bool] = None
    expiry_date: Optional[str] = None


def _format_food_row(r: Any) -> Dict[str, Any]:
    """Formats a database row into a structured food catalog item."""
    keys = r.keys() if hasattr(r, "keys") else []

    allergen_raw = r["allergen_flags"] if "allergen_flags" in keys and r["allergen_flags"] else ""
    allergens = [a.strip() for a in str(allergen_raw).split(",") if a.strip()]

    fiber_val = r["fiber_g"] if "fiber_g" in keys and r["fiber_g"] is not None else None

    price_val = float(r["price"]) if "price" in keys and r["price"] is not None else None
    price_unit = r["price_unit"] if "price_unit" in keys and r["price_unit"] else None
    price_fmt = format_inr(price_val, price_unit)

    return {
        "id": r["id"],
        "name": r["name"],
        "name_local": r["name_local"] if "name_local" in keys else None,
        "data_source": r["data_source"] if "data_source" in keys else "Catalog",
        "external_id": r["external_id"] if "external_id" in keys else None,
        "food_category": r["food_category"] if "food_category" in keys else "General",
        "calories_kcal": round(float(r["calories_kcal"]), 1) if "calories_kcal" in keys and r["calories_kcal"] is not None else 0.0,
        "protein_g": round(float(r["protein_g"]), 1) if "protein_g" in keys and r["protein_g"] is not None else 0.0,
        "carbohydrates_g": round(float(r["carbohydrates_g"]), 1) if "carbohydrates_g" in keys and r["carbohydrates_g"] is not None else 0.0,
        "fat_g": round(float(r["fat_g"]), 1) if "fat_g" in keys and r["fat_g"] is not None else 0.0,
        "fiber_g": round(float(fiber_val), 1) if fiber_val is not None else None,
        "is_vegetarian": bool(r["is_vegetarian"]) if "is_vegetarian" in keys and r["is_vegetarian"] is not None else True,
        "is_vegan": bool(r["is_vegan"]) if "is_vegan" in keys and r["is_vegan"] is not None else False,
        "is_gluten_free": bool(r["is_gluten_free"]) if "is_gluten_free" in keys and r["is_gluten_free"] is not None else True,
        "allergen_flags": allergens,
        # Pantry integration fields
        "in_pantry": bool(r["in_pantry"]) if "in_pantry" in keys else False,
        "pantry_item_id": r["pantry_item_id"] if "pantry_item_id" in keys and r["pantry_item_id"] else None,
        "pantry_quantity": r["pantry_quantity"] if "pantry_quantity" in keys and r["pantry_quantity"] else None,
        "pantry_in_stock": bool(r["pantry_in_stock"]) if "pantry_in_stock" in keys and r["pantry_in_stock"] is not None else None,
        "pantry_expiry_date": r["pantry_expiry_date"] if "pantry_expiry_date" in keys else None,
        # Pricing integration fields
        "price": price_val,
        "price_formatted": price_fmt,
        "price_unit": price_unit,
        "price_region": r["price_region"] if "price_region" in keys and r["price_region"] else None,
        "price_source": r["price_source"] if "price_source" in keys and r["price_source"] else None,
        "price_type": r["price_type"] if "price_type" in keys and r["price_type"] else None,
        "price_last_updated": r["price_last_updated"] if "price_last_updated" in keys and r["price_last_updated"] else None,
    }


@router.get("/categories")
async def get_food_categories():
    """Returns sorted distinct food categories from SQLite food catalog."""
    with get_db_cursor() as cur:
        cur.execute("SELECT DISTINCT food_category FROM foods WHERE food_category IS NOT NULL AND food_category != '' ORDER BY food_category ASC")
        rows = cur.fetchall()
        categories = [r["food_category"] for r in rows]
    return {"categories": categories}


@router.get("/food-of-the-day")
@router.get("/daily/featured")
async def get_food_of_the_day_endpoint(
    date: Optional[str] = Query(None, description="Calendar date in YYYY-MM-DD format (defaults to current day in IST)"),
    region: Optional[str] = Query("National", description="Pricing region benchmark (National, Delhi, Mumbai, Bengaluru, Kolkata)"),
    user: Optional[Dict[str, Any]] = Depends(get_optional_current_user),
):
    """
    Returns the deterministic Food of the Day for the specified or current calendar date.
    Enriched with factual nutrition per 100g, Indian pricing (verified/estimated),
    user-specific pantry status, and similar catalog foods.
    """
    user_id = user["id"] if user else None
    target_region = (region or "National").strip()
    with get_db_cursor() as cur:
        try:
            return get_or_create_food_of_the_day(cur, target_date=date, region=target_region, user_id=user_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve Food of the Day: {str(e)}")


@router.get("/")
async def list_foods(
    view: str = Query("all", pattern="^(all|in_pantry|not_in_pantry)$"),
    q: Optional[str] = None,
    category: Optional[str] = None,
    region: Optional[str] = Query("National"),
    is_vegetarian: Optional[bool] = None,
    is_vegan: Optional[bool] = None,
    is_gluten_free: Optional[bool] = None,
    min_protein: Optional[float] = None,
    max_calories: Optional[float] = None,
    sort_by: str = Query("name", pattern="^(name|calories|protein|carbs|fat|price)$"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(24, ge=1, le=100),
    user: Optional[Dict[str, Any]] = Depends(get_optional_current_user),
):
    """
    Paginated search, filter, and sorting across the 3 views:
    - 'all': All catalog foods, annotated with pantry presence
    - 'in_pantry': Only foods currently in authenticated user's pantry
    - 'not_in_pantry': Catalog foods not currently in user's pantry
    """
    user_id = user["id"] if user else None
    offset = (page - 1) * limit

    # Build price subquery for regional priority: requested region > National > any
    target_region = (region or "National").strip().replace("'", "''")
    _price_join = f"""
        LEFT JOIN (
            SELECT fp.food_id, fp.price, fp.unit AS price_unit, fp.region AS price_region,
                   fp.source AS price_source, fp.price_type, fp.last_updated AS price_last_updated
            FROM food_prices fp
            INNER JOIN (
                SELECT food_id,
                       MIN(CASE WHEN LOWER(region) = LOWER('{target_region}') THEN '1_'
                                WHEN LOWER(region) = 'national' THEN '2_'
                                ELSE '3_' END || price_id) AS best_key
                FROM food_prices
                GROUP BY food_id
            ) pref ON (CASE WHEN LOWER(fp.region) = LOWER('{target_region}') THEN '1_'
                             WHEN LOWER(fp.region) = 'national' THEN '2_'
                             ELSE '3_' END || fp.price_id) = pref.best_key
        ) pr ON pr.food_id = f.id
    """

    # Determine ordering expression
    direction = "DESC" if sort_order.lower() == "desc" else "ASC"
    if sort_by == "calories":
        order_clause = f"calories_kcal {direction}"
    elif sort_by == "protein":
        order_clause = f"protein_g {direction}"
    elif sort_by == "carbs":
        order_clause = f"carbohydrates_g {direction}"
    elif sort_by == "fat":
        order_clause = f"fat_g {direction}"
    elif sort_by == "price":
        order_clause = f"CASE WHEN pr.price IS NULL THEN 1 ELSE 0 END ASC, pr.price {direction}"
    else:  # "name"
        # Prioritize Indian ICMR_NIN catalog, then alphabetical
        order_clause = f"(CASE WHEN f.data_source = 'ICMR_NIN' THEN 0 ELSE 1 END) ASC, f.name COLLATE NOCASE {direction}"

    in_pantry_order = (
        f"COALESCE(f.name, p.name) COLLATE NOCASE {direction}"
        if sort_by == "name"
        else order_clause
    )

    with get_db_cursor() as cur:
        # Build query depending on requested view.
        # IMPORTANT: We separate the FROM+JOIN block (base_join) from the WHERE+conditions block
        # (base_where) so that _price_join (a LEFT JOIN) is always inserted BEFORE the WHERE clause.
        # Final query shape: SELECT ... {base_join} {_price_join} {base_where} ORDER BY ... LIMIT ? OFFSET ?

        if view == "in_pantry":
            if not user_id:
                # Unauthenticated users have an empty pantry
                return {
                    "items": [],
                    "total": 0,
                    "page": page,
                    "limit": limit,
                    "total_pages": 0,
                    "view": view,
                }

            base_join = """
                FROM pantry_items p
                LEFT JOIN foods f ON (
                    p.matched_food_id = f.id
                    OR (p.matched_food_id IS NULL AND LOWER(f.name) = LOWER(p.name))
                )
            """
            base_where = "WHERE p.user_id = ?"
            params: List[Any] = [user_id]

            # Common filters applied to in_pantry view
            if q and q.strip():
                clean_q = f"%{q.strip()}%"
                base_where += " AND (p.name LIKE ? OR f.name LIKE ? OR f.name_local LIKE ?)"
                params.extend([clean_q, clean_q, clean_q])
            if category and category.strip():
                base_where += " AND (f.food_category = ? OR p.category = ?)"
                params.extend([category.strip(), category.strip()])
            if is_vegetarian is not None:
                base_where += " AND COALESCE(f.is_vegetarian, 1) = ?"
                params.append(1 if is_vegetarian else 0)
            if is_vegan is not None:
                base_where += " AND COALESCE(f.is_vegan, 0) = ?"
                params.append(1 if is_vegan else 0)
            if is_gluten_free is not None:
                base_where += " AND COALESCE(f.is_gluten_free, 1) = ?"
                params.append(1 if is_gluten_free else 0)
            if min_protein is not None:
                base_where += " AND COALESCE(f.protein_g, 0.0) >= ?"
                params.append(min_protein)
            if max_calories is not None:
                base_where += " AND COALESCE(f.calories_kcal, 0.0) <= ?"
                params.append(max_calories)

            # Count total matching rows (no price join needed for count)
            cur.execute(f"SELECT COUNT(*) AS total {base_join} {base_where}", params)
            total = cur.fetchone()["total"]

            select_fields = """
                SELECT 
                    COALESCE(f.id, 0) AS id,
                    COALESCE(f.name, p.name) AS name,
                    f.name_local,
                    COALESCE(f.data_source, 'Custom') AS data_source,
                    f.external_id,
                    COALESCE(f.food_category, p.category) AS food_category,
                    COALESCE(f.calories_kcal, 0.0) AS calories_kcal,
                    COALESCE(f.protein_g, 0.0) AS protein_g,
                    COALESCE(f.carbohydrates_g, 0.0) AS carbohydrates_g,
                    COALESCE(f.fat_g, 0.0) AS fat_g,
                    f.fiber_g,
                    COALESCE(f.is_vegetarian, 1) AS is_vegetarian,
                    COALESCE(f.is_vegan, 0) AS is_vegan,
                    COALESCE(f.is_gluten_free, 1) AS is_gluten_free,
                    f.allergen_flags,
                    p.id AS pantry_item_id,
                    p.quantity AS pantry_quantity,
                    p.in_stock AS pantry_in_stock,
                    p.expiry_date AS pantry_expiry_date,
                    1 AS in_pantry,
                    pr.price, pr.price_unit, pr.price_region, pr.price_source, pr.price_type, pr.price_last_updated
            """
            cur.execute(
                f"{select_fields} {base_join} {_price_join} {base_where} ORDER BY {in_pantry_order} LIMIT ? OFFSET ?",
                params + [limit, offset],
            )
            rows = cur.fetchall()

        elif view == "not_in_pantry":
            if user_id:
                base_join = """
                    FROM foods f
                    LEFT JOIN (
                        SELECT matched_food_id, LOWER(name) AS lower_name, MAX(id) AS pantry_item_id
                        FROM pantry_items
                        WHERE user_id = ?
                        GROUP BY COALESCE(matched_food_id, LOWER(name))
                    ) p ON (
                        (p.matched_food_id IS NOT NULL AND p.matched_food_id = f.id)
                        OR (p.matched_food_id IS NULL AND p.lower_name = LOWER(f.name))
                    )
                """
                base_where = "WHERE p.pantry_item_id IS NULL"
                params = [user_id]
            else:
                base_join = "FROM foods f"
                base_where = "WHERE 1=1"
                params = []

            if q and q.strip():
                clean_q = f"%{q.strip()}%"
                base_where += " AND (f.name LIKE ? OR f.name_local LIKE ?)"
                params.extend([clean_q, clean_q])
            if category and category.strip():
                base_where += " AND f.food_category = ?"
                params.append(category.strip())
            if is_vegetarian is not None:
                base_where += " AND f.is_vegetarian = ?"
                params.append(1 if is_vegetarian else 0)
            if is_vegan is not None:
                base_where += " AND f.is_vegan = ?"
                params.append(1 if is_vegan else 0)
            if is_gluten_free is not None:
                base_where += " AND f.is_gluten_free = ?"
                params.append(1 if is_gluten_free else 0)
            if min_protein is not None:
                base_where += " AND f.protein_g >= ?"
                params.append(min_protein)
            if max_calories is not None:
                base_where += " AND f.calories_kcal <= ?"
                params.append(max_calories)

            cur.execute(f"SELECT COUNT(*) AS total {base_join} {base_where}", params)
            total = cur.fetchone()["total"]

            select_fields = """
                SELECT 
                    f.id, f.name, f.name_local, f.data_source, f.external_id, f.food_category,
                    f.calories_kcal, f.protein_g, f.carbohydrates_g, f.fat_g, f.fiber_g,
                    f.is_vegetarian, f.is_vegan, f.is_gluten_free, f.allergen_flags,
                    NULL AS pantry_item_id, NULL AS pantry_quantity, NULL AS pantry_in_stock,
                    NULL AS pantry_expiry_date, 0 AS in_pantry,
                    pr.price, pr.price_unit, pr.price_region, pr.price_source, pr.price_type, pr.price_last_updated
            """
            cur.execute(
                f"{select_fields} {base_join} {_price_join} {base_where} ORDER BY {order_clause} LIMIT ? OFFSET ?",
                params + [limit, offset],
            )
            rows = cur.fetchall()

        else:  # view == "all"
            if user_id:
                base_join = """
                    FROM foods f
                    LEFT JOIN (
                        SELECT 
                            matched_food_id,
                            LOWER(name) AS lower_name,
                            MAX(id) AS pantry_item_id,
                            MAX(quantity) AS pantry_quantity,
                            MAX(in_stock) AS pantry_in_stock,
                            MAX(expiry_date) AS pantry_expiry_date
                        FROM pantry_items
                        WHERE user_id = ?
                        GROUP BY COALESCE(matched_food_id, LOWER(name))
                    ) p ON (
                        (p.matched_food_id IS NOT NULL AND p.matched_food_id = f.id)
                        OR (p.matched_food_id IS NULL AND p.lower_name = LOWER(f.name))
                    )
                """
                base_where = "WHERE 1=1"
                params = [user_id]
                select_fields = """
                    SELECT 
                        f.id, f.name, f.name_local, f.data_source, f.external_id, f.food_category,
                        f.calories_kcal, f.protein_g, f.carbohydrates_g, f.fat_g, f.fiber_g,
                        f.is_vegetarian, f.is_vegan, f.is_gluten_free, f.allergen_flags,
                        p.pantry_item_id, p.pantry_quantity, p.pantry_in_stock, p.pantry_expiry_date,
                        CASE WHEN p.pantry_item_id IS NOT NULL THEN 1 ELSE 0 END AS in_pantry,
                        pr.price, pr.price_unit, pr.price_region, pr.price_source, pr.price_type, pr.price_last_updated
                """
            else:
                base_join = "FROM foods f"
                base_where = "WHERE 1=1"
                params = []
                select_fields = """
                    SELECT 
                        f.id, f.name, f.name_local, f.data_source, f.external_id, f.food_category,
                        f.calories_kcal, f.protein_g, f.carbohydrates_g, f.fat_g, f.fiber_g,
                        f.is_vegetarian, f.is_vegan, f.is_gluten_free, f.allergen_flags,
                        NULL AS pantry_item_id, NULL AS pantry_quantity, NULL AS pantry_in_stock,
                        NULL AS pantry_expiry_date, 0 AS in_pantry,
                        pr.price, pr.price_unit, pr.price_region, pr.price_source, pr.price_type, pr.price_last_updated
                """

            if q and q.strip():
                clean_q = f"%{q.strip()}%"
                base_where += " AND (f.name LIKE ? OR f.name_local LIKE ?)"
                params.extend([clean_q, clean_q])
            if category and category.strip():
                base_where += " AND f.food_category = ?"
                params.append(category.strip())
            if is_vegetarian is not None:
                base_where += " AND f.is_vegetarian = ?"
                params.append(1 if is_vegetarian else 0)
            if is_vegan is not None:
                base_where += " AND f.is_vegan = ?"
                params.append(1 if is_vegan else 0)
            if is_gluten_free is not None:
                base_where += " AND f.is_gluten_free = ?"
                params.append(1 if is_gluten_free else 0)
            if min_protein is not None:
                base_where += " AND f.protein_g >= ?"
                params.append(min_protein)
            if max_calories is not None:
                base_where += " AND f.calories_kcal <= ?"
                params.append(max_calories)

            cur.execute(f"SELECT COUNT(*) AS total {base_join} {base_where}", params)
            total = cur.fetchone()["total"]

            cur.execute(
                f"{select_fields} {base_join} {_price_join} {base_where} ORDER BY {order_clause} LIMIT ? OFFSET ?",
                params + [limit, offset],
            )
            rows = cur.fetchall()

    items = [_format_food_row(r) for r in rows]
    total_pages = math.ceil(total / limit) if total > 0 else 0

    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "view": view,
    }


@router.get("/{food_id}")
async def get_food_detail(
    food_id: int = Path(..., ge=1),
    region: Optional[str] = Query("National"),
    user: Optional[Dict[str, Any]] = Depends(get_optional_current_user),
):
    """
    Fetch comprehensive nutritional details, pricing breakdown, and pantry presence for a specific food.
    """
    user_id = user["id"] if user else None

    with get_db_cursor() as cur:
        cur.execute("SELECT * FROM foods WHERE id = ?", (food_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Food item not found in catalog")

        pantry_data = None
        if user_id:
            cur.execute(
                """
                SELECT id, quantity, in_stock, expiry_date, updated_at
                FROM pantry_items
                WHERE user_id = ? AND (matched_food_id = ? OR name = ? COLLATE NOCASE)
                LIMIT 1
                """,
                (user_id, food_id, row["name"]),
            )
            p_row = cur.fetchone()
            if p_row:
                pantry_data = dict(p_row)

        price_data = get_food_price(cur, food_id, region=region)
        all_prices = get_all_food_prices(cur, food_id)

    food_dict = _format_food_row(row)
    if pantry_data:
        food_dict["in_pantry"] = True
        food_dict["pantry_item_id"] = pantry_data["id"]
        food_dict["pantry_quantity"] = pantry_data["quantity"]
        food_dict["pantry_in_stock"] = bool(pantry_data["in_stock"])
        food_dict["pantry_expiry_date"] = pantry_data.get("expiry_date")

    if price_data:
        food_dict["price"] = price_data["price"]
        food_dict["price_formatted"] = price_data["formatted_price"]
        food_dict["price_unit"] = price_data["unit"]
        food_dict["price_region"] = price_data["region"]
        food_dict["price_source"] = price_data["source"]
        food_dict["price_type"] = price_data["price_type"]
        food_dict["price_last_updated"] = price_data["last_updated"]
    else:
        food_dict["price"] = None
        food_dict["price_formatted"] = "Price unavailable"
        food_dict["price_unit"] = None
        food_dict["price_region"] = None
        food_dict["price_source"] = None
        food_dict["price_type"] = None
        food_dict["price_last_updated"] = None

    food_dict["prices"] = all_prices

    return food_dict


@router.get("/{food_id}/price")
async def get_food_price_endpoint(
    food_id: int = Path(..., ge=1),
    region: Optional[str] = Query("National"),
):
    """
    Fetches the price of a specific food item in Indian Rupees (INR).
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


@router.get("/{food_id}/prices")
async def get_food_all_prices_endpoint(food_id: int = Path(..., ge=1)):
    """
    Fetches all available regional and historical price records for a specific food.
    """
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


@router.post("/{food_id}/add-to-pantry")
async def add_food_to_pantry(
    food_id: int = Path(..., ge=1),
    payload: Optional[AddToPantryRequest] = None,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Adds a catalog food to the authenticated user's pantry.
    - Prevents duplicates (updates quantity and in_stock if already present).
    - Links via stable matched_food_id without altering food catalog.
    - Enqueues cloud sync operation for Supabase replication.
    """
    user_id = user["id"]
    quantity = (payload.quantity if payload and payload.quantity else "1 unit").strip()
    expiry_date = payload.expiry_date if payload else None
    in_stock = 1 if (not payload or payload.in_stock is None or payload.in_stock) else 0
    now = datetime.now(timezone.utc).isoformat()

    with get_db_cursor() as cur:
        cur.execute("SELECT id, name, food_category FROM foods WHERE id = ?", (food_id,))
        food = cur.fetchone()
        if not food:
            raise HTTPException(status_code=404, detail="Food item not found in catalog")

        food_name = food["name"]
        food_category = food["food_category"]

        # Check if already present for this user
        cur.execute(
            """
            SELECT id, quantity, in_stock
            FROM pantry_items
            WHERE user_id = ? AND (matched_food_id = ? OR name = ? COLLATE NOCASE)
            """,
            (user_id, food_id, food_name),
        )
        existing = cur.fetchone()

        if existing:
            item_id = existing["id"]
            cur.execute(
                """
                UPDATE pantry_items
                SET in_stock = ?, quantity = ?, matched_food_id = ?, updated_at = ?
                WHERE id = ?
                """,
                (in_stock, quantity, food_id, now, item_id),
            )
            already_in_pantry = True
            msg = f"'{food_name}' is already in your pantry (quantity updated to {quantity})."
        else:
            item_id = f"pantry_{uuid.uuid4().hex[:12]}"
            cur.execute(
                """
                INSERT INTO pantry_items (
                    id, user_id, name, category, quantity, in_stock, source,
                    expiry_date, matched_food_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, 'catalog', ?, ?, ?, ?)
                """,
                (item_id, user_id, food_name, food_category, quantity, in_stock, expiry_date, food_id, now, now),
            )
            already_in_pantry = False
            msg = f"'{food_name}' added to your pantry."

        # Enqueue to sync queue for Supabase replication
        enqueue_sync_operation(
            user_id=user_id,
            entity_type="pantry_item",
            entity_id=item_id,
            operation="UPSERT",
            payload={
                "id": item_id,
                "user_id": user_id,
                "name": food_name,
                "category": food_category,
                "quantity": quantity,
                "in_stock": bool(in_stock),
                "expiry_date": expiry_date,
                "matched_food_id": food_id,
                "source": "catalog",
                "updated_at": now,
            },
            cur=cur,
        )

    return {
        "status": "success",
        "message": msg,
        "already_in_pantry": already_in_pantry,
        "pantry_item": {
            "id": item_id,
            "matched_food_id": food_id,
            "name": food_name,
            "category": food_category,
            "quantity": quantity,
            "inStock": bool(in_stock),
            "in_stock": bool(in_stock),
            "expiry_date": expiry_date,
        },
    }


@router.delete("/{food_id}/remove-from-pantry")
async def remove_food_from_pantry(
    food_id: int = Path(..., ge=1),
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Removes a catalog food from the authenticated user's pantry.
    - Scoped strictly to authenticated user's inventory.
    - Does not alter the food catalog record.
    - Enqueues cloud DELETE sync operation for Supabase replication.
    """
    user_id = user["id"]

    with get_db_cursor() as cur:
        cur.execute("SELECT name FROM foods WHERE id = ?", (food_id,))
        food = cur.fetchone()
        food_name = food["name"] if food else None

        cur.execute(
            """
            SELECT id FROM pantry_items
            WHERE user_id = ? AND (matched_food_id = ? OR (name = ? COLLATE NOCASE AND ? IS NOT NULL))
            """,
            (user_id, food_id, food_name, food_name),
        )
        existing_items = cur.fetchall()
        if not existing_items:
            raise HTTPException(status_code=404, detail="Food is not in your pantry")

        for item in existing_items:
            item_id = item["id"]
            cur.execute("DELETE FROM pantry_items WHERE id = ? AND user_id = ?", (item_id, user_id))
            enqueue_sync_operation(
                user_id=user_id,
                entity_type="pantry_item",
                entity_id=item_id,
                operation="DELETE",
                payload={"id": item_id, "user_id": user_id},
                cur=cur,
            )

    return {
        "status": "success",
        "message": f"Food #{food_id} removed from pantry.",
        "removed_food_id": food_id,
    }


@router.patch("/{food_id}/pantry-entry")
async def update_food_pantry_entry(
    food_id: int = Path(..., ge=1),
    payload: Optional[UpdatePantryEntryRequest] = None,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Updates quantity or in_stock status of a pantry item linked to food_id.
    """
    user_id = user["id"]
    now = datetime.now(timezone.utc).isoformat()

    with get_db_cursor() as cur:
        cur.execute("SELECT name, food_category FROM foods WHERE id = ?", (food_id,))
        food = cur.fetchone()
        food_name = food["name"] if food else None

        cur.execute(
            """
            SELECT id, name, category, quantity, in_stock, expiry_date
            FROM pantry_items
            WHERE user_id = ? AND (matched_food_id = ? OR (name = ? COLLATE NOCASE AND ? IS NOT NULL))
            LIMIT 1
            """,
            (user_id, food_id, food_name, food_name),
        )
        existing = cur.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Food is not in your pantry")

        item_id = existing["id"]
        new_quantity = payload.quantity if payload and payload.quantity is not None else existing["quantity"]
        new_in_stock = (1 if payload.in_stock else 0) if payload and payload.in_stock is not None else existing["in_stock"]
        new_expiry = payload.expiry_date if payload and payload.expiry_date is not None else existing["expiry_date"]

        cur.execute(
            """
            UPDATE pantry_items
            SET quantity = ?, in_stock = ?, expiry_date = ?, matched_food_id = ?, updated_at = ?
            WHERE id = ?
            """,
            (new_quantity, new_in_stock, new_expiry, food_id, now, item_id),
        )

        enqueue_sync_operation(
            user_id=user_id,
            entity_type="pantry_item",
            entity_id=item_id,
            operation="UPSERT",
            payload={
                "id": item_id,
                "user_id": user_id,
                "name": existing["name"],
                "category": existing["category"],
                "quantity": new_quantity,
                "in_stock": bool(new_in_stock),
                "expiry_date": new_expiry,
                "matched_food_id": food_id,
                "updated_at": now,
            },
            cur=cur,
        )

    return {
        "status": "success",
        "message": "Pantry entry updated.",
        "pantry_item": {
            "id": item_id,
            "matched_food_id": food_id,
            "quantity": new_quantity,
            "inStock": bool(new_in_stock),
            "in_stock": bool(new_in_stock),
            "expiry_date": new_expiry,
        },
    }
