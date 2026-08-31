# DietSense — Backend (Member 2)

FastAPI · PostgreSQL (Supabase) · Pydantic · Supabase Auth

---

## Setup

```bash
cd backend
cp .env.example .env          # Fill in your Supabase credentials

python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload
```

- **API Base**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Database Setup

The full schema is in `db/schema.sql`. To apply it:

```bash
# Option 1: Supabase SQL Editor (paste the file)
# Option 2: psql
psql $DATABASE_URL -f db/schema.sql
psql $DATABASE_URL -f db/seed.sql
```

---

## Folder Structure

```
backend/
├── app/
│   ├── main.py               # FastAPI app, CORS, router registration
│   ├── core/
│   │   ├── config.py         # Environment variables (Pydantic Settings)
│   │   ├── dependencies.py   # get_db(), get_current_user() dependency injections
│   │   └── safety_gate.py    # Hard constraint filter (Phase 6)
│   ├── routers/              # One file per domain (auth, foods, recipes, plans, etc.)
│   ├── schemas/              # Pydantic request/response models
│   └── models/               # SQLAlchemy ORM models (mirrors schema.sql)
└── db/
    ├── schema.sql            # Full PostgreSQL DDL
    └── seed.sql              # Reference data: restriction types, food categories
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Login, returns JWT |
| GET | `/auth/me` | Current user profile |
| GET | `/foods` | List foods (paginated) |
| GET | `/foods/{food_id}` | Single food with all macros |
| GET | `/foods/search?q=` | Text search |
| GET | `/recipes` | List recipes |
| GET | `/recipes/{recipe_id}` | Recipe with ingredients + macros |
| POST | `/meal-plans` | Generate meal plan for user + date |
| GET | `/meal-plans/{user_id}` | User`s meal plan history |
| POST | `/feedback` | Submit post-meal rating |
| GET | `/progress/{user_id}` | Weight + calorie trends |
| POST | `/progress` | Log daily progress |

All endpoints except `/auth/register` and `/auth/login` require:
```
Authorization: Bearer <supabase-jwt>
```

---

## Naming Conventions

- **Schemas** (Pydantic): `UserCreate`, `UserResponse`, `RecipeResponse`
- **Models** (SQLAlchemy): `User`, `Food`, `Recipe`
- **Routers**: one file per resource domain (e.g., `routers/foods.py`)
- **Database columns**: `snake_case`
