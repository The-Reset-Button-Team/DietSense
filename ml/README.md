# DietSense — ML Engine (Member 3)

Scikit-learn · SHAP · Gemini API · NumPy

---

## Responsibilities

| Component | Description |
|-----------|-------------|
| **Hybrid Scoring** | Multi-factor weighted scoring of candidate recipes |
| **Preference Model** | Ridge Regression to learn per-user cuisine/ingredient weights |
| **Safety Gate** | Hard constraint filter (allergens, restrictions) — runs BEFORE scoring |
| **SHAP/XAI** | Feature attribution to generate human-readable explanations |
| **Gemini Interface** | Structured prompt builder + response parser for NL explanations |
| **Adaptive Re-Ranking** | Update preference weights from post-meal feedback |

---

## Scoring Formula

```
score = (
    0.30 × macro_match_score      # How well macros fit the user's daily targets
  + 0.20 × goal_alignment_score   # Alignment with lose/maintain/gain goal
  + 0.20 × user_pref_score        # Learned cuisine/ingredient preferences (Ridge)
  + 0.15 × feedback_history_score # Average rating from similar past meals
  + 0.10 × diversity_score        # Penalise repetition of recent meals
  + 0.05 × prep_complexity_score  # Simpler prep preferred (user setting)
)
```

All sub-scores are normalized to [0, 1] before combining.

---

## Setup

```bash
cd ml
cp .env.example .env
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

---

## Folder Structure

```
ml/
├── scoring/
│   ├── __init__.py
│   └── formula.py          # Weight constants + compute_score()
├── explainability/
│   ├── __init__.py
│   └── shap_explainer.py   # SHAP LinearExplainer wrapper (Phase 8)
├── models/                 # Saved Scikit-learn model artifacts (Phase 6+)
├── gemini/
│   └── prompts.py          # Structured prompt templates for Gemini (Phase 8)
└── __init__.py
```

---

## Key Constraints (from plan.pdf)

- **Rule 1**: The LLM NEVER generates or alters calorie, macro, or medical facts.
  All nutrition context sent to Gemini comes from the PostgreSQL DB.
- **Rule 2**: The hard safety gate (allergen/restriction filter) ALWAYS runs
  before any ML scoring — no unsafe recipe ever reaches the scoring stage.

---

## Evaluation Metrics

| Metric | Description |
|--------|-------------|
| `Precision@K` | Fraction of top-K recommended meals the user rated ≥ 4/5 |
| `NDCG` | Normalized Discounted Cumulative Gain on ranked meal list |

Target benchmarks are defined and measured in Phase 10 (Deployment & Evaluation).
