"""Adaptive layer — downweights future candidates matching a user's skip reason."""

# maps a skip reason to which tag(s) should be downweighted next time
REASON_TAG_MAP = {
    "time": "long-prep-time",
    "cost": "expensive",
    "taste": None,  # handled by boosting similarity to a different cluster instead
    "unavailable": "hard-to-find",
}

def get_user_penalties(meal_logs: list[dict]) -> dict:
    """
    meal_logs: list of {'status': 'skipped'/'eaten', 'reason': str, 'item_tags': list[str]}
    Returns {tag: penalty_weight} built from this user's skip history.
    """
    penalties = {}
    for log in meal_logs:
        if log["status"] != "skipped":
            continue
        
        reason = log.get("reason")
        tag = REASON_TAG_MAP.get(reason)
        if tag:
            penalties[tag] = penalties.get(tag, 0) + 0.1  # accumulate, capped below
            
    # cap penalty so one bad tag never fully zeroes out a category
    return {tag: min(p, 0.5) for tag, p in penalties.items()}

def apply_penalties(score_breakdown: dict, item: dict, penalties: dict) -> dict:
    """Applies accumulated penalties to a candidate's final_score in place."""
    item_tags = set(t.lower() for t in item.get("tags", []))
    penalty_total = sum(p for tag, p in penalties.items() if tag in item_tags)
    
    score_breakdown["final_score"] = max(0.0, score_breakdown["final_score"] - penalty_total)
    score_breakdown["adaptive_penalty"] = penalty_total
    
    return score_breakdown
