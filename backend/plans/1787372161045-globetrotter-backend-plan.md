# GlobeTrotter Backend Implementation Plan

## Project Overview
Build a FastAPI + SQLAlchemy 2.0 + PostgreSQL backend for a personalized travel planning application with JWT authentication, multi-city itineraries, budget tracking, city/activity search, and public trip sharing.

## Tech Stack
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **ORM**: SQLAlchemy 2.0 (async)
- **Database**: PostgreSQL 15+
- **Migrations**: Alembic
- **Validation**: Pydantic v2
- **Auth**: JWT (PyJWT) + Argon2 (argon2-cffi)
- **Static Files**: FastAPI StaticFiles (local uploads)
- **Testing**: pytest + httpx
- **Lint/Type**: ruff, mypy

---

## Database Schema (Alembic Migrations)

### Core Tables
```sql
-- users
id UUID PK, email UNIQUE, password_hash, full_name, avatar_path, 
language_pref, role ENUM('user','admin'), created_at, updated_at

-- trips
id UUID PK, user_id FK, name, description, cover_photo_path,
start_date, end_date, visibility ENUM('private','public'), 
share_slug UNIQUE, total_budget, created_at, updated_at

-- stops (cities in a trip)
id UUID PK, trip_id FK, city_id FK, arrival_date, departure_date, 
stop_order, notes, created_at

-- activities
id UUID PK, stop_id FK, name, description, activity_type, 
start_time, end_time, estimated_cost, currency, location_name, 
latitude, longitude, created_at

-- cities (catalog - seeded + extensible)
id UUID PK, name, country, country_code, region, timezone,
cost_index (1-100), popularity_score, latitude, longitude,
image_url, description, created_at

-- activities_catalog (catalog - seeded + extensible)
id UUID PK, city_id FK, name, description, activity_type, 
avg_cost, currency, duration_minutes, tags[], image_url, 
latitude, longitude, source ENUM('seed','external'), external_id, created_at

-- trip_shares (public share tracking)
id UUID PK, trip_id FK, share_slug UNIQUE, view_count, 
created_at, expires_at (nullable)

-- trip_copies (fork tracking)
id UUID PK, original_trip_id FK, copied_trip_id FK, 
copied_by_user_id FK, created_at

-- user_saved_destinations
id UUID PK, user_id FK, city_id FK, created_at
```

### Indexes
- `trips(user_id, start_date)`
- `stops(trip_id, stop_order)`
- `activities(stop_id, start_time)`
- `cities(country, popularity_score DESC)`
- `activities_catalog(city_id, activity_type)`

---

## API Endpoints

### Auth (`/api/v1/auth`)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/signup` | Register new user |
| POST | `/login` | Return access + refresh tokens |
| POST | `/refresh` | Rotate refresh token |
| POST | `/forgot-password` | Request reset email (stub) |
| POST | `/reset-password` | Reset with token (stub) |
| GET | `/me` | Current user profile |
| PATCH | `/me` | Update profile (name, avatar, language) |
| DELETE | `/me` | Delete account |

### Trips (`/api/v1/trips`)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/` | Create trip |
| GET | `/` | List user's trips (paginated, filter: upcoming/past) |
| GET | `/{trip_id}` | Get trip with stops + activities |
| PATCH | `/{trip_id}` | Update trip metadata |
| DELETE | `/{trip_id}` | Delete trip |
| POST | `/{trip_id}/stops` | Add stop (city + dates) |
| PATCH | `/{trip_id}/stops/{stop_id}` | Update stop |
| DELETE | `/{trip_id}/stops/{stop_id}` | Delete stop |
| POST | `/{trip_id}/stops/reorder` | Bulk reorder stops |
| GET | `/{trip_id}/budget` | Cost breakdown + charts data |
| GET | `/{trip_id}/calendar` | Timeline/calendar view data |

### Activities (`/api/v1/trips/{trip_id}/stops/{stop_id}/activities`)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/` | Add activity to stop |
| GET | `/` | List activities for stop |
| PATCH | `/{activity_id}` | Update activity |
| DELETE | `/{activity_id}` | Delete activity |
| POST | `/{activity_id}/reorder` | Reorder within stop |

### City Search (`/api/v1/cities`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Search cities (q, country, region, limit, offset) |
| GET | `/{city_id}` | City details |
| GET | `/{city_id}/activities` | Catalog activities for city (filter: type, cost, duration) |

### Activity Search (`/api/v1/activities/catalog`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Search activities (city_id, type, cost_min, cost_max, duration_max) |

### Sharing (`/api/v1/sharing`)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/trips/{trip_id}/share` | Generate public share slug |
| DELETE | `/trips/{trip_id}/share` | Revoke public share |
| GET | `/public/{share_slug}` | Public read-only trip view |
| POST | `/public/{share_slug}/copy` | Fork trip to current user |

### Admin (`/api/v1/admin`) - Requires `role=admin`
| Method | Path | Description |
|--------|------|-------------|
| GET | `/stats` | Users count, trips count, top cities, top activities |
| GET | `/users` | Paginated user list |
| PATCH | `/users/{user_id}/deactivate` | Deactivate user |
| GET | `/trips` | All trips (paginated, filter by user) |

### Uploads (`/api/v1/uploads`)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/trip-cover` | Upload trip cover photo |
| POST | `/avatar` | Upload user avatar |

---

## Service Layer Architecture

