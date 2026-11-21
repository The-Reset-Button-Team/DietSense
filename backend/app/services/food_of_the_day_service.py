"""
DietSense — Food of the Day Service
Provides deterministic daily food selection, factual nutritional & culinary profiles,
pricing integration, pantry presence checks, and similar food recommendations.
Never invents nutrition values or prices; always grounded in database records.
"""

import hashlib
import math
from datetime import datetime, timezone, date, timedelta
from typing import Dict, Any, List, Optional
import sqlite3

from app.services.pricing_service import get_food_price, get_all_food_prices, format_inr


# Curated culinary and preparation knowledge base mapped to Indian food categories and staples
CATEGORY_FACTS = {
    "Cereals and Millets": {
        "intro": "A traditional Indian staple grain providing complex carbohydrates and sustained dietary energy.",
        "usage": "Widely consumed as rotis, khichdi, porridges, and fermented batters across Indian households.",
        "prep": "Rinse thoroughly; for whole millets or unpolished grains, soak for 2-4 hours before boiling or pressure cooking. Often ground into flour for flatbreads.",
    },
    "Grain Legumes": {
        "intro": "A primary vegetarian source of protein in the Indian diet, rich in essential amino acids and soluble fiber.",
        "usage": "Used in daily dals, sambars, sprouts, curries, and savory snacks like chillas and vadas.",
        "prep": "Wash until water runs clear. Soak for 30-60 minutes (split dals) or 6-8 hours (whole legumes). Pressure cook with turmeric, salt, and temper with ghee, cumin, and hing.",
    },
    "Green Leafy Vegetables": {
        "intro": "A nutrient-dense leafy vegetable packed with vital dietary minerals, folates, and plant antioxidants.",
        "usage": "Stir-fried as saag, blended into curries like palak paneer, or mixed into parathas and dal.",
        "prep": "Wash leaves thoroughly in salted cold water to remove soil. Steam, blanch, or gently saute with garlic and mustard seeds to retain heat-sensitive vitamins.",
    },
    "Other Vegetables": {
        "intro": "A wholesome dietary vegetable contributing micronutrients, natural hydration, and fiber.",
        "usage": "Core ingredient in subzis, curries, gravies, raitas, and mixed vegetable preparations.",
        "prep": "Peel if necessary and chop uniformly. Steam, roast, or saute with mild Indian spices like cumin, coriander, and turmeric.",
    },
    "Roots and Tubers": {
        "intro": "A hearty starchy vegetable providing readily accessible culinary energy and dietary potassium.",
        "usage": "Staple in curries, dry roasts, flatbread fillings (aloo paratha), and blended thickeners.",
        "prep": "Boil with skin intact to retain vitamins, peel when cooled, or cut into cubes for curries and baking.",
    },
    "Fruits": {
        "intro": "A naturally refreshing seasonal fruit offering dietary fiber, vitamin complexes, and natural hydration.",
        "usage": "Eaten fresh as a mid-morning or pre-workout snack, added to fruit chaats, smoothies, and curd bowls.",
        "prep": "Rinse under cold running water. Consume whole or freshly sliced to minimize exposure to atmospheric oxidation.",
    },
    "Milk and Milk Products": {
        "intro": "A complete dairy protein source providing bioavailable calcium, riboflavin, and healthy fats.",
        "usage": "Consumed directly as warm milk, cultured into dahi (yogurt), paneer, chaas (buttermilk), and ghee.",
        "prep": "Boil milk before consumption. For paneer, curd lightly with lemon juice or vinegar, drain whey, and press.",
    },
    "Nuts and Oil Seeds": {
        "intro": "A concentrated nutritional package rich in heart-healthy unsaturated fatty acids, plant protein, and vitamin E.",
        "usage": "Eaten raw, roasted as snacks, garnished over curries, or ground into rich gravies and chutneys.",
        "prep": "Soaking overnight softens cell walls and improves micronutrient bioavailability; light dry-roasting enhances flavor.",
    },
    "Condiments and Spices": {
        "intro": "An aromatic Indian spice with traditional culinary significance, rich in natural phytochemical compounds.",
        "usage": "Used in tadkas (tempering), curry pastes, garam masalas, and herbal teas (kadhas).",
        "prep": "Bloom whole spices in warm oil or ghee at the start of cooking, or dry-roast and grind into fresh powders.",
    },
}

