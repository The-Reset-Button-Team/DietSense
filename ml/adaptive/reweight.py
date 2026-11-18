"""
DietSense ML — Adaptive Feedback & Seven-Day Diversity Layer.

Priority 1: Seven-day meal diversity
- Analyzes recent meal logs within a 7-day rolling window (168 hours).
- Reduces repetitive meal recommendations with exponential recency decay.
- Tracks recently eaten/recommended foods and frequency.
- Prevents excessive repetition while preserving catalog coverage (max penalty 0.30).

Priority 2: Adaptive feedback with stability damping
- Uses actual user feedback (eaten confirmations and skip reasons).
- Sub-linear / logarithmic dampening prevents wild scoring swings.
- Positive feedback awards bounded affinity boosts (+0.02 to +0.10).
- Negative feedback applies targeted tag penalties capped at -0.35.
- Guarantees final score is strictly clamped in [0.0, 1.0].
"""

import math
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple

# Maps user skip reason to target food tags / attributes
REASON_TAG_MAP: Dict[str, Optional[str]] = {
    "time": "long-prep-time",
    "cost": "expensive",
    "unavailable": "hard-to-find",
    "taste": "taste-mismatch",
}

# Positive tags favored when user confirms eaten meals
POSITIVE_TRAITS = ["quick", "comfort", "high-protein", "high-fiber", "light"]


def _parse_timestamp(raw_ts: Any) -> Optional[datetime]:
    """Safely parse various timestamp formats into UTC datetime."""
    if not raw_ts:
        return None
    if isinstance(raw_ts, datetime):
        if raw_ts.tzinfo is None:
            return raw_ts.replace(tzinfo=timezone.utc)
        return raw_ts.astimezone(timezone.utc)

    ts_str = str(raw_ts).strip()
    try:
        # Support ISO 8601 with Z or offset
        if ts_str.endswith("Z"):
            ts_str = ts_str[:-1] + "+00:00"
        return datetime.fromisoformat(ts_str).astimezone(timezone.utc)
    except Exception:
        pass

    try:
        # Numeric epoch timestamp
        epoch = float(ts_str)
        return datetime.fromtimestamp(epoch, tz=timezone.utc)
    except Exception:
        return None


def get_user_penalties(meal_logs: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Legacy-compatible penalty calculator.
    meal_logs: list of {'status': 'skipped'/'eaten', 'reason': str, 'item_tags': list[str]}
    Returns {tag: penalty_weight} built from this user's skip history.
    +0.1 per skip, capped at 0.5 maximum penalty per tag.
    """
    penalties: Dict[str, float] = {}
    for log in meal_logs or []:
        if str(log.get("status", "")).strip().lower() != "skipped":
            continue

        raw_reason = str(log.get("reason") or "").strip().lower()
        tag = REASON_TAG_MAP.get(raw_reason)
        if tag:
            penalties[tag] = round(penalties.get(tag, 0.0) + 0.1, 2)

    return {tag: min(p, 0.5) for tag, p in penalties.items()}


def get_adaptive_feedback_weights(meal_logs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Priority 2: Stable, Damped Adaptive Feedback Model.
    
    Prevents unstable scoring changes using sub-linear logarithmic scaling:
      penalty(tag) = min(0.35, 0.10 * ln(1 + count))
      positive_boost(tag) = min(0.10, 0.04 * ln(1 + count))

    This guarantees:
    1. Single skips register a gentle adjustment without instantly disqualifying meals.
    2. Repeated skips accumulate with diminishing marginal impact (asymptotically stable).
    3. Extreme feedback cascades are prevented via strict global bounds.
    """
    skip_counts: Dict[str, int] = {}
    eaten_counts: Dict[str, int] = {}

    for log in meal_logs or []:
        status = str(log.get("status", "")).strip().lower()
        if status == "skipped":
            raw_reason = str(log.get("reason") or "").strip().lower()
            tag = REASON_TAG_MAP.get(raw_reason)
            if tag:
                skip_counts[tag] = skip_counts.get(tag, 0) + 1
        elif status == "eaten":
            tags = log.get("item_tags") or []
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(",") if t.strip()]
            for t in tags:
                tl = str(t).strip().lower()
                if tl in POSITIVE_TRAITS:
                    eaten_counts[tl] = eaten_counts.get(tl, 0) + 1

    # Damped penalty mapping (bounded [0.0, 0.35])
    penalties: Dict[str, float] = {}
    for tag, count in skip_counts.items():
        damped = 0.12 * math.log(1.0 + count)
        penalties[tag] = round(min(0.35, damped), 3)

    # Damped positive affinity (bounded [0.0, 0.10])
    affinities: Dict[str, float] = {}
    for tag, count in eaten_counts.items():
        damped = 0.04 * math.log(1.0 + count)
        affinities[tag] = round(min(0.10, damped), 3)

    return {
        "penalties": penalties,
        "affinities": affinities,
        "skip_counts": skip_counts,
        "eaten_counts": eaten_counts,
    }