```
app/
├── main.py                 # FastAPI app factory
├── core/
│   ├── config.py           # Settings (pydantic-settings)
│   ├── security.py         # JWT, Argon2, password hashing
│   ├── database.py         # Async engine, session dependency
│   └── exceptions.py       # Custom exceptions + handlers
├── models/                 # SQLAlchemy models
├── schemas/                # Pydantic schemas (request/response)
├── repositories/           # Data access layer (CRUD per model)
├── services/               # Business logic
│   ├── auth_service.py
│   ├── trip_service.py
│   ├── city_service.py     # Hybrid: local DB + external adapter interface
│   ├── activity_service.py
│   ├── budget_service.py
│   ├── sharing_service.py
│   └── upload_service.py
├── api/
│   ├── deps.py             # Dependencies (current_user, admin_user, db)
│   └── v1/                 # Route modules
├── tasks/                  # Background tasks (email stubs, etc.)
└── scripts/
    └── seed_data.py        # Seed cities + activities catalog
```

### Hybrid City/Activity Service Interface
```python
# services/city_service.py
class CityProvider(Protocol):
    async def search(self, q: str, country: str | None, limit: int) -> list[City]: ...
    async def get(self, city_id: UUID) -> City | None: ...
    async def get_activities(self, city_id: UUID, filters: ActivityFilters) -> list[Activity]: ...

class LocalCityProvider(CityProvider):
    def __init__(self, repo: CityRepository): ...

# Later: class ExternalCityProvider(CityProvider): ...
```

---

## Authentication & Authorization

- **Access Token**: 15 min, RS256 (or HS256 for simplicity), payload: `sub=user_id`, `role`, `exp`
- **Refresh Token**: 7 days, stored hashed in DB (revocable), rotation on use
- **Password**: Argon2id (argon2-cffi), min 8 chars
- **Dependencies**:
  - `get_current_user` → User model
  - `require_admin` → raises 403 if not admin
  - `get_optional_user` → for public share views

---

## Budget Calculation Logic

```
Trip Budget = Σ(stop budgets)
Stop Budget = Σ(activity.estimated_cost) + daily_estimates
Daily Estimates (per stop):
  - accommodation: cost_index * base_rate * nights
  - meals: cost_index * meal_rate * days
  - local_transport: cost_index * transport_rate * days
```
- All amounts stored in trip currency (default USD), conversion rates stubbed
- Over-budget alert: any day > 1.5 * average daily budget

---

## File Uploads

- `POST /uploads/trip-cover` → saves to `./uploads/trips/{trip_id}/{uuid}.{ext}`
- `POST /uploads/avatar` → saves to `./uploads/avatars/{user_id}/{uuid}.{ext}`
- Max 5MB, allowed: jpg, png, webp
- Served via `StaticFiles(mount="/uploads", directory="uploads")`
- Return `{ "url": "/uploads/trips/.../file.jpg" }`

---

## Seeding Strategy

- `scripts/seed_data.py` run via `alembic upgrade head && python -m scripts.seed_data`
- ~60 major cities across 6 continents with cost_index, popularity, coordinates
- ~300 activities across types: sightseeing, food, adventure, culture, nature, nightlife
- JSON fixtures in `app/fixtures/cities.json`, `activities.json`

---

## Validation & Error Handling

- Pydantic models for all request/response
- Global exception handler → `{ "detail": "...", "code": "ERROR_CODE" }`
- 404 for not found, 403 for forbidden, 422 for validation
- Custom codes: `TRIP_NOT_FOUND`, `SHARE_EXPIRED`, `OVER_BUDGET`, `UNAUTHORIZED`

---

## Testing Strategy

| Layer | Tool | Coverage Target |
|-------|------|-----------------|
| Unit | pytest | Services, utilities, budget calc |
| Integration | pytest + httpx + testcontainers (PostgreSQL) | All API endpoints |
| Contract | schemathesis | OpenAPI spec compliance |

- Fixtures: `user_factory`, `trip_factory`, `city_factory`
- Run: `pytest -xvs --cov=app --cov-report=term-missing`

---

## Lint & Type Check Commands

```bash
ruff check app tests
ruff format app tests
mypy app
```

---

## Environment Variables (`.env`)

```env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/globetrotter
SECRET_KEY=change-me-32-chars-min
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
UPLOAD_DIR=./uploads
MAX_UPLOAD_MB=5
```

---

## Migration Order (Alembic)

1. `create_users_table`
2. `create_cities_table`
3. `create_activities_catalog_table`
4. `create_trips_table`
5. `create_stops_table`
6. `create_activities_table`
7. `create_trip_shares_table`
8. `create_trip_copies_table`
9. `create_user_saved_destinations_table`
10. `add_indexes`

---

## Open Questions / Out of Scope

- **Email delivery**: Forgot/reset password emails stubbed (log to console)
- **Currency conversion**: Fixed USD, rates service interface defined but not implemented
- **Real-time collaboration**: Not in scope (only copy/fork)
- **Push notifications**: Out of scope
- **Rate limiting**: Basic slowapi middleware, not configured
- **API versioning**: `/api/v1` prefix only
- **Docker/Deploy**: Not in this plan

---

## Implementation Order (Suggested)

1. Project scaffolding + config + database + security
2. User auth (signup, login, JWT, refresh, me)
3. Cities + Activities catalog (models, repos, seed script, search endpoints)
4. Trips CRUD + Stops CRUD + Reorder
5. Activities CRUD per stop
6. Budget calculation service + endpoints
7. Calendar/Timeline endpoint
8. Sharing (public slug, view, copy)
9. Uploads (avatar, trip cover)
10. Admin stats + user management
11. Tests + lint/type CI
12. OpenAPI docs review