DEFAULT_FACTS = {
    "intro": "A nutritious food item from the verified DietSense catalog contributing essential dietary nutrients.",
    "usage": "Incorporated into balanced daily meals according to dietary preferences and culinary traditions.",
    "prep": "Wash, prepare according to standard culinary methods, and pair with diverse food groups for optimal nutrient absorption.",
}


def _get_today_date_str() -> str:
    """Returns today's date in YYYY-MM-DD format (IST timezone)."""
    # Indian Standard Time is UTC+5:30
    ist_offset = timedelta(hours=5, minutes=30)
    now_ist = datetime.now(timezone.utc) + ist_offset
    return now_ist.strftime("%Y-%m-%d")


def _generate_factual_profile(food: Dict[str, Any]) -> Dict[str, str]:
    """
    Generates factual, evidence-based descriptions for a food item.
    Avoids all medical/therapeutic claims. Grounded strictly in database values.
    """
    category = food.get("food_category", "General")
    facts = CATEGORY_FACTS.get(category, DEFAULT_FACTS)

    name = food.get("name", "This food")
    local = food.get("name_local")
    local_part = f" (known locally as {local})" if local and local != name else ""

    calories = round(float(food.get("calories_kcal", 0)), 1)
    protein = round(float(food.get("protein_g", 0)), 1)
    carbs = round(float(food.get("carbohydrates_g", 0)), 1)
    fat = round(float(food.get("fat_g", 0)), 1)
    fiber = food.get("fiber_g")
    fiber_val = round(float(fiber), 1) if fiber is not None else 0.0

    # Build descriptive highlights
    highlights = []
    if protein >= 10.0:
        highlights.append(f"high protein content ({protein}g per 100g)")
    elif protein >= 5.0:
        highlights.append(f"moderate protein ({protein}g per 100g)")

    if fiber_val >= 5.0:
        highlights.append(f"high dietary fiber ({fiber_val}g per 100g)")
    elif fiber_val >= 2.0:
        highlights.append(f"good source of fiber ({fiber_val}g)")

    if carbs >= 40.0:
        highlights.append("rich in complex carbohydrates")

    if fat < 2.0:
        highlights.append("naturally low in fat")
    elif fat >= 15.0:
        highlights.append("contains calorie-dense healthy fats")

    highlights_str = ", ".join(highlights) if highlights else "a balanced macronutrient profile"

    short_intro = f"{name}{local_part} is {facts['intro']} It features {highlights_str}."

    description_paragraphs = [
        (
            f"{name}{local_part} is classified under the '{category}' category. "
            f"Per 100g reference serving, it provides {calories} kcal of energy, {protein}g of protein, "
            f"{carbs}g of carbohydrates, and {fat}g of fat"
            + (f" along with {fiber_val}g of dietary fiber." if fiber_val > 0 else ".")
        ),
        (
            f"From a nutritional standpoint, {name} provides {highlights_str}. "
            f"In everyday dining, it is widely utilized for {facts['usage'].lower()} "
            f"Pairing it with complementary ingredients ensures balanced macronutrient distribution throughout the day."
        ),
    ]

    return {
        "short_intro": short_intro,
        "description": "\n\n".join(description_paragraphs),
        "common_usage": facts["usage"],
        "preparation_methods": facts["prep"],
    }


