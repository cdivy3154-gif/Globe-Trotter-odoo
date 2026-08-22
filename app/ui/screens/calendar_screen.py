"""
Phase 8 — Calendar / Trip Timeline Screen
Features:
  - Trip selector dropdown
  - Month-grid calendar renderer (7-col grid, day cells)
    - Today highlighted with primary ring
    - Trip days tinted with primary_container
    - Days with activities show orange dot + count badge
  - Day click → popover panel showing stops + activities for that day
  - "Jump to Trip Start" button
  - Horizontal timeline strip (day cards scrollable)
  - Navigate → Itinerary Builder CTA per day
"""
import calendar as _cal
import customtkinter as ctk
from datetime import datetime, date, timezone

from app.ui.theme import THEME, FONTS, SHAPE, LAYOUT
from app.ui.components.header import Header
from app.ui.components.cards import EmptyState
from app.services.trip_service import TripService

_WEEKDAYS  = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
_MONTHS    = ["January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]

_ACT_ICONS = {
    "sightseeing": "🏛️", "food": "🍽️", "adventure": "🧗", "cultural": "🎭",
    "nature": "🌿", "nightlife": "🌙", "shopping": "🛍️", "wellness": "🧘",
    "transport": "🚌", "other": "📍",
}


def _norm_date(dt) -> date:
    if isinstance(dt, date) and not isinstance(dt, datetime):
        return dt
    if isinstance(dt, datetime):
        if dt.tzinfo:
            return dt.astimezone(timezone.utc).date()
        return dt.date()
    return dt


# ══════════════════════════════════════════════════════════════════
class CalendarScreen(ctk.CTkScrollableFrame):
    def __init__(self, master, navigate_callback, session_factory, current_user, trip_id=None, **kwargs):
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
        self.trip_id           = trip_id
        self._view_year        = datetime.now().year
        self._view_month       = datetime.now().month
        self._selected_date    = None
        self.grid_columnconfigure(0, weight=1)
        self.refresh()

    # ─────────────────────────────────────────────────────────────
    def refresh(self):
        for w in self.winfo_children():
            w.destroy()
        self._day_panel = None

        with self.session_factory() as session:
            user_trips = TripService(session).list_trips(self.current_user.id, limit=50)

        if not user_trips:
            Header(self, title="Trip Calendar 📅", breadcrumb=["Dashboard", "Calendar"]).pack(fill="x", padx=20, pady=(18, 10))
            EmptyState(self, icon="📅", title="No trips planned", message="Create a trip to see it on the calendar.", action_label="➕  Create Trip", action_cmd=lambda: self.navigate_callback("create_trip")).pack(fill="x", padx=20, pady=40)
            return

        if self.trip_id:
            self._trip = next((t for t in user_trips if t.id == self.trip_id), user_trips[0])
        else:
            self._trip = user_trips[0]
        self.trip_id = self._trip.id

        # Load calendar data
        with self.session_factory() as session:
            self._cal_days = TripService(session).get_calendar(self.trip_id, self.current_user.id)
            self._full_trip = TripService(session).get_trip(self.trip_id, self.current_user.id)

        # Build lookup: date → day dict
        self._day_map: dict[date, dict] = {}
        for day in self._cal_days:
            d = _norm_date(day["date"])
            self._day_map[d] = day

        # Jump view to trip start month
        s = _norm_date(self._trip.start_date)
        self._view_year  = s.year
        self._view_month = s.month

        Header(
            self,
            title="Trip Calendar & Flow Timeline 📅",
            subtitle="Day-by-day destinations, schedule, and booked experiences.",
            action_button=("✏️  Open Builder", lambda: self.navigate_callback("itinerary_builder", trip_id=self.trip_id), THEME["primary"]),
            breadcrumb=["Dashboard", "Calendar"],
        ).pack(fill="x", padx=20, pady=(18, 10))

        # ── Trip selector + nav ───────────────────────────────────
        self._build_controls(user_trips)

        # ── Month grid ────────────────────────────────────────────
        self._grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._grid_frame.pack(fill="x", padx=20, pady=(0, 10))
        self._render_month_grid()

        # ── Day detail panel (populated on click) ─────────────────
        self._day_detail_area = ctk.CTkFrame(self, fg_color="transparent")
        self._day_detail_area.pack(fill="x", padx=20, pady=(0, 10))

        # ── Horizontal timeline strip ─────────────────────────────
        self._build_timeline()

    # ─────────────────────────────────────────────────────────────
    def _build_controls(self, user_trips):
        ctrl = ctk.CTkFrame(self, fg_color=THEME["bg_card"], corner_radius=SHAPE["medium"], border_width=1, border_color=THEME["border"])
        ctrl.pack(fill="x", padx=20, pady=(0, 10))
        inner = ctk.CTkFrame(ctrl, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)
        inner.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(inner, text="Viewing:", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).grid(row=0, column=0, padx=(0, 10))
        trip_names = [t.name for t in user_trips]
        trip_cb = ctk.CTkComboBox(inner, values=trip_names, height=LAYOUT["input_height"], font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"], text_color=THEME["text_primary"], command=self._on_trip_change)
        trip_cb.set(self._trip.name)
        trip_cb.grid(row=0, column=1, sticky="ew")
        self._user_trips = user_trips

        # Month nav buttons
        nav = ctk.CTkFrame(inner, fg_color="transparent")
        nav.grid(row=0, column=2, padx=(12, 0))
        ctk.CTkButton(nav, text="◀", width=32, height=LAYOUT["input_height"], font=FONTS["body_sm"], fg_color=THEME["bg_input"], hover_color=THEME["bg_card_hover"], border_width=1, border_color=THEME["border"], command=self._prev_month).pack(side="left", padx=2)
        self._month_lbl = ctk.CTkLabel(nav, text=self._month_text(), font=FONTS["body_lg"], text_color=THEME["text_primary"], width=160)
        self._month_lbl.pack(side="left", padx=4)
        ctk.CTkButton(nav, text="▶", width=32, height=LAYOUT["input_height"], font=FONTS["body_sm"], fg_color=THEME["bg_input"], hover_color=THEME["bg_card_hover"], border_width=1, border_color=THEME["border"], command=self._next_month).pack(side="left", padx=2)

    # ─────────────────────────────────────────────────────────────
    def _month_text(self) -> str:
        return f"{_MONTHS[self._view_month - 1]}  {self._view_year}"

    def _prev_month(self):
        self._view_month -= 1
        if self._view_month < 1:
            self._view_month = 12
            self._view_year -= 1
        self._month_lbl.configure(text=self._month_text())
        self._render_month_grid()

    def _next_month(self):
        self._view_month += 1
        if self._view_month > 12:
            self._view_month = 1
            self._view_year += 1
        self._month_lbl.configure(text=self._month_text())
        self._render_month_grid()

    # ─────────────────────────────────────────────────────────────
    # MONTH GRID
    # ─────────────────────────────────────────────────────────────
    def _render_month_grid(self):
        for w in self._grid_frame.winfo_children():
            w.destroy()

        trip_start = _norm_date(self._trip.start_date)
        trip_end   = _norm_date(self._trip.end_date)
        today      = date.today()

        grid_card = ctk.CTkFrame(self._grid_frame, fg_color=THEME["bg_card"], corner_radius=SHAPE["medium"], border_width=1, border_color=THEME["border"])
        grid_card.pack(fill="x")
        ctk.CTkFrame(grid_card, height=3, fg_color=THEME["primary"], corner_radius=0).pack(fill="x")

        # Weekday header
        hdr = ctk.CTkFrame(grid_card, fg_color=THEME["bg_input"])
        hdr.pack(fill="x", padx=12, pady=(12, 4))
        for col, day_name in enumerate(_WEEKDAYS):
            hdr.grid_columnconfigure(col, weight=1)
            ctk.CTkLabel(hdr, text=day_name, font=FONTS["badge"], text_color=THEME["text_muted"]).grid(row=0, column=col, padx=4, pady=6, sticky="ew")

        # Calendar matrix
        cal = _cal.monthcalendar(self._view_year, self._view_month)
        grid = ctk.CTkFrame(grid_card, fg_color="transparent")
        grid.pack(fill="x", padx=12, pady=(0, 12))

        for row_idx, week in enumerate(cal):
            for col_idx, day_num in enumerate(week):
                grid.grid_columnconfigure(col_idx, weight=1)
                if day_num == 0:
                    ctk.CTkFrame(grid, height=64, fg_color="transparent").grid(row=row_idx, column=col_idx, padx=3, pady=3, sticky="ew")
                    continue

                d = date(self._view_year, self._view_month, day_num)
                in_trip  = trip_start <= d <= trip_end
                is_today = d == today
                day_data = self._day_map.get(d)
                act_count = len(day_data.get("activities", [])) if day_data else 0

                # Cell color
                if is_today:
                    cell_bg = THEME["primary"]
                    tc      = THEME["on_primary"]
                elif in_trip:
                    cell_bg = THEME["primary_container"]
                    tc      = THEME["on_primary_container"]
                else:
                    cell_bg = THEME["bg_input"]
                    tc      = THEME["text_muted"]

                cell = ctk.CTkFrame(
                    grid,
                    fg_color=cell_bg,
                    corner_radius=SHAPE["small"],
                    border_width=2 if is_today else (1 if in_trip else 0),
                    border_color=THEME["primary"] if is_today else THEME["border"],
                    cursor="hand2" if in_trip else "",
                )
                cell.grid(row=row_idx, column=col_idx, padx=3, pady=3, sticky="ew")

                ctk.CTkLabel(cell, text=str(day_num), font=FONTS["body_sm"], text_color=tc).pack(pady=(8, 2))

                if act_count > 0:
                    ctk.CTkLabel(
                        cell,
                        text=f"🎟 {act_count}",
                        font=FONTS["badge"],
                        fg_color=THEME["primary"],
                        text_color=THEME["on_primary"],
                        corner_radius=SHAPE["full"],
                    ).pack(pady=(0, 6))
                elif in_trip:
                    stops = day_data.get("stops", []) if day_data else []
                    if stops:
                        city = stops[0].city.name[:8] if (stops[0].city and stops[0].city.name) else ""
                        ctk.CTkLabel(cell, text=f"📍 {city}", font=FONTS["badge"], text_color=THEME["text_muted"]).pack(pady=(0, 6))
                    else:
                        ctk.CTkFrame(cell, height=20, fg_color="transparent").pack()

                if in_trip:
                    cell.bind("<Button-1>", lambda _, dd=d: self._on_day_click(dd))
                    for ch in cell.winfo_children():
                        ch.bind("<Button-1>", lambda _, dd=d: self._on_day_click(dd))

    # ─────────────────────────────────────────────────────────────
    # DAY DETAIL PANEL
    # ─────────────────────────────────────────────────────────────
    def _on_day_click(self, d: date):
        for w in self._day_detail_area.winfo_children():
            w.destroy()

        day_data = self._day_map.get(d)
        if not day_data:
            return

        self._selected_date = d
        panel = ctk.CTkFrame(
            self._day_detail_area,
            fg_color=THEME["bg_card"],
            corner_radius=SHAPE["medium"],
            border_width=1,
            border_color=THEME["primary"],
        )
        panel.pack(fill="x")
        ctk.CTkFrame(panel, height=3, fg_color=THEME["primary"], corner_radius=0).pack(fill="x")

        # Header
        ph = ctk.CTkFrame(panel, fg_color="transparent")
        ph.pack(fill="x", padx=20, pady=(14, 6))
        ctk.CTkLabel(ph, text=f"📅  {d.strftime('%A, %B %d, %Y')}", font=FONTS["title_sm"], text_color=THEME["primary"]).pack(side="left")
        ctk.CTkButton(ph, text="✏️  Edit in Builder", font=FONTS["body_sm"], height=28, corner_radius=SHAPE["small"], fg_color=THEME["primary"], hover_color=THEME["primary_hover"], command=lambda: self.navigate_callback("itinerary_builder", trip_id=self.trip_id)).pack(side="right")

        stops     = day_data.get("stops", [])
        activities = day_data.get("activities", [])

        if stops:
            city_names = ", ".join(s.city.name for s in stops if s.city)
            ctk.CTkLabel(panel, text=f"📍  Destinations today: {city_names}", font=FONTS["body"], text_color=THEME["text_secondary"], anchor="w").pack(fill="x", padx=20, pady=(0, 8))

        if not activities:
            ctk.CTkLabel(panel, text="No activities scheduled for this day.", font=FONTS["body_sm"], text_color=THEME["text_muted"], anchor="w").pack(fill="x", padx=20, pady=(4, 16))
        else:
            for act in activities:
                act_type = str(getattr(act, "activity_type", "other") or "other").lower()
                if hasattr(getattr(act, "activity_type", None), "value"):
                    act_type = act.activity_type.value
                icon = _ACT_ICONS.get(act_type, "📍")
                cost = float(act.estimated_cost or 0)

                row = ctk.CTkFrame(panel, fg_color=THEME["bg_input"], corner_radius=SHAPE["extra_small"], border_width=1, border_color=THEME["border"])
                row.pack(fill="x", padx=20, pady=3)

                ctk.CTkLabel(row, text=icon, font=FONTS["body_lg"]).pack(side="left", padx=(12, 8), pady=8)
                info = ctk.CTkFrame(row, fg_color="transparent")
                info.pack(side="left", fill="x", expand=True, pady=8)
                ctk.CTkLabel(info, text=act.name, font=FONTS["body_lg"], text_color=THEME["text_primary"], anchor="w").pack(anchor="w")
                try:
                    sub = f"⏰ {act.start_time.strftime('%H:%M')} - {act.end_time.strftime('%H:%M')}   •   {act_type.title()}"
                except Exception:
                    sub = act_type.title()
                ctk.CTkLabel(info, text=sub, font=FONTS["body_sm"], text_color=THEME["text_secondary"], anchor="w").pack(anchor="w")
                ctk.CTkLabel(row, text=f"${cost:,.0f}", font=FONTS["badge"], fg_color=THEME["success_bg"], text_color=THEME["success"], corner_radius=SHAPE["extra_small"]).pack(side="right", padx=(0, 12))

            ctk.CTkFrame(panel, height=12, fg_color="transparent").pack()

    # ─────────────────────────────────────────────────────────────
    # HORIZONTAL TIMELINE
    # ─────────────────────────────────────────────────────────────
    def _build_timeline(self):
        if not self._cal_days:
            return

        section = ctk.CTkFrame(self, fg_color=THEME["bg_card"], corner_radius=SHAPE["medium"], border_width=1, border_color=THEME["border"])
        section.pack(fill="x", padx=20, pady=(0, 24))
        ctk.CTkFrame(section, height=3, fg_color=THEME["accent"], corner_radius=0).pack(fill="x")

        ctk.CTkLabel(section, text="Trip Timeline — Day by Day", font=FONTS["title_sm"], text_color=THEME["text_primary"]).pack(anchor="w", padx=20, pady=(14, 8))

        scroll = ctk.CTkScrollableFrame(
            section,
            orientation="horizontal",
            fg_color="transparent",
            height=140,
            scrollbar_button_color=THEME["border"],
            scrollbar_button_hover_color=THEME["primary"],
        )
        scroll.pack(fill="x", padx=12, pady=(0, 12))

        for day in self._cal_days:
            d          = _norm_date(day["date"])
            acts       = day.get("activities", [])
            stops      = day.get("stops", [])
            act_count  = len(acts)
            is_today   = d == date.today()
            city       = stops[0].city.name[:10] if (stops and stops[0].city) else "Transit"

            card = ctk.CTkFrame(
                scroll,
                fg_color=THEME["primary"] if is_today else THEME["bg_input"],
                corner_radius=SHAPE["small"],
                border_width=1,
                border_color=THEME["primary"] if (act_count > 0 or is_today) else THEME["border"],
                width=100,
                cursor="hand2",
            )
            card.pack(side="left", padx=4, fill="y")
            card.pack_propagate(False)

            tc = THEME["on_primary"] if is_today else THEME["text_secondary"]
            ctk.CTkLabel(card, text=d.strftime("%a"), font=FONTS["badge"], text_color=tc).pack(pady=(10, 0))
            ctk.CTkLabel(card, text=d.strftime("%d"), font=FONTS["title_md"], text_color=THEME["primary"] if not is_today else THEME["on_primary"]).pack()
            ctk.CTkLabel(card, text=city, font=FONTS["badge"], text_color=tc, wraplength=90).pack()
            if act_count > 0:
                ctk.CTkLabel(card, text=f"🎟 {act_count}", font=FONTS["badge"], fg_color=THEME["accent"], text_color=THEME["on_accent"], corner_radius=SHAPE["full"]).pack(pady=(4, 8))
            else:
                ctk.CTkFrame(card, height=28, fg_color="transparent").pack()

            card.bind("<Button-1>", lambda _, dd=d: self._on_day_click(dd))
            for ch in card.winfo_children():
                ch.bind("<Button-1>", lambda _, dd=d: self._on_day_click(dd))

    # ─────────────────────────────────────────────────────────────
    def _on_trip_change(self, trip_name: str):
        t = next((t for t in self._user_trips if t.name == trip_name), None)
        if t:
            self.trip_id = t.id
            self.refresh()
