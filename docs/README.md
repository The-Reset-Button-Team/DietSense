# DietSense — Docs

Visual documentation for the DietSense project. Open these HTML files in a browser or the IDE preview.

## Files

| File | Description |
|------|-------------|
| [er_diagram_classical.html](er_diagram_classical.html) | **Classical Peter Chen ER Diagram Web** — 100% comprehensive schema web with authentic Entity Rectangles, Relationship Diamonds, Attribute Ovals/Keys, and Cardinality lines for all 11 tables. |
| [ER_DIAGRAM.md](ER_DIAGRAM.md) | **Classical ER Theory & ASCII Web** — Full Peter Chen relational notation breakdown and entity dictionary. |
| [er_diagram.html](er_diagram.html) | **Interactive Relational Schema Explorer** — all 11 PostgreSQL tables, columns, data types, FK linkages with interactive highlighting. |
| [ieee_system_architecture.html](ieee_system_architecture.html) | **IEEE Publication Block Architecture** — 2-column formal IEEE format with mathematical formulas and system blocks. |
| [IEEE_ARCHITECTURE_MAP.md](IEEE_ARCHITECTURE_MAP.md) | **IEEE Architecture Markdown** — Plain ASCII diagram and LaTeX formulas. |
| [system_map.html](system_map.html) | **Interactive Architecture Studio** — visual 5-stage interactive map with animated dataflow pipelines and subsystem filters. |
| [SYSTEM_MAP.md](SYSTEM_MAP.md) | **End-to-End System & User Journey Map** — technical architecture, 5-stage data flow, and visual Mermaid system blueprint. |
| [LOGIC_AND_FORMULAS.md](LOGIC_AND_FORMULAS.md) | **Complete Scientific Logic & Formulas Guide** — Mifflin-St Jeor, BMR/TDEE, WHO 2026 macro splits, USDA/ICMR data sources, and ML scoring. |
| [pipeline.html](pipeline.html) | **Architectural Pipeline** — end-to-end data flow from USDA/ICMR-NIN → ETL → DB → Safety Gate → ML Scoring → SHAP → Gemini → UI → Feedback loop. |
| [	ech_stack.html](tech_stack.html) | **Tech Stack & Team Roles** — 4-member domain ownership, all technologies, scoring formula bar chart. |
| [oadmap.html](roadmap.html) | **20-Week Roadmap** — all 10 phases with deliverables, timeline, and lead owners. |

## Quick Reference — Scoring Formula

`
score = 0.30×Macro + 0.20×Goal + 0.20×Preference + 0.15×Feedback + 0.10×Diversity + 0.05×Prep
`

Source: ml/scoring/formula.py

## Architecture Rules (Non-Negotiable)

- **Rule 1**: LLM (Gemini) **NEVER** generates or alters calorie, macro, or medical facts.
- **Rule 2**: Hard safety constraints (allergies, restrictions) execute **BEFORE** recommendation scoring.