def get_candidate_food_ids(cur: sqlite3.Cursor, exclude_ids: List[int]) -> List[int]:
    """
    Selects candidate food IDs for daily feature:
    - Filters for nutritional completeness (calories > 0, protein > 0)
    - Excludes recently featured foods
    - Prioritizes:
      1. ICMR-NIN Indian foods with pricing records
      2. Any food with pricing records
      3. ICMR-NIN Indian foods with rich nutrition
      4. General catalog foods with full macro profiles
    """
    exclude_clause = ""
    params: List[Any] = []
    if exclude_ids:
        placeholders = ",".join(["?"] * len(exclude_ids))
        exclude_clause = f"AND f.id NOT IN ({placeholders})"
        params = list(exclude_ids)

    # Priority 1: Indian ICMR-NIN foods that have pricing in food_prices
    query_p1 = f"""
        SELECT DISTINCT f.id
        FROM foods f
        INNER JOIN food_prices fp ON fp.food_id = f.id
        WHERE f.calories_kcal > 0 AND f.protein_g > 0
          AND f.data_source = 'ICMR_NIN'
          {exclude_clause}
        ORDER BY f.id ASC
    """
    cur.execute(query_p1, params)
    p1_ids = [r["id"] for r in cur.fetchall()]
    if p1_ids:
        return p1_ids

    # Priority 2: Any food that has pricing in food_prices
    query_p2 = f"""
        SELECT DISTINCT f.id
        FROM foods f
        INNER JOIN food_prices fp ON fp.food_id = f.id
        WHERE f.calories_kcal > 0 AND f.protein_g > 0
          {exclude_clause}
        ORDER BY f.id ASC
    """
    cur.execute(query_p2, params)
    p2_ids = [r["id"] for r in cur.fetchall()]
    if p2_ids:
        return p2_ids

    # Priority 3: ICMR-NIN Indian foods with positive calories & protein
    query_p3 = f"""
        SELECT f.id
        FROM foods f
        WHERE f.calories_kcal > 0 AND f.protein_g > 0
          AND f.data_source = 'ICMR_NIN'
          {exclude_clause}
        ORDER BY f.id ASC
    """
    cur.execute(query_p3, params)
    p3_ids = [r["id"] for r in cur.fetchall()]
    if p3_ids:
        return p3_ids

    # Priority 4: All catalog foods with complete macro data
    query_p4 = f"""
        SELECT f.id
        FROM foods f
        WHERE f.calories_kcal > 0 AND f.protein_g > 0
          {exclude_clause}
        ORDER BY f.id ASC
        LIMIT 100
    """
    cur.execute(query_p4, params)
    p4_ids = [r["id"] for r in cur.fetchall()]
    if p4_ids:
        return p4_ids

    # If completely exhausted due to exclusions, fallback to all foods with pricing ignoring exclusions
    cur.execute("""
        SELECT DISTINCT f.id
        FROM foods f
        INNER JOIN food_prices fp ON fp.food_id = f.id
        WHERE f.calories_kcal > 0 AND f.protein_g > 0
        ORDER BY f.id ASC
    """)
    return [r["id"] for r in cur.fetchall()]


