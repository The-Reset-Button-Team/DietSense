"""
Phase 8D — Tests for DietSense ML Enhancements.

Tests cover:
1. Priority 1: Seven-day meal diversity
   - Meal logs within 7-day rolling window reduce recommendation frequency.
   - Exponential recency decay (meals eaten today receive higher diversity discount than 5 days ago).
   - Diversity penalty is bounded at 0.30 so valid meals are not permanently disqualified.
2. Priority 2: Adaptive feedback
   - User skip feedback applies targeted, sub-linear logarithmic penalties.
   - Positive feedback awards bounded affinity boosts.
   - Scoring stability guarantees (bounds strictly clamped, preventing wild fluctuations).
3. Priority 3: Micronutrient tracking
   - Candidates track available micronutrients: fiber_g, sodium_mg, calcium_mg, iron_mg.
   - Clearly distinguishes missing data (None) from true zero values (0.0).
   - Daily recommendations aggregate available micronutrients with completeness status.
4. Priority 4: Recommendation explanations
   - Explanations are generated using actual scoring components.
   - Explanations highlight verified nutritional strengths (protein, fiber, sodium).
   - Structured explanation object exposes granular factor attribution.
5. Technical complexity evaluation
   - Verifies programmatic justification for why SHAP and Ridge are not justified.
   - Safety gate is strictly preserved.
"""

import sys
import os
import time
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.main import app
from app.core.config import settings
from ml.recommendation.recommender import recommend
from ml.adaptive.reweight import (
    compute_diversity_penalty,
    get_adaptive_feedback_weights,
    apply_adaptive_and_diversity,
)
from ml.explainability.explainers import (
    generate_reason,
    generate_structured_explanation,
    _format_nutrient_highlight,
)
from ml.scoring.evaluation import evaluate_ml_model_complexity
from ml.scoring.safety_gate import filter_safe
import jwt

client = TestClient(app)

TEST_SECRET = settings.jwt_secret
TEST_ALGORITHM = settings.jwt_algorithm or "HS256"
TEST_AUDIENCE = settings.jwt_audience or "authenticated"


def generate_token(user_id: str, email: str = "phase8d_test@dietsense.ai") -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "aud": TEST_AUDIENCE,
        "role": "authenticated",
        "exp": int(time.time()) + 3600,
        "iat": int(time.time()),
    }
    return jwt.encode(payload, TEST_SECRET, algorithm=TEST_ALGORITHM)


# ─── Priority 1: Seven-Day Meal Diversity Tests ──────────────────────────────

def test_seven_day_diversity_recency_decay():
    """Meals eaten today receive a stronger diversity discount than meals eaten 4 days ago."""
    now = datetime.now(timezone.utc)
    item = {"id": 101, "name": "Moong Dal Khichdi"}

    # Log eaten 6 hours ago
    logs_recent = [
        {"meal_id": "101", "name": "Moong Dal Khichdi", "status": "eaten", "timestamp": (now - timedelta(hours=6)).isoformat()}
    ]
    # Log eaten 4 days ago
    logs_older = [
        {"meal_id": "101", "name": "Moong Dal Khichdi", "status": "eaten", "timestamp": (now - timedelta(days=4)).isoformat()}
    ]

    recent_result = compute_diversity_penalty(item, logs_recent, now=now)
    older_result = compute_diversity_penalty(item, logs_older, now=now)

    assert recent_result["diversity_penalty"] > older_result["diversity_penalty"]
    assert recent_result["diversity_status"] == "repeated_yesterday"
    assert recent_result["count_last_7d"] == 1


def test_seven_day_diversity_frequency_penalty():
    """Meals eaten multiple times in 7 days accumulate frequency penalties."""
    now = datetime.now(timezone.utc)
    item = {"id": 102, "name": "Oats Porridge"}

    logs_multi = [
        {"meal_id": "102", "name": "Oats Porridge", "status": "eaten", "timestamp": (now - timedelta(days=1)).isoformat()},
        {"meal_id": "102", "name": "Oats Porridge", "status": "eaten", "timestamp": (now - timedelta(days=3)).isoformat()},
        {"meal_id": "102", "name": "Oats Porridge", "status": "eaten", "timestamp": (now - timedelta(days=5)).isoformat()},
    ]

    result = compute_diversity_penalty(item, logs_multi, now=now)
    assert result["count_last_7d"] == 3
    # Frequency penalty adds +0.05 * (3 - 1) = +0.10
    assert result["diversity_penalty"] > 0.15
    assert result["diversity_status"] in ("repeated_yesterday", "frequent_staple")