def item_matches_penalty_tag(item: Dict[str, Any], tag: str) -> bool:
    """
    Determines if candidate matches a penalty tag, checking both explicit tags
    and documented attribute thresholds if tags are not directly present.
    """
    item_tags = set(str(t).lower() for t in (item.get("tags") or []))
    if tag in item_tags:
        return True

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


def item_matches_affinity_tag(item: Dict[str, Any], tag: str) -> bool:
    """Check if candidate exhibits a favored positive trait."""
    item_tags = set(str(t).lower() for t in (item.get("tags") or []))
    if tag in item_tags:
        return True
    if tag == "quick" and item.get("prep_time", 999) <= 15:
        return True
    if tag == "high-protein" and item.get("protein_g", 0) >= 20:
        return True
    if tag == "high-fiber" and item.get("fiber_g", 0) >= 5:
        return True
    return False


def compute_diversity_penalty(
    item: Dict[str, Any],
    meal_logs: List[Dict[str, Any]],
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Priority 1: Seven-Day Meal Diversity Model.

    Analyzes meal logs from the rolling 7-day window (168 hours).
    Applies exponential recency decay:
      - Consumed < 24h ago: strong diversity discount (~0.20 * exp(-0.35 * days))
      - Consumed 2-4 days ago: moderate diversity discount
      - Repeated >= 2 times in 7d: frequency penalty +0.05 * (freq - 1)
      - Bounded strictly at 0.30 maximum penalty so staples remain viable.
    """
    if now is None:
        now = datetime.now(timezone.utc)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    seven_days_ago = now - timedelta(days=7)
    item_id = str(item.get("id", ""))
    item_name = str(item.get("name", "")).strip().lower()

    recent_occurrences = []
    for log in meal_logs or []:
        # Count eaten meals or logged meals
        status = str(log.get("status", "")).strip().lower()
        if status not in ("eaten", "logged", "completed", "accepted"):
            continue

        log_ts = _parse_timestamp(log.get("timestamp") or log.get("created_at"))
        if not log_ts or log_ts < seven_days_ago:
            continue

        # Match by ID or Name
        log_meal_id = str(log.get("meal_id", ""))
        log_name = str(log.get("name") or log.get("meal_name") or "").strip().lower()

        is_match = False
        if item_id and log_meal_id and item_id == log_meal_id:
            is_match = True
        elif item_name and log_name and (item_name == log_name or item_name in log_name or log_name in item_name):
            is_match = True

        if is_match:
            days_ago = max(0.0, (now - log_ts).total_seconds() / 86400.0)
            recent_occurrences.append(days_ago)

    if not recent_occurrences:
        return {
            "diversity_penalty": 0.0,
            "days_since_last": None,
            "count_last_7d": 0,
            "diversity_status": "fresh",
        }

    recent_occurrences.sort()
    most_recent_days = recent_occurrences[0]
    count_7d = len(recent_occurrences)

    # Exponential recency decay: decay rate lambda = 0.35
    recency_penalty = 0.20 * math.exp(-0.35 * most_recent_days)

    # Frequency penalty for meals repeated >= 2 times in 7 days
    frequency_penalty = 0.05 * (count_7d - 1) if count_7d > 1 else 0.0

    total_diversity_penalty = min(0.30, recency_penalty + frequency_penalty)

    status_label = "fresh"
    if most_recent_days < 1.5:
        status_label = "repeated_yesterday"
    elif count_7d > 2:
        status_label = "frequent_staple"
    else:
        status_label = "recently_eaten"

    return {
        "diversity_penalty": round(total_diversity_penalty, 3),
        "days_since_last": round(most_recent_days, 1),
        "count_last_7d": count_7d,
        "diversity_status": status_label,
    }


def apply_penalties(score_breakdown: dict, item: dict, penalties: dict) -> dict:
    """
    Legacy penalty application — preserved for full backward compatibility.
    """
    penalty_total = 0.0
    applied_tags = []

    for tag, penalty in (penalties or {}).items():
        if item_matches_penalty_tag(item, tag):
            penalty_total += penalty
            applied_tags.append(tag)

    original_score = score_breakdown["final_score"]
    new_score = max(0.0, original_score - penalty_total)

    score_breakdown["final_score"] = new_score
    score_breakdown["adaptive_penalty"] = round(penalty_total, 2)
    score_breakdown["penalized_tags"] = applied_tags

    return score_breakdown


def apply_adaptive_and_diversity(
    score_breakdown: Dict[str, Any],
    item: Dict[str, Any],
    meal_logs: List[Dict[str, Any]] = None,
    penalties: Dict[str, float] = None,
) -> Dict[str, Any]:
    """
    Unified Adaptive Feedback and Seven-Day Diversity Applier.
    
    1. Evaluates damped skip penalties (capped at -0.35).
    2. Evaluates damped positive affinity boosts (capped at +0.10).
    3. Evaluates 7-day diversity decay penalty (capped at -0.30).
    4. Binds and clamps final_score strictly in [0.0, 1.0].
    """
    logs = meal_logs or []

    # 1. Feedback penalties & affinities
    feedback_meta = get_adaptive_feedback_weights(logs)
    effective_penalties = penalties if penalties is not None else feedback_meta["penalties"]

    penalty_total = 0.0
    applied_tags = []
    for tag, pen_val in effective_penalties.items():
        if item_matches_penalty_tag(item, tag):
            penalty_total += pen_val
            applied_tags.append(tag)

    affinity_total = 0.0
    applied_affinities = []
    for tag, aff_val in feedback_meta.get("affinities", {}).items():
        if item_matches_affinity_tag(item, tag):
            affinity_total += aff_val
            applied_affinities.append(tag)

    # 2. 7-Day Diversity
    diversity_info = compute_diversity_penalty(item, logs)
    div_penalty = diversity_info["diversity_penalty"]

    # 3. Score update with dampening & bounded clamping
    base_score = score_breakdown["final_score"]
    adjusted_score = base_score - penalty_total + affinity_total - div_penalty
    final_clamped = max(0.0, min(1.0, adjusted_score))

    score_breakdown["final_score"] = round(final_clamped, 4)
    score_breakdown["adaptive_penalty"] = round(penalty_total, 3)
    score_breakdown["penalized_tags"] = applied_tags
    score_breakdown["affinity_boost"] = round(affinity_total, 3)
    score_breakdown["affinity_tags"] = applied_affinities
    score_breakdown["diversity_penalty"] = div_penalty
    score_breakdown["days_since_last"] = diversity_info["days_since_last"]
    score_breakdown["frequency_7d"] = diversity_info["count_last_7d"]
    score_breakdown["diversity_status"] = diversity_info["diversity_status"]

    return score_breakdown
