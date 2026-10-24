"""Hard safety floor — excludes unsafe items BEFORE any scoring runs."""

def filter_safe(candidates: list[dict], user_profile: dict) -> list[dict]:
    """
    candidates: list of food/recipe dicts, each with 'tags' (list[str]) and
                'allergens' (list[str])
    user_profile: dict with 'dietary_pref' (e.g. 'vegetarian', 'vegan') and
                  'allergies' (list[str])
    Returns only candidates that are safe for this user.
    Unknown allergen data is treated conservatively (excluded when user declares allergies).
    """
    if not candidates:
        return []

    safe = []
    diet = str(user_profile.get("dietary_pref") or "").strip().lower()
    user_allergies = set(
        str(a).strip().lower() for a in (user_profile.get("allergies") or []) if str(a).strip()
    )

    for item in candidates:
        # Normalize tags
        raw_tags = item.get("tags") or []
        tags = set(str(t).strip().lower() for t in raw_tags if str(t).strip())

        # Vegetarian rule: reject items with 'non-veg', 'meat', 'poultry', 'fish', 'seafood'
        if diet == "vegetarian":
            if any(t in tags for t in ["non-veg", "meat", "poultry", "fish", "seafood", "beef", "pork", "chicken"]):
                continue

        # Vegan rule: reject non-veg and animal products (dairy, egg, honey)
        if diet == "vegan":
            if any(t in tags for t in ["non-veg", "meat", "poultry", "fish", "seafood", "dairy", "egg", "eggs", "milk", "cheese", "honey"]):
                continue

        # Allergen safety check
        raw_allergens = item.get("allergens")
        if user_allergies:
            # If user has allergies and item's allergen info is missing/unknown, treat conservatively and exclude
            if raw_allergens is None or item.get("allergen_info_unknown") is True:
                continue

            item_allergens = set(str(a).strip().lower() for a in raw_allergens if str(a).strip())
            # If intersection with user's declared allergies, exclude
            if item_allergens & user_allergies:
                continue

        safe.append(item)

    return safe
