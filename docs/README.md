# DietSense — Docs

Visual documentation for the DietSense project. Open these HTML files in a browser or the IDE preview.

## Files

| File | Description |
|------|-------------|
| [`er_diagram.html`](er_diagram.html) | **Entity Relationship Diagram** — all 11 PostgreSQL tables, columns, data types, FK relationships. Click any table to highlight its connections. |
| [`pipeline.html`](pipeline.html) | **Architectural Pipeline** — end-to-end data flow from USDA/ICMR-NIN → ETL → DB → Safety Gate → ML Scoring → SHAP → Gemini → UI → Feedback loop |
| [`tech_stack.html`](tech_stack.html) | **Tech Stack & Team Roles** — 4-member domain ownership, all technologies, scoring formula bar chart |
| [`roadmap.html`](roadmap.html) | **20-Week Roadmap** — all 10 phases with deliverables, timeline, and lead owners |

## Quick Reference — Scoring Formula

```
score = 0.30×Macro + 0.20×Goal + 0.20×Preference + 0.15×Feedback + 0.10×Diversity + 0.05×Prep
```

Source: `ml/scoring/formula.py`

## Architecture Rules (Non-Negotiable)

- **Rule 1**: LLM (Gemini) **NEVER** generates or alters calorie, macro, or medical facts.
- **Rule 2**: Hard safety constraints (allergies, restrictions) execute **BEFORE** recommendation scoring.
