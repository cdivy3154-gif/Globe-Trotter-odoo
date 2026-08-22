import customtkinter as ctk
from app.ui.theme import THEME, LAYOUT
from app.ui.components.sidebar import Sidebar
from app.ui.screens.login_screen import LoginScreen
from app.ui.screens.dashboard_screen import DashboardScreen
from app.ui.screens.create_trip_screen import CreateTripScreen
from app.ui.screens.my_trips_screen import MyTripsScreen
from app.ui.screens.itinerary_builder_screen import ItineraryBuilderScreen
from app.ui.screens.itinerary_view_screen import ItineraryViewScreen
from app.ui.screens.city_search_screen import CitySearchScreen
from app.ui.screens.activity_search_screen import ActivitySearchScreen
from app.ui.screens.budget_screen import BudgetScreen
from app.ui.screens.calendar_screen import CalendarScreen
from app.ui.screens.share_screen import ShareScreen
from app.ui.screens.profile_screen import ProfileScreen
from app.ui.screens.admin_screen import AdminScreen
from app.core.database import SessionLocal, init_db
from app.scripts.seed_cities import seed_database


class GlobeTrotterApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.title("GlobeTrotter — Personalized Travel Planning Studio")
        self.geometry("1360x860")
        self.minsize(1100, 720)
        self.configure(fg_color=THEME["bg_dark"])

        # Database session factory
        self.session_factory = SessionLocal
        self.current_user = None

        # Container root
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._ensure_seed_data()
        self._show_login()

    def _ensure_seed_data(self):
        """Auto-seed initial demo dataset if database is freshly created."""
        init_db()
        try:
            with self.session_factory() as session:
                seed_database(session)
        except Exception:
            pass

    def _show_login(self):
        self.current_user = None
        for widget in self.winfo_children():
            widget.destroy()

        self.login_screen = LoginScreen(
            self,
            on_login_success=self._on_login_success,
            session_factory=self.session_factory,
        )
        self.login_screen.grid(row=0, column=0, sticky="nsew")

    def _on_login_success(self, user):
        self.current_user = user
        self._build_main_layout()
        self.navigate("dashboard")

    def _build_main_layout(self):
        for widget in self.winfo_children():
            widget.destroy()

        self.grid_columnconfigure(0, weight=0)  # Sidebar fixed
        self.grid_columnconfigure(1, weight=1)  # Main Content expands
        self.grid_rowconfigure(0, weight=1)

        # Left Sidebar
        self.sidebar = Sidebar(
            self,
            navigate_callback=self.navigate,
            current_user=self.current_user,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        # Right Main Content Area
        self.content_container = ctk.CTkFrame(self, fg_color=THEME["bg_dark"], corner_radius=0)
        self.content_container.grid(row=0, column=1, sticky="nsew")
        self.content_container.grid_columnconfigure(0, weight=1)
        self.content_container.grid_rowconfigure(0, weight=1)

    def navigate(self, screen_key: str, **kwargs):
        if screen_key == "logout":
            self._show_login()
            return

        # Clear existing active screen in content container
        for widget in self.content_container.winfo_children():
            widget.destroy()

        screen_widget = None

        if screen_key == "dashboard":
            screen_widget = DashboardScreen(self.content_container, self.navigate, self.session_factory, self.current_user)
        elif screen_key == "my_trips":
            screen_widget = MyTripsScreen(self.content_container, self.navigate, self.session_factory, self.current_user)
        elif screen_key == "create_trip":
            city_id = kwargs.get("city_id")
            screen_widget = CreateTripScreen(self.content_container, self.navigate, self.session_factory, self.current_user, initial_city_id=city_id)
        elif screen_key == "itinerary_builder":
            trip_id = kwargs.get("trip_id")
            screen_widget = ItineraryBuilderScreen(self.content_container, self.navigate, self.session_factory, self.current_user, trip_id=trip_id)
        elif screen_key == "itinerary_view":
            trip_id = kwargs.get("trip_id")
            screen_widget = ItineraryViewScreen(self.content_container, self.navigate, self.session_factory, self.current_user, trip_id=trip_id)
        elif screen_key == "city_search":
            screen_widget = CitySearchScreen(self.content_container, self.navigate, self.session_factory, self.current_user)
        elif screen_key == "activity_search":
            screen_widget = ActivitySearchScreen(self.content_container, self.navigate, self.session_factory, self.current_user)
        elif screen_key == "budget":
            trip_id = kwargs.get("trip_id")
            screen_widget = BudgetScreen(self.content_container, self.navigate, self.session_factory, self.current_user, trip_id=trip_id)
        elif screen_key == "calendar":
            trip_id = kwargs.get("trip_id")
            screen_widget = CalendarScreen(self.content_container, self.navigate, self.session_factory, self.current_user, trip_id=trip_id)
        elif screen_key == "share":
            trip_id = kwargs.get("trip_id")
            screen_widget = ShareScreen(self.content_container, self.navigate, self.session_factory, self.current_user, trip_id=trip_id)
        elif screen_key == "profile":
            screen_widget = ProfileScreen(self.content_container, self.navigate, self.session_factory, self.current_user)
        elif screen_key == "admin":
            screen_widget = AdminScreen(self.content_container, self.navigate, self.session_factory, self.current_user)

        if screen_widget:
            screen_widget.grid(row=0, column=0, sticky="nsew")


def run_app():
    app = GlobeTrotterApp()
    app.mainloop()


if __name__ == "__main__":
    run_app()
