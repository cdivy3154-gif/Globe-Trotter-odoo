import customtkinter as ctk
from app.ui.theme import THEME, FONTS
from app.ui.components.header import Header
from app.ui.components.cards import TripCard
from app.services.trip_service import TripService
from tkinter import messagebox


class MyTripsScreen(ctk.CTkScrollableFrame):
    def __init__(self, master, navigate_callback, session_factory, current_user, **kwargs):
        super().__init__(master, fg_color=THEME["bg_dark"], **kwargs)
        self.navigate_callback = navigate_callback
        self.session_factory = session_factory
        self.current_user = current_user
        self.grid_columnconfigure(0, weight=1)
        self.search_query = ""
        self.refresh()

    def refresh(self):
        for widget in self.winfo_children():
            widget.destroy()

        header = Header(
            self,
            title="My Travel Journeys 🎒",
            subtitle="Manage, edit, customize, and share all your personalized itineraries.",
            action_button=("➕  New Trip", lambda: self.navigate_callback("create_trip"), THEME["primary"]),
        )
        header.pack(fill="x", padx=20, pady=(15, 10))

        # Search Bar
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.pack(fill="x", padx=20, pady=(0, 15))

        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="🔍 Search trips by name or destination...",
            height=38,
            font=FONTS["body"],
            fg_color=THEME["bg_card"],
            border_color=THEME["border"],
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        if self.search_query:
            self.search_entry.insert(0, self.search_query)

        search_btn = ctk.CTkButton(
            search_frame,
            text="Filter",
            font=FONTS["body_sm"],
            height=38,
            width=80,
            fg_color=THEME["border"],
            hover_color=THEME["bg_card_hover"],
            command=self._handle_search,
        )
        search_btn.pack(side="right")

        # Fetch Trips
        trips = []
        with self.session_factory() as session:
            trip_service = TripService(session)
            trips = trip_service.list_trips(self.current_user.id, limit=100)

        # Apply search filter if present
        if self.search_query:
            q = self.search_query.lower()
            trips = [
                t for t in trips
                if q in t.name.lower() or any(q in (s.city.name.lower() if s.city else "") for s in t.stops)
            ]

        # Render Trips Grid
        if trips:
            grid_frame = ctk.CTkFrame(self, fg_color="transparent")
            grid_frame.pack(fill="x", padx=20, pady=5)
            grid_frame.grid_columnconfigure((0, 1), weight=1)

            for idx, trip in enumerate(trips):
                card = TripCard(
                    grid_frame,
                    trip=trip,
                    on_view=lambda t: self.navigate_callback("itinerary_builder", trip_id=t.id),
                    on_share=lambda t: self.navigate_callback("share", trip_id=t.id),
                    on_delete=lambda t: self._handle_delete(t),
                    height=185,
                )
                r, c = divmod(idx, 2)
                card.grid(row=r, column=c, padx=6, pady=6, sticky="ew")
        else:
            empty_frame = ctk.CTkFrame(self, fg_color=THEME["bg_card"], corner_radius=12, border_width=1, border_color=THEME["border"])
            empty_frame.pack(fill="x", padx=20, pady=30)
            ctk.CTkLabel(empty_frame, text="🔍 No trips found", font=FONTS["title_md"], text_color=THEME["text_secondary"]).pack(pady=(30, 6))
            ctk.CTkLabel(empty_frame, text="Try clearing your search query or create a brand new adventure.", font=FONTS["body_sm"], text_color=THEME["text_muted"]).pack(pady=(0, 20))
            ctk.CTkButton(empty_frame, text="➕ Create a New Trip", font=FONTS["body_lg"], height=38, fg_color=THEME["primary"], hover_color=THEME["primary_hover"], command=lambda: self.navigate_callback("create_trip")).pack(pady=(0, 30))

    def _handle_search(self):
        self.search_query = self.search_entry.get().strip()
        self.refresh()

    def _handle_delete(self, trip):
        confirm = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete '{trip.name}'?\nThis will remove all stops and planned activities.")
        if confirm:
            try:
                with self.session_factory() as session:
                    trip_service = TripService(session)
                    trip_service.delete_trip(trip.id, self.current_user.id)
                    session.commit()
                self.refresh()
            except Exception as ex:
                messagebox.showerror("Error", f"Failed to delete trip: {str(ex)}")
