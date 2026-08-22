"""
Phase 6b — Activity Search / Catalog Screen
Features:
  - Type filter chip bar (All, Sightseeing, Food, Adventure…)
  - City dropdown filter
  - Cost range min/max inputs
  - 3-column ActivityCatalogCard grid with "Add to Trip" flow
  - Add Custom Activity modal
  - "Add to Trip" pops a trip/stop selector then calls TripService.add_activity
"""
import customtkinter as ctk
from datetime import datetime, UTC
from app.ui.theme import THEME, FONTS, SHAPE, LAYOUT
from app.ui.components.header import Header
from app.ui.components.cards import ActivityCatalogCard, EmptyState
from app.services.city_service import CityService
from app.services.trip_service import TripService
from app.schemas.city import ActivitySearchParams, ActivityCatalogCreate
from app.schemas.trip import ActivityCreate
from app.core.exceptions import AppException

_TYPES = ["All Types", "Sightseeing", "Food", "Adventure", "Cultural",
          "Nature", "Nightlife", "Shopping", "Wellness", "Transport", "Other"]

_TYPE_ICONS = {
    "All Types": "🎟️", "Sightseeing": "🏛️", "Food": "🍽️", "Adventure": "🧗",
    "Cultural": "🎭", "Nature": "🌿", "Nightlife": "🌙", "Shopping": "🛍️",
    "Wellness": "🧘", "Transport": "🚌", "Other": "📍",
}


def _mk_entry(parent, placeholder="", val="") -> ctk.CTkEntry:
    e = ctk.CTkEntry(
        parent,
        placeholder_text=placeholder,
        height=LAYOUT["input_height"],
        font=FONTS["body"],
        fg_color=THEME["bg_input"],
        border_color=THEME["border"],
        border_width=1,
        corner_radius=SHAPE["small"],
        text_color=THEME["text_primary"],
        placeholder_text_color=THEME["text_muted"],
    )
    if val:
        e.insert(0, val)
    e.bind("<FocusIn>",  lambda _: e.configure(border_color=THEME["border_focus"]))
    e.bind("<FocusOut>", lambda _: e.configure(border_color=THEME["border"]))
    return e


