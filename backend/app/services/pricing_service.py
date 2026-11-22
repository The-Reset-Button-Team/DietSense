"""
DietSense — Indian Food Pricing & Unit Conversion Service
Evidence-based pricing calculation and unit conversion engine for Indian food items in INR (₹).

Core Features:
1. Strict unit conversion within physical dimensions (Weight, Volume, Count).
   - Rejects unsupported cross-dimension conversions (e.g. litre to grams without food density).
2. Per-unit price conversion (e.g. ₹/kg -> ₹/g, ₹/dozen -> ₹/piece, ₹/litre -> ₹/ml).
3. Indian Rupee (INR) currency formatting.
4. Food price lookups with regional prioritization (National, Delhi, Mumbai, Bengaluru, etc.).
5. Recipe and meal cost calculations with completeness validation.
"""

from typing import Optional, List, Dict, Any, Tuple
import math
import sqlite3

# ─── Unit Dimension Definitions & Base Multipliers ───────────────────────────

# Base dimension unit: gram (g)
WEIGHT_MULTIPLIERS_TO_GRAMS: Dict[str, float] = {
    "g": 1.0,
    "gram": 1.0,
    "grams": 1.0,
    "gm": 1.0,
    "gms": 1.0,
    "100g": 100.0,
    "100gm": 100.0,
    "100gms": 100.0,
    "kg": 1000.0,
    "kilogram": 1000.0,
    "kilograms": 1000.0,
    "mg": 0.001,
    "milligram": 0.001,
    "milligrams": 0.001,
}

# Base dimension unit: millilitre (ml)
VOLUME_MULTIPLIERS_TO_ML: Dict[str, float] = {
    "ml": 1.0,
    "millilitre": 1.0,
    "milliliter": 1.0,
    "millilitres": 1.0,
    "milliliters": 1.0,
    "100ml": 100.0,
    "l": 1000.0,
    "litre": 1000.0,
    "liter": 1000.0,
    "litres": 1000.0,
    "liters": 1000.0,
}

# Base dimension unit: single piece (piece)
COUNT_MULTIPLIERS_TO_PIECES: Dict[str, float] = {
    "piece": 1.0,
    "pieces": 1.0,
    "pc": 1.0,
    "pcs": 1.0,
    "unit": 1.0,
    "units": 1.0,
    "item": 1.0,
    "items": 1.0,
    "egg": 1.0,
    "eggs": 1.0,
    "banana": 1.0,
    "bananas": 1.0,
    "dozen": 12.0,
    "dozens": 12.0,
    "half_dozen": 6.0,
    "half dozen": 6.0,
}


def normalize_unit_string(unit: str) -> str:
    """Normalizes unit strings for canonical dictionary lookups."""
    if not unit:
        return ""
    clean = unit.strip().lower()
    # Normalize slashes or leading numbers
    clean = clean.replace("/ ", "/").replace(" /", "/")
    if clean.startswith("per "):
        clean = clean[4:].strip()
    return clean


def get_unit_dimension(unit: str) -> Optional[str]:
    """
    Returns the physical dimension of the unit: 'weight', 'volume', 'count', or None.
    """
    u = normalize_unit_string(unit)
    if u in WEIGHT_MULTIPLIERS_TO_GRAMS:
        return "weight"
    if u in VOLUME_MULTIPLIERS_TO_ML:
        return "volume"
    if u in COUNT_MULTIPLIERS_TO_PIECES:
        return "count"
    return None


def convert_units(quantity: float, from_unit: str, to_unit: str) -> Optional[float]:
    """
    Converts a physical quantity from one unit to another within the same dimension.
    If units belong to different dimensions (e.g. litre to grams or dozen to kg),
    returns None to prevent inaccurate or fabricated conversions.
    """
    if quantity is None:
        return None

    u_from = normalize_unit_string(from_unit)
    u_to = normalize_unit_string(to_unit)

    if u_from == u_to:
        return float(quantity)

    dim_from = get_unit_dimension(u_from)
    dim_to = get_unit_dimension(u_to)

    if not dim_from or not dim_to or dim_from != dim_to:
        # Cross-dimensional conversion without verified food density is unsupported.
        return None

    if dim_from == "weight":
        grams = quantity * WEIGHT_MULTIPLIERS_TO_GRAMS[u_from]
        return grams / WEIGHT_MULTIPLIERS_TO_GRAMS[u_to]

    if dim_from == "volume":
        ml = quantity * VOLUME_MULTIPLIERS_TO_ML[u_from]
        return ml / VOLUME_MULTIPLIERS_TO_ML[u_to]

    if dim_from == "count":
        pieces = quantity * COUNT_MULTIPLIERS_TO_PIECES[u_from]
        return pieces / COUNT_MULTIPLIERS_TO_PIECES[u_to]

    return None


