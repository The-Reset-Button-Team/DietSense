# DietSense — Adaptive AI Meal Planning System

> Evidence-based, explainable, personalized meal planning powered by USDA & ICMR-NIN nutrition data, Scikit-learn, and FastAPI.

[![Build & Test Status](https://img.shields.io/badge/Pytest-39%20Passed-brightgreen)](tests/)
[![Architecture](https://img.shields.io/badge/Architecture-Local--First%20SQLite%20%2B%20FastAPI-blue)](ARCHITECTURE.md)
[![License](https://img.shields.io/badge/License-MIT-lightgrey)]()

---

## 🧑‍💻 Team & Assigned Roles

| Member | Role | Primary Ownership |
|--------|------|-------------------|
| **Daksh Chaukhande** | M1 — Frontend Lead | Next.js 14/16 app, TypeScript screens, Recharts analytics, API integration |
| **Pranav Chaudhari** | M2 — Backend Lead | FastAPI REST API, local SQLite persistence, JWT & session auth, route isolation |
| **Prasoon Bodke** | M3 — AI/ML Lead | Safety gate, TF-IDF + cosine similarity, 4-factor scoring, adaptive skip penalties |
| **Atharv Bodkhe** | M4 — Data & QA Lead | USDA & ICMR-NIN ETL pipeline (14,181 foods), CI automation, end-to-end testing |

---

## 🎯 Project Overview & Core Principles

DietSense is an adaptive meal-planning and recommendation system designed to provide personalized, transparent, and safe nutrition recommendations without relying on cloud services.

### Non-Negotiable Core Principles
1. **Authoritative Nutrition Data:** Calorie and macronutrient values are derived **strictly** from authoritative food composition tables (USDA FoodData Central and ICMR-NIN / IFCT 2017). An AI model **never** generates, predicts, or alters nutrition numbers.
2. **Safety Gate Runs First:** Hard dietary constraints (vegetarian, vegan) and allergen safety exclusions execute **before any scoring occurs**. Boosts and penalties never re-introduce an excluded item.
3. **Deterministic & Explainable Scoring:** Recommendations are ranked using transparent multi-factor scoring (similarity, macro fit, budget, and prep time) and provide human-readable explanations derived from the scoring factors.
4. **Adaptive Feedback Loop:** When a user logs a meal as *skipped*, DietSense infers reasons (e.g. *time* → long cooking duration, *cost* → expensive) to gently penalize matching items in future recommendations (+0.1 per skip, capped at 0.5).
5. **Non-Medical Disclaimer:** DietSense is a lifestyle decision-support tool, not a diagnostic or clinical medical application.

---

## ⚡ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│               LOCAL FOOD CATALOG & ETL (M4)                 │
│                                                             │
│   USDA FoodData Central (13,694 foods)                      │
│   ICMR-NIN / IFCT 2017  (487 foods)                         │
│             ↓                                               │
│   ETL Pipeline (Pandas: clean units, verify 0 NaNs)         │
│   Saved to data/processed/foods_merged.csv & SQLite         │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 FASTAPI BACKEND API (M2)                    │
│                                                             │
│   • Local SQLite Database (database/dietsense.db)           │
│     Tables: users, profiles, meal_plans, meal_logs,         │
│             feedback, pantry_items, foods                   │
│   • Secure Session / JWT Auth with Password Hashing         │
│   • Strict user-level data isolation on every query         │
│   • Endpoints: /api/auth, /api/foods, /api/recommendations, │
│                /api/meal-plans, /api/meal-logs, /api/pantry │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│             MACHINE LEARNING & SCORING (M3)                 │
│                                                             │
│   1. Hard Safety Gate: Dietary & allergen hard exclusion    │
│   2. Text Vectorization: TF-IDF + Cosine similarity (0.4)   │
│   3. Multi-Factor Scoring:                                  │
│      Score = 0.40 × Similarity + 0.30 × Macro Fit           │
│            + 0.20 × Budget Fit + 0.10 × Prep-Time Fit       │
│   4. Adaptive Feedback Reweighting:                         │
│      Applies skip penalties (time, cost, availability)      │
│   5. Explanation Generation:                                │
│      Templates driven exclusively by active score factors   │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                  NEXT.JS FRONTEND (M1)                      │
│                                                             │
│   • Next.js + React + TypeScript + Tailwind CSS             │
│   • Interactive Dashboard, Profile Studio, Meal Plan View   │
│   • Pantry Scanner (Receipt PDF/Image & Fridge Snapshot)    │
│   • Real-Time Progress Analytics powered by Recharts        │
│   • Running locally on http://localhost:3000                │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start (Local Setup)

The entire system runs locally on your machine with zero external cloud accounts.

### 1. Prerequisites
- Python 3.10+
- Node.js 18+
- Git

### 2. Clone the Repository
```bash
git clone https://github.com/The-Reset-Button-Team/DietSense-.git
cd DietSense-
```

### 3. One-Click Start (Windows PowerShell)
```powershell
.\start_local.ps1
```
This script initializes the local SQLite database and launches both the backend and frontend in parallel.

### Or Run Manually:

#### A. Initialize Database & Start Backend
```bash
# Install backend dependencies
pip install -r backend/requirements.txt
pip install -r ml/requirements.txt

# Initialize database tables
python backend/db/init_db.py

# Launch FastAPI backend
python run_backend.py
# → Backend running at: http://127.0.0.1:8000
# → Swagger API Docs:  http://127.0.0.1:8000/docs
```

#### B. Start Frontend
```bash
cd frontend
npm install
npm run dev
# → Frontend running at: http://localhost:3000
```

---

## 🧪 Testing & Verification

DietSense maintains a comprehensive automated and manual test suite:

### 1. Backend & ML Automated Tests (Pytest)
```bash
pytest tests/ -v
# Runs 39 automated tests covering:
# - test_auth.py: Authentication, token verification, session protection
# - test_local_auth_db.py: SQLite persistence, registration, user isolation
# - test_etl.py: Dataset integrity, column standardization, zero NaNs
# - test_scoring.py: Scoring formula weights, bounds, safety gate logic
# - test_recommendations.py: Top-N output, pantry integration, explainability
# - test_pantry_scanner.py: Bill receipt OCR parsing, fridge image analysis
# - test_meal_workflow.py: Complete logging, skips, adaptive re-ranking
```

### 2. Frontend Validation
```bash
cd frontend
npm run type-check   # Strict TypeScript verification
npm run lint         # Code style and syntax check
npm run build        # Production Next.js build
```

### 3. Manual Testing Checklist
Refer to [`docs/manual-test-checklist.md`](docs/manual-test-checklist.md) for step-by-step user acceptance flows.

---

## 📊 Dataset Provenance

| Dataset | Records | Description | Usage in DietSense |
|---------|---------|-------------|--------------------|
| **USDA FoodData Central** | 13,694 | Foundation Foods & SR Legacy reference nutrients | General macro and micronutrient benchmarks |
| **ICMR-NIN / IFCT 2017** | 487 | Indian Food Composition Tables | Authentic Indian recipes, regional dishes, and staples |
| **Total Merged Catalog** | **14,181** | Unified food database (`data/processed/foods_merged.csv`) | 100% verified, 0 missing/NaN calorie values |

---

## 📄 Documentation Links

- [`ARCHITECTURE.md`](ARCHITECTURE.md) — Detailed technical architecture and data schemas
- [`docs/manual-test-checklist.md`](docs/manual-test-checklist.md) — Manual end-to-end test checklist
- [`samples/README.md`](samples/README.md) — Offline pantry scanner sample receipts and images
- [`backend/README.md`](backend/README.md) — FastAPI endpoints, auth models, and SQLite queries
- [`frontend/README.md`](frontend/README.md) — Next.js components, state management, and Recharts
