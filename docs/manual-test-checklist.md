# DietSense — Manual Verification & End-to-End QA Checklist

This checklist documents the manual testing procedures, verification steps, and expected outcomes for the DietSense local architecture. It serves as the primary testing protocol for Quality Assurance (M4 Atharv Bodkhe) and integration verification between Frontend (M1 Daksh Chaukhande), Backend (M2 Pranav Chaudhari), and ML Engine (M3 Prasoon Bodke).

---

## 1. Pre-Flight System Readiness

Before running end-to-end tests, ensure both backend and frontend are running locally:

| Component | Command | URL / Port | Expected State |
|-----------|---------|------------|----------------|
| **Database** | `python backend/db/init_db.py` | `database/dietsense.db` | All 11 tables initialized |
| **Backend API** | `python run_backend.py` | `http://127.0.0.1:8000` | Swagger UI loads at `/docs` |
| **Frontend** | `cd frontend && npm run dev` | `http://localhost:3000` | Landing page renders |
| **Automated Suite** | `pytest` | Root repository | 39 passed |

---

## 2. End-to-End User Flow Verification

### Flow A: Registration & Authentication
- [ ] **Action:** Open `http://localhost:3000/signup`. Enter a unique email (e.g., `tester1@example.com`) and password (`Password123!`).
- [ ] **Expectation:** User is registered, password is encrypted with bcrypt in the `users` table, and a secure session/JWT cookie is stored. User is redirected to `/profile` or dashboard.
- [ ] **Action:** Log out via the header. Attempt to access `/dashboard` or `/profile` directly.
- [ ] **Expectation:** Unauthenticated user is safely redirected to `/login`.
- [ ] **Action:** Log in with invalid credentials.
- [ ] **Expectation:** UI displays clear error: "Invalid email or password" (HTTP 401).

### Flow B: User Profile & Dietary Safety Gate
- [ ] **Action:** Open `/profile`. Set dietary preference to **Vegetarian** and add allergen **Peanut**. Save profile.
- [ ] **Expectation:** Profile persists in SQLite `profiles` table.
- [ ] **Action:** Request meal recommendations on `/dashboard`.
- [ ] **Expectation:**
  - Hard safety gate runs **first** before scoring.
  - Zero non-vegetarian dishes appear in the ranked list.
  - Zero peanut-containing dishes appear in the ranked list.
  - Foods with unknown allergen status are treated conservatively and excluded.

### Flow C: Multi-Factor Scoring & Explainability
- [ ] **Action:** Inspect the ranked meal cards on `/dashboard`.
- [ ] **Expectation:**
  - Each meal card displays a plain-language explanation tag (e.g., *"Recommended because it matches your vegetarian preference and fits your budget"*).
  - Score breakdown is visible and bounded within `[0.0, 1.0]`.
  - Nutrition values (calories, protein, carbs, fats) match authoritative USDA / ICMR-NIN catalog numbers (never hallucinated).
  - Non-medical disclaimer is clearly present on the screen.

### Flow D: Meal Logging & Adaptive Feedback Loop
- [ ] **Action:** Mark a recommended meal as **Eaten**.
- [ ] **Expectation:** Stored in SQLite `meal_logs` table with `outcome="eaten"`.
- [ ] **Action:** Select a meal with preparation time > 25 minutes (e.g., `Rajma Chawal Bowl`) and mark it as **Skipped** with reason `time`.
- [ ] **Expectation:**
  - Log saved with `outcome="skipped"` and `reason="time"`.
  - Adaptive re-weighting derives the `long-prep-time` penalty tag and adds `+0.1` penalty.
- [ ] **Action:** Re-fetch recommendations on `/dashboard`.
- [ ] **Expectation:**
  - Meals with `long-prep-time` drop in relative score rank.
  - Quicker-to-prepare meals (e.g., `Vegetable Poha`) rise to the top.
  - The explanation dynamically reflects the penalty (e.g., *"Ranked lower because you have skipped long-preparation meals before"*).
  - Penalty cap is respected: repeated skips never exceed `0.5`, and scores clamp at `0.0` (never negative).

### Flow E: Progress Analytics (Recharts Integration)
- [ ] **Action:** Navigate to the `/progress` tab.
- [ ] **Expectation:**
  - Adherence percentage is calculated directly from actual logged meals (`eaten / total`).
  - Bar/pie charts show real distribution of skip reasons (`time`, `cost`, `unavailable`, `taste`).
  - Daily trend line reflects actual logged timestamps.
  - Fresh users with zero logs see a friendly empty state, never fabricated or placeholder numbers.

### Flow F: Pantry & Receipt Scanner
- [ ] **Action:** Open `/pantry` (or Pantry tab). Click **Load Sample Blinkit Bill**.
- [ ] **Expectation:** Backend extracts items (`Paneer`, `Tomato`, `Palak`, etc.) and adds them to `pantry_items`.
- [ ] **Action:** Click **Load Sample Fridge Snapshot**.
- [ ] **Expectation:** Fridge detection identifies fresh produce and adds to stock.
- [ ] **Action:** Request recommendations again.
- [ ] **Expectation:** Meals using existing pantry stock receive an ingredient-match bonus.

### Flow G: Cross-User Data Isolation
- [ ] **Action:** Open an incognito browser window. Register a second account (`tester2@example.com`).
- [ ] **Expectation:** User 2 sees an empty log history, zero logs in `/progress`, and baseline recommendations unaffected by User 1's skips.
- [ ] **Action:** Using developer tools or API client, attempt to query User 1's meal plans or logs with User 2's session token.
- [ ] **Expectation:** Backend rejects the request with HTTP 401 or HTTP 403. Every SQL query filters strictly by authenticated `user_id`.

---

## 3. Evidence Sign-off Sheet

| Role | Name | Component Verified | Date | Status |
|------|------|--------------------|------|--------|
| **M1** | Daksh Chaukhande | Frontend UI, Routes, Recharts, Responsive views | 2026-10-26 | [ ] Verified |
| **M2** | Pranav Chaudhari | FastAPI Endpoints, SQLite Isolation, JWT Cookies | 2026-10-26 | [ ] Verified |
| **M3** | Prasoon Bodke | Safety Gate, 4-Factor Weights, Adaptive Loop | 2026-10-26 | [ ] Verified |
| **M4** | Atharv Bodkhe | 14,181 Food Catalog ETL, Pytest Suite, CI Pipeline | 2026-10-26 | [ ] Verified |