def convert_price(price: float, from_unit: str, to_unit: str) -> Optional[float]:
    """
    Converts unit price (e.g., price per kg to price per gram).
    Formula: price_per_to_unit = price_per_from_unit * (amount of from_unit in 1 to_unit).
    """
    if price is None or price < 0:
        return None

    u_from = normalize_unit_string(from_unit)
    u_to = normalize_unit_string(to_unit)

    if u_from == u_to:
        return float(price)

    # 1 to_unit in from_unit:
    factor = convert_units(1.0, u_to, u_from)
    if factor is None:
        return None

    return price * factor


def format_inr(price: Optional[float], unit: Optional[str] = None) -> str:
    """
    Formats price in Indian Rupees (₹) according to DietSense specifications:
    e.g. ₹40/kg, ₹25/100g, ₹60/litre, ₹7/piece, ₹84/dozen.
    Never returns ₹0 for missing prices — returns 'Price unavailable'.
    """
    if price is None or price <= 0:
        return "Price unavailable"

    # Display clean integer if whole number, else 2 decimal places
    if isinstance(price, (int, float)) and math.isclose(price, round(price), abs_tol=1e-5):
        val_str = str(int(round(price)))
    else:
        val_str = f"{price:.2f}"

    if unit:
        clean_unit = normalize_unit_string(unit)
        return f"₹{val_str}/{clean_unit}"
    return f"₹{val_str}"


# ─── Database Price Retrieval & Lookups ───────────────────────────────────────

def get_food_price(
    cur: sqlite3.Cursor,
    food_id: int,
    region: Optional[str] = "National",
) -> Optional[Dict[str, Any]]:
    """
    Fetches the best matching price record for a food item.
    Prioritizes the requested region; falls back to 'National' or the most recent record.
    """
    clean_region = (region or "National").strip()

    cur.execute(
        """
        SELECT price_id, food_id, price, currency, unit, region, source, price_type, last_updated
        FROM food_prices
        WHERE food_id = ?
        ORDER BY 
            CASE 
                WHEN LOWER(region) = LOWER(?) THEN 1
                WHEN LOWER(region) = 'national' THEN 2
                ELSE 3
            END,
            last_updated DESC
        LIMIT 1
        """,
        (food_id, clean_region),
    )
    row = cur.fetchone()
    if not row:
        return None

    item = dict(row)
    item["formatted_price"] = format_inr(item["price"], item["unit"])
    return item


def get_all_food_prices(cur: sqlite3.Cursor, food_id: int) -> List[Dict[str, Any]]:
    """
    Fetches all price records (all regions, dates, sources) for a specific food item.
    """
    cur.execute(
        """
        SELECT price_id, food_id, price, currency, unit, region, source, price_type, last_updated
        FROM food_prices
        WHERE food_id = ?
        ORDER BY 
            CASE WHEN LOWER(region) = 'national' THEN 1 ELSE 2 END,
            region ASC,
            last_updated DESC
        """,
        (food_id,),
    )
    rows = cur.fetchall()
    results = []
    for r in rows:
        item = dict(r)
        item["formatted_price"] = format_inr(item["price"], item["unit"])
        results.append(item)
    return results


def get_available_regions(cur: sqlite3.Cursor) -> List[str]:
    """Returns a list of distinct regions with pricing data."""
    cur.execute(
        "SELECT DISTINCT region FROM food_prices WHERE region IS NOT NULL AND region != '' ORDER BY region ASC"
    )
    rows = cur.fetchall()
    regions = [r["region"] for r in rows]
    # Put National first if present
    if "National" in regions:
        regions.remove("National")
        regions.insert(0, "National")
    return regions


# ─── Recipe & Ingredient Cost Calculations ────────────────────────────────────

