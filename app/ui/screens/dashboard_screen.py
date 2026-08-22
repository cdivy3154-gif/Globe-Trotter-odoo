"""
Phase 3 — Dashboard Screen
Rich landing hub:
  - Hero gradient banner (greeting + quick-action CTA)
  - 4 MetricCards with accent stripe colors
  - Recent & Upcoming Trips grid (TripCard with status chips)
  - Trending Destinations row (CityCard with save star)
  - Empty states with clear CTAs
"""
import customtkinter as ctk
from datetime import datetime, timezone
from app.ui.theme import THEME, FONTS, SHAPE, LAYOUT
from app.ui.components.header import Header
from app.ui.components.cards import MetricCard, TripCard, CityCard, EmptyState
from app.services.trip_service import TripService
from app.services.city_service import CityService
from app.schemas.city import CitySearchParams


class DashboardScreen(ctk.CTkScrollableFrame):
    def __init__(self, master, navigate_callback, session_factory, current_user, **kwargs):
        super().__init__(
            master,
            fg_color=THEME["bg_dark"],
            scrollbar_button_color=THEME["border"],
            scrollbar_button_hover_color=THEME["border_light"],
            **kwargs,
        )
        self.navigate_callback = navigate_callback
        self.session_factory   = session_factory
        self.current_user      = current_user
        self.grid_columnconfigure(0, weight=1)
        self.refresh()

    # ─────────────────────────────────────────────────────────────
    def refresh(self):
        for w in self.winfo_children():
            w.destroy()

        # ── Fetch data ────────────────────────────────────────────
        trips          = []
        popular_cities = []
        saved_city_ids = set()
        total_days     = 0

        with self.session_factory() as session:
            ts = TripService(session)
            cs = CityService(session)

            trips = ts.list_trips(self.current_user.id, limit=50)
            saved = cs.get_saved_destinations(self.current_user.id)
            saved_city_ids = {s.city_id for s in saved}
            pop, _ = cs.search_cities(CitySearchParams(limit=6))
            popular_cities = pop

            for t in trips:
                d = (t.end_date.date() - t.start_date.date()).days + 1
                total_days += max(d, 1)

        user_name      = getattr(self.current_user, "full_name", None) or "Traveler"
        total_budget   = sum(float(t.total_budget or 0) for t in trips)
        now            = datetime.now(timezone.utc)

        # ── Hero Banner ───────────────────────────────────────────
        self._hero(user_name)

        # ── Metrics Row ───────────────────────────────────────────
        self._metrics(len(trips), total_days, len(saved_city_ids), total_budget)

        # ── Trips Section ─────────────────────────────────────────
        self._trips_section(trips)

        # ── Cities Section ────────────────────────────────────────
        self._cities_section(popular_cities, saved_city_ids)

    # ─────────────────────────────────────────────────────────────
    # HERO BANNER
    # ─────────────────────────────────────────────────────────────
    def _hero(self, user_name: str):
        hero = ctk.CTkFrame(
            self,
            fg_color=THEME["primary_container"],
            corner_radius=SHAPE["large"],
            border_width=1,
            border_color=THEME["primary_dim"],
        )
        hero.pack(fill="x", padx=20, pady=(18, 12))

        # Accent left stripe
        ctk.CTkFrame(hero, width=5, fg_color=THEME["primary"], corner_radius=0).pack(side="left", fill="y")

        inner = ctk.CTkFrame(hero, fg_color="transparent")
        inner.pack(side="left", fill="both", expand=True, padx=24, pady=20)
        inner.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            inner,
            text=f"Welcome back, {user_name}! ✈️",
            font=FONTS["title_xl"],
            text_color=THEME["text_primary"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            inner,
            text="Where will your next adventure take you? Plan, budget, and explore — all in one place.",
            font=FONTS["body"],
            text_color=THEME["on_primary_container"],
            anchor="w",
            wraplength=600,
        ).grid(row=1, column=0, sticky="w", pady=(4, 16))

        actions = ctk.CTkFrame(inner, fg_color="transparent")
        actions.grid(row=2, column=0, sticky="w")

        ctk.CTkButton(
            actions,
            text="➕  Plan New Trip",
            font=FONTS["body_lg"],
            height=LAYOUT["btn_height"],
            corner_radius=SHAPE["small"],
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            command=lambda: self.navigate_callback("create_trip"),
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            actions,
            text="🏙️  City Directory",
            font=FONTS["body_lg"],
            height=LAYOUT["btn_height"],
            corner_radius=SHAPE["small"],
            fg_color=THEME["bg_card"],
            hover_color=THEME["bg_card_hover"],
            border_width=1,
            border_color=THEME["border"],
            text_color=THEME["text_secondary"],
            command=lambda: self.navigate_callback("city_search"),
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            actions,
            text="🔗  Community",
            font=FONTS["body_lg"],
            height=LAYOUT["btn_height"],
            corner_radius=SHAPE["small"],
            fg_color=THEME["bg_card"],
            hover_color=THEME["bg_card_hover"],
            border_width=1,
            border_color=THEME["border"],
            text_color=THEME["text_secondary"],
            command=lambda: self.navigate_callback("share"),
        ).pack(side="left")

        # Globe decoration on right
        ctk.CTkLabel(hero, text="🌍", font=(FONTS["display"][0], 80)).pack(side="right", padx=32)

    # ─────────────────────────────────────────────────────────────
    # METRICS ROW
    # ─────────────────────────────────────────────────────────────
    def _metrics(self, trips: int, days: int, saved: int, budget: float):
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(0, 8))
        row.grid_columnconfigure((0, 1, 2, 3), weight=1)

        cards_data = [
            ("My Trips",      str(trips),             "✈️",  "Active & Planned",    THEME["primary"]),
            ("Planned Days",  str(days),               "🗓️", "Total Duration",       THEME["accent"]),
            ("Saved Places",  str(saved),              "⭐",  "Bookmarked Cities",   THEME["success"]),
            ("Total Budget",  f"${budget:,.0f}",       "💰",  "Allocated",           THEME["info"]),
        ]

        for i, (title, value, icon, subtitle, color) in enumerate(cards_data):
            MetricCard(
                row,
                title=title,
                value=value,
                icon=icon,
                subtitle=subtitle,
                accent_color=color,
            ).grid(row=0, column=i, padx=(0 if i == 0 else 6, 6 if i < 3 else 0), sticky="ew")

    # ─────────────────────────────────────────────────────────────
    # TRIPS SECTION
    # ─────────────────────────────────────────────────────────────
    def _trips_section(self, trips: list):
        section = ctk.CTkFrame(self, fg_color="transparent")
        section.pack(fill="x", padx=20, pady=(12, 8))

        # Section header
        hdr = ctk.CTkFrame(section, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            hdr,
            text="Recent & Upcoming Trips",
            font=FONTS["title_md"],
            text_color=THEME["text_primary"],
        ).pack(side="left")

        if trips:
            ctk.CTkButton(
                hdr,
                text="View All  →",
                font=FONTS["body_sm"],
                height=28,
                fg_color="transparent",
                hover_color=THEME["bg_card"],
                text_color=THEME["primary"],
                border_width=1,
                border_color=THEME["border"],
                corner_radius=SHAPE["full"],
                command=lambda: self.navigate_callback("my_trips"),
            ).pack(side="right")

        if not trips:
            EmptyState(
                section,
                icon="✈️",
                title="No trips planned yet!",
                message="Start by creating your first multi-city adventure.",
                action_label="➕  Create First Trip",
                action_cmd=lambda: self.navigate_callback("create_trip"),
            ).pack(fill="x")
            return

        # 2-column grid
        grid = ctk.CTkFrame(section, fg_color="transparent")
        grid.pack(fill="x")
        grid.grid_columnconfigure((0, 1), weight=1)

        for i, trip in enumerate(trips[:6]):
            r, c = divmod(i, 2)
            TripCard(
                grid,
                trip=trip,
                on_view=lambda t: self.navigate_callback("itinerary_builder", trip_id=t.id),
                on_share=lambda t: self.navigate_callback("share", trip_id=t.id),
            ).grid(row=r, column=c, padx=(0 if c == 0 else 6, 6 if c == 0 else 0), pady=5, sticky="ew")

    # ─────────────────────────────────────────────────────────────
    # CITIES SECTION
    # ─────────────────────────────────────────────────────────────
    def _cities_section(self, cities: list, saved_ids: set):
        section = ctk.CTkFrame(self, fg_color="transparent")
        section.pack(fill="x", padx=20, pady=(12, 24))

        hdr = ctk.CTkFrame(section, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(hdr, text="Trending Destinations", font=FONTS["title_md"], text_color=THEME["text_primary"]).pack(side="left")
        ctk.CTkButton(
            hdr,
            text="Explore Directory  →",
            font=FONTS["body_sm"],
            height=28,
            fg_color="transparent",
            hover_color=THEME["bg_card"],
            text_color=THEME["primary"],
            border_width=1,
            border_color=THEME["border"],
            corner_radius=SHAPE["full"],
            command=lambda: self.navigate_callback("city_search"),
        ).pack(side="right")

        if not cities:
            ctk.CTkLabel(section, text="No cities in directory yet.", font=FONTS["body_sm"], text_color=THEME["text_muted"]).pack(pady=20)
            return

        grid = ctk.CTkFrame(section, fg_color="transparent")
        grid.pack(fill="x")
        grid.grid_columnconfigure((0, 1, 2), weight=1)

        for i, city in enumerate(cities[:6]):
            r, c = divmod(i, 3)
            CityCard(
                grid,
                city=city,
                is_saved=city.id in saved_ids,
                on_plan=lambda ct: self.navigate_callback("create_trip", city_id=ct.id),
                on_save=lambda ct: self._toggle_save(ct),
            ).grid(row=r, column=c, padx=4, pady=5, sticky="ew")

    # ─────────────────────────────────────────────────────────────
    def _toggle_save(self, city):
        with self.session_factory() as session:
            CityService(session).toggle_save_destination(self.current_user.id, city.id)
            session.commit()
        self.refresh()
