# BuildOptima Backend Design Spec
**Date:** 2026-04-22
**Status:** Approved

---

## Overview

Full backend for the MPOptima PC build optimizer web app. The frontend is a completed single-file React app (`frontend/BuildOptima.html`) with hardcoded mock data. This backend replaces all mock data with a real API, database, auth system, and optimization engine.

---

## Tech Stack

| Layer | Choice |
|-------|--------|
| Runtime | Python 3.12 |
| Framework | FastAPI (sync) |
| Database | PostgreSQL |
| ORM | SQLAlchemy (sync sessions) |
| Auth | JWT via python-jose, bcrypt via passlib |
| Config | python-dotenv + .env file |
| Seed | Standalone seed.py script |

---

## Project Structure

```
/backend
  main.py                  # FastAPI app, CORS, router registration
  seed.py                  # Populates parts table with real data
  requirements.txt
  .env                     # DATABASE_URL, JWT_SECRET, token expiry times

  /routers
    auth.py                # /auth/register, /auth/login, /auth/refresh
    builds.py              # /builds CRUD (auth required)
    optimizer.py           # /optimize (public)

  /models
    __init__.py
    user.py                # User SQLAlchemy model
    build.py               # Build + BuildComponent SQLAlchemy models
    part.py                # Part SQLAlchemy model

  /schemas
    __init__.py
    auth.py                # Register/Login/Token Pydantic schemas
    build.py               # Build save/response Pydantic schemas
    optimizer.py           # OptimizeRequest/OptimizeResponse Pydantic schemas

  /core
    config.py              # Settings loaded from .env via pydantic-settings
    security.py            # JWT creation/validation, bcrypt hashing

  /db
    database.py            # SQLAlchemy engine, SessionLocal, Base, get_db dependency
```

---

## Database Schema

### `users`
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | auto-increment |
| email | String(255) | unique, indexed |
| hashed_password | String(255) | bcrypt hash |
| created_at | DateTime | server default UTC now |

### `builds`
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | auto-increment |
| user_id | Integer FK → users.id | cascade delete |
| build_name | String(255) | |
| use_case | String(50) | gaming / content_creation / workstation / general |
| budget | Integer | dollars |
| total_price | Float | actual total of selected parts |
| created_at | DateTime | server default UTC now |

### `build_components`
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | auto-increment |
| build_id | Integer FK → builds.id | cascade delete |
| component_category | String(50) | cpu / gpu / ram / storage / motherboard / psu / case / cooler |
| part_name | String(255) | |
| part_price | Float | |
| reason_selected | Text | human-readable explanation |

### `parts`
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | auto-increment |
| category | String(50) | cpu / gpu / ram / storage / motherboard / psu / case / cooler |
| name | String(255) | |
| brand | String(100) | |
| price | Float | |
| specs | JSON | category-specific (see below) |

**Specs shape per category:**
- `cpu`: `{ cores, base_clock_ghz, tdp_watts, architecture }`
- `gpu`: `{ vram_gb, tdp_watts, benchmark_score, tier }` — tier: "budget" | "mid" | "high" | "flagship"
- `ram`: `{ size_gb, speed_mhz }`
- `storage`: `{ size_gb, read_speed_mbs, type }` — type: "nvme" | "sata"
- `psu`: `{ wattage, efficiency_rating }` — rating: "80plus" | "bronze" | "gold" | "platinum"
- `motherboard`: `{ socket, form_factor, chipset }`
- `case`: `{ form_factor, max_gpu_length_mm }`
- `cooler`: `{ type, tdp_rating_watts, noise_db, is_quiet }` — type: "air" | "aio"

---

## Auth System

### Endpoints

**POST /auth/register**
- Body: `{ email: str, password: str }`
- Validates email uniqueness; hashes password with bcrypt
- Returns: `{ access_token, refresh_token, token_type: "bearer" }`
- Errors: 400 if email already registered

**POST /auth/login**
- Body: `{ email: str, password: str }` (OAuth2PasswordRequestForm)
- Validates credentials; returns same token shape as register
- Errors: 401 if credentials invalid

**POST /auth/refresh**
- Body: `{ refresh_token: str }`
- Validates refresh token; returns new access token
- Errors: 401 if token invalid or expired