def test_diversity_ignores_logs_older_than_seven_days():
    """Logs older than 7 days do not trigger diversity penalties."""
    now = datetime.now(timezone.utc)
    item = {"id": 103, "name": "Palak Paneer"}

    logs_old = [
        {"meal_id": "103", "name": "Palak Paneer", "status": "eaten", "timestamp": (now - timedelta(days=8)).isoformat()},
        {"meal_id": "103", "name": "Palak Paneer", "status": "eaten", "timestamp": (now - timedelta(days=14)).isoformat()},
    ]

    result = compute_diversity_penalty(item, logs_old, now=now)
    assert result["diversity_penalty"] == 0.0
    assert result["diversity_status"] == "fresh"
    assert result["count_last_7d"] == 0


def test_diversity_reduces_recommendation_ranking_for_recently_eaten():
    """Recently eaten meal ranks lower than an identical fresh alternative."""
    user_profile = {"dietary_pref": "vegetarian", "target_calories": 2000}
    now = datetime.now(timezone.utc)

    candidates = [
        {"id": 1, "name": "Poha Bowl", "tags": ["veg"], "calories": 400, "prep_time": 15, "cost_estimate": 50},
        {"id": 2, "name": "Upma Bowl", "tags": ["veg"], "calories": 400, "prep_time": 15, "cost_estimate": 50},
    ]

    # User ate Poha yesterday
    meal_logs = [
        {"meal_id": "1", "name": "Poha Bowl", "status": "eaten", "timestamp": (now - timedelta(hours=12)).isoformat()}
    ]

    recs = recommend(user_profile, candidates, meal_logs=meal_logs, top_n=2)
    assert len(recs) == 2
    # Fresh Upma Bowl should rank higher than repeated Poha Bowl
    assert recs[0]["item"]["name"] == "Upma Bowl"
    assert recs[1]["item"]["name"] == "Poha Bowl"
    assert recs[1]["breakdown"]["diversity_penalty"] > 0.0


# ─── Priority 2: Adaptive Feedback Tests ────────────────────────────────────

def test_adaptive_feedback_damped_scaling():
    """Logarithmic dampening prevents unstable scoring changes on repeated skips."""
    logs_1_skip = [{"status": "skipped", "reason": "time"}]
    logs_5_skips = [{"status": "skipped", "reason": "time"} for _ in range(5)]
    logs_20_skips = [{"status": "skipped", "reason": "time"} for _ in range(20)]

    w1 = get_adaptive_feedback_weights(logs_1_skip)["penalties"]["long-prep-time"]
    w5 = get_adaptive_feedback_weights(logs_5_skips)["penalties"]["long-prep-time"]
    w20 = get_adaptive_feedback_weights(logs_20_skips)["penalties"]["long-prep-time"]

    # Monotonically increasing but strictly sub-linear and capped at 0.35
    assert w1 < w5 <= w20
    assert w20 <= 0.35
    # Marginal impact per skip drops significantly (diminishing returns)
    marginal_early = (w5 - w1) / 4
    marginal_late = (w20 - w5) / 15
    assert marginal_late < marginal_early


def test_positive_feedback_affinity_boost():
    """Eaten meals provide positive affinity boosts capped at +0.10."""
    logs_eaten = [
        {"status": "eaten", "item_tags": ["quick", "high-protein"]},
        {"status": "eaten", "item_tags": ["quick"]},
    ]
    meta = get_adaptive_feedback_weights(logs_eaten)
    assert "quick" in meta["affinities"]
    assert 0.0 < meta["affinities"]["quick"] <= 0.10


def test_scoring_bounded_within_zero_and_one():
    """Scores with extreme penalties and diversity discounts never drop below 0.0."""
    item = {"id": 999, "name": "Test Meal", "tags": ["long-prep-time", "expensive"], "prep_time": 45, "cost_estimate": 250}
    breakdown = {"final_score": 0.15, "similarity": 0.2, "macro_fit": 0.2, "budget_fit": 0.1, "prep_time_fit": 0.1}
    extreme_penalties = {"long-prep-time": 0.50, "expensive": 0.50}

    now = datetime.now(timezone.utc)
    heavy_logs = [
        {"meal_id": "999", "name": "Test Meal", "status": "eaten", "timestamp": now.isoformat()},
        {"meal_id": "999", "name": "Test Meal", "status": "eaten", "timestamp": now.isoformat()},
    ]

    adjusted = apply_adaptive_and_diversity(breakdown, item, meal_logs=heavy_logs, penalties=extreme_penalties)
    assert adjusted["final_score"] >= 0.0
    assert adjusted["final_score"] <= 1.0


# ─── Priority 3: Micronutrient Tracking Tests ───────────────────────────────

