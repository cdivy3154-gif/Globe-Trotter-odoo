"""
Phase 5 — My Trips Screen
Full-featured trips manager:
  - Filter tabs: All | Upcoming | Ongoing | Past | Public
  - Sort bar: Date (newest) / Duration / Budget / Name (A-Z)
  - Live search field (filters as-you-type on Enter)
  - 2-column TripCard grid with Open / Edit / Delete / Share actions
  - Edit modal (inline TripUpdate: name, dates, budget, visibility)
  - Delete confirmation via messagebox
  - Count badge per tab
  - EmptyState with CTA
"""
import customtkinter as ctk
from datetime import datetime, timezone, UTC
from tkinter import messagebox
from tkcalendar import DateEntry

from app.ui.theme import THEME, FONTS, SHAPE, LAYOUT
from app.ui.components.header import Header
from app.ui.components.cards import TripCard, EmptyState
from app.services.trip_service import TripService
from app.schemas.trip import TripUpdate
from app.core.exceptions import AppException

_TABS   = ["All", "Upcoming", "Ongoing", "Past", "Public"]
_SORTS  = ["Newest First", "Oldest First", "Longest Trip", "Highest Budget", "A → Z"]
_VIS    = ["Private 🔒", "Public 🌐"]


def _status(trip) -> str:
    now = datetime.now(timezone.utc)
    try:
        s = trip.start_date if trip.start_date.tzinfo else trip.start_date.replace(tzinfo=timezone.utc)
        e = trip.end_date   if trip.end_date.tzinfo   else trip.end_date.replace(tzinfo=timezone.utc)
    except Exception:
        return "past"
    if now < s:   return "upcoming"
    if now > e:   return "past"
    return "ongoing"


def _is_public(trip) -> bool:
    vis = getattr(trip, "visibility", "")
    return str(vis).lower() == "public" or str(getattr(vis, "value", "")).lower() == "public"


def _apply_tab(trips: list, tab: str) -> list:
    if tab == "All":     return trips
    if tab == "Public":  return [t for t in trips if _is_public(t)]
    return [t for t in trips if _status(t) == tab.lower()]


def _apply_sort(trips: list, sort: str) -> list:
    if sort == "Newest First":
        return sorted(trips, key=lambda t: t.start_date, reverse=True)
    if sort == "Oldest First":
        return sorted(trips, key=lambda t: t.start_date)
    if sort == "Longest Trip":
        return sorted(trips, key=lambda t: (t.end_date - t.start_date).days, reverse=True)
    if sort == "Highest Budget":
        return sorted(trips, key=lambda t: float(t.total_budget or 0), reverse=True)
    if sort == "A → Z":
        return sorted(trips, key=lambda t: t.name.lower())
    return trips


