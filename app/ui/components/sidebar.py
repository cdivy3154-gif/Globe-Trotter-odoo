import customtkinter as ctk
from app.ui.theme import THEME, FONTS


class Sidebar(ctk.CTkFrame):
    def __init__(self, master, navigate_callback, current_user=None, **kwargs):
        super().__init__(master, fg_color=THEME["bg_sidebar"], width=230, corner_radius=0, **kwargs)
        self.navigate_callback = navigate_callback
        self.current_user = current_user
        self.buttons = {}
        self.active_tab = "dashboard"

        self.grid_rowconfigure(10, weight=1)
        self._build_ui()

    def _build_ui(self):
        # Brand Logo / Title
        brand_frame = ctk.CTkFrame(self, fg_color="transparent")
        brand_frame.grid(row=0, column=0, padx=20, pady=(24, 20), sticky="w")

        logo_label = ctk.CTkLabel(
            brand_frame,
            text="🌍 GlobeTrotter",
            font=FONTS["title_md"],
            text_color=THEME["primary"],
        )
        logo_label.pack(anchor="w")

        sub_label = ctk.CTkLabel(
            brand_frame,
            text="Personalized Travel Studio",
            font=FONTS["body_sm"],
            text_color=THEME["text_muted"],
        )
        sub_label.pack(anchor="w")

        # Divider
        sep = ctk.CTkFrame(self, height=1, fg_color=THEME["border"])
        sep.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="ew")

        # Navigation items
        nav_items = [
            ("dashboard", "🏠  Dashboard"),
            ("my_trips", "✈️  My Trips"),
            ("create_trip", "➕  Plan New Trip"),
            ("city_search", "🏙️  City Directory"),
            ("activity_search", "🎟️  Activities"),
            ("budget", "💰  Budget & Cost"),
            ("calendar", "📅  Calendar Timeline"),
            ("share", "🔗  Shared Trips"),
            ("profile", "👤  My Profile"),
        ]

        # Add admin option if user is admin
        is_admin = False
        if self.current_user:
            role = getattr(self.current_user, "role", "")
            is_admin = (str(role).lower() == "admin" or str(getattr(role, "value", "")).lower() == "admin")

        if is_admin:
            nav_items.append(("admin", "📊  Admin Analytics"))

        row = 2
        for key, label in nav_items:
            btn = ctk.CTkButton(
                self,
                text=label,
                font=FONTS["body"],
                anchor="w",
                height=38,
                corner_radius=8,
                fg_color="transparent",
                text_color=THEME["text_secondary"],
                hover_color=THEME["bg_card_hover"],
                command=lambda k=key: self.set_active(k),
            )
            btn.grid(row=row, column=0, padx=12, pady=3, sticky="ew")
            self.buttons[key] = btn
            row += 1

        # Bottom section: user pill & logout
        bottom_frame = ctk.CTkFrame(self, fg_color=THEME["bg_card"], corner_radius=10)
        bottom_frame.grid(row=11, column=0, padx=12, pady=16, sticky="ew")

        user_name = "Traveler"
        user_email = ""
        if self.current_user:
            user_name = getattr(self.current_user, "full_name", None) or getattr(self.current_user, "email", "Traveler")
            user_email = getattr(self.current_user, "email", "")

        u_label = ctk.CTkLabel(
            bottom_frame,
            text=f"👤 {user_name}",
            font=FONTS["body_lg"],
            text_color=THEME["text_primary"],
        )
        u_label.pack(padx=10, pady=(8, 2), anchor="w")

        if user_email:
            e_label = ctk.CTkLabel(
                bottom_frame,
                text=user_email,
                font=FONTS["body_sm"],
                text_color=THEME["text_muted"],
            )
            e_label.pack(padx=10, pady=(0, 6), anchor="w")

        logout_btn = ctk.CTkButton(
            bottom_frame,
            text="Log Out",
            font=FONTS["body_sm"],
            height=28,
            corner_radius=6,
            fg_color=THEME["danger_bg"],
            hover_color=THEME["danger"],
            text_color=THEME["text_primary"],
            command=lambda: self.navigate_callback("logout"),
        )
        logout_btn.pack(padx=10, pady=(4, 8), fill="x")

        # Set default active
        self.set_active("dashboard", notify=False)

    def set_active(self, tab_key: str, notify: bool = True):
        self.active_tab = tab_key
        for k, btn in self.buttons.items():
            if k == tab_key:
                btn.configure(
                    fg_color=THEME["primary"],
                    text_color=THEME["text_on_primary"],
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=THEME["text_secondary"],
                )
        if notify:
            self.navigate_callback(tab_key)