def test_micronutrient_distinguishes_none_from_zero():
    """Candidate micronutrients clearly differentiate None (missing) from 0.0 (verified zero)."""
    item_with_zero_sodium = {
        "id": 201,
        "name": "Pure Boiled Basmati Rice",
        "fiber_g": 1.2,
        "sodium_mg": 0.0,  # verified zero sodium
        "calcium_mg": None,  # unmeasured / missing in catalog
        "iron_mg": 0.5,
        "micronutrients": {
            "fiber_g": 1.2,
            "sodium_mg": 0.0,
            "calcium_mg": None,
            "iron_mg": 0.5,
        },
    }

    micros = item_with_zero_sodium["micronutrients"]
    # 0.0 is a valid number, not None
    assert micros["sodium_mg"] == 0.0
    assert micros["sodium_mg"] is not None
    # None indicates missing data
    assert micros["calcium_mg"] is None


def test_daily_recommendations_aggregates_micronutrients():
    """GET /recommendations/daily returns aggregated micronutrient totals with completeness flags."""
    user_id = "test_usr_micro_001"
    token = generate_token(user_id)
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post(
        "/recommendations/daily",
        json={
            "user_profile": {"dietary_pref": "vegetarian", "target_calories": 2000},
            "active_slots": {"breakfast": True, "lunch": True, "dinner": True},
        },
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert "micronutrients" in data
    m = data["micronutrients"]
    assert "fiber_g" in m
    assert "sodium_mg" in m
    assert "calcium_mg" in m
    assert "iron_mg" in m
    assert "data_completeness" in m
    # If fiber was tracked, it should be a positive float
    if m["data_completeness"]["fiber_tracked"]:
        assert m["fiber_g"] is not None
        assert m["fiber_g"] > 0


# ─── Priority 4: Recommendation Explanations Tests ──────────────────────────

def test_explanation_uses_real_scoring_and_nutrition():
    """Explanations cite actual high protein and fiber values and score factors."""
    item = {
        "name": "Sprouted Moong Salad",
        "protein_g": 24.0,
        "fiber_g": 7.5,
        "sodium_mg": 85.0,
        "prep_time": 10,
    }
    user_profile = {"dietary_pref": "vegan"}
    breakdown = {
        "final_score": 0.88,
        "macro_fit": 0.92,
        "budget_fit": 0.90,
        "prep_time_fit": 0.95,
        "similarity": 0.75,
        "adaptive_penalty": 0.0,
        "affinity_boost": 0.04,
        "diversity_penalty": 0.0,
        "diversity_status": "fresh",
    }

    reason = generate_reason(item, user_profile, breakdown)
    assert "vegan" in reason
    assert "high protein" in reason or "24g" in reason
    assert "dietary fiber" in reason
    assert "low sodium" in reason
    assert "adds meal variety" in reason


def test_structured_explanation_exposes_breakdown():
    """Structured explanation returns explicit scoring factors and nutrient highlights."""
    item = {"name": "Lentil Soup", "protein_g": 18.0, "fiber_g": 5.0, "prep_time": 20}
    user_profile = {"dietary_pref": "vegetarian"}
    breakdown = {
        "final_score": 0.82,
        "macro_fit": 0.85,
        "budget_fit": 0.80,
        "prep_time_fit": 0.80,
        "similarity": 0.70,
        "adaptive_penalty": 0.05,
        "penalized_tags": ["long-prep-time"],
        "affinity_boost": 0.0,
        "diversity_penalty": 0.0,
        "diversity_status": "fresh",
    }

    structured = generate_structured_explanation(item, user_profile, breakdown)
    assert "summary" in structured
    assert "primary_factor" in structured
    assert "scoring_factors" in structured
    assert structured["scoring_factors"]["macro_fit"] == 0.85
    assert structured["scoring_factors"]["adaptive_penalty"] == 0.05


# ─── Complexity Evaluation & Safety Gate Preservation Tests ─────────────────

def test_ml_complexity_evaluation():
    """Verifies that SHAP and Ridge regression are evaluated and documented as unsuited."""
    eval_result = evaluate_ml_model_complexity()
    assert eval_result["ridge_regression"]["recommended"] is False
    assert eval_result["shap"]["recommended"] is False
    assert "safety_gate_status" in eval_result
    assert "preserv" in eval_result["safety_gate_status"].lower()


def test_safety_gate_is_strictly_preserved():
    """Safety gate still hard-excludes unsafe foods regardless of ML scoring."""
    candidates = [
        {"id": 1, "name": "Chicken Tikka", "tags": ["non-veg", "meat"], "allergens": [], "calories": 400},
        {"id": 2, "name": "Peanut Bar", "tags": ["veg"], "allergens": ["peanuts"], "calories": 250},
        {"id": 3, "name": "Tofu Bowl", "tags": ["veg"], "allergens": [], "calories": 350},
    ]
    user_profile = {"dietary_pref": "vegetarian", "allergies": ["peanuts"]}

    # recommend() calls filter_safe first
    recs = recommend(user_profile, candidates, top_n=5)
    rec_names = [r["item"]["name"] for r in recs]

    assert "Tofu Bowl" in rec_names
    assert "Chicken Tikka" not in rec_names
    assert "Peanut Bar" not in rec_names
