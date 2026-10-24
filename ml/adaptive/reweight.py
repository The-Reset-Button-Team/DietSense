"""
Adaptive layer — downweights future candidates matching a user's skip reason.
0.1 penalty per skip, capped at 0.5 per tag, final score clamped at 0.0.
"""

# Maps skip reason to target food tag:
# - time -> 'long-prep-time' (quicker meals rank higher next time)
# - cost -> 'expensive' (cheaper meals rank higher next time)
# - unavailable -> 'hard-to-find' (common, easy-to-source meals rank higher)
# - taste -> None (documented: taste preferences require ingredient clustering / ratings)
REASON_TAG_MAP = {
    "time": "long-prep-time",
    "cost": "expensive",
    "unavailable": "hard-to-find",
    "taste": None,
}


def get_user_penalties(meal_logs: list[dict]) -> dict:
    """
    meal_logs: list of {'status': 'skipped'/'eaten', 'reason': str, 'item_tags': list[str]}
    Returns {tag: penalty_weight} built from this user's skip history.
    +0.1 per skip, capped at 0.5 maximum penalty per tag.
    """
    penalties: dict[str, float] = {}
    for log in meal_logs:
        if str(log.get("status", "")).strip().lower() != "skipped":
            continue

        raw_reason = str(log.get("reason") or "").strip().lower()
        tag = REASON_TAG_MAP.get(raw_reason)
        if tag:
            penalties[tag] = round(penalties.get(tag, 0.0) + 0.1, 2)

    # Cap each penalty at 0.5 so one skip reason never completely zeroes out valid meals
    return {tag: min(p, 0.5) for tag, p in penalties.items()}


def item_matches_penalty_tag(item: dict, tag: str) -> bool:
    """
    Determines if candidate matches a penalty tag, checking both explicit tags
    and documented attribute thresholds if tags are not directly present.
    """
    item_tags = set(str(t).lower() for t in (item.get("tags") or []))
    if tag in item_tags:
        return True

    # Documented threshold derivations for foods lacking explicit penalty tags:
    if tag == "long-prep-time":
        prep = item.get("prep_time")
        if prep is not None and prep > 25:
            return True

    if tag == "expensive":
        cost = item.get("cost_estimate")
        if cost is not None and cost > 100:
            return True

    if tag == "hard-to-find":
        if item.get("is_rare") or "imported" in item_tags or "hard-to-find" in item_tags:
            return True

    return False


def apply_penalties(score_breakdown: dict, item: dict, penalties: dict) -> dict:
    """
    Applies accumulated penalties to a candidate's final_score.
    Final score is clamped at 0.0. Records adaptive_penalty in score_breakdown.
    """
    penalty_total = 0.0
    applied_tags = []

    for tag, penalty in penalties.items():
        if item_matches_penalty_tag(item, tag):
            penalty_total += penalty
            applied_tags.append(tag)

    original_score = score_breakdown["final_score"]
    new_score = max(0.0, original_score - penalty_total)

    score_breakdown["final_score"] = new_score
    score_breakdown["adaptive_penalty"] = round(penalty_total, 2)
    score_breakdown["penalized_tags"] = applied_tags

    return score_breakdown
