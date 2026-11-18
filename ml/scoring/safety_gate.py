"""Hard safety floor — excludes unsafe items BEFORE any scoring runs."""

ALLERGEN_ALIASES: dict[str, set[str]] = {
    "peanuts": {"peanuts", "peanut", "nuts", "groundnuts"},
    "tree_nuts": {"tree_nuts", "nuts", "walnuts", "cashews", "almonds", "pistachios", "hazelnuts"},
    "dairy": {"dairy", "milk", "lactose", "cheese", "butter", "paneer", "ghee", "curd", "yogurt"},
    "gluten": {"gluten", "wheat", "flour", "maida", "atta", "barley", "rye"},
    "eggs": {"eggs", "egg", "egg_white", "egg_yolk"},
    "fish": {"fish", "salmon", "tuna", "cod", "rohu", "katla"},
    "shellfish": {"shellfish", "crustaceans", "shrimp", "prawns", "crab", "lobster"},
    "soy": {"soy", "soya", "soybeans", "edamame", "tofu"},
}

MEAT_TAGS = {"non-veg", "meat", "poultry", "fish", "seafood", "beef", "pork", "chicken", "mutton", "lamb"}
ANIMAL_PRODUCT_TAGS = MEAT_TAGS | {"dairy", "egg", "eggs", "milk", "cheese", "honey", "ghee", "butter", "paneer"}


def audit_safe(candidates: list[dict], user_profile: dict) -> dict:
    """
    Evaluates candidates against user dietary restrictions and allergens.
    Returns:
    {
        "safe": list of safe candidate dicts,
        "blocked": list of dicts with {"item": item, "reason": str, "rule": str, "conflict": str}
    }
    """
    if not candidates:
        return {"safe": [], "blocked": []}

    safe = []
    blocked = []
    diet = str(user_profile.get("dietary_pref") or user_profile.get("dietary_preference") or "").strip().lower()
    user_allergies = set(
        str(a).strip().lower() for a in (user_profile.get("allergies") or []) if str(a).strip()
    )

    # Expand user allergy synonyms
    expanded_user_allergies = set()
    for a in user_allergies:
        expanded_user_allergies.add(a)
        if a in ALLERGEN_ALIASES:
            expanded_user_allergies.update(ALLERGEN_ALIASES[a])

    for item in candidates:
        raw_tags = item.get("tags") or []
        tags = set(str(t).strip().lower() for t in raw_tags if str(t).strip())

        # 1. Vegetarian rule
        if diet in ("vegetarian", "lacto-vegetarian"):
            meat_conflicts = tags & MEAT_TAGS
            if meat_conflicts:
                blocked.append({
                    "item": item,
                    "reason": f"Dietary restriction conflict: contains {', '.join(sorted(meat_conflicts))}",
                    "rule": "vegetarian",
                    "conflict": list(meat_conflicts)[0],
                })
                continue

        # 2. Vegan rule: reject non-veg and animal products
        if diet == "vegan":
            animal_conflicts = tags & ANIMAL_PRODUCT_TAGS
            if animal_conflicts:
                blocked.append({
                    "item": item,
                    "reason": f"Vegan restriction conflict: contains animal-derived {', '.join(sorted(animal_conflicts))}",
                    "rule": "vegan",
                    "conflict": list(animal_conflicts)[0],
                })
                continue

        # 3. Eggetarian rule: reject meat/poultry/fish but allow eggs & dairy
        if diet in ("eggetarian", "ovo-vegetarian"):
            meat_conflicts = tags & MEAT_TAGS
            if meat_conflicts:
                blocked.append({
                    "item": item,
                    "reason": f"Eggetarian restriction conflict: contains {', '.join(sorted(meat_conflicts))}",
                    "rule": "eggetarian",
                    "conflict": list(meat_conflicts)[0],
                })
                continue

        # 4. Pescatarian rule: reject red meat and poultry
        if diet == "pescatarian":
            pesc_conflicts = tags & {"meat", "poultry", "beef", "pork", "chicken", "mutton", "lamb"}
            if pesc_conflicts:
                blocked.append({
                    "item": item,
                    "reason": f"Pescatarian restriction conflict: contains {', '.join(sorted(pesc_conflicts))}",
                    "rule": "pescatarian",
                    "conflict": list(pesc_conflicts)[0],
                })
                continue

        # 5. Allergen safety check
        raw_allergens = item.get("allergens")
        if user_allergies:
            # Missing allergen info treated conservatively
            if raw_allergens is None or item.get("allergen_info_unknown") is True:
                blocked.append({
                    "item": item,
                    "reason": "Missing verified allergen declaration (excluded in conservative safety mode)",
                    "rule": "allergen_unknown",
                    "conflict": "unknown_allergen_data",
                })
                continue

            item_allergens = set(str(a).strip().lower() for a in raw_allergens if str(a).strip())
            # Expand item allergens with synonyms
            expanded_item_allergens = set(item_allergens)
            for ia in item_allergens:
                if ia in ALLERGEN_ALIASES:
                    expanded_item_allergens.update(ALLERGEN_ALIASES[ia])

            allergen_conflicts = expanded_item_allergens & expanded_user_allergies
            if allergen_conflicts:
                blocked.append({
                    "item": item,
                    "reason": f"Declared allergen conflict: contains {', '.join(sorted(allergen_conflicts))}",
                    "rule": "allergen_conflict",
                    "conflict": list(allergen_conflicts)[0],
                })
                continue

        safe.append(item)

    return {"safe": safe, "blocked": blocked}


def filter_safe(candidates: list[dict], user_profile: dict) -> list[dict]:
    """
    candidates: list of food/recipe dicts, each with 'tags' (list[str]) and
                'allergens' (list[str])
    user_profile: dict with 'dietary_pref' (e.g. 'vegetarian', 'vegan') and
                  'allergies' (list[str])
    Returns only candidates that are safe for this user.
    Unknown allergen data is treated conservatively (excluded when user declares allergies).
    """
    return audit_safe(candidates, user_profile)["safe"]
