import customtkinter as ctk
from app.ui.theme import THEME, FONTS
from app.ui.components.header import Header
from app.ui.components.cards import ActivityCard
from app.services.city_service import CityService
from app.services.trip_service import TripService
from app.schemas.city import ActivitySearchParams, ActivityCatalogCreate
from app.schemas.trip import ActivityCreate
from datetime import datetime, UTC
from tkinter import messagebox


class ActivitySearchScreen(ctk.CTkScrollableFrame):
    def __init__(self, master, navigate_callback, session_factory, current_user, **kwargs):
        super().__init__(master, fg_color=THEME["bg_dark"], **kwargs)
        self.navigate_callback = navigate_callback
        self.session_factory = session_factory
        self.current_user = current_user
        self.selected_type = "All Types"
        self.selected_city_id = None
        self.grid_columnconfigure(0, weight=1)
        self.refresh()

    def refresh(self):
        for widget in self.winfo_children():
            widget.destroy()

        header = Header(
            self,
            title="Experiences & Things To Do 🎟️",
            subtitle="Browse activities by category, budget, and city to enrich your travel itinerary.",
            action_button=("➕ Custom Activity", self._open_create_activity_modal, THEME["border"]),
        )
        header.pack(fill="x", padx=20, pady=(15, 10))

        # Filter bar
        filter_bar = ctk.CTkFrame(self, fg_color=THEME["bg_card"], corner_radius=12, border_width=1, border_color=THEME["border"])
        filter_bar.pack(fill="x", padx=20, pady=(0, 15))

        f_row = ctk.CTkFrame(filter_bar, fg_color="transparent")
        f_row.pack(fill="x", padx=16, pady=12)
        f_row.grid_columnconfigure((0, 1, 2), weight=1)

        # Cities combo
        cities = []
        with self.session_factory() as session:
            city_service = CityService(session)
            cities, _ = city_service.search_cities(CitySearchParams(limit=100))
        self.cities = cities

        city_names = ["All Cities"] + [f"{c.name}, {c.country}" for c in cities]
        self.city_cb = ctk.CTkComboBox(f_row, values=city_names, height=36, font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"], command=self._on_city_change)
        self.city_cb.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        # Category combo
        types = ["All Types", "Sightseeing", "Food", "Adventure", "Culture", "Nature", "Nightlife", "Shopping", "Relaxation"]
        self.type_cb = ctk.CTkComboBox(f_row, values=types, height=36, font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"], command=self._on_type_change)
        self.type_cb.set(self.selected_type)
        self.type_cb.grid(row=0, column=1, sticky="ew", padx=(0, 8))

        # Max Cost Entry
        self.cost_entry = ctk.CTkEntry(f_row, placeholder_text="Max Cost ($)", height=36, font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"])
        self.cost_entry.grid(row=0, column=2, sticky="ew", padx=(0, 8))

        apply_btn = ctk.CTkButton(f_row, text="Filter", font=FONTS["body_sm"], height=36, width=70, fg_color=THEME["primary"], hover_color=THEME["primary_hover"], command=self._handle_filter)
        apply_btn.grid(row=0, column=3, sticky="e")

        # Fetch Activities
        activities = []
        user_trips = []
        with self.session_factory() as session:
            city_service = CityService(session)
            trip_service = TripService(session)

            type_param = None if self.selected_type == "All Types" else self.selected_type.lower()
            cost_max = None
            try:
                if self.cost_entry.get().strip():
                    cost_max = float(self.cost_entry.get().strip())
            except ValueError:
                pass

            params = ActivitySearchParams(
                city_id=self.selected_city_id,
                activity_type=type_param,
                cost_max=cost_max,
                limit=100,
            )
            activities, _ = city_service.search_activities(params)
            user_trips = trip_service.list_trips(self.current_user.id, limit=50)

        self.user_trips = user_trips

        # Activities Grid
        if activities:
            grid_frame = ctk.CTkFrame(self, fg_color="transparent")
            grid_frame.pack(fill="x", padx=20, pady=5)
            grid_frame.grid_columnconfigure((0, 1), weight=1)

            for idx, act in enumerate(activities):
                card = ActivityCard(
                    grid_frame,
                    activity=act,
                    on_add=lambda a: self._open_add_to_trip_dialog(a),
                )
                r, c = divmod(idx, 2)
                card.grid(row=r, column=c, padx=6, pady=6, sticky="ew")
        else:
            empty_frame = ctk.CTkFrame(self, fg_color=THEME["bg_card"], corner_radius=12)
            empty_frame.pack(fill="x", padx=20, pady=30)
            ctk.CTkLabel(empty_frame, text="🎟️ No activities found matching your filters.", font=FONTS["body_lg"], text_color=THEME["text_secondary"]).pack(pady=30)

    def _on_city_change(self, choice):
        if choice == "All Cities":
            self.selected_city_id = None
        else:
            selected_city = next((c for c in self.cities if f"{c.name}, {c.country}" == choice), None)
            self.selected_city_id = selected_city.id if selected_city else None
        self.refresh()

    def _on_type_change(self, choice):
        self.selected_type = choice
        self.refresh()

    def _handle_filter(self):
        self.refresh()

    def _open_add_to_trip_dialog(self, activity):
        if not self.user_trips:
            messagebox.showinfo("No Trips", "Create a trip first before assigning activities.")
            return

        # Find stops in user trips matching activity's city or any stop
        all_user_stops = []
        for t in self.user_trips:
            for s in t.stops:
                all_user_stops.append((t, s))

        if not all_user_stops:
            messagebox.showinfo("No Stops", "You have trips, but no destination stops added yet. Open Itinerary Builder to add a stop.")
            return

        win = ctk.CTkToplevel(self)
        win.title(f"Add {activity.name} to Trip Stop")
        win.geometry("450x380")
        win.configure(fg_color=THEME["bg_card"])
        win.grab_set()

        ctk.CTkLabel(win, text=f"Assign Activity: {activity.name}", font=FONTS["title_md"], text_color=THEME["text_primary"]).pack(padx=20, pady=(20, 8), anchor="w")

        ctk.CTkLabel(win, text="Select Trip & Stop *", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w", padx=20, pady=(6, 2))
        stop_choices = [f"{t.name} ➔ {s.city.name if s.city else 'Stop'} ({s.arrival_date.strftime('%b %d')})" for t, s in all_user_stops]
        stop_cb = ctk.CTkComboBox(win, values=stop_choices, height=36, font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"])
        stop_cb.pack(fill="x", padx=20, pady=(0, 12))

        # Time
        ctk.CTkLabel(win, text="Start Time (YYYY-MM-DD HH:MM)", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w", padx=20, pady=(4, 2))
        t_entry = ctk.CTkEntry(win, height=36, font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"])
        t_entry.insert(0, f"{datetime.now().strftime('%Y-%m-%d')} 10:00")
        t_entry.pack(fill="x", padx=20, pady=(0, 12))

        err_lbl = ctk.CTkLabel(win, text="", font=FONTS["body_sm"], text_color=THEME["danger"])
        err_lbl.pack(fill="x", padx=20, pady=(0, 4))

        def confirm():
            idx = stop_cb.get()
            selected_pair = next(((t, s) for t, s in all_user_stops if f"{t.name} ➔ {s.city.name if s.city else 'Stop'} ({s.arrival_date.strftime('%b %d')})" == idx), None)
            if not selected_pair:
                err_lbl.configure(text="Please choose a valid destination stop")
                return

            try:
                st = datetime.strptime(t_entry.get().strip(), "%Y-%m-%d %H:%M").replace(tzinfo=UTC)
                dur = getattr(activity, "duration_minutes", 120) or 120
                et = st + (timedelta(minutes=dur))

                t_obj, s_obj = selected_pair
                with self.session_factory() as session:
                    trip_service = TripService(session)
                    trip_service.add_activity(
                        t_obj.id,
                        self.current_user.id,
                        s_obj.id,
                        ActivityCreate(
                            name=activity.name,
                            description=activity.description,
                            activity_type=activity.activity_type.value if hasattr(activity.activity_type, "value") else str(activity.activity_type),
                            start_time=st,
                            end_time=et,
                            estimated_cost=activity.avg_cost or 0.0,
                        ),
                    )
                    session.commit()
                win.destroy()
                messagebox.showinfo("Success", f"'{activity.name}' added to {t_obj.name}!")
            except Exception as ex:
                err_lbl.configure(text=f"Error: {str(ex)}")

        ctk.CTkButton(win, text="Confirm & Add to Stop", height=38, font=FONTS["body_lg"], fg_color=THEME["primary"], hover_color=THEME["primary_hover"], command=confirm).pack(fill="x", padx=20, pady=10)

    def _open_create_activity_modal(self):
        win = ctk.CTkToplevel(self)
        win.title("Create Catalog Activity")
        win.geometry("460x480")
        win.configure(fg_color=THEME["bg_card"])
        win.grab_set()

        ctk.CTkLabel(win, text="Add New Activity to Catalog", font=FONTS["title_md"], text_color=THEME["text_primary"]).pack(padx=20, pady=(20, 8), anchor="w")

        ctk.CTkLabel(win, text="City *", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w", padx=20, pady=(4, 2))
        city_names = [f"{c.name}, {c.country}" for c in self.cities]
        city_cb = ctk.CTkComboBox(win, values=city_names, height=36, font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"])
        city_cb.pack(fill="x", padx=20, pady=(0, 8))

        ctk.CTkLabel(win, text="Activity Name *", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w", padx=20, pady=(4, 2))
        name_e = ctk.CTkEntry(win, placeholder_text="e.g. Traditional Cooking Masterclass", height=36, font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"])
        name_e.pack(fill="x", padx=20, pady=(0, 8))

        ctk.CTkLabel(win, text="Category *", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w", padx=20, pady=(4, 2))
        type_cb = ctk.CTkComboBox(win, values=["sightseeing", "food", "adventure", "culture", "nature", "nightlife", "shopping", "relaxation"], height=36, font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"])
        type_cb.pack(fill="x", padx=20, pady=(0, 8))

        ctk.CTkLabel(win, text="Average Cost (USD $)", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w", padx=20, pady=(4, 2))
        cost_e = ctk.CTkEntry(win, placeholder_text="e.g. 45", height=36, font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"])
        cost_e.insert(0, "25")
        cost_e.pack(fill="x", padx=20, pady=(0, 10))

        err_lbl = ctk.CTkLabel(win, text="", font=FONTS["body_sm"], text_color=THEME["danger"])
        err_lbl.pack(fill="x", padx=20, pady=(0, 4))

        def save():
            c_val = city_cb.get()
            selected_city = next((c for c in self.cities if f"{c.name}, {c.country}" == c_val), None)
            if not selected_city or not name_e.get().strip():
                err_lbl.configure(text="City and Activity name are required")
                return

            try:
                c_val = float(cost_e.get().strip() or 0)
                with self.session_factory() as session:
                    city_service = CityService(session)
                    city_service.create_activity(
                        ActivityCatalogCreate(
                            city_id=selected_city.id,
                            name=name_e.get().strip(),
                            activity_type=type_cb.get().lower(),
                            avg_cost=c_val,
                        )
                    )
                    session.commit()
                win.destroy()
                self.refresh()
            except Exception as ex:
                err_lbl.configure(text=f"Error: {str(ex)}")

        ctk.CTkButton(win, text="Save Activity", height=38, font=FONTS["body_lg"], fg_color=THEME["primary"], hover_color=THEME["primary_hover"], command=save).pack(fill="x", padx=20, pady=10)
