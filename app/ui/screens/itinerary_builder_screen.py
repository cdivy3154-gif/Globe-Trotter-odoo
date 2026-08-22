import customtkinter as ctk
from datetime import datetime, timedelta, UTC
from tkinter import messagebox
from app.ui.theme import THEME, FONTS
from app.ui.components.header import Header
from app.services.trip_service import TripService
from app.services.city_service import CityService
from app.schemas.trip import StopCreate, ActivityCreate, StopUpdate, ActivityUpdate
from app.schemas.city import CitySearchParams
from app.core.exceptions import AppException


class ItineraryBuilderScreen(ctk.CTkScrollableFrame):
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

        if not self.trip_id:
            # If no trip ID specified, list user trips or prompt creation
            ctk.CTkLabel(self, text="⚠️ No trip selected for editing", font=FONTS["title_md"]).pack(pady=30)
            ctk.CTkButton(self, text="Select from My Trips", command=lambda: self.navigate_callback("my_trips")).pack()
            return

        # Fetch Trip Data
        trip = None
        all_cities = []
        try:
            with self.session_factory() as session:
                trip_service = TripService(session)
                city_service = CityService(session)
                trip = trip_service.get_trip(self.trip_id, self.current_user.id)
                all_cities, _ = city_service.search_cities(CitySearchParams(limit=100))
        except Exception as ex:
            ctk.CTkLabel(self, text=f"Error loading trip: {str(ex)}", font=FONTS["body"]).pack(pady=30)
            return

        self.all_cities = all_cities

        # Trip Summary Top Banner
        top_banner = ctk.CTkFrame(self, fg_color=THEME["bg_card"], corner_radius=14, border_width=1, border_color=THEME["border"])
        top_banner.pack(fill="x", padx=20, pady=(15, 15))

        b_hdr = ctk.CTkFrame(top_banner, fg_color="transparent")
        b_hdr.pack(fill="x", padx=20, pady=(16, 8))

        ctk.CTkLabel(b_hdr, text=trip.name, font=FONTS["title_lg"], text_color=THEME["text_primary"]).pack(side="left")

        # Action Buttons in Top Banner
        actions_frame = ctk.CTkFrame(b_hdr, fg_color="transparent")
        actions_frame.pack(side="right")

        ctk.CTkButton(actions_frame, text="👁️ Itinerary View", width=110, height=32, font=FONTS["body_sm"], fg_color=THEME["border"], hover_color=THEME["bg_card_hover"], command=lambda: self.navigate_callback("itinerary_view", trip_id=self.trip_id)).pack(side="left", padx=4)
        ctk.CTkButton(actions_frame, text="💰 Budget", width=90, height=32, font=FONTS["body_sm"], fg_color=THEME["border"], hover_color=THEME["bg_card_hover"], command=lambda: self.navigate_callback("budget", trip_id=self.trip_id)).pack(side="left", padx=4)
        ctk.CTkButton(actions_frame, text="📅 Timeline", width=95, height=32, font=FONTS["body_sm"], fg_color=THEME["border"], hover_color=THEME["bg_card_hover"], command=lambda: self.navigate_callback("calendar", trip_id=self.trip_id)).pack(side="left", padx=4)
        ctk.CTkButton(actions_frame, text="🔗 Share", width=80, height=32, font=FONTS["body_sm"], fg_color=THEME["primary"], hover_color=THEME["primary_hover"], command=lambda: self.navigate_callback("share", trip_id=self.trip_id)).pack(side="left", padx=4)

        # Meta Subtitle
        s_date = trip.start_date.strftime("%b %d, %Y")
        e_date = trip.end_date.strftime("%b %d, %Y")
        meta_str = f"🗓️ {s_date}  to  {e_date}   •   📍 {len(trip.stops)} Destinations"
        if trip.total_budget:
            meta_str += f"   •   🎯 Budget: ${float(trip.total_budget):,.2f}"

        ctk.CTkLabel(top_banner, text=meta_str, font=FONTS["body"], text_color=THEME["text_secondary"]).pack(anchor="w", padx=20, pady=(0, 16))

        # Stop Builder Controls Header
        builder_bar = ctk.CTkFrame(self, fg_color="transparent")
        builder_bar.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(builder_bar, text="Trip Itinerary Stops", font=FONTS["title_md"], text_color=THEME["text_primary"]).pack(side="left")
        ctk.CTkButton(builder_bar, text="➕ Add City Stop", font=FONTS["body_lg"], height=34, fg_color=THEME["accent"], hover_color=THEME["accent_hover"], command=lambda: self._open_add_stop_modal(trip)).pack(side="right")

        # Render Stops Accordions/Cards
        if not trip.stops:
            no_stops = ctk.CTkFrame(self, fg_color=THEME["bg_card"], corner_radius=12, border_width=1, border_color=THEME["border"])
            no_stops.pack(fill="x", padx=20, pady=20)
            ctk.CTkLabel(no_stops, text="📍 No stops added to this trip yet!", font=FONTS["title_md"], text_color=THEME["text_secondary"]).pack(pady=(24, 6))
            ctk.CTkLabel(no_stops, text="Add your first destination city to start attaching activities and estimating budgets.", font=FONTS["body_sm"], text_color=THEME["text_muted"]).pack(pady=(0, 16))
            ctk.CTkButton(no_stops, text="➕ Add First Stop", font=FONTS["body_lg"], fg_color=THEME["accent"], hover_color=THEME["accent_hover"], command=lambda: self._open_add_stop_modal(trip)).pack(pady=(0, 24))
        else:
            for idx, stop in enumerate(trip.stops):
                self._render_stop_card(stop, idx, len(trip.stops), trip)

    def _render_stop_card(self, stop, index, total_stops, trip):
        card = ctk.CTkFrame(self, fg_color=THEME["bg_card"], corner_radius=12, border_width=1, border_color=THEME["border"])
        card.pack(fill="x", padx=20, pady=8)

        # Stop Header Row
        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(14, 8))

        city_name = f"{stop.city.name}, {stop.city.country}" if stop.city else "Unknown City"
        title_text = f"Stop {index + 1}:  🏙️ {city_name}"
        ctk.CTkLabel(hdr, text=title_text, font=FONTS["title_md"], text_color=THEME["text_primary"]).pack(side="left")

        # Control buttons: Move Up, Move Down, Delete
        ctrls = ctk.CTkFrame(hdr, fg_color="transparent")
        ctrls.pack(side="right")

        if index > 0:
            ctk.CTkButton(ctrls, text="▲ Up", width=46, height=26, font=FONTS["badge"], fg_color=THEME["border"], hover_color=THEME["bg_card_hover"], command=lambda: self._move_stop(stop.id, -1)).pack(side="left", padx=2)
        if index < total_stops - 1:
            ctk.CTkButton(ctrls, text="▼ Down", width=46, height=26, font=FONTS["badge"], fg_color=THEME["border"], hover_color=THEME["bg_card_hover"], command=lambda: self._move_stop(stop.id, 1)).pack(side="left", padx=2)

        ctk.CTkButton(ctrls, text="🗑️", width=30, height=26, font=FONTS["body_sm"], fg_color=THEME["danger_bg"], hover_color=THEME["danger"], command=lambda: self._delete_stop(stop.id)).pack(side="left", padx=(6, 0))

        # Dates & City Metadata
        arr_str = stop.arrival_date.strftime("%b %d, %Y")
        dep_str = stop.departure_date.strftime("%b %d, %Y")
        stay_days = max((stop.departure_date.date() - stop.arrival_date.date()).days + 1, 1)

        dates_bar = ctk.CTkFrame(card, fg_color="transparent")
        dates_bar.pack(fill="x", padx=16, pady=(0, 10))

        ctk.CTkLabel(dates_bar, text=f"🗓️ Stay: {arr_str}  ➔  {dep_str}  ({stay_days} Days)", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(side="left")

        # Activities Sub-Section
        act_box = ctk.CTkFrame(card, fg_color=THEME["bg_input"], corner_radius=8, border_width=1, border_color=THEME["border"])
        act_box.pack(fill="x", padx=16, pady=(0, 14))

        act_hdr = ctk.CTkFrame(act_box, fg_color="transparent")
        act_hdr.pack(fill="x", padx=12, pady=(10, 6))

        ctk.CTkLabel(act_hdr, text=f"Planned Activities ({len(stop.activities)})", font=FONTS["body_lg"], text_color=THEME["text_primary"]).pack(side="left")
        ctk.CTkButton(act_hdr, text="➕ Add Activity", font=FONTS["body_sm"], height=26, fg_color=THEME["primary"], hover_color=THEME["primary_hover"], command=lambda: self._open_add_activity_modal(stop)).pack(side="right")

        if not stop.activities:
            ctk.CTkLabel(act_box, text="No activities assigned to this stop yet. Click '+ Add Activity' to browse catalog or create custom.", font=FONTS["body_sm"], text_color=THEME["text_muted"]).pack(padx=12, pady=(4, 12), anchor="w")
        else:
            for act in stop.activities:
                self._render_activity_row(act_box, act, stop.id)

    def _render_activity_row(self, container, act, stop_id):
        row = ctk.CTkFrame(container, fg_color=THEME["bg_card"], corner_radius=6, border_width=1, border_color=THEME["border"])
        row.pack(fill="x", padx=10, pady=4)

        l_frame = ctk.CTkFrame(row, fg_color="transparent")
        l_frame.pack(side="left", padx=10, pady=8, fill="x", expand=True)

        name_lbl = ctk.CTkLabel(l_frame, text=act.name, font=FONTS["body_lg"], text_color=THEME["text_primary"], anchor="w")
        name_lbl.pack(anchor="w")

        time_str = f"⏰ {act.start_time.strftime('%b %d, %H:%M')} - {act.end_time.strftime('%H:%M')}"
        cost_str = f"💰 ${float(act.estimated_cost or 0):,.2f}"
        type_str = f"🏷️ {act.activity_type.upper()}"
        sub_txt = f"{type_str}   •   {time_str}   •   {cost_str}"

        ctk.CTkLabel(l_frame, text=sub_txt, font=FONTS["body_sm"], text_color=THEME["text_secondary"], anchor="w").pack(anchor="w")

        del_btn = ctk.CTkButton(row, text="✕", width=28, height=28, font=FONTS["badge"], fg_color="transparent", hover_color=THEME["danger_bg"], text_color=THEME["text_muted"], command=lambda: self._delete_activity(stop_id, act.id))
        del_btn.pack(side="right", padx=10)

    # ------------------ Modals & Operations ------------------
    def _open_add_stop_modal(self, trip):
        win = ctk.CTkToplevel(self)
        win.title("Add Destination Stop")
        win.geometry("450x420")
        win.configure(fg_color=THEME["bg_card"])
        win.grab_set()

        ctk.CTkLabel(win, text="Add New City Stop", font=FONTS["title_md"], text_color=THEME["text_primary"]).pack(padx=20, pady=(20, 10), anchor="w")

        # City picker
        ctk.CTkLabel(win, text="Destination City *", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w", padx=20, pady=(6, 2))
        city_names = [f"{c.name}, {c.country}" for c in self.all_cities]
        city_cb = ctk.CTkComboBox(win, values=city_names, height=36, font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"])
        city_cb.pack(fill="x", padx=20, pady=(0, 10))

        # Dates
        def_arr = trip.start_date.strftime("%Y-%m-%d")
        def_dep = trip.end_date.strftime("%Y-%m-%d")

        ctk.CTkLabel(win, text="Arrival Date (YYYY-MM-DD) *", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w", padx=20, pady=(4, 2))
        arr_entry = ctk.CTkEntry(win, height=36, font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"])
        arr_entry.insert(0, def_arr)
        arr_entry.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(win, text="Departure Date (YYYY-MM-DD) *", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w", padx=20, pady=(4, 2))
        dep_entry = ctk.CTkEntry(win, height=36, font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"])
        dep_entry.insert(0, def_dep)
        dep_entry.pack(fill="x", padx=20, pady=(0, 10))

        err_lbl = ctk.CTkLabel(win, text="", font=FONTS["body_sm"], text_color=THEME["danger"])
        err_lbl.pack(fill="x", padx=20, pady=(0, 6))

        def save_stop():
            c_val = city_cb.get()
            selected_city = next((c for c in self.all_cities if f"{c.name}, {c.country}" == c_val), None)
            if not selected_city:
                err_lbl.configure(text="Please choose a valid city")
                return

            try:
                a_dt = datetime.strptime(arr_entry.get().strip(), "%Y-%m-%d").replace(tzinfo=UTC)
                d_dt = datetime.strptime(dep_entry.get().strip(), "%Y-%m-%d").replace(tzinfo=UTC)
                if a_dt > d_dt:
                    err_lbl.configure(text="Arrival date cannot be after departure date")
                    return

                with self.session_factory() as session:
                    service = TripService(session)
                    service.add_stop(
                        trip.id,
                        self.current_user.id,
                        StopCreate(city_id=selected_city.id, arrival_date=a_dt, departure_date=d_dt),
                    )
                    session.commit()
                win.destroy()
                self.refresh()
            except Exception as ex:
                err_lbl.configure(text=f"Error: {str(ex)}")

        ctk.CTkButton(win, text="Save Stop", height=38, font=FONTS["body_lg"], fg_color=THEME["primary"], hover_color=THEME["primary_hover"], command=save_stop).pack(fill="x", padx=20, pady=10)

    def _open_add_activity_modal(self, stop):
        win = ctk.CTkToplevel(self)
        win.title("Add Activity")
        win.geometry("520x540")
        win.configure(fg_color=THEME["bg_card"])
        win.grab_set()

        ctk.CTkLabel(win, text=f"Add Activity for {stop.city.name if stop.city else 'Stop'}", font=FONTS["title_md"], text_color=THEME["text_primary"]).pack(padx=20, pady=(16, 6), anchor="w")

        # Fetch city activities catalog
        catalog = getattr(stop.city, "activities_catalog", []) if stop.city else []
        catalog_names = ["(Custom Activity)"] + [f"{a.name} (${float(a.avg_cost or 0):,.0f})" for a in catalog]

        ctk.CTkLabel(win, text="Select from Catalog (or Custom) *", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w", padx=20, pady=(6, 2))
        cat_combo = ctk.CTkComboBox(win, values=catalog_names, height=36, font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"])
        cat_combo.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(win, text="Activity Name *", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w", padx=20, pady=(4, 2))
        name_entry = ctk.CTkEntry(win, placeholder_text="e.g. Louvre Museum Tour", height=36, font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"])
        name_entry.pack(fill="x", padx=20, pady=(0, 10))

        # Auto-populate if catalog selected
        def on_cat_change(choice):
            if choice != "(Custom Activity)":
                for a in catalog:
                    if choice.startswith(a.name):
                        name_entry.delete(0, "end")
                        name_entry.insert(0, a.name)
                        cost_entry.delete(0, "end")
                        cost_entry.insert(0, str(a.avg_cost or 0))
                        type_combo.set(a.activity_type.value if hasattr(a.activity_type, "value") else str(a.activity_type))
                        break

        cat_combo.configure(command=on_cat_change)

        # Row with Type & Cost
        tc_row = ctk.CTkFrame(win, fg_color="transparent")
        tc_row.pack(fill="x", padx=20, pady=(0, 10))
        tc_row.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(tc_row, text="Category *", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).grid(row=0, column=0, sticky="w", padx=(0, 8))
        types = ["sightseeing", "food", "adventure", "culture", "nature", "nightlife", "shopping", "relaxation"]
        type_combo = ctk.CTkComboBox(tc_row, values=types, height=36, font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"])
        type_combo.grid(row=1, column=0, sticky="ew", padx=(0, 8))

        ctk.CTkLabel(tc_row, text="Estimated Cost (USD $)", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).grid(row=0, column=1, sticky="w", padx=(8, 0))
        cost_entry = ctk.CTkEntry(tc_row, placeholder_text="e.g. 35", height=36, font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"])
        cost_entry.insert(0, "0")
        cost_entry.grid(row=1, column=1, sticky="ew", padx=(8, 0))

        # Dates & Times
        s_date_str = stop.arrival_date.strftime("%Y-%m-%d")
        ctk.CTkLabel(win, text="Start Time (YYYY-MM-DD HH:MM) *", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w", padx=20, pady=(4, 2))
        start_t_entry = ctk.CTkEntry(win, height=36, font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"])
        start_t_entry.insert(0, f"{s_date_str} 10:00")
        start_t_entry.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(win, text="End Time (YYYY-MM-DD HH:MM) *", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w", padx=20, pady=(4, 2))
        end_t_entry = ctk.CTkEntry(win, height=36, font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"])
        end_t_entry.insert(0, f"{s_date_str} 12:30")
        end_t_entry.pack(fill="x", padx=20, pady=(0, 10))

        err_lbl = ctk.CTkLabel(win, text="", font=FONTS["body_sm"], text_color=THEME["danger"])
        err_lbl.pack(fill="x", padx=20, pady=(0, 6))

        def save_activity():
            act_name = name_entry.get().strip()
            if not act_name:
                err_lbl.configure(text="Please provide an activity name")
                return

            try:
                st = datetime.strptime(start_t_entry.get().strip(), "%Y-%m-%d %H:%M").replace(tzinfo=UTC)
                et = datetime.strptime(end_t_entry.get().strip(), "%Y-%m-%d %H:%M").replace(tzinfo=UTC)
                if st > et:
                    err_lbl.configure(text="Start time cannot be after end time")
                    return

                cost_f = float(cost_entry.get().strip() or 0)

                with self.session_factory() as session:
                    service = TripService(session)
                    service.add_activity(
                        self.trip_id,
                        self.current_user.id,
                        stop.id,
                        ActivityCreate(
                            name=act_name,
                            activity_type=type_combo.get().lower(),
                            start_time=st,
                            end_time=et,
                            estimated_cost=cost_f,
                        ),
                    )
                    session.commit()
                win.destroy()
                self.refresh()
            except Exception as ex:
                err_lbl.configure(text=f"Error: {str(ex)}")

        ctk.CTkButton(win, text="Save Activity to Stop", height=38, font=FONTS["body_lg"], fg_color=THEME["primary"], hover_color=THEME["primary_hover"], command=save_activity).pack(fill="x", padx=20, pady=10)

    def _move_stop(self, stop_id, direction):
        with self.session_factory() as session:
            trip_service = TripService(session)
            trip = trip_service.get_trip(self.trip_id, self.current_user.id)
            stops = list(trip.stops)

            curr_idx = next((i for i, s in enumerate(stops) if s.id == stop_id), None)
            if curr_idx is not None:
                swap_idx = curr_idx + direction
                if 0 <= swap_idx < len(stops):
                    # Swap orders
                    stops[curr_idx], stops[swap_idx] = stops[swap_idx], stops[curr_idx]
                    reorders = [(s.id, i + 1) for i, s in enumerate(stops)]
                    trip_service.reorder_stops(trip.id, self.current_user.id, reorders)
                    session.commit()
        self.refresh()

    def _delete_stop(self, stop_id):
        if messagebox.askyesno("Delete Stop", "Are you sure you want to remove this stop and its activities?"):
            with self.session_factory() as session:
                trip_service = TripService(session)
                trip_service.delete_stop(self.trip_id, self.current_user.id, stop_id)
                session.commit()
            self.refresh()

    def _delete_activity(self, stop_id, activity_id):
        with self.session_factory() as session:
            trip_service = TripService(session)
            trip_service.delete_activity(self.trip_id, self.current_user.id, stop_id, activity_id)
            session.commit()
        self.refresh()