def calculate_ingredient_cost(
    cur: sqlite3.Cursor,
    food_id: int,
    quantity: float,
    unit: str,
    region: Optional[str] = "National",
    food_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Calculates cost for a single recipe ingredient based on its food_id and quantity/unit.
    """
    # Fetch food name if not passed
    display_name = food_name
    if not display_name:
        cur.execute("SELECT name FROM foods WHERE id = ?", (food_id,))
        f_row = cur.fetchone()
        display_name = f_row["name"] if f_row else f"Food #{food_id}"

    price_rec = get_food_price(cur, food_id, region=region)
    if not price_rec:
        return {
            "food_id": food_id,
            "food_name": display_name,
            "quantity": quantity,
            "unit": unit,
            "available": False,
            "cost": None,
            "cost_formatted": "Price unavailable",
            "unit_price": None,
            "price_unit": None,
            "region": region,
            "source": None,
            "price_type": None,
            "reason": "No price record found in database for this food.",
        }

    # Convert ingredient quantity to price unit
    converted_qty = convert_units(quantity, unit, price_rec["unit"])
    if converted_qty is None:
        return {
            "food_id": food_id,
            "food_name": display_name,
            "quantity": quantity,
            "unit": unit,
            "available": False,
            "cost": None,
            "cost_formatted": "Price unavailable",
            "unit_price": price_rec["price"],
            "price_unit": price_rec["unit"],
            "region": price_rec["region"],
            "source": price_rec["source"],
            "price_type": price_rec["price_type"],
            "reason": f"Cannot convert ingredient unit '{unit}' to price unit '{price_rec['unit']}' without density data.",
        }

    cost = round(converted_qty * price_rec["price"], 2)

    return {
        "food_id": food_id,
        "food_name": display_name,
        "quantity": quantity,
        "unit": unit,
        "available": True,
        "cost": cost,
        "cost_formatted": f"₹{cost:.2f}",
        "unit_price": price_rec["price"],
        "price_unit": price_rec["unit"],
        "currency": "INR",
        "region": price_rec["region"],
        "source": price_rec["source"],
        "price_type": price_rec["price_type"],
        "last_updated": price_rec["last_updated"],
    }


def calculate_recipe_cost(
    cur: sqlite3.Cursor,
    ingredients: List[Dict[str, Any]],
    servings: int = 1,
    region: Optional[str] = "National",
    recipe_name: Optional[str] = None,
    pantry_item_names: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Calculates the total cost and per-serving cost for a recipe.
    - If ALL ingredients have available prices: is_complete=True, total_cost=sum.
    - If ANY ingredient price is missing: is_complete=False, total_cost=None,
      partial_cost=sum(available), missing_ingredients list provided.
      NEVER outputs a misleading total when items are missing.
    - If pantry_item_names is provided, tracks pantry availability and calculates
      the additional purchase cost for missing ingredients.
    """
    ingredient_results = []
    missing_items = []
    available_costs = []
    price_types = set()

    pantry_set = {p.strip().lower() for p in (pantry_item_names or []) if p.strip()}
    pantry_matched = []
    pantry_missing = []
    missing_ing_costs = []
    missing_ing_incomplete = False

    for ing in ingredients:
        food_id = int(ing.get("food_id") or 0)
        quantity = float(ing.get("quantity") or 0.0)
        unit = str(ing.get("unit") or "g")
        name = ing.get("food_name") or ing.get("name")

        res = calculate_ingredient_cost(
            cur, food_id=food_id, quantity=quantity, unit=unit, region=region, food_name=name
        )
        display_name = res["food_name"]

        # Check pantry availability
        in_stock = False
        if pantry_set:
            norm_name = display_name.lower()
            name_words = {w for w in norm_name.replace(",", " ").replace("(", " ").replace(")", " ").split() if len(w) > 2}
            in_stock = any(
                p in norm_name or norm_name in p or bool(name_words & {w for w in p.split() if len(w) > 2})
                for p in pantry_set
            )

        res["in_pantry"] = in_stock
        if in_stock:
            pantry_matched.append(display_name)
        else:
            pantry_missing.append(display_name)
            if res["available"] and res["cost"] is not None:
                missing_ing_costs.append(res["cost"])
            else:
                missing_ing_incomplete = True

        ingredient_results.append(res)

        if res["available"] and res["cost"] is not None:
            available_costs.append(res["cost"])
            if res.get("price_type"):
                price_types.add(res["price_type"])
        else:
            missing_items.append(display_name)

    partial_sum = round(sum(available_costs), 2)
    is_complete = len(missing_items) == 0 and len(ingredient_results) > 0

    if is_complete:
        total_cost = partial_sum
        cost_per_serving = round(total_cost / max(1, servings), 2)
        total_formatted = f"₹{total_cost:.2f}"
        serving_formatted = f"₹{cost_per_serving:.2f}"
    else:
        total_cost = None
        cost_per_serving = None
        total_formatted = "Estimate incomplete (missing ingredient prices)"
        serving_formatted = "Estimate incomplete"

    # Consolidated price type
    if not price_types:
        overall_price_type = None
    elif len(price_types) == 1:
        overall_price_type = next(iter(price_types))
    else:
        overall_price_type = "mixed"

    # Additional purchase cost for ingredients not in pantry
    if pantry_item_names is not None:
        if len(pantry_missing) == 0:
            additional_cost = 0.0
            additional_cost_formatted = "₹0.00 (all in pantry)"
        elif missing_ing_incomplete:
            additional_cost = None
            additional_cost_formatted = "Incomplete cost (missing prices)"
        else:
            additional_cost = round(sum(missing_ing_costs), 2)
            additional_cost_formatted = f"₹{additional_cost:.2f}"
    else:
        additional_cost = total_cost
        additional_cost_formatted = total_formatted

    return {
        "recipe_name": recipe_name or "Custom Recipe",
        "servings": max(1, servings),
        "region": region or "National",
        "currency": "INR",
        "is_complete": is_complete,
        "total_cost": total_cost,
        "total_cost_formatted": total_formatted,
        "cost_per_serving": cost_per_serving,
        "cost_per_serving_formatted": serving_formatted,
        "partial_cost": partial_sum,
        "partial_cost_formatted": f"₹{partial_sum:.2f}",
        "price_type": overall_price_type,
        "missing_count": len(missing_items),
        "missing_ingredients": missing_items,
        "ingredients": ingredient_results,
        "pantry_matched_ingredients": pantry_matched,
        "pantry_missing_ingredients": pantry_missing,
        "missing_ingredients_cost": additional_cost,
        "missing_ingredients_cost_formatted": additional_cost_formatted,
        "pantry_coverage_pct": round(len(pantry_matched) / max(1, len(ingredient_results)) * 100) if ingredient_results else 0,
    }


def evaluate_meal_budget_status(
    cost: Optional[float],
    is_complete: bool,
    budget: Optional[float],
    tolerance_pct: float = 0.20,
) -> Dict[str, Any]:
    """
    Evaluates budget compatibility for a meal against a given budget threshold.
    Returns structured status, label, excess difference, and affordability flag.
    Never treats incomplete costs or missing prices as within budget.
    """
    if cost is None or not is_complete:
        if cost is None and not is_complete:
            return {
                "status": "incomplete_cost",
                "status_label": "Incomplete Cost Estimate",
                "cost_difference": 0.0,
                "cost_difference_formatted": "",
                "is_affordable": False,
                "fits_within_budget": False,
                "fits_slightly_above": False,
            }
        return {
            "status": "cost_unavailable",
            "status_label": "Cost Unavailable",
            "cost_difference": 0.0,
            "cost_difference_formatted": "",
            "is_affordable": False,
            "fits_within_budget": False,
            "fits_slightly_above": False,
        }

    # If no budget specified, default to unrestricted
    if budget is None or budget <= 0:
        return {
            "status": "within_budget",
            "status_label": "Within Budget",
            "cost_difference": 0.0,
            "cost_difference_formatted": "",
            "is_affordable": True,
            "fits_within_budget": True,
            "fits_slightly_above": True,
        }

    max_tolerance_budget = round(budget * (1.0 + tolerance_pct), 2)

    if cost <= budget:
        return {
            "status": "within_budget",
            "status_label": "Within Budget",
            "cost_difference": 0.0,
            "cost_difference_formatted": "",
            "is_affordable": True,
            "fits_within_budget": True,
            "fits_slightly_above": True,
        }
    elif cost <= max_tolerance_budget:
        diff = round(cost - budget, 2)
        return {
            "status": "slightly_above",
            "status_label": f"Slightly Above Budget (+₹{diff:.2f})",
            "cost_difference": diff,
            "cost_difference_formatted": f"+₹{diff:.2f}",
            "is_affordable": True,
            "fits_within_budget": False,
            "fits_slightly_above": True,
        }
    else:
        diff = round(cost - budget, 2)
        return {
            "status": "above_budget",
            "status_label": f"Above Budget (+₹{diff:.2f})",
            "cost_difference": diff,
            "cost_difference_formatted": f"+₹{diff:.2f}",
            "is_affordable": False,
            "fits_within_budget": False,
            "fits_slightly_above": False,
        }