# ══════════════════════════════════════════════════════════════════
class ActivitySearchScreen(ctk.CTkScrollableFrame):
    def __init__(self, master, navigate_callback, session_factory, current_user, **kwargs):
        super().__init__(
            master,
            fg_color=THEME["bg_dark"],
            scrollbar_button_color=THEME["border"],
            scrollbar_button_hover_color=THEME["border_light"],
            **kwargs,
        )
        self.navigate_callback  = navigate_callback
        self.session_factory    = session_factory
        self.current_user       = current_user
        self.selected_type      = "All Types"
        self.selected_city_id   = None
        self.cost_min           = None
        self.cost_max           = None
        self.cities             = []
        self.grid_columnconfigure(0, weight=1)
        self.refresh()

    # ─────────────────────────────────────────────────────────────
    def refresh(self):
        for w in self.winfo_children():
            w.destroy()

        with self.session_factory() as session:
            self.cities, _ = CityService(session).search_cities(
                ActivitySearchParams.__bases__[0](limit=200) if False else
                type("P", (), {"limit": 200, "offset": 0})()
            )

        Header(
            self,
            title="Experiences & Things To Do 🎟️",
            subtitle="Browse activities by category, city, and budget range to enrich your itinerary.",
            action_button=("➕  Custom Activity", self._open_add_activity_modal, THEME["bg_input"]),
            breadcrumb=["Dashboard", "Activities"],
        ).pack(fill="x", padx=20, pady=(18, 10))

        # ── Filter card ───────────────────────────────────────────
        fcard = ctk.CTkFrame(
            self,
            fg_color=THEME["bg_card"],
            corner_radius=SHAPE["medium"],
            border_width=1,
            border_color=THEME["border"],
        )
        fcard.pack(fill="x", padx=20, pady=(0, 10))
        fi = ctk.CTkFrame(fcard, fg_color="transparent")
        fi.pack(fill="x", padx=16, pady=14)

        # City + cost range row
        top_row = ctk.CTkFrame(fi, fg_color="transparent")
        top_row.pack(fill="x", pady=(0, 10))
        top_row.grid_columnconfigure(0, weight=2)
        top_row.grid_columnconfigure((1, 2), weight=1)

        city_names = ["All Cities"] + [f"{c.name}, {c.country}" for c in self.cities]
        self._city_cb = ctk.CTkComboBox(
            top_row,
            values=city_names,
            height=LAYOUT["input_height"],
            font=FONTS["body"],
            fg_color=THEME["bg_input"],
            border_color=THEME["border"],
            text_color=THEME["text_primary"],
            command=self._on_city_change,
        )
        if self.selected_city_id:
            for c in self.cities:
                if c.id == self.selected_city_id:
                    self._city_cb.set(f"{c.name}, {c.country}")
                    break
        else:
            self._city_cb.set("All Cities")
        self._city_cb.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self._min_e = _mk_entry(top_row, "Min Cost", str(int(self.cost_min)) if self.cost_min else "")
        self._min_e.grid(row=0, column=1, sticky="ew", padx=(0, 6))

        self._max_e = _mk_entry(top_row, "Max Cost", str(int(self.cost_max)) if self.cost_max else "")
        self._max_e.grid(row=0, column=2, sticky="ew", padx=(0, 8))

        ctk.CTkButton(
            top_row,
            text="Apply",
            font=FONTS["body_sm"],
            height=LAYOUT["input_height"],
            width=70,
            corner_radius=SHAPE["small"],
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            command=self._apply_cost_filter,
        ).grid(row=0, column=3)

        # Type chip bar
        chip_row = ctk.CTkFrame(fi, fg_color="transparent")
        chip_row.pack(fill="x")
        for t in _TYPES:
            icon   = _TYPE_ICONS.get(t, "📍")
            active = t == self.selected_type
            fg     = THEME["primary"] if active else THEME["bg_input"]
            tc     = THEME["on_primary"] if active else THEME["text_secondary"]
            ctk.CTkButton(
                chip_row,
                text=f"{icon} {t}",
                font=FONTS["badge"],
                height=28,
                corner_radius=SHAPE["full"],
                fg_color=fg,
                hover_color=THEME["primary_hover"],
                text_color=tc,
                border_width=0 if active else 1,
                border_color=THEME["border"],
                command=lambda tp=t: self._set_type(tp),
            ).pack(side="left", padx=(0, 4), pady=2)

        # ── Results ───────────────────────────────────────────────
        self._render_results()

    # ─────────────────────────────────────────────────────────────
    def _render_results(self):
        if hasattr(self, "_res_frame") and self._res_frame.winfo_exists():
            self._res_frame.destroy()

        type_filter = None if self.selected_type == "All Types" else self.selected_type.lower()

        params = ActivitySearchParams(
            city_id=self.selected_city_id,
            activity_type=type_filter,
            cost_min=self.cost_min,
            cost_max=self.cost_max,
            limit=60,
        )
        with self.session_factory() as session:
            activities, total = CityService(session).search_activities(params)

        self._res_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._res_frame.pack(fill="x", padx=20, pady=(4, 24))

        ctk.CTkLabel(
            self._res_frame,
            text=f"{total} activities found" if total else f"{len(activities)} activities",
            font=FONTS["body_sm"],
            text_color=THEME["text_muted"],
            anchor="w",
        ).pack(fill="x", pady=(0, 8))

        if not activities:
            EmptyState(
                self._res_frame,
                icon="🎟️",
                title="No activities match your filters",
                message="Try selecting 'All Types', removing cost limits, or a different city.",
                action_label="Clear Filters",
                action_cmd=self._clear_filters,
            ).pack(fill="x")
            return

        grid = ctk.CTkFrame(self._res_frame, fg_color="transparent")
        grid.pack(fill="x")
        grid.grid_columnconfigure((0, 1, 2), weight=1)

        for i, act in enumerate(activities):
            r, c = divmod(i, 3)
            ActivityCatalogCard(
                grid,
                activity=act,
                on_add=lambda a: self._open_add_to_trip(a),
            ).grid(row=r, column=c, padx=4, pady=5, sticky="ew")

    # ─────────────────────────────────────────────────────────────
    def _set_type(self, type_name: str):
        self.selected_type = type_name
        self.refresh()

    def _on_city_change(self, choice: str):
        if choice == "All Cities":
            self.selected_city_id = None
        else:
            for c in self.cities:
                if f"{c.name}, {c.country}" == choice:
                    self.selected_city_id = c.id
                    break
        self._render_results()

    def _apply_cost_filter(self):
        try:
            mn = self._min_e.get().strip()
            mx = self._max_e.get().strip()
            self.cost_min = float(mn) if mn else None
            self.cost_max = float(mx) if mx else None
        except ValueError:
            pass
        self._render_results()

    def _clear_filters(self):
        self.selected_type    = "All Types"
        self.selected_city_id = None
        self.cost_min         = None
        self.cost_max         = None
        self.refresh()

    # ─────────────────────────────────────────────────────────────
    # ADD TO TRIP MODAL
    # ─────────────────────────────────────────────────────────────
    def _open_add_to_trip(self, activity):
        # Load user trips + stops
        trips = []
        with self.session_factory() as session:
            trips = TripService(session).list_trips(self.current_user.id, limit=50)

        if not trips:
            win = ctk.CTkToplevel(self)
            win.title("No Trips")
            win.geometry("380x180")
            win.configure(fg_color=THEME["bg_card"])
            win.grab_set()
            ctk.CTkLabel(win, text="You have no trips yet.", font=FONTS["title_sm"], text_color=THEME["text_primary"]).pack(pady=(32, 8))
            ctk.CTkButton(win, text="Create a Trip →", font=FONTS["body_lg"], height=LAYOUT["btn_height"], corner_radius=SHAPE["small"], fg_color=THEME["primary"], hover_color=THEME["primary_hover"], command=lambda: [win.destroy(), self.navigate_callback("create_trip")]).pack(padx=24, fill="x")
            return

        win = ctk.CTkToplevel(self)
        win.title("Add to Trip")
        win.geometry("500x480")
        win.configure(fg_color=THEME["bg_card"])
        win.grab_set()
        win.focus()

        ctk.CTkFrame(win, height=4, fg_color=THEME["accent"]).pack(fill="x")
        ctk.CTkLabel(win, text=f"Add  「{activity.name}」  to Trip", font=FONTS["title_sm"], text_color=THEME["text_primary"]).pack(anchor="w", padx=24, pady=(18, 4))

        # Trip selector
        ctk.CTkLabel(win, text="Select Trip  *", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w", padx=24, pady=(10, 2))
        trip_names = [t.name for t in trips]
        trip_cb = ctk.CTkComboBox(win, values=trip_names, height=LAYOUT["input_height"], font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"], text_color=THEME["text_primary"])
        trip_cb.set(trip_names[0])
        trip_cb.pack(fill="x", padx=24, pady=(0, 10))

        # Stop selector (updated when trip changes)
        ctk.CTkLabel(win, text="Select Stop  *", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w", padx=24, pady=(4, 2))
        stop_cb = ctk.CTkComboBox(win, values=[], height=LAYOUT["input_height"], font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"], text_color=THEME["text_primary"])
        stop_cb.pack(fill="x", padx=24, pady=(0, 10))

        def load_stops(trip_name):
            selected_trip = next((t for t in trips if t.name == trip_name), None)
            if not selected_trip or not selected_trip.stops:
                stop_cb.configure(values=["(No stops — add one first)"])
                stop_cb.set("(No stops — add one first)")
                return
            with self.session_factory() as session:
                full_trip = TripService(session).get_trip(selected_trip.id, self.current_user.id)
            stop_names = [f"{s.city.name if s.city else 'Stop'} ({s.arrival_date.strftime('%b %d')})" for s in full_trip.stops]
            stop_cb.configure(values=stop_names)
            stop_cb.set(stop_names[0])
            stop_cb._stops = full_trip.stops

        trip_cb.configure(command=load_stops)
        load_stops(trip_names[0])

        # Date + time
        ctk.CTkLabel(win, text="Start Date & Time", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w", padx=24, pady=(4, 2))
        from tkcalendar import DateEntry
        t_row = ctk.CTkFrame(win, fg_color="transparent")
        t_row.pack(fill="x", padx=24, pady=(0, 8))
        from datetime import date
        s_cal = DateEntry(t_row, font=("Segoe UI", 11), background=THEME["primary"], foreground="white", date_pattern="yyyy-mm-dd")
        s_cal.set_date(date.today())
        s_cal.pack(side="left", padx=(0, 8))
        s_time_e = _mk_entry(t_row, "HH:MM", "10:00")
        s_time_e.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(win, text="End Time", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w", padx=24, pady=(4, 2))
        e_time_e = _mk_entry(win, "HH:MM", "12:00")
        e_time_e.pack(fill="x", padx=24, pady=(0, 8))

        err = ctk.CTkLabel(win, text="", font=FONTS["body_sm"], text_color=THEME["danger"])
        err.pack(fill="x", padx=24)

        def save():
            selected_trip = next((t for t in trips if t.name == trip_cb.get()), None)
            if not selected_trip:
                err.configure(text="Select a valid trip")
                return
            stops = getattr(stop_cb, "_stops", [])
            stop_idx = stop_cb.cget("values").index(stop_cb.get()) if stop_cb.get() in stop_cb.cget("values") else -1
            if stop_idx < 0 or stop_idx >= len(stops):
                err.configure(text="Select a valid stop")
                return
            stop = stops[stop_idx]
            try:
                s_dt = datetime.combine(s_cal.get_date(), datetime.strptime(s_time_e.get().strip(), "%H:%M").time()).replace(tzinfo=UTC)
                e_dt = datetime.combine(s_cal.get_date(), datetime.strptime(e_time_e.get().strip(), "%H:%M").time()).replace(tzinfo=UTC)
                if s_dt > e_dt:
                    err.configure(text="Start time cannot be after end time")
                    return
                act_type = str(getattr(activity, "activity_type", "other") or "other")
                if hasattr(activity.activity_type, "value"):
                    act_type = activity.activity_type.value
                with self.session_factory() as session:
                    TripService(session).add_activity(
                        selected_trip.id,
                        self.current_user.id,
                        stop.id,
                        ActivityCreate(
                            name=activity.name,
                            activity_type=act_type.lower(),
                            start_time=s_dt,
                            end_time=e_dt,
                            estimated_cost=float(activity.avg_cost or 0),
                        ),
                    )
                    session.commit()
                win.destroy()
            except Exception as ex:
                err.configure(text=f"Error: {ex}")

        ctk.CTkButton(win, text="✅  Add to Trip", font=FONTS["body_lg"], height=LAYOUT["btn_height"], corner_radius=SHAPE["small"], fg_color=THEME["primary"], hover_color=THEME["primary_hover"], command=save).pack(fill="x", padx=24, pady=(8, 16))

    # ─────────────────────────────────────────────────────────────
    # ADD CUSTOM ACTIVITY MODAL
    # ─────────────────────────────────────────────────────────────
    def _open_add_activity_modal(self):
        win = ctk.CTkToplevel(self)
        win.title("Add Custom Activity to Catalog")
        win.geometry("520x540")
        win.configure(fg_color=THEME["bg_card"])
        win.grab_set()
        win.focus()

        ctk.CTkFrame(win, height=4, fg_color=THEME["accent"]).pack(fill="x")
        ctk.CTkLabel(win, text="➕  Create Catalog Activity", font=FONTS["title_md"], text_color=THEME["text_primary"]).pack(anchor="w", padx=24, pady=(18, 4))

        def lbl(text):
            ctk.CTkLabel(win, text=text, font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w", padx=24, pady=(10, 2))

        lbl("Activity Name  *")
        name_e = _mk_entry(win, "e.g. Eiffel Tower Visit")
        name_e.pack(fill="x", padx=24, pady=(0, 4))

        lbl("City  *")
        city_names = [f"{c.name}, {c.country}" for c in self.cities]
        city_cb = ctk.CTkComboBox(win, values=city_names if city_names else ["(No cities — add one first)"], height=LAYOUT["input_height"], font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"], text_color=THEME["text_primary"])
        if city_names:
            city_cb.set(city_names[0])
        city_cb.pack(fill="x", padx=24, pady=(0, 4))

        # Type + Cost + Duration row
        tcd = ctk.CTkFrame(win, fg_color="transparent")
        tcd.pack(fill="x", padx=24, pady=(4, 4))
        tcd.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(tcd, text="Category", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).grid(row=0, column=0, sticky="w", padx=(0, 6))
        ctk.CTkLabel(tcd, text="Avg Cost", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).grid(row=0, column=1, sticky="w", padx=(0, 6))
        ctk.CTkLabel(tcd, text="Duration (min)", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).grid(row=0, column=2, sticky="w")

        type_cb = ctk.CTkComboBox(tcd, values=[t.lower() for t in _TYPES[1:]], height=LAYOUT["input_height"], font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"], text_color=THEME["text_primary"])
        type_cb.set("sightseeing")
        type_cb.grid(row=1, column=0, sticky="ew", padx=(0, 6))

        cost_e = _mk_entry(tcd, "0")
        cost_e.insert(0, "0")
        cost_e.grid(row=1, column=1, sticky="ew", padx=(0, 6))

        dur_e = _mk_entry(tcd, "120")
        dur_e.insert(0, "120")
        dur_e.grid(row=1, column=2, sticky="ew")

        lbl("Description (optional)")
        desc_box = ctk.CTkTextbox(win, height=70, font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"], border_width=1, text_color=THEME["text_primary"])
        desc_box.pack(fill="x", padx=24, pady=(0, 4))

        err = ctk.CTkLabel(win, text="", font=FONTS["body_sm"], text_color=THEME["danger"])
        err.pack(fill="x", padx=24, pady=4)

        def save():
            nm   = name_e.get().strip()
            city_val = city_cb.get()
            city = next((c for c in self.cities if f"{c.name}, {c.country}" == city_val), None)
            if not nm:
                err.configure(text="Activity name is required")
                return
            if not city:
                err.configure(text="Please select a valid city")
                return
            try:
                with self.session_factory() as session:
                    CityService(session).create_activity(
                        ActivityCatalogCreate(
                            city_id=city.id,
                            name=nm,
                            activity_type=type_cb.get(),
                            avg_cost=float(cost_e.get().strip() or 0),
                            duration_minutes=int(dur_e.get().strip() or 120),
                            description=desc_box.get("1.0", "end-1c").strip() or None,
                        )
                    )
                    session.commit()
                win.destroy()
                self.refresh()
            except AppException as ex:
                err.configure(text=str(ex.detail))
            except Exception as ex:
                err.configure(text=f"Error: {ex}")

        ctk.CTkButton(win, text="Save to Catalog", font=FONTS["body_lg"], height=LAYOUT["btn_height"], corner_radius=SHAPE["small"], fg_color=THEME["accent"], hover_color=THEME["accent_hover"], command=save).pack(fill="x", padx=24, pady=(4, 16))
