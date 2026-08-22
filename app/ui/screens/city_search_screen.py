import customtkinter as ctk
from app.ui.theme import THEME, FONTS
from app.ui.components.header import Header
from app.ui.components.cards import CityCard
from app.services.city_service import CityService
from app.services.trip_service import TripService
from app.schemas.city import CitySearchParams, CityCreate
from app.schemas.trip import StopCreate
from datetime import datetime, UTC
from tkinter import messagebox


class CitySearchScreen(ctk.CTkScrollableFrame):
    def __init__(self, master, navigate_callback, session_factory, current_user, **kwargs):
        super().__init__(master, fg_color=THEME["bg_dark"], **kwargs)
        self.navigate_callback = navigate_callback
        self.session_factory = session_factory
        self.current_user = current_user
        self.search_query = ""
        self.selected_region = "All Regions"
        self.grid_columnconfigure(0, weight=1)
        self.refresh()

    def refresh(self):
        for widget in self.winfo_children():
            widget.destroy()

        header = Header(
            self,
            title="Global City Directory 🏙️",
            subtitle="Discover top travel destinations, explore local activity catalogs, and add stops to your journeys.",
            action_button=("➕ Add New City", self._open_create_city_modal, THEME["border"]),
        )
        header.pack(fill="x", padx=20, pady=(15, 10))

        # Search & Filter Controls Bar
        filter_bar = ctk.CTkFrame(self, fg_color=THEME["bg_card"], corner_radius=12, border_width=1, border_color=THEME["border"])
        filter_bar.pack(fill="x", padx=20, pady=(0, 15))

        f_inner = ctk.CTkFrame(filter_bar, fg_color="transparent")
        f_inner.pack(fill="x", padx=16, pady=12)
        f_inner.grid_columnconfigure(0, weight=3)
        f_inner.grid_columnconfigure(1, weight=2)

        # Search box
        self.search_entry = ctk.CTkEntry(
            f_inner,
            placeholder_text="🔍 Search cities by name or country...",
            height=38,
            font=FONTS["body"],
            fg_color=THEME["bg_input"],
            border_color=THEME["border"],
        )
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        if self.search_query:
            self.search_entry.insert(0, self.search_query)

        # Region filter combo
        regions = ["All Regions", "Europe", "Asia", "North America", "Middle East", "Oceania", "South America", "Africa"]
        self.region_cb = ctk.CTkComboBox(
            f_inner,
            values=regions,
            height=38,
            font=FONTS["body"],
            fg_color=THEME["bg_input"],
            border_color=THEME["border"],
            command=self._on_region_change,
        )
        self.region_cb.set(self.selected_region)
        self.region_cb.grid(row=0, column=1, sticky="ew", padx=(0, 10))

        apply_btn = ctk.CTkButton(
            f_inner,
            text="Filter",
            font=FONTS["body_lg"],
            height=38,
            width=90,
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            command=self._handle_search,
        )
        apply_btn.grid(row=0, column=2, sticky="e")

        # Fetch matching cities & saved status
        cities = []
        saved_dests = []
        user_trips = []

        with self.session_factory() as session:
            city_service = CityService(session)
            trip_service = TripService(session)

            reg_param = None if self.selected_region == "All Regions" else self.selected_region
            params = CitySearchParams(q=self.search_query if self.search_query else None, region=reg_param, limit=100)
            cities, _ = city_service.search_cities(params)

            saved_dests = city_service.get_saved_destinations(self.current_user.id)
            saved_city_ids = {s.city_id for s in saved_dests}

            user_trips = trip_service.list_trips(self.current_user.id, limit=50)

        self.user_trips = user_trips

        # Render Cities Grid
        if cities:
            grid_frame = ctk.CTkFrame(self, fg_color="transparent")
            grid_frame.pack(fill="x", padx=20, pady=5)
            grid_frame.grid_columnconfigure((0, 1), weight=1)

            for idx, city in enumerate(cities):
                card = CityCard(
                    grid_frame,
                    city=city,
                    is_saved=(city.id in saved_city_ids),
                    on_add_to_trip=lambda c: self._open_add_to_trip_dialog(c),
                    on_toggle_save=lambda c: self._handle_toggle_save(c),
                )
                r, c = divmod(idx, 2)
                card.grid(row=r, column=c, padx=6, pady=6, sticky="ew")
        else:
            empty_frame = ctk.CTkFrame(self, fg_color=THEME["bg_card"], corner_radius=12)
            empty_frame.pack(fill="x", padx=20, pady=20)
            ctk.CTkLabel(empty_frame, text="🔍 No cities found matching your filter criteria.", font=FONTS["body_lg"], text_color=THEME["text_secondary"]).pack(pady=30)

    def _handle_search(self):
        self.search_query = self.search_entry.get().strip()
        self.selected_region = self.region_cb.get()
        self.refresh()

    def _on_region_change(self, choice):
        self.selected_region = choice
        self._handle_search()

    def _handle_toggle_save(self, city):
        with self.session_factory() as session:
            city_service = CityService(session)
            city_service.toggle_save_destination(self.current_user.id, city.id)
            session.commit()
        self.refresh()

    def _open_add_to_trip_dialog(self, city):
        if not self.user_trips:
            create_new = messagebox.askyesno(
                "No Active Trips",
                f"You don't have any trips created yet.\nWould you like to start a new trip with {city.name}?",
            )
            if create_new:
                self.navigate_callback("create_trip", city_id=city.id)
            return

        win = ctk.CTkToplevel(self)
        win.title(f"Add {city.name} to Trip")
        win.geometry("420x340")
        win.configure(fg_color=THEME["bg_card"])
        win.grab_set()

        ctk.CTkLabel(win, text=f"Add {city.name} to Trip Stop", font=FONTS["title_md"], text_color=THEME["text_primary"]).pack(padx=20, pady=(20, 10), anchor="w")

        ctk.CTkLabel(win, text="Select Trip *", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w", padx=20, pady=(4, 2))
        trip_names = [t.name for t in self.user_trips]
        trip_cb = ctk.CTkComboBox(win, values=trip_names, height=36, font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"])
        trip_cb.pack(fill="x", padx=20, pady=(0, 10))

        # Dates
        ctk.CTkLabel(win, text="Arrival Date (YYYY-MM-DD)", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w", padx=20, pady=(4, 2))
        arr_entry = ctk.CTkEntry(win, height=36, font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"])
        arr_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        arr_entry.pack(fill="x", padx=20, pady=(0, 10))

        err_lbl = ctk.CTkLabel(win, text="", font=FONTS["body_sm"], text_color=THEME["danger"])
        err_lbl.pack(fill="x", padx=20, pady=(0, 4))

        def confirm_add():
            t_choice = trip_cb.get()
            chosen_trip = next((t for t in self.user_trips if t.name == t_choice), None)
            if not chosen_trip:
                err_lbl.configure(text="Please select a valid trip")
                return

            try:
                a_dt = datetime.strptime(arr_entry.get().strip(), "%Y-%m-%d").replace(tzinfo=UTC)
                d_dt = a_dt + (chosen_trip.end_date - chosen_trip.start_date)

                with self.session_factory() as session:
                    trip_service = TripService(session)
                    trip_service.add_stop(
                        chosen_trip.id,
                        self.current_user.id,
                        StopCreate(city_id=city.id, arrival_date=a_dt, departure_date=d_dt),
                    )
                    session.commit()
                win.destroy()
                messagebox.showinfo("Success", f"{city.name} was added as a stop in '{chosen_trip.name}'!")
                self.navigate_callback("itinerary_builder", trip_id=chosen_trip.id)
            except Exception as ex:
                err_lbl.configure(text=f"Error: {str(ex)}")

        ctk.CTkButton(win, text="Confirm & Add Stop", height=38, font=FONTS["body_lg"], fg_color=THEME["primary"], hover_color=THEME["primary_hover"], command=confirm_add).pack(fill="x", padx=20, pady=10)

    def _open_create_city_modal(self):
        win = ctk.CTkToplevel(self)
        win.title("Add New Destination City")
        win.geometry("450x480")
        win.configure(fg_color=THEME["bg_card"])
        win.grab_set()

        ctk.CTkLabel(win, text="Add New City to Directory", font=FONTS["title_md"], text_color=THEME["text_primary"]).pack(padx=20, pady=(20, 10), anchor="w")

        ctk.CTkLabel(win, text="City Name *", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w", padx=20, pady=(4, 2))
        name_e = ctk.CTkEntry(win, placeholder_text="e.g. Vienna", height=36, font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"])
        name_e.pack(fill="x", padx=20, pady=(0, 8))

        ctk.CTkLabel(win, text="Country *", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w", padx=20, pady=(4, 2))
        country_e = ctk.CTkEntry(win, placeholder_text="e.g. Austria", height=36, font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"])
        country_e.pack(fill="x", padx=20, pady=(0, 8))

        ctk.CTkLabel(win, text="Region *", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w", padx=20, pady=(4, 2))
        reg_cb = ctk.CTkComboBox(win, values=["Europe", "Asia", "North America", "Middle East", "Oceania", "South America", "Africa"], height=36, font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"])
        reg_cb.pack(fill="x", padx=20, pady=(0, 8))

        ctk.CTkLabel(win, text="Description", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w", padx=20, pady=(4, 2))
        desc_e = ctk.CTkEntry(win, placeholder_text="Brief highlights", height=36, font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"])
        desc_e.pack(fill="x", padx=20, pady=(0, 12))

        err_lbl = ctk.CTkLabel(win, text="", font=FONTS["body_sm"], text_color=THEME["danger"])
        err_lbl.pack(fill="x", padx=20, pady=(0, 4))

        def save_new_city():
            c_name = name_e.get().strip()
            c_country = country_e.get().strip()
            if not c_name or not c_country:
                err_lbl.configure(text="City name and Country are required")
                return

            try:
                with self.session_factory() as session:
                    city_service = CityService(session)
                    city_service.create_city(
                        CityCreate(
                            name=c_name,
                            country=c_country,
                            country_code=c_country[:2].upper(),
                            region=reg_cb.get(),
                            description=desc_e.get().strip() or None,
                            cost_index=55,
                            popularity_score=80,
                        )
                    )
                    session.commit()
                win.destroy()
                self.refresh()
            except Exception as ex:
                err_lbl.configure(text=f"Error: {str(ex)}")

        ctk.CTkButton(win, text="Save City", height=38, font=FONTS["body_lg"], fg_color=THEME["primary"], hover_color=THEME["primary_hover"], command=save_new_city).pack(fill="x", padx=20, pady=10)
