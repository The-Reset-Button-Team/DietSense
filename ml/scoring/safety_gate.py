"""Hard safety floor — excludes unsafe items BEFORE any scoring runs."""

def filter_safe(candidates: list[dict], user_profile: dict) -> list[dict]:
    """
    candidates: list of food/recipe dicts, each with 'tags' (list[str]) and
                'allergens' (list[str])
    user_profile: dict with 'dietary_pref' (e.g. 'vegetarian') and
                  'allergies' (list[str])
    Returns only candidates that are safe for this user.
    """
    safe = []
    diet = user_profile.get("dietary_pref", "").lower()
    allergies = set(a.lower() for a in user_profile.get("allergies", []))

    for item in candidates:
        tags = set(t.lower() for t in item.get("tags", []))
        item_allergens = set(a.lower() for a in item.get("allergens", []))

        if diet == "vegetarian" and "non-veg" in tags:
            continue
        if diet == "vegan" and ("non-veg" in tags or "dairy" in tags or "egg" in tags):
            continue
        if item_allergens & allergies:
            continue
        
        safe.append(item)
        
    return safe