def get_or_create_food_of_the_day(
    cur: sqlite3.Cursor,
    target_date: Optional[str] = None,
    region: str = "National",
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retrieves or deterministically selects the Food of the Day for target_date.
    - Persisted in daily_featured_foods table for deterministic consistency throughout the day.
    - Avoids repeats from the last 30 days.
    - Enriched with regional pricing, nutritional micronutrients, and user-specific pantry status.
    """
    date_str = target_date.strip() if target_date and target_date.strip() else _get_today_date_str()

    # 1. Check if already selected and stored for this calendar date
    cur.execute(
        """
        SELECT d.feature_date, d.food_id, d.short_intro, d.description,
               d.common_usage, d.preparation_methods, d.image_url, d.created_at
        FROM daily_featured_foods d
        WHERE d.feature_date = ?
        LIMIT 1
        """,
        (date_str,),
    )
    existing_featured = cur.fetchone()

    if existing_featured:
        food_id = existing_featured["food_id"]
        short_intro = existing_featured["short_intro"]
        description = existing_featured["description"]
        common_usage = existing_featured["common_usage"]
        prep_methods = existing_featured["preparation_methods"]
        image_url = existing_featured["image_url"]
    else:
        # 2. Need to select a food for this date
        # Query recently featured food IDs within the last 30 days (excluding today)
        cur.execute(
            """
            SELECT food_id
            FROM daily_featured_foods
            WHERE feature_date < ? AND feature_date >= date(?, '-30 days')
            """,
            (date_str, date_str),
        )
        recent_ids = [r["food_id"] for r in cur.fetchall()]

        candidates = get_candidate_food_ids(cur, recent_ids)
        if not candidates:
            raise RuntimeError("No candidate foods available in database for daily feature selection")

        # Deterministic pseudo-random selection based on date string hash
        seed_hash = hashlib.sha256(f"dietsense_fotd_{date_str}".encode()).hexdigest()
        selected_index = int(seed_hash, 16) % len(candidates)
        food_id = candidates[selected_index]

        # Fetch the selected food's attributes to generate factual editorial profile
        cur.execute("SELECT * FROM foods WHERE id = ?", (food_id,))
        food_raw = cur.fetchone()
        if not food_raw:
            raise RuntimeError(f"Candidate food id {food_id} not found in foods table")

        food_dict = dict(food_raw)
        profile = _generate_factual_profile(food_dict)
        short_intro = profile["short_intro"]
        description = profile["description"]
        common_usage = profile["common_usage"]
        prep_methods = profile["preparation_methods"]
        image_url = None

        # Insert into daily_featured_foods table for persistence
        now_iso = datetime.now(timezone.utc).isoformat()
        cur.execute(
            """
            INSERT OR REPLACE INTO daily_featured_foods (
                feature_date, food_id, short_intro, description,
                common_usage, preparation_methods, image_url, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (date_str, food_id, short_intro, description, common_usage, prep_methods, image_url, now_iso),
        )

    # 3. Fetch comprehensive food nutrition details
    cur.execute("SELECT * FROM foods WHERE id = ?", (food_id,))
    food_row = cur.fetchone()
    if not food_row:
        raise RuntimeError(f"Featured food #{food_id} not found in catalog")

    keys = food_row.keys()

    # Parse allergen flags
    allergen_raw = food_row["allergen_flags"] if "allergen_flags" in keys and food_row["allergen_flags"] else ""
    allergens = [a.strip() for a in str(allergen_raw).split(",") if a.strip()]

    # 4. Fetch Pricing via pricing_service
    price_info = get_food_price(cur, food_id, region=region)
    all_prices = get_all_food_prices(cur, food_id)

    if price_info:
        pricing_data = {
            "available": True,
            "price": price_info["price"],
            "formatted_price": price_info["formatted_price"],
            "currency": price_info["currency"],
            "unit": price_info["unit"],
            "region": price_info["region"],
            "source": price_info["source"],
            "price_type": price_info["price_type"],
            "last_updated": price_info["last_updated"],
            "regional_options": all_prices,
        }
    else:
        pricing_data = {
            "available": False,
            "price": None,
            "formatted_price": "Price unavailable",
            "currency": "INR",
            "unit": None,
            "region": region,
            "source": None,
            "price_type": None,
            "last_updated": None,
            "regional_options": [],
        }

    # 5. Fetch Pantry Presence if user_id is provided
    pantry_data = {
        "in_pantry": False,
        "pantry_item_id": None,
        "pantry_quantity": None,
        "pantry_in_stock": None,
        "pantry_expiry_date": None,
    }

    if user_id:
        cur.execute(
            """
            SELECT id, quantity, in_stock, expiry_date
            FROM pantry_items
            WHERE user_id = ? AND (matched_food_id = ? OR name = ? COLLATE NOCASE)
            LIMIT 1
            """,
            (user_id, food_id, food_row["name"]),
        )
        p_row = cur.fetchone()
        if p_row:
            p_dict = dict(p_row)
            pantry_data["in_pantry"] = True
            pantry_data["pantry_item_id"] = p_dict["id"]
            pantry_data["pantry_quantity"] = p_dict["quantity"]
            pantry_data["pantry_in_stock"] = bool(p_dict["in_stock"])
            pantry_data["pantry_expiry_date"] = p_dict.get("expiry_date")

    # 6. Fetch Similar Foods from same category
    category = food_row["food_category"] if "food_category" in keys else "General"
    similar_foods = get_similar_foods(cur, food_id, category, region=region, limit=4)

    # 7. Assemble Complete Response
    return {
        "date": date_str,
        "food": {
            "id": food_row["id"],
            "name": food_row["name"],
            "name_local": food_row["name_local"] if "name_local" in keys else None,
            "food_category": category,
            "data_source": food_row["data_source"] if "data_source" in keys else "Catalog",
            "external_id": food_row["external_id"] if "external_id" in keys else None,
            # Macronutrients per 100g
            "calories_kcal": round(float(food_row["calories_kcal"]), 1) if food_row["calories_kcal"] is not None else 0.0,
            "protein_g": round(float(food_row["protein_g"]), 1) if food_row["protein_g"] is not None else 0.0,
            "carbohydrates_g": round(float(food_row["carbohydrates_g"]), 1) if food_row["carbohydrates_g"] is not None else 0.0,
            "fat_g": round(float(food_row["fat_g"]), 1) if food_row["fat_g"] is not None else 0.0,
            "fiber_g": round(float(food_row["fiber_g"]), 1) if "fiber_g" in keys and food_row["fiber_g"] is not None else None,
            # Micronutrients (only non-null, actual database values)
            "micronutrients": {
                "calcium_mg": round(float(food_row["calcium_mg"]), 1) if "calcium_mg" in keys and food_row["calcium_mg"] is not None else None,
                "iron_mg": round(float(food_row["iron_mg"]), 2) if "iron_mg" in keys and food_row["iron_mg"] is not None else None,
                "zinc_mg": round(float(food_row["zinc_mg"]), 2) if "zinc_mg" in keys and food_row["zinc_mg"] is not None else None,
                "vitamin_c_mg": round(float(food_row["vitamin_c_mg"]), 1) if "vitamin_c_mg" in keys and food_row["vitamin_c_mg"] is not None else None,
                "vitamin_a_mcg": round(float(food_row["vitamin_a_mcg"]), 1) if "vitamin_a_mcg" in keys and food_row["vitamin_a_mcg"] is not None else None,
                "vitamin_d_mcg": round(float(food_row["vitamin_d_mcg"]), 1) if "vitamin_d_mcg" in keys and food_row["vitamin_d_mcg"] is not None else None,
                "potassium_mg": round(float(food_row["potassium_mg"]), 1) if "potassium_mg" in keys and food_row["potassium_mg"] is not None else None,
                "sodium_mg": round(float(food_row["sodium_mg"]), 1) if "sodium_mg" in keys and food_row["sodium_mg"] is not None else None,
            },
            # Dietary & Allergen Attributes
            "is_vegetarian": bool(food_row["is_vegetarian"]) if "is_vegetarian" in keys and food_row["is_vegetarian"] is not None else True,
            "is_vegan": bool(food_row["is_vegan"]) if "is_vegan" in keys and food_row["is_vegan"] is not None else False,
            "is_gluten_free": bool(food_row["is_gluten_free"]) if "is_gluten_free" in keys and food_row["is_gluten_free"] is not None else True,
            "allergen_flags": allergens,
            # Pricing
            "pricing": pricing_data,
            # Pantry Presence
            "pantry": pantry_data,
            # Editorial & Food Knowledge
            "editorial": {
                "short_intro": short_intro,
                "description": description,
                "common_usage": common_usage,
                "preparation_methods": prep_methods,
                "image_url": image_url,
            },
        },
        "similar_foods": similar_foods,
    }


def get_similar_foods(
    cur: sqlite3.Cursor,
    food_id: int,
    category: str,
    region: str = "National",
    limit: int = 4,
) -> List[Dict[str, Any]]:
    """
    Finds up to `limit` related foods from the same category or general catalog,
    annotated with key macros and pricing.
    """
    cur.execute(
        """
        SELECT f.id, f.name, f.name_local, f.food_category, f.data_source,
               f.calories_kcal, f.protein_g, f.carbohydrates_g, f.fat_g, f.fiber_g,
               f.is_vegetarian, f.is_vegan, f.is_gluten_free
        FROM foods f
        WHERE f.id != ? AND (f.food_category = ? OR f.data_source = 'ICMR_NIN')
        ORDER BY (CASE WHEN f.food_category = ? THEN 0 ELSE 1 END),
                 (CASE WHEN f.data_source = 'ICMR_NIN' THEN 0 ELSE 1 END),
                 f.name ASC
        LIMIT ?
        """,
        (food_id, category, category, limit),
    )
    rows = cur.fetchall()

    similar_list = []
    for r in rows:
        price_info = get_food_price(cur, r["id"], region=region)
        similar_list.append({
            "id": r["id"],
            "name": r["name"],
            "name_local": r["name_local"],
            "food_category": r["food_category"],
            "calories_kcal": round(float(r["calories_kcal"]), 1) if r["calories_kcal"] is not None else 0.0,
            "protein_g": round(float(r["protein_g"]), 1) if r["protein_g"] is not None else 0.0,
            "carbohydrates_g": round(float(r["carbohydrates_g"]), 1) if r["carbohydrates_g"] is not None else 0.0,
            "fat_g": round(float(r["fat_g"]), 1) if r["fat_g"] is not None else 0.0,
            "fiber_g": round(float(r["fiber_g"]), 1) if r["fiber_g"] is not None else None,
            "is_vegetarian": bool(r["is_vegetarian"]),
            "price_formatted": price_info["formatted_price"] if price_info else "Price unavailable",
            "price_type": price_info["price_type"] if price_info else None,
        })

    return similar_list
