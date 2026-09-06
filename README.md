# DietSense — Adaptive AI Meal Planning for Obesity Prevention

> Evidence-based, explainable, personalized meal planning powered by USDA/ICMR-NIN nutrition data, Scikit-learn, and the Gemini API.

[![Phase](https://img.shields.io/badge/Phase-1%20Requirements%20%26%20Specs-blue)](docs/)
[![Stack](https://img.shields.io/badge/Stack-Next.js%20%7C%20FastAPI%20%7C%20PostgreSQL%20%7C%20Scikit--learn-green)](ARCHITECTURE.md)
[![License](https://img.shields.io/badge/License-MIT-lightgrey)]()

---

## 📊 Visual Documentation

| Diagram | Description |
|---------|-------------|
| [🗂️ Entity Relationship Diagram](docs/er_diagram.html) | All 11 PostgreSQL tables, columns, data types, FK links — click any table to highlight relationships |
| [⚡ Architectural Pipeline](docs/pipeline.html) | Full data flow: USDA/ICMR-NIN → ETL → DB → Safety Gate → ML Scoring → SHAP → Gemini → UI → Feedback |
| [🧑‍💻 Tech Stack & Team Roles](docs/tech_stack.html) | 4-member domain ownership, all technologies, scoring formula bar chart |
| [📅 20-Week Roadmap](docs/roadmap.html) | All 10 phases with deliverables, timeline, lead owners |

> Open HTML files in a browser. GitHub renders them via Pages or clone + open locally.



## 🎯 Project Goal

Build an adaptive, evidence-based personalized meal planning system where:
- **Nutrition facts come strictly from validated datasets** (USDA FoodData Central, ICMR-NIN/IFCT 2017).
- **AI is confined to personalization, re-ranking, and natural-language interaction** — never to generating or altering calorie/macro data.

---

## ⚡ Primary Architectural Pipeline

```
USDA/ICMR-NIN Data
      ↓
ETL & Normalization (Pandas/NumPy)
      ↓
PostgreSQL Database (Supabase)
      ↓
Hard Safety Gate  ← allergies & restrictions checked FIRST
      ↓
Hybrid Recommendation Scoring
  0.30 × Macro Match
  0.20 × Goal Alignment
  0.20 × User Preferences
  0.15 × Feedback History
  0.10 × Diversity
  0.05 × Prep Complexity
      ↓
SHAP / Rules Explainability
      ↓
Gemini API (Natural Language Explanations ONLY)
      ↓
User Feedback Loop → Adaptive Re-Ranking
```

### Non-Negotiable Rules
| Rule | Description |
|------|-------------|
| **Rule 1** | The LLM **NEVER** generates or alters calorie, macro, or medical facts. |
| **Rule 2** | Hard safety constraints (allergies, restrictions) execute **BEFORE** recommendation scoring. |

---

## 🗂️ Repository Structure

```
DietSense/
├── frontend/          # Next.js 14 + TypeScript + Tailwind (Member 1)
├── backend/           # FastAPI + PostgreSQL + Pydantic (Member 2)
│   ├── app/
│   └── db/            # SQL schemas and seeds
├── ml/                # Scikit-learn + SHAP + Gemini prompts (Member 3)
├── data/              # Raw & processed USDA/ICMR-NIN datasets (Member 4)
├── scripts/           # ETL pipeline scripts (Member 4)
├── tests/             # Unit & integration tests (Member 4)
├── database/          # Reference documents (WHO, IFCT PDFs, etc.)
└── .github/           # PR templates, issue templates, CI workflows
```

---

## 🧑‍💻 Team Roles

| Member | Role | Domain | Key Deliverables |
|--------|------|---------|-----------------|
| Member 1 | Frontend Lead | `/frontend` | Multi-screen UI, onboarding wizard, meal dashboard, feedback forms |
| Member 2 | Backend Lead | `/backend` | Async API routes, SQL schemas, JWT middleware, RLS |
| Member 3 | AI/ML Lead | `/ml` | Scoring engine, adaptive re-ranking, SHAP/XAI, Gemini prompts |
| Member 4 | Data Lead | `/data`, `/scripts`, `/tests` | ETL pipeline, cleaned seed dataset, safety gate |

---

## 🔧 Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS, Recharts | SSR dashboard, type-safe UI |
| Backend | Python 3.11+, FastAPI, Pydantic, SQLAlchemy | Async REST API, schema validation |
| Database | PostgreSQL (Supabase) | Relational food/recipe store, JSONB logs, RLS |
| Auth | Supabase Auth | JWT authentication, session hooks |
| ML | Scikit-learn | Preference regression, candidate re-ranking, clustering |
| XAI | SHAP + deterministic rules | Feature attribution, prose explanation generation |
| Generative AI | Gemini API | NL explanations, recipe instructions, chat assistant |
| ETL | Pandas, NumPy | Data ingestion, cleaning, unit normalization |
| Hosting | Vercel (FE), Render/Railway (BE) | Continuous deployment |

---

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- Git

### 1. Clone the repository
```bash
git clone https://github.com/The-Reset-Button-Team/DietSense-.git
cd DietSense-
```

### 2. Frontend Setup (Member 1)
```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
# → http://localhost:3000
```

### 3. Backend Setup (Member 2)
```bash
cd backend
cp .env.example .env
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# → http://localhost:8000
# → Swagger UI: http://localhost:8000/docs
```

### 4. ML Setup (Member 3)
```bash
cd ml
cp .env.example .env
python -m venv venv
venv\Scripts\activate  # or source venv/bin/activate
pip install -r requirements.txt
```

### 5. Data / Scripts Setup (Member 4)
```bash
cd scripts
pip install -r requirements.txt
# See scripts/README.md for ETL pipeline instructions
```

---

## 📋 Implementation Roadmap

| Phase | Milestone | Timeline | Lead |
|-------|-----------|----------|------|
| **1** | ✅ Requirements & Specs | Weeks 1–2 | All |
| 2 | Data Extraction & ETL | Weeks 3–4 | Member 4 |
| 3 | Database & Auth Setup | Weeks 5–6 | Member 2 |
| 4 | Backend API Foundation | Weeks 7–8 | Member 2 |
| 5 | Frontend UI Foundation | Weeks 9–10 | Member 1 |
| 6 | Rule-Based Rec Engine | Weeks 11–12 | Member 3 |
| 7 | Adaptive Feedback Loop | Weeks 13–14 | Members 2 & 3 |
| 8 | XAI & Gemini Integration | Weeks 15–16 | Member 3 |
| 9 | End-to-End System Sync | Weeks 17–18 | All |
| 10 | Deployment & Evaluation | Weeks 19–20 | All |

---

## 📚 Reference Documents

- [`ARCHITECTURE.md`](ARCHITECTURE.md) — Full technical architecture
- [`backend/db/schema.sql`](backend/db/schema.sql) — PostgreSQL schema (all tables)
- [`data/sources.md`](data/sources.md) — Dataset sources and normalization rules
- [`database/WHO_Healthy_Diet_Fact_Sheet.md`](database/WHO_Healthy_Diet_Fact_Sheet.md) — WHO dietary guidelines reference

---

## 🤝 Contributing

See [`.github/PULL_REQUEST_TEMPLATE.md`](.github/PULL_REQUEST_TEMPLATE.md) for PR conventions and [`.github/ISSUE_TEMPLATE/`](.github/ISSUE_TEMPLATE/) for bug/feature reporting.

**Branch naming convention:**
```
feat/[domain]/[short-description]    # e.g. feat/backend/add-foods-endpoint
fix/[domain]/[short-description]     # e.g. fix/ml/scoring-weight-update
docs/[short-description]             # e.g. docs/update-architecture
```
