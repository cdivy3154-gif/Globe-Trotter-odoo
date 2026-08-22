import customtkinter as ctk
from datetime import datetime, timedelta, UTC
from tkinter import filedialog
from app.ui.theme import THEME, FONTS
from app.ui.components.header import Header
from app.services.trip_service import TripService
from app.services.city_service import CityService
from app.services.upload_service import UploadService
from app.schemas.trip import TripCreate, StopCreate
from app.schemas.city import CitySearchParams
from app.core.exceptions import AppException


class CreateTripScreen(ctk.CTkScrollableFrame):
    def __init__(self, master, navigate_callback, session_factory, current_user, initial_city_id=None, **kwargs):
        super().__init__(master, fg_color=THEME["bg_dark"], **kwargs)
        self.navigate_callback = navigate_callback
        self.session_factory = session_factory
        self.current_user = current_user
        self.initial_city_id = initial_city_id
        self.selected_cover_path = None
        self.cities = []
        self._build_ui()

    def _build_ui(self):
        # Fetch cities for optional first stop
        with self.session_factory() as session:
            city_service = CityService(session)
            self.cities, _ = city_service.search_cities(CitySearchParams(limit=100))

        header = Header(
            self,
            title="Plan a New Journey 🚀",
            subtitle="Define your trip dates, destination goals, and overall budget.",
        )
        header.pack(fill="x", padx=20, pady=(15, 10))

        # Main Form Container Card
        card = ctk.CTkFrame(self, fg_color=THEME["bg_card"], corner_radius=14, border_width=1, border_color=THEME["border"])
        card.pack(fill="x", padx=20, pady=10)

        # 1. Trip Name
        ctk.CTkLabel(card, text="Trip Name *", font=FONTS["body_lg"], text_color=THEME["text_primary"]).pack(anchor="w", padx=20, pady=(20, 2))
        self.name_entry = ctk.CTkEntry(card, placeholder_text="e.g. Grand European Summer Tour, Tokyo & Kyoto Express", height=38, font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"])
        self.name_entry.pack(fill="x", padx=20, pady=(0, 14))

        # 2. Date Range Row
        dates_row = ctk.CTkFrame(card, fg_color="transparent")
        dates_row.pack(fill="x", padx=20, pady=(0, 14))
        dates_row.grid_columnconfigure((0, 1), weight=1)

        # Start Date
        ctk.CTkLabel(dates_row, text="Start Date (YYYY-MM-DD) *", font=FONTS["body_lg"], text_color=THEME["text_primary"]).grid(row=0, column=0, sticky="w", padx=(0, 10), pady=(0, 2))
        today_str = datetime.now().strftime("%Y-%m-%d")
        self.start_date_entry = ctk.CTkEntry(dates_row, placeholder_text="YYYY-MM-DD", height=38, font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"])
        self.start_date_entry.insert(0, today_str)
        self.start_date_entry.grid(row=1, column=0, sticky="ew", padx=(0, 10))

        # End Date
        ctk.CTkLabel(dates_row, text="End Date (YYYY-MM-DD) *", font=FONTS["body_lg"], text_color=THEME["text_primary"]).grid(row=0, column=1, sticky="w", padx=(10, 0), pady=(0, 2))
        next_week_str = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        self.end_date_entry = ctk.CTkEntry(dates_row, placeholder_text="YYYY-MM-DD", height=38, font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"])
        self.end_date_entry.insert(0, next_week_str)
        self.end_date_entry.grid(row=1, column=1, sticky="ew", padx=(10, 0))

        # 3. Budget Target & Starting City
        mid_row = ctk.CTkFrame(card, fg_color="transparent")
        mid_row.pack(fill="x", padx=20, pady=(0, 14))
        mid_row.grid_columnconfigure((0, 1), weight=1)

        # Budget
        ctk.CTkLabel(mid_row, text="Total Estimated Budget (USD $)", font=FONTS["body_lg"], text_color=THEME["text_primary"]).grid(row=0, column=0, sticky="w", padx=(0, 10), pady=(0, 2))
        self.budget_entry = ctk.CTkEntry(mid_row, placeholder_text="e.g. 2500", height=38, font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"])
        self.budget_entry.grid(row=1, column=0, sticky="ew", padx=(0, 10))

        # Starting City
        ctk.CTkLabel(mid_row, text="First Destination (Optional)", font=FONTS["body_lg"], text_color=THEME["text_primary"]).grid(row=0, column=1, sticky="w", padx=(10, 0), pady=(0, 2))
        city_names = ["(Select later in builder)"] + [f"{c.name}, {c.country}" for c in self.cities]
        self.city_combo = ctk.CTkComboBox(mid_row, values=city_names, height=38, font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"])
        
        # If pre-selected city
        if self.initial_city_id:
            for idx, c in enumerate(self.cities):
                if c.id == self.initial_city_id:
                    self.city_combo.set(f"{c.name}, {c.country}")
                    break
        self.city_combo.grid(row=1, column=1, sticky="ew", padx=(10, 0))

        # 4. Description
        ctk.CTkLabel(card, text="Trip Description & Notes", font=FONTS["body_lg"], text_color=THEME["text_primary"]).pack(anchor="w", padx=20, pady=(0, 2))
        self.desc_textbox = ctk.CTkTextbox(card, height=80, font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"], border_width=1)
        self.desc_textbox.pack(fill="x", padx=20, pady=(0, 14))

        # 5. Cover Photo File Picker
        cover_row = ctk.CTkFrame(card, fg_color="transparent")
        cover_row.pack(fill="x", padx=20, pady=(0, 20))

        self.cover_label = ctk.CTkLabel(cover_row, text="Cover Photo: None selected", font=FONTS["body_sm"], text_color=THEME["text_secondary"])
        self.cover_label.pack(side="left", padx=(0, 10))

        pick_btn = ctk.CTkButton(
            cover_row,
            text="🖼️ Choose Image...",
            font=FONTS["body_sm"],
            height=32,
            fg_color=THEME["border"],
            hover_color=THEME["bg_card_hover"],
            command=self._pick_cover_file,
        )
        pick_btn.pack(side="left")

        # Status / Error Banner
        self.error_label = ctk.CTkLabel(card, text="", font=FONTS["body"], text_color=THEME["danger"])
        self.error_label.pack(fill="x", padx=20, pady=(0, 8))

        # Action Buttons
        btn_bar = ctk.CTkFrame(card, fg_color="transparent")
        btn_bar.pack(fill="x", padx=20, pady=(0, 24))

        save_btn = ctk.CTkButton(
            btn_bar,
            text="🚀 Create Trip & Open Itinerary Builder",
            font=FONTS["body_lg"],
            height=42,
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            command=self._handle_create,
        )
        save_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))

        cancel_btn = ctk.CTkButton(
            btn_bar,
            text="Cancel",
            font=FONTS["body_lg"],
            height=42,
            width=100,
            fg_color=THEME["border"],
            hover_color=THEME["bg_card_hover"],
            command=lambda: self.navigate_callback("dashboard"),
        )
        cancel_btn.pack(side="right")

    def _pick_cover_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Trip Cover Photo",
            filetypes=[("Image Files", "*.jpg *.jpeg *.png *.webp"), ("All Files", "*.*")],
        )
        if file_path:
            self.selected_cover_path = file_path
            self.cover_label.configure(text=f"Cover Photo: {file_path.split('/')[-1].split('\\')[-1]}", text_color=THEME["success"])

    def _handle_create(self):
        name = self.name_entry.get().strip()
        s_date_str = self.start_date_entry.get().strip()
        e_date_str = self.end_date_entry.get().strip()
        desc = self.desc_textbox.get("1.0", "end-1c").strip()
        budget_str = self.budget_entry.get().strip()
        selected_city_label = self.city_combo.get()

        if not name:
            self.error_label.configure(text="Please provide a trip name")
            return

        try:
            s_date = datetime.strptime(s_date_str, "%Y-%m-%d").replace(tzinfo=UTC)
            e_date = datetime.strptime(e_date_str, "%Y-%m-%d").replace(tzinfo=UTC)
        except ValueError:
            self.error_label.configure(text="Dates must be in YYYY-MM-DD format")
            return

        if s_date > e_date:
            self.error_label.configure(text="Start date cannot be after end date")
            return

        budget_val = None
        if budget_str:
            try:
                budget_val = float(budget_str)
                if budget_val < 0:
                    raise ValueError
            except ValueError:
                self.error_label.configure(text="Budget must be a positive number")
                return

        try:
            with self.session_factory() as session:
                trip_service = TripService(session)
                upload_service = UploadService()

                # Create trip
                trip_data = TripCreate(
                    name=name,
                    description=desc if desc else None,
                    start_date=s_date,
                    end_date=e_date,
                    total_budget=budget_val,
                )
                new_trip = trip_service.create_trip(self.current_user.id, trip_data)

                # If cover photo chosen, save it
                if self.selected_cover_path:
                    try:
                        saved_path = upload_service.save_trip_cover(new_trip.id, self.selected_cover_path)
                        new_trip.cover_photo_path = saved_path
                        session.flush()
                    except Exception:
                        pass

                # If first city was chosen, add as initial stop
                if selected_city_label and selected_city_label != "(Select later in builder)":
                    for city in self.cities:
                        if f"{city.name}, {city.country}" == selected_city_label:
                            stop_data = StopCreate(
                                city_id=city.id,
                                arrival_date=s_date,
                                departure_date=e_date,
                                stop_order=1,
                            )
                            trip_service.add_stop(new_trip.id, self.current_user.id, stop_data)
                            break

                session.commit()
                # Redirect directly to interactive Itinerary Builder for this trip
                self.navigate_callback("itinerary_builder", trip_id=new_trip.id)
        except AppException as ae:
            self.error_label.configure(text=str(ae.detail))
        except Exception as ex:
            self.error_label.configure(text=f"Failed to create trip: {str(ex)}")
