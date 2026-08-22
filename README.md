# GlobeTrotter ✈️ — Personalized Travel Planning Studio

A full-featured **desktop travel planning app** built with Python + CustomTkinter.

---

## Features

| Module | Screens |
|--------|---------|
| **Auth** | Login (2-panel animated) · Sign Up · Reset Password |
| **Dashboard** | Hero banner · Metrics · Recent trips · Trending cities |
| **Trip Manager** | My Trips (filter tabs · sort · search) · 3-Step Create Wizard |
| **Itinerary Builder** | City stops with reorder/delete · Activities with type icons · Live budget bar |
| **Budget Intelligence** | Pie chart · Category bars · Per-stop costs · Day-by-day table |
| **Calendar** | Month grid · Trip-range tint · Day-click detail · Horizontal timeline |
| **City Directory** | Region chips · City cards with save star · Add City modal |
| **Activity Search** | Type chips · Cost range filter · Add to Trip flow |
| **Share & Community** | Generate/Revoke share link · Import by slug · Clone trips |
| **Profile** | Stats · Edit name/language · Change password · Delete account |
| **Admin** | Platform metrics · Top cities chart · Users table · All trips table |

---

## Tech Stack

- **GUI**: [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) 5.2.2 (Material 3 Warm Orange theme)
- **Database**: SQLite via SQLAlchemy 2.0 ORM
- **Schemas**: Pydantic v2
- **Charts**: Matplotlib (Agg backend — thread-safe)
- **Date Pickers**: tkcalendar
- **Auth**: bcrypt password hashing

---

## Quick Start

```bash
# 1. Clone the repo & switch to the desktop branch
git clone <repo-url>
cd Globe-Trotter-odoo
git checkout frontend-v2

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch
python run.py
```

The database is auto-created and seeded with demo cities on first launch.

---

## Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | `admin@globetrotter.com` | `admin123` |
| User | `demo@globetrotter.com` | `demo123` |

---

## Project Structure

```
Globe-Trotter-odoo/
├── run.py                      # ← Entry point
├── requirements.txt
├── app/
│   ├── core/                   # DB engine, exceptions
│   ├── models/                 # SQLAlchemy models
│   ├── repositories/           # Data access layer
│   ├── schemas/                # Pydantic schemas
│   ├── services/               # Business logic
│   └── ui/
│       ├── app.py              # Root CTk window + router
│       ├── theme.py            # M3 Warm Orange design system
│       ├── components/
│       │   ├── cards.py        # TripCard, CityCard, MetricCard, EmptyState…
│       │   ├── header.py       # Page header with breadcrumb + CTA
│       │   └── sidebar.py      # Fixed nav with active-pill tracking
│       └── screens/
│           ├── login_screen.py
│           ├── dashboard_screen.py
│           ├── create_trip_screen.py
│           ├── itinerary_builder_screen.py
│           ├── my_trips_screen.py
│           ├── city_search_screen.py
│           ├── activity_search_screen.py
│           ├── budget_screen.py
│           ├── calendar_screen.py
│           ├── share_screen.py
│           ├── profile_screen.py
│           └── admin_screen.py
└── tests/
```

---

## Branch

All frontend work lives on **`frontend-v2`**. The `backend` branch contains the original API-only backend.
