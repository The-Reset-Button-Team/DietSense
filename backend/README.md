# DietSense — Backend (M2 Pranav Chaudhari)

FastAPI · Local SQLite Database · Pydantic v2 · Local Session/JWT Authentication

---

## 🚀 Quick Setup

```bash
# From repository root or backend/
cd backend
python -m venv venv

# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
pip install -r ../ml/requirements.txt

# Initialize local SQLite database
python db/init_db.py

# Launch server
python ../run_backend.py
# Or: uvicorn app.main:app --reload --port 8000
```

- **API Base**: `http://127.0.0.1:8000`
- **Interactive Swagger UI**: `http://127.0.0.1:8000/docs`
- **Alternative ReDoc**: `http://127.0.0.1:8000/redoc`

---

## 🗄️ Local SQLite Database

DietSense uses a local-first SQLite database stored at `database/dietsense.db`.

To inspect or initialize the schema:
```bash
python backend/db/init_db.py
```

### Managed Tables:
1. `foods` — 14,181 foods sourced from USDA and ICMR-NIN.
2. `users` — Hashed passwords (bcrypt), email, status, timestamps.
3. `profiles` — Biometrics, calorie targets, dietary preferences, and allergy lists.
4. `meal_plans` — Saved daily meal plans per authenticated user.
5. `meal_logs` — Recorded meal logs with outcome (`eaten` or `skipped`) and validated skip reasons (`time`, `cost`, `unavailable`, `taste`).
6. `feedback` — User meal ratings and subjective notes.
7. `pantry_items` — Scanned or manually added grocery items per user.

---

## 🔒 Authentication & Data Isolation

- **Local Session/JWT Auth:** Authentication is managed locally by FastAPI. Login returns a secure, signed JWT token (as a Bearer token or HttpOnly cookie).
- **Strict User Isolation:** Every database query filters by `user_id` derived directly from the verified token. User IDs sent in request bodies are never trusted.
- **Offline Email Support:** In local operation, account registration does not depend on cloud email services; registration activates immediately.

---

## 📂 Directory Structure

```
backend/
├── app/
│   ├── main.py               # FastAPI application entry point, CORS, routers
│   ├── core/
│   │   ├── config.py         # Pydantic BaseSettings (DB path, secrets, CORS)
│   │   ├── security.py       # Password hashing & JWT generation/verification
│   │   └── dependencies.py   # get_current_user, get_optional_user dependencies
│   └── routers/
│       ├── auth.py           # Register, login, me, logout endpoints
│       └── foods.py          # Food search and pagination endpoints
├── db/
│   ├── database.py           # SQLite connection pool, WAL mode, schema init
│   └── init_db.py            # Standalone database initialization script
└── routes/
    ├── users.py              # User profile endpoints
    ├── recommendations.py    # Recommendation pipeline endpoint
    ├── meal_plans.py         # Saved plan CRUD endpoints
    ├── meal_logs.py          # Meal outcome logging & analytics
    ├── feedback.py           # Meal ratings & notes
    └── pantry.py             # Grocery receipt & fridge scanner endpoints
```

---

## 🧪 Testing

```bash
pytest ../tests/test_auth.py ../tests/test_local_auth_db.py ../tests/test_pantry_scanner.py -v
```
