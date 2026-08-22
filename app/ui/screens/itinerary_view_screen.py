import customtkinter as ctk
from app.ui.theme import THEME, FONTS, format_money
from app.ui.components.header import Header
from app.services.trip_service import TripService


class ItineraryViewScreen(ctk.CTkScrollableFrame):
    def __init__(self, master, navigate_callback, session_factory, current_user, trip_id=None, **kwargs):
        super().__init__(master, fg_color=THEME["bg_dark"], **kwargs)
        self.navigate_callback = navigate_callback
        self.session_factory = session_factory
        self.current_user = current_user
        self.trip_id = trip_id
        self.view_mode = "day"  # 'day' or 'city'
        self.grid_columnconfigure(0, weight=1)
        self.refresh()

    def refresh(self):
        for widget in self.winfo_children():
            widget.destroy()

        if not self.trip_id:
            ctk.CTkLabel(self, text="⚠️ No trip selected", font=FONTS["title_md"]).pack(pady=30)
            ctk.CTkButton(self, text="Select from My Trips", command=lambda: self.navigate_callback("my_trips")).pack()
            return

        trip = None
        calendar_days = []
        try:
            with self.session_factory() as session:
                trip_service = TripService(session)
                trip = trip_service.get_trip(self.trip_id, self.current_user.id)
                calendar_days = trip_service.get_calendar(self.trip_id, self.current_user.id)
        except Exception as ex:
            ctk.CTkLabel(self, text=f"Error loading trip: {str(ex)}", font=FONTS["body"]).pack(pady=30)
            return

        # Header
        header = Header(
            self,
            title=f"📖 {trip.name} - Itinerary Overview",
            subtitle=f"{trip.start_date.strftime('%B %d')} — {trip.end_date.strftime('%B %d, %Y')} • {len(trip.stops)} Destinations",
            action_button=("✏️ Edit in Builder", lambda: self.navigate_callback("itinerary_builder", trip_id=self.trip_id), THEME["primary"]),
        )
        header.pack(fill="x", padx=20, pady=(15, 10))

        # View Mode Switcher
        toggle_bar = ctk.CTkFrame(self, fg_color="transparent")
        toggle_bar.pack(fill="x", padx=20, pady=(0, 15))

        self.seg_btn = ctk.CTkSegmentedButton(
            toggle_bar,
            values=["Day-by-Day Timeline", "City-by-City Breakdown"],
            selected_color=THEME["primary"],
            selected_hover_color=THEME["primary_hover"],
            unselected_color=THEME["bg_card"],
            command=self._on_mode_change,
        )
        self.seg_btn.set("Day-by-Day Timeline" if self.view_mode == "day" else "City-by-City Breakdown")
        self.seg_btn.pack(side="left")

        # Container for content
        if self.view_mode == "day":
            self._render_day_view(calendar_days)
        else:
            self._render_city_view(trip)

    def _on_mode_change(self, value):
        self.view_mode = "day" if "Day" in value else "city"
        self.refresh()

    def _render_day_view(self, calendar_days):
        if not calendar_days:
            ctk.CTkLabel(self, text="No days scheduled yet. Add destination stops in the Itinerary Builder.", font=FONTS["body_sm"], text_color=THEME["text_muted"]).pack(pady=20)
            return

        for idx, d in enumerate(calendar_days):
            date_obj = d["date"]
            d_str = date_obj.strftime("%A, %B %d, %Y")
            stops = d["stops"]
            activities = d["activities"]

            day_card = ctk.CTkFrame(self, fg_color=THEME["bg_card"], corner_radius=12, border_width=1, border_color=THEME["border"])
            day_card.pack(fill="x", padx=20, pady=6)

            # Day Title Row
            d_hdr = ctk.CTkFrame(day_card, fg_color="transparent")
            d_hdr.pack(fill="x", padx=16, pady=(12, 6))

            ctk.CTkLabel(d_hdr, text=f"Day {idx + 1}: {d_str}", font=FONTS["title_md"], text_color=THEME["primary"]).pack(side="left")

            if stops:
                city_tags = ", ".join(s.city.name for s in stops if s.city)
                ctk.CTkLabel(d_hdr, text=f"📍 {city_tags}", font=FONTS["body_sm"], text_color=THEME["info"]).pack(side="right")

            if not activities:
                ctk.CTkLabel(day_card, text="Free Day / Travel Day (No scheduled activities)", font=FONTS["body_sm"], text_color=THEME["text_muted"]).pack(padx=16, pady=(0, 12), anchor="w")
            else:
                for act in activities:
                    act_frame = ctk.CTkFrame(day_card, fg_color=THEME["bg_input"], corner_radius=6, border_width=1, border_color=THEME["border"])
                    act_frame.pack(fill="x", padx=16, pady=3)

                    a_row = ctk.CTkFrame(act_frame, fg_color="transparent")
                    a_row.pack(fill="x", padx=12, pady=6)

                    t_str = f"⏰ {act.start_time.strftime('%H:%M')} - {act.end_time.strftime('%H:%M')}"
                    ctk.CTkLabel(a_row, text=f"{t_str}  •  {act.name}", font=FONTS["body_lg"], text_color=THEME["text_primary"]).pack(side="left")

                    cost_str = f"💰 {format_money(act.estimated_cost, getattr(act, 'currency', getattr(trip, 'currency', 'USD')), decimals=2)}"
                    ctk.CTkLabel(a_row, text=cost_str, font=FONTS["body_sm"], text_color=THEME["success"]).pack(side="right")

                ctk.CTkFrame(day_card, height=6, fg_color="transparent").pack()

    def _render_city_view(self, trip):
        if not trip.stops:
            ctk.CTkLabel(self, text="No destination stops added yet.", font=FONTS["body_sm"], text_color=THEME["text_muted"]).pack(pady=20)
            return

        for idx, stop in enumerate(trip.stops):
            c_card = ctk.CTkFrame(self, fg_color=THEME["bg_card"], corner_radius=12, border_width=1, border_color=THEME["border"])
            c_card.pack(fill="x", padx=20, pady=8)

            c_hdr = ctk.CTkFrame(c_card, fg_color="transparent")
            c_hdr.pack(fill="x", padx=16, pady=(14, 6))

            city_name = f"{stop.city.name}, {stop.city.country}" if stop.city else "Unknown City"
            ctk.CTkLabel(c_hdr, text=f"Stop {idx + 1}: 🏙️ {city_name}", font=FONTS["title_md"], text_color=THEME["text_primary"]).pack(side="left")

            s_date = stop.arrival_date.strftime("%b %d")
            e_date = stop.departure_date.strftime("%b %d, %Y")
            ctk.CTkLabel(c_hdr, text=f"🗓️ {s_date} - {e_date}", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(side="right")

            if stop.notes:
                ctk.CTkLabel(c_card, text=f"Notes: {stop.notes}", font=FONTS["body_sm"], text_color=THEME["text_muted"], anchor="w").pack(fill="x", padx=16, pady=(0, 6))

            # Stop activities
            if stop.activities:
                act_container = ctk.CTkFrame(c_card, fg_color=THEME["bg_input"], corner_radius=8)
                act_container.pack(fill="x", padx=16, pady=(4, 12))
                for a in stop.activities:
                    r = ctk.CTkFrame(act_container, fg_color="transparent")
                    r.pack(fill="x", padx=10, pady=4)
                    act_type_str = str(getattr(a, "activity_type", "OTHER") or "OTHER")
                    if hasattr(a.activity_type, "value"):
                        act_type_str = a.activity_type.value
                    ctk.CTkLabel(r, text=f"🎟️ {a.name} ({act_type_str.upper()})", font=FONTS["body"], text_color=THEME["text_primary"]).pack(side="left")
                    a_cost_str = format_money(a.estimated_cost, getattr(a, 'currency', getattr(trip, 'currency', 'USD')), decimals=2)
                    ctk.CTkLabel(r, text=a_cost_str, font=FONTS["body_sm"], text_color=THEME["success"]).pack(side="right")
            else:
                ctk.CTkLabel(c_card, text="No activities planned in this city yet.", font=FONTS["body_sm"], text_color=THEME["text_muted"]).pack(padx=16, pady=(0, 12), anchor="w")
