# DietSense — Supabase Integration Architecture & Implementation Plan

**Document ID**: DIETSENSE-SUPABASE-ARCH-01  
**Status**: Ready for Review / Pre-Implementation  
**Target Phase**: Phase 2/3 Preparation  
**Audience**: Backend Engineers, Full-Stack Architects, DevOps  

---

## Executive Overview

This document defines the architectural blueprint and operational plan for integrating **Supabase** (PostgreSQL, Supabase Auth, Row-Level Security, and Supabase Storage) into the DietSense platform.

### Core Architecture Principles:
1. **Zero Downtime / Dual-Database Capability**: SQLite remains the local offline development and test database. Supabase provides cloud persistence, multi-device synchronization, and managed PostgreSQL capabilities.
2. **Strict Nutritional Data Integrity**: The 14,099 reference food records (USDA & ICMR-NIN) remain the sole ground truth for macronutrient and micronutrient values.
3. **Secure Backend-Only Credential Isolation**: Sensitive credentials (`SUPABASE_SERVICE_ROLE_KEY`, `DATABASE_URL` with password) reside exclusively within the FastAPI backend environment. The client browser never receives elevated service credentials.
4. **Row-Level Security (RLS) as Non-Bypasable Guardrail**: Every user-owned table (`profiles`, `meal_plans`, `meal_logs`, `feedback`, `pantry_items`) enforces strict RLS policies tied to `auth.uid()`.

---

## 1. Backend Integration Locations

To avoid tight coupling and preserve local SQLite testability, the Supabase integration will be placed in dedicated modules following the repository pattern:

```
backend/
├── app/
│   ├── core/
│   │   ├── config.py              # Settings model (load Supabase environment variables)
│   │   ├── dependencies.py        # Update get_current_user to verify Supabase JWTs
│   │   └── supabase.py            # [NEW] Supabase client singleton & session helpers
│   └── routers/
│       └── auth.py                # Bridge routes for Supabase Auth flows
├── db/
│   ├── client.py                  # Database connection dispatcher (SQLite vs PostgreSQL)
│   ├── database.py                # Preserved SQLite engine (local & tests)
│   ├── supabase_db.py             # [NEW] PostgreSQL connection pooler (SQLAlchemy / asyncpg)
│   └── migrations/
│       ├── 001_create_profiles.sql        # Existing Supabase RLS profiles schema
│       ├── 002_user_profile_meal_logs.sql # Existing Supabase RLS logs schema
│       └── 003_foods_and_pantry.sql       # [NEW] Foods catalog & pantry storage schema
└── scripts/
    └── migrate_sqlite_to_supabase.py      # [NEW] Bulk ETL tool for 14,099 foods & existing users
```

### Module Responsibilities:
- `backend/app/core/supabase.py`: Initializes `supabase-py` client instances using `SUPABASE_URL` and `SUPABASE_ANON_KEY` (for client-impersonated calls) or `SUPABASE_SERVICE_ROLE_KEY` (for administrative background tasks).
- `backend/db/supabase_db.py`: Establishes direct connection pooling to Supabase PostgreSQL (via transaction pooler port 6543) using SQLAlchemy 2.0.
- `backend/app/core/dependencies.py`: Updates token decoding logic to support Supabase JWT verification (validating signature, issuer `https://<project-ref>.supabase.co/auth/v1`, and audience `authenticated`).

---

## 2. Required Supabase Python Dependencies

The following packages will be added to `backend/requirements.txt` and root `requirements.txt` when implementation commences:

```txt
# ─── Supabase SDK & PostgREST ──────────────────────────────────────────────────
supabase>=2.10.0           # Official Supabase Python client (includes postgrest, gotrue, realtime, storage3)

# ─── PostgreSQL Driver & Pooling ──────────────────────────────────────────────
psycopg2-binary>=2.9.9     # Authoritative PostgreSQL adapter for synchronous SQLAlchemy queries
asyncpg>=0.29.0            # High-performance asynchronous PostgreSQL driver for async routes

# ─── JWT & Cryptographic Verification ─────────────────────────────────────────
PyJWT[crypto]>=2.8.0       # Already present in DietSense; validates Supabase HS256/RS256 JWTs
cryptography>=42.0.0       # Required for RS256 / JWKS public key token verification
```

*Note: No dependencies will be installed during this planning phase.*

---

## 3. Client APIs vs. Direct PostgreSQL: The Hybrid Strategy

DietSense handles two distinct workloads:
1. High-throughput read-heavy queries over the **14,099 food catalog**.
2. Strict user-scoped mutations on **profiles, meal plans, meal logs, and receipt images**.

We recommend a **Hybrid Architecture**:

