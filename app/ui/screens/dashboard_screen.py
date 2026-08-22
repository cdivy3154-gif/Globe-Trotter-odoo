import customtkinter as ctk
from app.ui.theme import THEME, FONTS
from app.ui.components.header import Header
from app.ui.components.cards import MetricCard, TripCard, CityCard
from app.services.trip_service import TripService
from app.services.city_service import CityService
from app.schemas.city import CitySearchParams


class DashboardScreen(ctk.CTkScrollableFrame):
    def __init__(self, master, navigate_callback, session_factory, current_user, **kwargs):
        super().__init__(master, fg_color=THEME["bg_dark"], **kwargs)
        self.navigate_callback = navigate_callback
        self.session_factory = session_factory
        self.current_user = current_user
        self.grid_columnconfigure(0, weight=1)
        self.refresh()

    def refresh(self):
        # Clear existing children
        for widget in self.winfo_children():
            widget.destroy()

        user_name = getattr(self.current_user, "full_name", None) or "Traveler"

        # Header with Call to Action
        header = Header(
            self,
            title=f"Welcome back, {user_name}! ✈️",
            subtitle="Plan, dream, and organize your multi-city journeys with ease.",
            action_button=("➕  Plan New Trip", lambda: self.navigate_callback("create_trip"), THEME["primary"]),
        )
        header.pack(fill="x", padx=20, pady=(15, 10))

        # Fetch Data
        trips = []
        saved_dests = []
        popular_cities = []
        total_days = 0

        with self.session_factory() as session:
            trip_service = TripService(session)
            city_service = CityService(session)

            trips = trip_service.list_trips(self.current_user.id, limit=6)
            saved_dests = city_service.get_saved_destinations(self.current_user.id)
            saved_city_ids = {s.city_id for s in saved_dests}

            c_list, _ = city_service.search_cities(CitySearchParams(limit=4))
            popular_cities = c_list

            for t in trips:
                days = (t.end_date.date() - t.start_date.date()).days + 1
                total_days += max(days, 1)

        # Top Metric Cards Grid
        metrics_row = ctk.CTkFrame(self, fg_color="transparent")
        metrics_row.pack(fill="x", padx=20, pady=10)
        metrics_row.grid_columnconfigure((0, 1, 2, 3), weight=1)

        total_budget_sum = sum(float(t.total_budget or 0) for t in trips)

        m1 = MetricCard(metrics_row, title="My Trips", value=str(len(trips)), icon="✈️", subtitle="Active & Planned")
        m1.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        m2 = MetricCard(metrics_row, title="Planned Days", value=str(total_days), icon="🗓️", subtitle="Total Duration")
        m2.grid(row=0, column=1, padx=8, sticky="ew")

        m3 = MetricCard(metrics_row, title="Saved Places", value=str(len(saved_dests)), icon="⭐", subtitle="Bookmarked")
        m3.grid(row=0, column=2, padx=8, sticky="ew")

        m4 = MetricCard(metrics_row, title="Total Budget", value=f"${total_budget_sum:,.0f}", icon="💰", subtitle="Allocated")
        m4.grid(row=0, column=3, padx=(8, 0), sticky="ew")

        # Upcoming Trips Section
        trips_section = ctk.CTkFrame(self, fg_color="transparent")
        trips_section.pack(fill="x", padx=20, pady=(20, 10))

        t_hdr = ctk.CTkFrame(trips_section, fg_color="transparent")
        t_hdr.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(t_hdr, text="Recent & Upcoming Trips", font=FONTS["title_md"], text_color=THEME["text_primary"]).pack(side="left")

        if trips:
            see_all_btn = ctk.CTkButton(
                t_hdr,
                text="View All Trips ➔",
                font=FONTS["body_sm"],
                height=26,
                fg_color="transparent",
                hover_color=THEME["bg_card"],
                text_color=THEME["primary"],
                command=lambda: self.navigate_callback("my_trips"),
            )
            see_all_btn.pack(side="right")

            grid_frame = ctk.CTkFrame(trips_section, fg_color="transparent")
            grid_frame.pack(fill="x")
            grid_frame.grid_columnconfigure((0, 1), weight=1)

            for idx, trip in enumerate(trips[:4]):
                card = TripCard(
                    grid_frame,
                    trip=trip,
                    on_view=lambda t: self.navigate_callback("itinerary_builder", trip_id=t.id),
                    on_share=lambda t: self.navigate_callback("share", trip_id=t.id),
                    height=180,
                )
                r, c = divmod(idx, 2)
                card.grid(row=r, column=c, padx=6, pady=6, sticky="ew")
        else:
            empty_frame = ctk.CTkFrame(trips_section, fg_color=THEME["bg_card"], corner_radius=12, border_width=1, border_color=THEME["border"])
            empty_frame.pack(fill="x", pady=5)
            ctk.CTkLabel(empty_frame, text="🗺️ No trips planned yet!", font=FONTS["body_lg"], text_color=THEME["text_secondary"]).pack(pady=(20, 4))
            ctk.CTkLabel(empty_frame, text="Create your first adventure by clicking 'Plan New Trip'", font=FONTS["body_sm"], text_color=THEME["text_muted"]).pack(pady=(0, 16))
            ctk.CTkButton(empty_frame, text="➕ Start Planning", font=FONTS["body_sm"], height=32, fg_color=THEME["primary"], hover_color=THEME["primary_hover"], command=lambda: self.navigate_callback("create_trip")).pack(pady=(0, 20))

        # Recommended Destinations
        rec_section = ctk.CTkFrame(self, fg_color="transparent")
        rec_section.pack(fill="x", padx=20, pady=(24, 30))

        r_hdr = ctk.CTkFrame(rec_section, fg_color="transparent")
        r_hdr.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(r_hdr, text="Trending Global Destinations", font=FONTS["title_md"], text_color=THEME["text_primary"]).pack(side="left")

        all_cities_btn = ctk.CTkButton(
            r_hdr,
            text="Explore Directory ➔",
            font=FONTS["body_sm"],
            height=26,
            fg_color="transparent",
            hover_color=THEME["bg_card"],
            text_color=THEME["primary"],
            command=lambda: self.navigate_callback("city_search"),
        )
        all_cities_btn.pack(side="right")

        city_grid = ctk.CTkFrame(rec_section, fg_color="transparent")
        city_grid.pack(fill="x")
        city_grid.grid_columnconfigure((0, 1), weight=1)

        for idx, city in enumerate(popular_cities):
            is_saved = city.id in saved_city_ids
            ccard = CityCard(
                city_grid,
                city=city,
                is_saved=is_saved,
                on_add_to_trip=lambda c: self.navigate_callback("create_trip", city_id=c.id),
                on_toggle_save=lambda c: self._handle_toggle_save(c),
            )
            r, c = divmod(idx, 2)
            ccard.grid(row=r, column=c, padx=6, pady=6, sticky="ew")

    def _handle_toggle_save(self, city):
        with self.session_factory() as session:
            city_service = CityService(session)
            city_service.toggle_save_destination(self.current_user.id, city.id)
            session.commit()
        self.refresh()
