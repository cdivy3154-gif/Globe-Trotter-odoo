"""
Phase 4b — Itinerary Builder Screen
Full CRUD for stops + activities.

Layout:
  Top banner: trip name, meta, action buttons (View / Budget / Calendar / Share)
  Section header: "Trip Stops" + "Add City Stop"
  Per-stop accordion card:
    - City name, dates, stay days
    - ↑ ↓ reorder buttons, 🗑 delete
    - Activities sub-panel with add / delete inline
    - Live cost tally at bottom of stop card
  Bottom: total estimated cost bar
  
Modals:
  _open_add_stop_modal → tkcalendar DateEntry, city search
  _open_add_activity_modal → segmented type selector, catalog autofill, time pickers
"""
import customtkinter as ctk
from datetime import datetime, UTC
from tkinter import messagebox
from tkcalendar import DateEntry

from app.ui.theme import THEME, FONTS, SHAPE, LAYOUT, format_money, get_currency_symbol
from app.ui.components.header import Header
from app.ui.components.cards import EmptyState
from app.services.trip_service import TripService
from app.services.city_service import CityService
from app.schemas.trip import StopCreate, ActivityCreate
from app.schemas.city import CitySearchParams
from app.core.exceptions import AppException

_ACT_TYPES  = ["sightseeing", "food", "adventure", "cultural", "nature", "nightlife", "shopping", "wellness", "transport", "other"]
_ACT_ICONS  = {"sightseeing": "🏛️", "food": "🍽️", "adventure": "🧗", "cultural": "🎭",
                "nature": "🌿", "nightlife": "🌙", "shopping": "🛍️", "wellness": "🧘",
                "transport": "🚌", "other": "📍"}


def _mk_entry(parent, placeholder="", show="") -> ctk.CTkEntry:
    e = ctk.CTkEntry(
        parent,
        placeholder_text=placeholder,
        show=show,
        height=LAYOUT["input_height"],
        font=FONTS["body"],
        fg_color=THEME["bg_input"],
        border_color=THEME["border"],
        border_width=1,
        corner_radius=SHAPE["small"],
        text_color=THEME["text_primary"],
    )
    e.bind("<FocusIn>",  lambda _: e.configure(border_color=THEME["border_focus"]))
    e.bind("<FocusOut>", lambda _: e.configure(border_color=THEME["border"]))
    return e