```
┌────────────────────────────────────────────────────────────────────────┐
│                          FASTAPI BACKEND                               │
├───────────────────────────────────┬────────────────────────────────────┤
│     SUPABASE CLIENT API           │   DIRECT POSTGRESQL (POOLER)       │
│     (supabase-py / PostgREST)     │   (SQLAlchemy + psycopg2 / asyncpg)│
├───────────────────────────────────┼────────────────────────────────────┤
│ • User Authentication & Sessions  │ • 14,099 Food Catalog Queries      │
│ • RLS-Enforced User Operations    │ • TF-IDF Candidate Batch Filtering │
│ • Storage API (Receipts & Photos) │ • Bulk ETL Migration Scripts       │
│ • Database Webhooks & Realtime    │ • Complex Multi-Table Aggregations │
└─────────────────┬─────────────────┴──────────────────┬─────────────────┘
                  │                                    │
                  ▼                                    ▼
┌───────────────────────────────────┐┌───────────────────────────────────┐
│     SUPABASE HTTPS GATEWAY        ││   SUPABASE PGBOUNCER POOLER       │
│     Port 443 (REST / Auth API)    ││   Port 6543 (Transaction Mode)    │
└─────────────────┬─────────────────┘└─────────────────┬─────────────────┘
                  │                                    │
                  └─────────────────┬──────────────────┘
                                    ▼
                     ┌─────────────────────────────┐
                     │     SUPABASE POSTGRESQL     │
                     │  • auth.users               │
                     │  • public.profiles          │
                     │  • public.foods (14,099)    │
                     │  • public.meal_plans        │
                     │  • public.meal_logs         │
                     │  • public.pantry_items      │
                     │  • public.ai_interaction_   │
                     │    logs                     │
                     └─────────────────────────────┘
```

### Why Both?
- **Supabase Client API (Port 443 HTTPS)**:
  - Automatically respects Row-Level Security when forwarded the user's JWT.
  - Native integration with **Supabase Storage** for uploading and managing receipt PDFs and fridge images.
  - Zero firewall issues on restricted corporate or cloud networks.
- **Direct PostgreSQL Connection (Port 6543 Transaction Pooler)**:
  - Sub-millisecond latency for complex vectorized candidate scans across 14,099 foods.
  - Efficient batch `INSERT` / `COPY` operations for ETL and data sync.
  - Full support for SQLAlchemy expression language and future pgvector queries.

---

## 4. Secure Backend-Only Configuration

To maintain strict security and protect clinical user data:

1. **Client Isolation**: The browser client (Next.js) **never** receives `SUPABASE_SERVICE_ROLE_KEY` or direct database connection strings.
2. **Reverse Proxy / Gateway Model**: Next.js communicates strictly with the FastAPI backend (`http://localhost:8000` or production API gateway). FastAPI acts as the gatekeeper.
3. **Service Role Restrictions**: `SUPABASE_SERVICE_ROLE_KEY` is utilized strictly for:
   - Creating initial food composition tables during migration.
   - Administrative audit operations on `ai_interaction_logs`.
   - Automated system cleanup jobs.
   Every normal user request runs within the context of that specific user's JWT, ensuring PostgreSQL RLS evaluates `auth.uid() = user_id`.

---

## 5. Required Environment Variables

The following variables must be added to `backend/.env` (and configured in production secret management):

```env
# =============================================================================
# DietSense — Supabase Integration Configuration
# =============================================================================

# Active database provider: 'sqlite' (local dev/testing) or 'supabase' (production)
DATABASE_PROVIDER=supabase

# Supabase Project API URL (Found in Project Settings > API)
SUPABASE_URL=https://[YOUR-PROJECT-REF].supabase.co

# Supabase Anonymous Public Key (Found in Project Settings > API)
SUPABASE_ANON_KEY=[YOUR-ANON-KEY]

# Supabase Service Role Secret Key (Found in Project Settings > API)
# WARNING: Keep secret. Never commit to Git or expose to client frontend.
SUPABASE_SERVICE_ROLE_KEY=[YOUR-SERVICE-ROLE-KEY]

# Supabase JWT Secret (Found in Project Settings > API > JWT Settings)
# Used by FastAPI to verify Supabase-issued Bearer tokens locally without API overhead.
SUPABASE_JWT_SECRET=[YOUR-SUPABASE-JWT-SECRET]

# Direct PostgreSQL Connection String via Supabase Transaction Pooler
# Found in Project Settings > Database > Connection String (URI, Mode: Transaction, Port: 6543)
SUPABASE_DB_URL=postgresql://postgres.[YOUR-PROJECT-REF]:[YOUR-DB-PASSWORD]@aws-0-[YOUR-REGION].pooler.supabase.com:6543/postgres

# Supabase Storage Buckets
SUPABASE_STORAGE_BUCKET_RECEIPTS=receipts
SUPABASE_STORAGE_BUCKET_FRIDGE=fridge-snapshots
```

---

## 6. Credentials to Obtain Manually from Supabase Dashboard