# ══════════════════════════════════════════════════════════════════
class MyTripsScreen(ctk.CTkScrollableFrame):
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
        self._active_tab       = "All"
        self._sort_mode        = "Newest First"
        self._query            = ""
        self.grid_columnconfigure(0, weight=1)
        self.refresh()

    # ─────────────────────────────────────────────────────────────
    def refresh(self):
        for w in self.winfo_children():
            w.destroy()

        # Load trips
        with self.session_factory() as session:
            self._all_trips = TripService(session).list_trips(self.current_user.id, limit=200)

        Header(
            self,
            title="My Travel Journeys 🎒",
            subtitle="Manage, edit, and share all your personalized itineraries.",
            action_button=("➕  Plan New Trip", lambda: self.navigate_callback("create_trip"), THEME["primary"]),
            breadcrumb=["Dashboard", "My Trips"],
        ).pack(fill="x", padx=20, pady=(18, 10))

        # ── Search + Sort row ─────────────────────────────────────
        ctrl_row = ctk.CTkFrame(
            self,
            fg_color=THEME["bg_card"],
            corner_radius=SHAPE["medium"],
            border_width=1,
            border_color=THEME["border"],
        )
        ctrl_row.pack(fill="x", padx=20, pady=(0, 10))
        inner = ctk.CTkFrame(ctrl_row, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)
        inner.grid_columnconfigure(0, weight=1)

        self._search_e = ctk.CTkEntry(
            inner,
            placeholder_text="🔍  Search trips by name or city...",
            height=LAYOUT["input_height"],
            font=FONTS["body"],
            fg_color=THEME["bg_input"],
            border_color=THEME["border"],
            border_width=1,
            corner_radius=SHAPE["small"],
            text_color=THEME["text_primary"],
        )
        self._search_e.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        if self._query:
            self._search_e.insert(0, self._query)
        self._search_e.bind("<Return>", lambda _: self._do_search())

        sort_cb = ctk.CTkComboBox(
            inner,
            values=_SORTS,
            width=160,
            height=LAYOUT["input_height"],
            font=FONTS["body_sm"],
            fg_color=THEME["bg_input"],
            border_color=THEME["border"],
            text_color=THEME["text_primary"],
            command=self._do_sort,
        )
        sort_cb.set(self._sort_mode)
        sort_cb.grid(row=0, column=1, sticky="ew", padx=(0, 8))

        ctk.CTkButton(
            inner,
            text="Search",
            font=FONTS["body_sm"],
            height=LAYOUT["input_height"],
            width=80,
            corner_radius=SHAPE["small"],
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            command=self._do_search,
        ).grid(row=0, column=2)

        # ── Filter tabs ───────────────────────────────────────────
        tab_frame = ctk.CTkFrame(self, fg_color="transparent")
        tab_frame.pack(fill="x", padx=20, pady=(0, 12))

        for tab in _TABS:
            subset = _apply_tab(self._all_trips, tab)
            count  = len(subset)
            active = tab == self._active_tab
            color  = THEME["primary"] if active else THEME["bg_card"]
            tc     = THEME["on_primary"] if active else THEME["text_secondary"]
            bc     = THEME["primary"] if active else THEME["border"]

            btn = ctk.CTkButton(
                tab_frame,
                text=f"{tab}  ({count})",
                font=FONTS["body_sm"],
                height=34,
                corner_radius=SHAPE["small"],
                fg_color=color,
                hover_color=THEME["primary_hover"],
                text_color=tc,
                border_width=1,
                border_color=bc,
                command=lambda t=tab: self._set_tab(t),
            )
            btn.pack(side="left", padx=(0, 6))

        # ── Grid ──────────────────────────────────────────────────
        self._render_grid()

    # ─────────────────────────────────────────────────────────────
    def _render_grid(self):
        # Remove old grid widgets (keep header, ctrl, tabs)
        if hasattr(self, "_grid_frame") and self._grid_frame.winfo_exists():
            self._grid_frame.destroy()

        trips = _apply_tab(self._all_trips, self._active_tab)
        trips = _apply_sort(trips, self._sort_mode)

        if self._query:
            q = self._query.lower()
            trips = [
                t for t in trips
                if q in t.name.lower()
                or any(q in (s.city.name.lower() if s.city else "") for s in t.stops)
            ]

        if not trips:
            self._grid_frame = EmptyState(
                self,
                icon="🎒",
                title="No trips found",
                message="Try a different filter or create your first adventure!",
                action_label="➕  Plan New Trip",
                action_cmd=lambda: self.navigate_callback("create_trip"),
            )
            self._grid_frame.pack(fill="x", padx=20, pady=20)
            return

        # Results count
        count_lbl = ctk.CTkLabel(
            self,
            text=f"{len(trips)} trip(s) found",
            font=FONTS["body_sm"],
            text_color=THEME["text_muted"],
            anchor="w",
        )
        count_lbl.pack(fill="x", padx=22, pady=(0, 4))

        self._grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._grid_frame.pack(fill="x", padx=20, pady=(0, 24))
        self._grid_frame.grid_columnconfigure((0, 1), weight=1)

        for i, trip in enumerate(trips):
            r, c = divmod(i, 2)
            TripCard(
                self._grid_frame,
                trip=trip,
                on_view=lambda t: self.navigate_callback("itinerary_builder", trip_id=t.id),
                on_edit=lambda t: self._open_edit_modal(t),
                on_delete=lambda t: self._delete_trip(t),
                on_share=lambda t: self.navigate_callback("share", trip_id=t.id),
            ).grid(row=r, column=c, padx=(0 if c == 0 else 6, 6 if c == 0 else 0), pady=5, sticky="ew")

    # ─────────────────────────────────────────────────────────────
    def _set_tab(self, tab: str):
        self._active_tab = tab
        self.refresh()

    def _do_sort(self, choice: str):
        self._sort_mode = choice
        self._render_grid()

    def _do_search(self):
        self._query = self._search_e.get().strip()
        self._render_grid()

    # ─────────────────────────────────────────────────────────────
    # EDIT MODAL
    # ─────────────────────────────────────────────────────────────
    def _open_edit_modal(self, trip):
        win = ctk.CTkToplevel(self)
        win.title("Edit Trip")
        win.geometry("540x560")
        win.configure(fg_color=THEME["bg_card"])
        win.grab_set()
        win.focus()

        ctk.CTkFrame(win, height=4, fg_color=THEME["primary"]).pack(fill="x")
        ctk.CTkLabel(win, text="✏️  Edit Trip", font=FONTS["title_md"], text_color=THEME["text_primary"]).pack(anchor="w", padx=24, pady=(20, 4))

        def lbl(text):
            ctk.CTkLabel(win, text=text, font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w", padx=24, pady=(10, 2))

        def entry(placeholder="", val="") -> ctk.CTkEntry:
            e = ctk.CTkEntry(win, placeholder_text=placeholder, height=LAYOUT["input_height"], font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"], border_width=1, corner_radius=SHAPE["small"], text_color=THEME["text_primary"])
            if val:
                e.insert(0, val)
            e.pack(fill="x", padx=24, pady=(0, 4))
            return e

        lbl("Trip Name")
        name_e = entry(val=trip.name)

        lbl("Description")
        desc_box = ctk.CTkTextbox(win, height=70, font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"], border_width=1, text_color=THEME["text_primary"])
        desc_box.pack(fill="x", padx=24, pady=(0, 4))
        if trip.description:
            desc_box.insert("1.0", trip.description)

        # Date row
        date_row = ctk.CTkFrame(win, fg_color="transparent")
        date_row.pack(fill="x", padx=24, pady=(8, 4))
        date_row.grid_columnconfigure((0, 1), weight=1)

        s_col = ctk.CTkFrame(date_row, fg_color="transparent")
        s_col.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkLabel(s_col, text="Start Date", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w")
        s_cal = DateEntry(s_col, font=("Segoe UI", 11), background=THEME["primary"], foreground="white", date_pattern="yyyy-mm-dd")
        s_cal.set_date(trip.start_date.date() if hasattr(trip.start_date, "date") else trip.start_date)
        s_cal.pack(fill="x", pady=(4, 0))

        e_col = ctk.CTkFrame(date_row, fg_color="transparent")
        e_col.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        ctk.CTkLabel(e_col, text="End Date", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w")
        e_cal = DateEntry(e_col, font=("Segoe UI", 11), background=THEME["primary"], foreground="white", date_pattern="yyyy-mm-dd")
        e_cal.set_date(trip.end_date.date() if hasattr(trip.end_date, "date") else trip.end_date)
        e_cal.pack(fill="x", pady=(4, 0))

        lbl("Budget (USD $)")
        budget_e = entry(val=str(int(float(trip.total_budget or 0))) if trip.total_budget else "")

        lbl("Visibility")
        current_vis = "Public 🌐" if _is_public(trip) else "Private 🔒"
        vis_seg = ctk.CTkSegmentedButton(
            win,
            values=_VIS,
            font=FONTS["body_sm"],
            fg_color=THEME["bg_input"],
            selected_color=THEME["primary"],
            selected_hover_color=THEME["primary_hover"],
            unselected_color=THEME["bg_input"],
            unselected_hover_color=THEME["bg_card_hover"],
            text_color=THEME["text_secondary"],
        )
        vis_seg.set(current_vis)
        vis_seg.pack(fill="x", padx=24, pady=(0, 4))

        err = ctk.CTkLabel(win, text="", font=FONTS["body_sm"], text_color=THEME["danger"])
        err.pack(fill="x", padx=24, pady=(4, 0))

        def save():
            new_name = name_e.get().strip()
            if not new_name:
                err.configure(text="Trip name is required")
                return
            try:
                from datetime import datetime
                s_dt = datetime.combine(s_cal.get_date(), datetime.min.time()).replace(tzinfo=UTC)
                e_dt = datetime.combine(e_cal.get_date(), datetime.min.time()).replace(tzinfo=UTC)
                if s_dt > e_dt:
                    err.configure(text="Start date cannot be after end date")
                    return
                bud_str = budget_e.get().strip()
                bud_val = float(bud_str) if bud_str else None
                vis_val = "public" if "Public" in vis_seg.get() else "private"

                with self.session_factory() as session:
                    TripService(session).update_trip(
                        trip.id,
                        self.current_user.id,
                        TripUpdate(
                            name=new_name,
                            description=desc_box.get("1.0", "end-1c").strip() or None,
                            start_date=s_dt,
                            end_date=e_dt,
                            total_budget=bud_val,
                            visibility=vis_val,
                        ),
                    )
                    session.commit()
                win.destroy()
                self.refresh()
            except AppException as ex:
                err.configure(text=str(ex.detail))
            except Exception as ex:
                err.configure(text=f"Error: {ex}")

        ctk.CTkButton(win, text="Save Changes", font=FONTS["body_lg"], height=LAYOUT["btn_height"], corner_radius=SHAPE["small"], fg_color=THEME["primary"], hover_color=THEME["primary_hover"], command=save).pack(fill="x", padx=24, pady=16)

    # ─────────────────────────────────────────────────────────────
    def _delete_trip(self, trip):
        if messagebox.askyesno("Delete Trip", f"Delete '{trip.name}' and all its data permanently?"):
            try:
                with self.session_factory() as session:
                    TripService(session).delete_trip(trip.id, self.current_user.id)
                    session.commit()
                self.refresh()
            except Exception as ex:
                messagebox.showerror("Error", str(ex))
