import customtkinter as ctk
from app.ui.theme import THEME, FONTS
from app.ui.components.header import Header
from app.services.trip_service import TripService


class CalendarScreen(ctk.CTkScrollableFrame):
    def __init__(self, master, navigate_callback, session_factory, current_user, trip_id=None, **kwargs):
        super().__init__(master, fg_color=THEME["bg_dark"], **kwargs)
        self.navigate_callback = navigate_callback
        self.session_factory = session_factory
        self.current_user = current_user
        self.trip_id = trip_id
        self.grid_columnconfigure(0, weight=1)
        self.refresh()

    def refresh(self):
        for widget in self.winfo_children():
            widget.destroy()

        user_trips = []
        with self.session_factory() as session:
            trip_service = TripService(session)
            user_trips = trip_service.list_trips(self.current_user.id, limit=50)

        if not user_trips:
            ctk.CTkLabel(self, text="📅 No trips found for calendar timeline.", font=FONTS["title_md"]).pack(pady=40)
            ctk.CTkButton(self, text="➕ Create a Trip", command=lambda: self.navigate_callback("create_trip")).pack()
            return

        selected_trip = None
        if self.trip_id:
            selected_trip = next((t for t in user_trips if t.id == self.trip_id), None)
        if not selected_trip:
            selected_trip = user_trips[0]
            self.trip_id = selected_trip.id

        header = Header(
            self,
            title="Trip Calendar & Flow Timeline 📅",
            subtitle="Day-by-day sequence of destinations, schedules, and booked experiences.",
            action_button=("✏️ Open Builder", lambda: self.navigate_callback("itinerary_builder", trip_id=self.trip_id), THEME["primary"]),
        )
        header.pack(fill="x", padx=20, pady=(15, 10))

        # Selector Row
        sel_card = ctk.CTkFrame(self, fg_color=THEME["bg_card"], corner_radius=12, border_width=1, border_color=THEME["border"])
        sel_card.pack(fill="x", padx=20, pady=(0, 15))

        s_in = ctk.CTkFrame(sel_card, fg_color="transparent")
        s_in.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(s_in, text="Active Trip Calendar:", font=FONTS["body_lg"], text_color=THEME["text_primary"]).pack(side="left", padx=(0, 12))
        trip_names = [t.name for t in user_trips]
        cb = ctk.CTkComboBox(s_in, values=trip_names, height=36, width=280, font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"], command=self._on_trip_change)
        cb.set(selected_trip.name)
        cb.pack(side="left")

        # Fetch Calendar Days
        calendar_days = []
        with self.session_factory() as session:
            trip_service = TripService(session)
            calendar_days = trip_service.get_calendar(selected_trip.id, self.current_user.id)

        if not calendar_days:
            ctk.CTkLabel(self, text="No days generated yet. Check trip dates in builder.", font=FONTS["body_lg"], text_color=THEME["text_secondary"]).pack(pady=30)
            return

        # Render Timeline list
        for idx, day_info in enumerate(calendar_days):
            d_obj = day_info["date"]
            stops = day_info["stops"]
            acts = day_info["activities"]

            d_card = ctk.CTkFrame(self, fg_color=THEME["bg_card"], corner_radius=12, border_width=1, border_color=THEME["border"])
            d_card.pack(fill="x", padx=20, pady=6)

            hdr = ctk.CTkFrame(d_card, fg_color="transparent")
            hdr.pack(fill="x", padx=16, pady=(12, 6))

            d_title = f"Day {idx + 1}:  {d_obj.strftime('%A, %b %d')}"
            ctk.CTkLabel(hdr, text=d_title, font=FONTS["title_md"], text_color=THEME["primary"]).pack(side="left")

            if stops:
                c_names = " ➔ ".join(s.city.name for s in stops if s.city)
                ctk.CTkLabel(hdr, text=f"📍 {c_names}", font=FONTS["body_sm"], text_color=THEME["info"]).pack(side="right")

            if acts:
                for act in sorted(acts, key=lambda a: a.start_time):
                    a_frame = ctk.CTkFrame(d_card, fg_color=THEME["bg_input"], corner_radius=6, border_width=1, border_color=THEME["border"])
                    a_frame.pack(fill="x", padx=16, pady=3)

                    r = ctk.CTkFrame(a_frame, fg_color="transparent")
                    r.pack(fill="x", padx=12, pady=6)

                    t_str = f"⏰ {act.start_time.strftime('%H:%M')} - {act.end_time.strftime('%H:%M')}"
                    ctk.CTkLabel(r, text=f"{t_str}  •  {act.name}", font=FONTS["body_lg"], text_color=THEME["text_primary"]).pack(side="left")

                    cost_str = f"💰 ${float(act.estimated_cost or 0):,.2f}"
                    ctk.CTkLabel(r, text=cost_str, font=FONTS["body_sm"], text_color=THEME["success"]).pack(side="right")
                ctk.CTkFrame(d_card, height=6, fg_color="transparent").pack()
            else:
                ctk.CTkLabel(d_card, text="🏖️ Free Day / Leisure Exploration", font=FONTS["body_sm"], text_color=THEME["text_muted"]).pack(padx=16, pady=(0, 12), anchor="w")

    def _on_trip_change(self, choice):
        with self.session_factory() as session:
            trip_service = TripService(session)
            trips = trip_service.list_trips(self.current_user.id, limit=50)
            chosen = next((t for t in trips if t.name == choice), None)
            if chosen:
                self.trip_id = chosen.id
        self.refresh()