def _fl(parent, text):
    ctk.CTkLabel(parent, text=text, font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w", pady=(8, 2))


# ══════════════════════════════════════════════════════════════════
class ItineraryBuilderScreen(ctk.CTkScrollableFrame):
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
        self.all_cities        = []
        self.grid_columnconfigure(0, weight=1)
        self.refresh()

    # ─────────────────────────────────────────────────────────────
    def refresh(self):
        for w in self.winfo_children():
            w.destroy()

        if not self.trip_id:
            EmptyState(
                self,
                icon="🗺️",
                title="No trip selected",
                message="Please choose a trip from My Trips to open the builder.",
                action_label="→  My Trips",
                action_cmd=lambda: self.navigate_callback("my_trips"),
            ).pack(fill="x", padx=20, pady=40)
            return

        # Fetch
        trip = None
        try:
            with self.session_factory() as session:
                ts = TripService(session)
                cs = CityService(session)
                trip = ts.get_trip(self.trip_id, self.current_user.id)
                self.all_cities, _ = cs.search_cities(CitySearchParams(limit=200))
        except Exception as ex:
            ctk.CTkLabel(self, text=f"Error loading trip: {ex}", font=FONTS["body"], text_color=THEME["danger"]).pack(pady=40)
            return

        self._build_banner(trip)
        self._build_stops_section(trip)
        self._build_total_bar(trip)

    # ─────────────────────────────────────────────────────────────
    # TOP BANNER
    # ─────────────────────────────────────────────────────────────
    def _build_banner(self, trip):
        banner = ctk.CTkFrame(
            self,
            fg_color=THEME["bg_card"],
            corner_radius=SHAPE["medium"],
            border_width=1,
            border_color=THEME["border"],
        )
        banner.pack(fill="x", padx=20, pady=(18, 10))
        ctk.CTkFrame(banner, height=4, fg_color=THEME["primary"], corner_radius=0).pack(fill="x")

        top = ctk.CTkFrame(banner, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=(14, 8))
        top.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            top,
            text=f"✈️  {trip.name}",
            font=FONTS["title_lg"],
            text_color=THEME["text_primary"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        # Action buttons
        btns = ctk.CTkFrame(top, fg_color="transparent")
        btns.grid(row=0, column=1, sticky="e", padx=(16, 0))

        _btn_data = [
            ("👁️  View",   "itinerary_view", THEME["bg_input"]),
            ("💰  Budget", "budget",          THEME["bg_input"]),
            ("📅  Calendar","calendar",        THEME["bg_input"]),
            ("🔗  Share",  "share",            THEME["primary"]),
        ]
        for label, key, color in _btn_data:
            ctk.CTkButton(
                btns,
                text=label,
                font=FONTS["body_sm"],
                height=LAYOUT["btn_height_sm"],
                width=100,
                corner_radius=SHAPE["small"],
                fg_color=color,
                hover_color=THEME["primary_hover"] if color == THEME["primary"] else THEME["bg_card_hover"],
                border_width=0 if color == THEME["primary"] else 1,
                border_color=THEME["border"],
                text_color=THEME["text_primary"] if color == THEME["primary"] else THEME["text_secondary"],
                command=lambda k=key: self.navigate_callback(k, trip_id=self.trip_id),
            ).pack(side="left", padx=3)

        # Meta row
        s = trip.start_date.strftime("%b %d, %Y")
        e = trip.end_date.strftime("%b %d, %Y")
        stops = len(trip.stops)
        total_acts = sum(len(st.activities) for st in trip.stops)
        meta = f"📅 {s}  →  {e}   •   📍 {stops} Destinations   •   🎟️ {total_acts} Activities"
        if trip.total_budget:
            curr = getattr(trip, "currency", "USD")
            meta += f"   •   💰 Budget: {format_money(trip.total_budget, curr, decimals=0)}"

        ctk.CTkLabel(banner, text=meta, font=FONTS["body_sm"], text_color=THEME["text_secondary"], anchor="w").pack(fill="x", padx=20, pady=(0, 14))

    # ─────────────────────────────────────────────────────────────
    # STOPS SECTION
    # ─────────────────────────────────────────────────────────────
    def _build_stops_section(self, trip):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(4, 6))

        ctk.CTkLabel(hdr, text="City Stops", font=FONTS["title_md"], text_color=THEME["text_primary"]).pack(side="left")
        ctk.CTkButton(
            hdr,
            text="➕  Add City Stop",
            font=FONTS["body_lg"],
            height=LAYOUT["btn_height_sm"],
            corner_radius=SHAPE["small"],
            fg_color=THEME["accent"],
            hover_color=THEME["accent_hover"],
            command=lambda: self._open_add_stop_modal(trip),
        ).pack(side="right")

        if not trip.stops:
            EmptyState(
                self,
                icon="📍",
                title="No stops added yet",
                message="Add your first destination city to start building your itinerary.",
                action_label="➕  Add First Stop",
                action_cmd=lambda: self._open_add_stop_modal(trip),
            ).pack(fill="x", padx=20, pady=12)
        else:
            for idx, stop in enumerate(trip.stops):
                self._render_stop_card(stop, idx, len(trip.stops), trip)

    # ─────────────────────────────────────────────────────────────
    # STOP CARD
    # ─────────────────────────────────────────────────────────────
    def _render_stop_card(self, stop, index: int, total: int, trip):
        card = ctk.CTkFrame(
            self,
            fg_color=THEME["bg_card"],
            corner_radius=SHAPE["medium"],
            border_width=1,
            border_color=THEME["border"],
        )
        card.pack(fill="x", padx=20, pady=6)

        # ── Stop header ──────────────────────────────────────────
        ctk.CTkFrame(card, height=3, fg_color=THEME["accent"], corner_radius=0).pack(fill="x")

        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(12, 6))

        city_name = f"Stop {index + 1}:  🏙️ {stop.city.name}, {stop.city.country}" if stop.city else f"Stop {index + 1}"
        ctk.CTkLabel(hdr, text=city_name, font=FONTS["title_sm"], text_color=THEME["text_primary"]).pack(side="left")

        # Reorder + delete
        ctrl = ctk.CTkFrame(hdr, fg_color="transparent")
        ctrl.pack(side="right")
        if index > 0:
            ctk.CTkButton(ctrl, text="▲", width=32, height=28, font=FONTS["badge"], fg_color=THEME["bg_input"], hover_color=THEME["bg_card_hover"], border_width=1, border_color=THEME["border"], command=lambda: self._move_stop(stop.id, -1)).pack(side="left", padx=2)
        if index < total - 1:
            ctk.CTkButton(ctrl, text="▼", width=32, height=28, font=FONTS["badge"], fg_color=THEME["bg_input"], hover_color=THEME["bg_card_hover"], border_width=1, border_color=THEME["border"], command=lambda: self._move_stop(stop.id, 1)).pack(side="left", padx=2)
        ctk.CTkButton(ctrl, text="🗑", width=32, height=28, font=FONTS["body_sm"], fg_color=THEME["danger_bg"], hover_color=THEME["danger"], text_color=THEME["danger"], command=lambda: self._delete_stop(stop.id)).pack(side="left", padx=(6, 0))

        # ── Dates strip ──────────────────────────────────────────
        try:
            arr = stop.arrival_date.strftime("%b %d, %Y")
            dep = stop.departure_date.strftime("%b %d, %Y")
            days = max((stop.departure_date.date() - stop.arrival_date.date()).days + 1, 1)
        except Exception:
            arr = dep = "—"
            days = 1

        dates_row = ctk.CTkFrame(card, fg_color="transparent")
        dates_row.pack(fill="x", padx=16, pady=(0, 10))
        ctk.CTkLabel(dates_row, text=f"🗓️  {arr}  →  {dep}  ({days} days)", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(side="left")

        # Cost index if available
        if stop.city and stop.city.cost_index:
            ctk.CTkLabel(dates_row, text=f"  💲 Cost Index: {stop.city.cost_index}", font=FONTS["body_sm"], text_color=THEME["text_muted"]).pack(side="left")

        # ── Activities panel ─────────────────────────────────────
        act_panel = ctk.CTkFrame(card, fg_color=THEME["bg_input"], corner_radius=SHAPE["small"], border_width=1, border_color=THEME["border"])
        act_panel.pack(fill="x", padx=16, pady=(0, 12))

        act_hdr = ctk.CTkFrame(act_panel, fg_color="transparent")
        act_hdr.pack(fill="x", padx=12, pady=(10, 6))
        ctk.CTkLabel(act_hdr, text=f"Activities  ({len(stop.activities)})", font=FONTS["body_lg"], text_color=THEME["text_primary"]).pack(side="left")
        ctk.CTkButton(act_hdr, text="➕ Add Activity", font=FONTS["body_sm"], height=28, corner_radius=SHAPE["extra_small"], fg_color=THEME["primary"], hover_color=THEME["primary_hover"], command=lambda: self._open_add_activity_modal(stop)).pack(side="right")

        if not stop.activities:
            ctk.CTkLabel(act_panel, text="No activities yet — click '+ Add Activity' to begin.", font=FONTS["body_sm"], text_color=THEME["text_muted"], anchor="w").pack(padx=12, pady=(0, 10), anchor="w")
        else:
            stop_cost = 0.0
            for act in stop.activities:
                self._render_activity_row(act_panel, act, stop.id)
                stop_cost += float(act.estimated_cost or 0)

            # Stop subtotal
            curr = getattr(trip, "currency", "USD")
            sub = ctk.CTkFrame(act_panel, fg_color="transparent")
            sub.pack(fill="x", padx=12, pady=(4, 10))
            ctk.CTkLabel(sub, text=f"Stop Subtotal: {format_money(stop_cost, curr, decimals=2)}", font=FONTS["body_lg"], text_color=THEME["success"]).pack(side="right")

    # ─────────────────────────────────────────────────────────────
    # ACTIVITY ROW
    # ─────────────────────────────────────────────────────────────
    def _render_activity_row(self, container, act, stop_id):
        act_type = str(getattr(act, "activity_type", "other") or "other").lower()
        if hasattr(act.activity_type, "value"):
            act_type = act.activity_type.value
        icon = _ACT_ICONS.get(act_type, "📍")

        row = ctk.CTkFrame(container, fg_color=THEME["bg_card"], corner_radius=SHAPE["extra_small"], border_width=1, border_color=THEME["border"])
        row.pack(fill="x", padx=10, pady=3)

        ctk.CTkLabel(row, text=icon, font=FONTS["body_lg"]).pack(side="left", padx=(10, 6), pady=8)

        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True, pady=8)

        ctk.CTkLabel(info, text=act.name, font=FONTS["body_lg"], text_color=THEME["text_primary"], anchor="w").pack(anchor="w")

        act_curr = getattr(act, "currency", "USD") or "USD"
        cost_formatted = format_money(act.estimated_cost, act_curr, decimals=2)
        try:
            t1 = act.start_time.strftime("%b %d, %H:%M")
            t2 = act.end_time.strftime("%H:%M")
            sub = f"⏰ {t1} - {t2}   •   {act_type.title()}   •   {cost_formatted}"
        except Exception:
            sub = act_type.title()

        ctk.CTkLabel(info, text=sub, font=FONTS["body_sm"], text_color=THEME["text_secondary"], anchor="w").pack(anchor="w")

        # Cost chip
        chip_cost = format_money(act.estimated_cost, act_curr, decimals=0)
        ctk.CTkLabel(row, text=f" {chip_cost} ", font=FONTS["badge"], fg_color=THEME["success_bg"], text_color=THEME["success"], corner_radius=SHAPE["extra_small"]).pack(side="right", padx=(0, 6))

        ctk.CTkButton(row, text="✕", width=28, height=28, font=FONTS["badge"], fg_color="transparent", hover_color=THEME["danger_bg"], text_color=THEME["text_muted"], command=lambda: self._delete_activity(stop_id, act.id)).pack(side="right", padx=4)

    # ─────────────────────────────────────────────────────────────
    # TOTAL BAR
    # ─────────────────────────────────────────────────────────────
    def _build_total_bar(self, trip):
        total_cost = sum(
            sum(float(a.estimated_cost or 0) for a in stop.activities)
            for stop in trip.stops
        )
        budget = float(trip.total_budget or 0)
        over   = budget > 0 and total_cost > budget
        curr   = getattr(trip, "currency", "USD")

        bar = ctk.CTkFrame(
            self,
            fg_color=THEME["danger_bg"] if over else THEME["bg_card"],
            corner_radius=SHAPE["medium"],
            border_width=1,
            border_color=THEME["danger"] if over else THEME["border"],
        )
        bar.pack(fill="x", padx=20, pady=(8, 24))

        inner = ctk.CTkFrame(bar, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=14)

        ctk.CTkLabel(inner, text=f"Total Estimated Cost:  {format_money(total_cost, curr, decimals=2)}", font=FONTS["title_sm"], text_color=THEME["danger"] if over else THEME["success"]).pack(side="left")

        if budget > 0:
            remaining = budget - total_cost
            sign = "-" if remaining < 0 else "+"
            color = THEME["danger"] if remaining < 0 else THEME["success"]
            rem_str = format_money(abs(remaining), curr, decimals=2)
            bud_str = format_money(budget, curr, decimals=0)
            ctk.CTkLabel(inner, text=f"Budget: {bud_str}   |   Remaining: {sign}{rem_str}", font=FONTS["body"], text_color=color).pack(side="right")

        if over:
            ctk.CTkLabel(bar, text="⚠️  Over budget! Review your activities or increase your budget allocation.", font=FONTS["body_sm"], text_color=THEME["warning"]).pack(fill="x", padx=20, pady=(0, 10), anchor="w")

    # ─────────────────────────────────────────────────────────────
    # ADD STOP MODAL
    # ─────────────────────────────────────────────────────────────
    def _open_add_stop_modal(self, trip):
        win = ctk.CTkToplevel(self)
        win.title("Add Destination Stop")
        win.geometry("500x480")
        win.configure(fg_color=THEME["bg_card"])
        win.grab_set()
        win.focus()

        ctk.CTkFrame(win, height=4, fg_color=THEME["primary"]).pack(fill="x")
        ctk.CTkLabel(win, text="➕  Add City Stop", font=FONTS["title_md"], text_color=THEME["text_primary"]).pack(anchor="w", padx=24, pady=(20, 4))
        ctk.CTkLabel(win, text="Choose a destination and specify the stay dates.", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w", padx=24, pady=(0, 14))

        # City search
        ctk.CTkLabel(win, text="Destination City  *", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w", padx=24)
        city_names = [f"{c.name}, {c.country}" for c in self.all_cities]
        city_cb = ctk.CTkComboBox(win, values=city_names, height=LAYOUT["input_height"], font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"], text_color=THEME["text_primary"])
        city_cb.pack(fill="x", padx=24, pady=(4, 12))

        # Date pickers side by side
        cal_row = ctk.CTkFrame(win, fg_color="transparent")
        cal_row.pack(fill="x", padx=24, pady=(0, 12))
        cal_row.grid_columnconfigure((0, 1), weight=1)

        a_col = ctk.CTkFrame(cal_row, fg_color="transparent")
        a_col.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkLabel(a_col, text="Arrival Date  *", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w")
        arr_cal = DateEntry(a_col, font=("Segoe UI", 11), background=THEME["primary"], foreground="white", date_pattern="yyyy-mm-dd")
        arr_cal.set_date(trip.start_date.date())
        arr_cal.pack(fill="x", pady=(4, 0))

        d_col = ctk.CTkFrame(cal_row, fg_color="transparent")
        d_col.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        ctk.CTkLabel(d_col, text="Departure Date  *", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w")
        dep_cal = DateEntry(d_col, font=("Segoe UI", 11), background=THEME["primary"], foreground="white", date_pattern="yyyy-mm-dd")
        dep_cal.set_date(trip.end_date.date())
        dep_cal.pack(fill="x", pady=(4, 0))

        # Notes
        ctk.CTkLabel(win, text="Notes (optional)", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w", padx=24, pady=(8, 2))
        notes_box = ctk.CTkTextbox(win, height=60, font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"], border_width=1, text_color=THEME["text_primary"])
        notes_box.pack(fill="x", padx=24)

        err = ctk.CTkLabel(win, text="", font=FONTS["body_sm"], text_color=THEME["danger"])
        err.pack(fill="x", padx=24, pady=6)

        def save():
            city_val = city_cb.get()
            selected = next((c for c in self.all_cities if f"{c.name}, {c.country}" == city_val), None)
            if not selected:
                err.configure(text="Please choose a valid city")
                return
            try:
                a_dt = datetime.combine(arr_cal.get_date(), datetime.min.time()).replace(tzinfo=UTC)
                d_dt = datetime.combine(dep_cal.get_date(), datetime.min.time()).replace(tzinfo=UTC)
                if a_dt > d_dt:
                    err.configure(text="Arrival date cannot be after departure date")
                    return
                notes = notes_box.get("1.0", "end-1c").strip() or None

                with self.session_factory() as session:
                    TripService(session).add_stop(
                        trip.id,
                        self.current_user.id,
                        StopCreate(city_id=selected.id, arrival_date=a_dt, departure_date=d_dt, notes=notes),
                    )
                    session.commit()
                win.destroy()
                self.refresh()
            except Exception as ex:
                err.configure(text=f"Error: {ex}")

        ctk.CTkButton(win, text="Save Stop", font=FONTS["body_lg"], height=LAYOUT["btn_height"], corner_radius=SHAPE["small"], fg_color=THEME["primary"], hover_color=THEME["primary_hover"], command=save).pack(fill="x", padx=24, pady=(4, 16))

    # ─────────────────────────────────────────────────────────────
    # ADD ACTIVITY MODAL
    # ─────────────────────────────────────────────────────────────
    def _open_add_activity_modal(self, stop):
        win = ctk.CTkToplevel(self)
        win.title("Add Activity")
        win.geometry("560x620")
        win.configure(fg_color=THEME["bg_card"])
        win.grab_set()
        win.focus()

        ctk.CTkFrame(win, height=4, fg_color=THEME["accent"]).pack(fill="x")
        city_lbl = stop.city.name if stop.city else "Stop"
        ctk.CTkLabel(win, text=f"🎟️  Add Activity — {city_lbl}", font=FONTS["title_md"], text_color=THEME["text_primary"]).pack(anchor="w", padx=24, pady=(18, 4))

        # Catalog or Custom
        catalog = getattr(stop.city, "activities_catalog", []) if stop.city else []
        cat_names = ["— Custom Activity —"] + [f"{a.name}  (${float(a.avg_cost or 0):.0f})" for a in catalog]

        ctk.CTkLabel(win, text="From Catalog (or Custom)", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w", padx=24, pady=(8, 2))
        cat_cb = ctk.CTkComboBox(win, values=cat_names, height=LAYOUT["input_height"], font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"], text_color=THEME["text_primary"])
        cat_cb.pack(fill="x", padx=24, pady=(0, 10))

        ctk.CTkLabel(win, text="Activity Name  *", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w", padx=24, pady=(4, 2))
        name_e = _mk_entry(win, "e.g. Louvre Museum Tour")
        name_e.pack(fill="x", padx=24, pady=(0, 10))

        # Type segmented button
        ctk.CTkLabel(win, text="Category", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w", padx=24, pady=(4, 2))
        type_seg = ctk.CTkSegmentedButton(
            win,
            values=[t.title() for t in _ACT_TYPES[:6]],
            font=FONTS["body_sm"],
            fg_color=THEME["bg_input"],
            selected_color=THEME["primary"],
            selected_hover_color=THEME["primary_hover"],
            unselected_color=THEME["bg_input"],
            unselected_hover_color=THEME["bg_card_hover"],
            text_color=THEME["text_secondary"],
        )
        type_seg.set("Sightseeing")
        type_seg.pack(fill="x", padx=24, pady=(0, 10))

        # Cost + extra types
        cost_row = ctk.CTkFrame(win, fg_color="transparent")
        cost_row.pack(fill="x", padx=24, pady=(0, 10))
        cost_row.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(cost_row, text="Estimated Cost ($)", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).grid(row=0, column=0, sticky="w", padx=(0, 8))
        ctk.CTkLabel(cost_row, text="Full Type (if not above)", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).grid(row=0, column=1, sticky="w", padx=(8, 0))

        cost_e = _mk_entry(cost_row, "0")
        cost_e.insert(0, "0")
        cost_e.grid(row=1, column=0, sticky="ew", padx=(0, 8))

        type_full = ctk.CTkComboBox(cost_row, values=_ACT_TYPES, height=LAYOUT["input_height"], font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"], text_color=THEME["text_primary"])
        type_full.set("sightseeing")
        type_full.grid(row=1, column=1, sticky="ew", padx=(8, 0))

        # Autofill from catalog
        def on_cat_change(choice):
            if choice == "— Custom Activity —":
                return
            for a in catalog:
                if choice.startswith(a.name):
                    name_e.delete(0, "end")
                    name_e.insert(0, a.name)
                    cost_e.delete(0, "end")
                    cost_e.insert(0, str(int(a.avg_cost or 0)))
                    t = a.activity_type.value if hasattr(a.activity_type, "value") else str(a.activity_type)
                    type_full.set(t)
                    if t.title() in [x.title() for x in _ACT_TYPES[:6]]:
                        type_seg.set(t.title())
                    break

        cat_cb.configure(command=on_cat_change)

        # Time pickers (DateEntry + hour:min combos)
        s_date_str = stop.arrival_date.strftime("%Y-%m-%d") if hasattr(stop.arrival_date, "strftime") else ""

        def time_row_builder(label_text, default_date, default_time):
            ctk.CTkLabel(win, text=label_text, font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w", padx=24, pady=(6, 2))
            row = ctk.CTkFrame(win, fg_color="transparent")
            row.pack(fill="x", padx=24, pady=(0, 8))
            cal = DateEntry(row, font=("Segoe UI", 11), background=THEME["primary"], foreground="white", date_pattern="yyyy-mm-dd")
            cal.set_date(default_date)
            cal.pack(side="left", padx=(0, 8))
            t_e = _mk_entry(row, "HH:MM")
            t_e.insert(0, default_time)
            t_e.pack(side="left", fill="x", expand=True)
            return cal, t_e

        start_date = stop.arrival_date.date() if hasattr(stop.arrival_date, "date") else datetime.now().date()
        start_cal, start_t = time_row_builder("Start Date & Time  *", start_date, "10:00")
        end_cal,   end_t   = time_row_builder("End Date & Time  *",   start_date, "12:00")

        err = ctk.CTkLabel(win, text="", font=FONTS["body_sm"], text_color=THEME["danger"])
        err.pack(fill="x", padx=24, pady=(0, 4))

        def save():
            act_name = name_e.get().strip()
            if not act_name:
                err.configure(text="Activity name is required")
                return
            try:
                s_dt = datetime.combine(start_cal.get_date(), datetime.strptime(start_t.get().strip(), "%H:%M").time()).replace(tzinfo=UTC)
                e_dt = datetime.combine(end_cal.get_date(),   datetime.strptime(end_t.get().strip(),   "%H:%M").time()).replace(tzinfo=UTC)
                if s_dt > e_dt:
                    err.configure(text="Start time cannot be after end time")
                    return

                act_type_val = type_full.get().lower()
                cost_val = float(cost_e.get().strip() or 0)

                with self.session_factory() as session:
                    TripService(session).add_activity(
                        self.trip_id,
                        self.current_user.id,
                        stop.id,
                        ActivityCreate(
                            name=act_name,
                            activity_type=act_type_val,
                            start_time=s_dt,
                            end_time=e_dt,
                            estimated_cost=cost_val,
                        ),
                    )
                    session.commit()
                win.destroy()
                self.refresh()
            except Exception as ex:
                err.configure(text=f"Error: {ex}")

        ctk.CTkButton(win, text="Save Activity", font=FONTS["body_lg"], height=LAYOUT["btn_height"], corner_radius=SHAPE["small"], fg_color=THEME["primary"], hover_color=THEME["primary_hover"], command=save).pack(fill="x", padx=24, pady=(2, 16))

    # ─────────────────────────────────────────────────────────────
    # CRUD OPS
    # ─────────────────────────────────────────────────────────────
    def _move_stop(self, stop_id, direction):
        with self.session_factory() as session:
            ts    = TripService(session)
            trip  = ts.get_trip(self.trip_id, self.current_user.id)
            stops = list(trip.stops)
            idx   = next((i for i, s in enumerate(stops) if s.id == stop_id), None)
            if idx is not None:
                swap = idx + direction
                if 0 <= swap < len(stops):
                    stops[idx], stops[swap] = stops[swap], stops[idx]
                    ts.reorder_stops(trip.id, self.current_user.id, [(s.id, i + 1) for i, s in enumerate(stops)])
                    session.commit()
        self.refresh()

    def _delete_stop(self, stop_id):
        if messagebox.askyesno("Delete Stop", "Remove this stop and all its activities?"):
            with self.session_factory() as session:
                TripService(session).delete_stop(self.trip_id, self.current_user.id, stop_id)
                session.commit()
            self.refresh()

    def _delete_activity(self, stop_id, act_id):
        with self.session_factory() as session:
            TripService(session).delete_activity(self.trip_id, self.current_user.id, stop_id, act_id)
            session.commit()
        self.refresh()