You must create a project at [supabase.com](https://supabase.com) and retrieve the following credentials:

| Credential Name | Dashboard Location | Description / Purpose |
|---|---|---|
| **Project URL** (`SUPABASE_URL`) | *Project Settings > API > Project URL* | Base HTTPS URL for API and Auth endpoints (e.g., `https://xyzcompany.supabase.co`). |
| **Anon Public Key** (`SUPABASE_ANON_KEY`) | *Project Settings > API > Project API keys > `anon` `public`* | Safe for public clients, used by backend to initiate requests on behalf of users. |
| **Service Role Key** (`SUPABASE_SERVICE_ROLE_KEY`) | *Project Settings > API > Project API keys > `service_role` `secret`* | Elevated administrative key that bypasses RLS. Must remain confidential. |
| **JWT Secret** (`SUPABASE_JWT_SECRET`) | *Project Settings > API > JWT Settings > JWT Secret* | Shared HMAC secret used to decode and verify JWTs issued by Supabase Auth. |
| **Database Password** | *Set during project creation* (or reset in *Database > Database Password*) | Password for the `postgres` administrative database user. |
| **Pooled Connection String** (`SUPABASE_DB_URL`) | *Project Settings > Database > Connection string > Mode: Transaction (Port 6543)* | High-performance pooled connection string for SQLAlchemy queries. |

---

## 7. Existing Architecture vs. Supabase Target Architecture

### Authentication Transition:
- **Current**: Custom bcrypt password hashing in SQLite `users` table; tokens signed by local `JWT_SECRET`.
- **Target**: Supabase GoTrue Auth manages users in `auth.users`. FastAPI verifies the incoming Supabase JWT token and extracts `sub` as `user_id`. A database trigger (`handle_new_user`) automatically provisions the user's record in `public.profiles`.
- **Backward Compatibility**: During transition, `dependencies.py` will inspect the token issuer: if local, verify via local secret; if Supabase, verify via Supabase JWT secret.

### Database Architecture Transition:

| Entity | Current SQLite State | Target Supabase PostgreSQL State |
|---|---|---|
| `users` | Local SQLite table (id TEXT, password_hash) | Managed by Supabase `auth.users` (UUID PK). |
| `profiles` | SQLite table, JSON strings for lists | `public.profiles` (UUID PK -> `auth.users(id)`), RLS enabled, JSONB for preferences. |
| `foods` | 14,099 rows in SQLite `foods` | `public.foods` (14,099 rows in PostgreSQL), `SELECT` open to public, `INSERT/UPDATE` restricted to admin. |
| `meal_plans` | SQLite table (0 rows) | `public.meal_plans` with RLS (`user_id = auth.uid()`). |
| `meal_logs` | SQLite table (5 rows) | `public.meal_logs` with RLS (`user_id = auth.uid()`). |
| `feedback` | SQLite table (0 rows) | `public.feedback` with RLS (`user_id = auth.uid()`). |
| `pantry_items` | SQLite table (5 rows) | `public.pantry_items` with RLS (`user_id = auth.uid()`). |
| Receipt Storage | Local disk (`samples/`) | Supabase Storage bucket (`receipts`) with private RLS access. |
| Audit Trail | None | `public.ai_interaction_logs` (tracking prompt context and Gemini token usage). |

---

## 8. Data Migration Plan (14,099 Foods & Existing Data)

A dedicated script (`scripts/migrate_sqlite_to_supabase.py`) will be developed to:
1. Connect simultaneously to local `database/dietsense.db` and Supabase PostgreSQL.
2. Read the 14,099 verified food records from SQLite.
3. Batch insert into `public.foods` in chunks of 1,000 using parameterized statements, ensuring exact nutrient retention (0 NaN values).
4. Create necessary PostgreSQL performance indexes:
   ```sql
   CREATE INDEX idx_foods_category ON public.foods (food_category);
   CREATE INDEX idx_foods_cals ON public.foods (calories_kcal);
   CREATE INDEX idx_foods_veg ON public.foods (is_vegetarian);
   CREATE INDEX idx_foods_name_trgm ON public.foods USING gin (name gin_trgm_ops);
   ```

---

## 9. Implementation Checklist (Next Phases)

- [ ] Create project on Supabase Dashboard.
- [ ] Retrieve manual credentials (`SUPABASE_URL`, `ANON_KEY`, `SERVICE_ROLE_KEY`, `JWT_SECRET`, `SUPABASE_DB_URL`).
- [ ] Execute `backend/db/schema.sql` and migrations `001`, `002`, `003` in the Supabase SQL Editor.
- [ ] Create private Supabase Storage buckets: `receipts` and `fridge-snapshots`.
- [ ] Add `supabase`, `psycopg2-binary`, and `asyncpg` to backend requirements.
- [ ] Implement `backend/app/core/supabase.py` client wrapper.
- [ ] Execute `scripts/migrate_sqlite_to_supabase.py` to upload the 14,099 food records.
- [ ] Update `backend/app/core/dependencies.py` to authenticate Supabase JWT tokens.
- [ ] Run test suite against Supabase test instance to verify 100% compliance.
