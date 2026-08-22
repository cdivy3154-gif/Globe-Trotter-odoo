# GlobeTrotter — Personalized Travel Planning Studio 🌍✈️

GlobeTrotter is a modern, responsive, and intelligent desktop application for personal and collaborative multi-city travel planning. Built with **CustomTkinter** and **SQLite / SQLAlchemy 2.0**.

---

## 🌟 Key Features

1. **Authentication & Profile Management**
   - User account registration & login with secure Argon2id password hashing.
   - Quick Demo Login buttons (Alex Traveler & Admin).
   - Profile settings, language preferences, and password change.

2. **Interactive Dashboard**
   - Quick overview metrics: Active Trips, Total Planned Days, Bookmarked Places, Total Allocated Budget.
   - Upcoming itineraries carousel with quick-actions.
   - Trending destination city highlights with 1-click trip addition.

3. **Trip Management (My Trips & Create Trip)**
   - Initiate multi-city trips with date bounds, descriptions, total budgets, and cover photos.
   - Search and filter personal trips with destination counters and live budget trackers.

4. **Interactive Itinerary Builder**
   - Add, remove, and reorder destination stops (drag / up-down controls).
   - Assign activities to each city stop with start/end time slots, category tags, and estimated costs.
   - Real-time expense recalculations.

5. **Day-wise & City-wise Itinerary View**
   - Toggle between chronological Day-by-Day timeline view and structured City-by-City breakdown.

6. **City & Activity Discovery Directory**
   - Global city directory with regional filters, cost indices (1-100), and popularity scores.
   - Bookmark / favorite destination cities.
   - Rich activity catalog (Sightseeing, Food, Adventure, Culture, Nature, Nightlife, Shopping, Relaxation) with cost and duration filters.

7. **Budget & Financial Intelligence**
   - Detailed cost breakdown across:
     - 🏨 Accommodation / Lodging
     - 🍽️ Food & Dining
     - 🎟️ Scheduled Activities
     - 🚗 Transit & Transportation
   - Daily average cost analysis.
   - Intelligent overbudget warnings for high-expense days.

8. **Calendar Timeline**
   - Day-by-day sequence of stops and scheduled activities with start/end timestamps.

9. **Trip Sharing & Cloning**
   - Generate unique 12-character share slugs for public sharing.
   - Clone / copy community-shared itineraries directly into your account with 1 click.

10. **Admin Analytics Dashboard**
    - Platform usage metrics (Total Users, Trips, Cities, Activities).
    - Top destination cities ranked by bookings.
    - Top activity categories and registered user directory.

---

## 🚀 Quickstart Guide

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Desktop Application
```bash
python main.py
```

*Note: On first startup, the database `globetrotter.db` is created and auto-populated with sample global cities, curated activities, and demo accounts.*

### Demo Credentials
- **Traveler User:** `demo@globetrotter.com` / `traveler123`
- **Admin User:** `admin@globetrotter.com` / `admin123`