### Token Configuration (.env)
```
JWT_SECRET_KEY=<random 32+ char secret>
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

### Protected Route Dependency
`get_current_user` FastAPI dependency: extracts Bearer token from `Authorization` header, decodes JWT, returns User ORM object. Applied to all `/builds` routes.

---

## Builds API

All routes require `Authorization: Bearer <access_token>`.

**POST /builds/save**
- Body: `{ build_name, use_case, budget, total_price, components: [{ category, part_name, part_price, reason_selected }] }`
- Creates Build + BuildComponent rows in a single transaction
- Returns: full saved build with components

**GET /builds**
- Returns all builds for the authenticated user, ordered by `created_at` desc
- Each item includes build metadata (no components list — for the index view)

**GET /builds/{id}**
- Returns single build with full component list
- 404 if not found; 403 if build belongs to a different user

**DELETE /builds/{id}**
- Deletes build and its components (cascade)
- Returns 204 No Content
- 404 if not found; 403 if build belongs to a different user

---

## Optimizer Engine

### Endpoint

**POST /optimize** — public, no auth required

**Request:**
```json
{
  "budget": 1500,
  "use_case": "gaming",
  "future_proofing": false,
  "owns_gpu": false,
  "prefer_quiet_cooling": false
}
```

**Response:**
```json
{
  "use_case": "gaming",
  "budget": 1500,
  "total_price": 1423.0,
  "components": [
    {
      "category": "cpu",
      "name": "AMD Ryzen 5 7600X",
      "brand": "AMD",
      "price": 229.0,
      "reason": "Strong gaming CPU — 6 cores at 4.7GHz base clock handles all modern titles at high frame rates.",
      "specs": { "cores": 6, "base_clock_ghz": 4.7, "tdp_watts": 105, "architecture": "Zen 4" }
    }
  ]
}
```

### Algorithm

**1. Category weights by use case:**

| Category    | Gaming | Content Creation | Workstation | General |
|-------------|--------|-----------------|-------------|---------|
| cpu         | 0.18   | 0.28            | 0.32        | 0.22    |
| gpu         | 0.38   | 0.20            | 0.10        | 0.18    |
| ram         | 0.10   | 0.18            | 0.18        | 0.16    |
| storage     | 0.08   | 0.12            | 0.16        | 0.12    |
| motherboard | 0.10   | 0.08            | 0.08        | 0.12    |
| psu         | 0.07   | 0.06            | 0.07        | 0.08    |
| case        | 0.05   | 0.04            | 0.05        | 0.06    |
| cooler      | 0.04   | 0.04            | 0.04        | 0.06    |

**2. Part performance score:**
At query time, the optimizer fetches all parts from the database and computes a `perf_score` (0.0–1.0) per part by ranking prices within each category. The cheapest part gets ~0.1, the most expensive gets 1.0, linearly interpolated across the range. No extra column is needed — this is derived from `price` at runtime.

**3. Budget allocation and part selection:**
1. Compute `target_budget[cat] = budget * weight[cat]` for each active category
2. If `owns_gpu=True`: remove `gpu` from active categories, redistribute its weight proportionally to the remaining 7 categories, recompute targets
3. For each category: select the highest `perf_score` part with `price <= target_budget[cat]`; fall back to cheapest part if none fits
4. Compute `remaining = budget - sum(selected prices)`
5. **Greedy upgrade pass**: for each category, find the cheapest part more expensive than the currently selected part; collect all such candidate upgrades across all categories; apply the one with the lowest upgrade cost that fits within `remaining`; subtract cost delta from remaining; repeat until no candidate upgrade fits

**4. Flag modifiers:**
- `future_proofing=True`: multiply `perf_score` by 1.3 for parts in the top price tier of each category (price > 75th percentile within category). This biases initial selection and upgrade pass toward higher-end parts.
- `prefer_quiet_cooling=True`: when selecting a cooler, filter candidates to `is_quiet=True` first; only consider non-quiet coolers if no quiet option fits the budget.
- `owns_gpu=True`: GPU category skipped entirely; its weight redistributed proportionally.

**5. Reason string generation:**
Built per-part from a template combining: use case label, category weight priority label ("top-weighted", "mid-priority", "supporting"), and the part's most relevant spec. Generated in Python (no LLM call).

---

## Parts Seed Data

`seed.py` populates the `parts` table with 6–8 real/realistic parts per category spanning budget to flagship. Categories:

- **CPU** (8 parts): budget Ryzen 5 → flagship Ryzen 9 / i9
- **GPU** (8 parts): budget RX 6600 → flagship RTX 4090
- **RAM** (6 parts): 16GB DDR4 3200 → 64GB DDR5 6400
- **Storage** (6 parts): 500GB SATA SSD → 2TB NVMe Gen4
- **Motherboard** (6 parts): budget B450 → flagship X670E
- **PSU** (6 parts): 550W Bronze → 1000W Platinum
- **Case** (6 parts): budget Micro-ATX → premium full-tower
- **Cooler** (6 parts): budget air (is_quiet=False) → 360mm AIO (is_quiet=True)

---

## Environment Variables (.env)

```
DATABASE_URL=postgresql://user:password@localhost:5432/buildoptima
JWT_SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

---

## CORS Configuration

`main.py` adds `CORSMiddleware` allowing all origins (`*`) during local development. Frontend served at `file://` or `localhost` will be able to reach `http://localhost:8000`.

---

## Key Implementation Constraints

- All `/builds` routes enforce ownership: a user can only read/delete their own builds (403 on mismatch)
- `seed.py` is idempotent: it checks for existing parts before inserting to allow safe re-runs
- Passwords must be at minimum 8 characters (validated in Pydantic schema)
- Budget accepted range: 300–5000 (validated in OptimizeRequest schema)
- Use case must be one of the four defined values (Pydantic Literal type)
