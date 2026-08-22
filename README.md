# 🌍 GlobeTrotter

> **Empowering Personalized Travel Planning**

GlobeTrotter is a personalized, intelligent, and collaborative platform that transforms the way individuals plan and experience travel. It empowers users to dream, design, and organize trips with ease by offering an end-to-end travel planning tool combining flexibility, interactivity, and Material 3 Expressive aesthetics.

---

## 🚀 The Vision

Our goal is to simplify the complexity of planning multi-city travel. We want to enable travelers to:
- **Design:** Create customized multi-city itineraries effortlessly.
- **Budget:** Automatically calculate expenses, receive cost breakdowns, and get over-budget alerts.
- **Visualize:** View full trip timelines and day-by-day plans in clean calendar formats.
- **Collaborate:** Share travel plans publicly or draw inspiration from a community of travelers.

## 🎨 Design System

GlobeTrotter is built with a **Material 3 (M3) Expressive** design system.
- **Theme:** Dynamic Light & Dark Modes
- **Primary Color:** Warm Orange (`#8C4A01`)
- **Typography:** `Inter` (An open-source Helvetica equivalent) for clean, readable interfaces.
- **Icons:** Material Symbols Rounded

## 🗺️ Key Features & Screens

We've implemented a Single Page Application (SPA) with 12 core screens to handle the full travel lifecycle:

1. **Login & Registration:** Secure authentication flows with M3 cards.
2. **Dashboard:** A central hub showing upcoming trips, recommended cities, and budget highlights.
3. **Create Trip:** Intuitive forms to set up trip names, dates, and descriptions.
4. **Itinerary Builder:** Interactive timeline to add cities, dates, and activities.
5. **My Trips:** A management view for all past and upcoming adventures.
6. **Profile & Settings:** User preferences, including currency and language selection.
7. **Discover (Search):** Search functionality for cities, activities, and destinations with cost/popularity indices.
8. **Itinerary View (Budget):** Financial breakdown of the trip (transport, accommodation, activities) with progress bars.
9. **Community Hub:** A feed to explore trending trips shared by other users and copy itineraries.
10. **Calendar View:** A visual monthly calendar grid showing the travel timeline across different cities.
11. **Admin Panel:** Analytics dashboard tracking users, active trips, and platform revenue.

## 🛠️ Tech Stack

- **Frontend:** Vanilla HTML5, CSS3, JavaScript (ES6+)
- **Architecture:** Client-side SPA routing via `<template>` injection and Event Delegation.
- **Styling:** CSS Variables (Tokens) for M3 dynamic theming, CSS Grid & Flexbox.
- **Icons/Fonts:** Google Fonts (Inter) & Material Symbols.

## 🏃‍♂️ How to Run Locally

Since this project uses modern ES6 modules and SPA routing, it needs to be served via a local web server (to avoid CORS issues with templates/modules).

1. Clone the repository.
2. Navigate to the project folder:
   ```bash
   cd Globe-Trotter-odoo
   ```
3. Start a local server. For example, using Python:
   ```bash
   python -m http.server 8080
   ```
4. Open your browser and navigate to: `http://localhost:8080`

## 📐 Architecture & Mockups

The initial wireframes and UX flows were designed using Excalidraw. 
You can view the raw conceptual mockups in the repository: `GlobeTrotter - 8 hours.excalidraw.svg`

---
*Built for the Odoo Hackathon — Frontend Branch*