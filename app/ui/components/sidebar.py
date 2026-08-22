"""
Sidebar navigation — fixed left panel with nav pills, user pill, logout.
"""
import customtkinter as ctk
from app.ui.theme import THEME, FONTS, LAYOUT, SHAPE

# Nav item: (screen_key, emoji_icon, label)
_NAV_ITEMS = [
    ("dashboard",        "🏠", "Dashboard"),
    ("my_trips",         "✈️", "My Trips"),
    ("create_trip",      "➕", "Plan New Trip"),
    ("city_search",      "🏙️", "City Directory"),
    ("activity_search",  "🎟️", "Activities"),
    ("budget",           "💰", "Budget & Cost"),
    ("calendar",         "📅", "Calendar"),
    ("share",            "🔗", "Community"),
    ("profile",          "👤", "My Profile"),
]


class Sidebar(ctk.CTkFrame):
    def __init__(self, master, navigate_callback, current_user=None, **kwargs):
        super().__init__(
            master,
            fg_color=THEME["bg_sidebar"],
            width=LAYOUT["sidebar_width"],
            corner_radius=0,
            **kwargs,
        )
        self.navigate_callback = navigate_callback
        self.current_user = current_user
        self.buttons: dict[str, ctk.CTkButton] = {}
        self.active_tab = "dashboard"

        # prevent sidebar from shrinking to content
        self.pack_propagate(False)
        self.grid_propagate(False)

        self._build_ui()

    # ──────────────────────────────────────────────────────────────
    def _build_ui(self):
        # ── Brand ─────────────────────────────────────────────────
        brand = ctk.CTkFrame(self, fg_color="transparent")
        brand.pack(fill="x", padx=20, pady=(28, 20))

        logo_row = ctk.CTkFrame(brand, fg_color="transparent")
        logo_row.pack(fill="x")

        ctk.CTkLabel(logo_row, text="🌍", font=FONTS["title_xl"]).pack(side="left", padx=(0, 6))

        name_col = ctk.CTkFrame(logo_row, fg_color="transparent")
        name_col.pack(side="left")
        ctk.CTkLabel(name_col, text="GlobeTrotter", font=FONTS["title_md"], text_color=THEME["primary"]).pack(anchor="w")
        ctk.CTkLabel(name_col, text="Travel Studio", font=FONTS["caption"], text_color=THEME["text_muted"]).pack(anchor="w")

        # ── Divider ────────────────────────────────────────────────
        ctk.CTkFrame(self, height=1, fg_color=THEME["border"]).pack(fill="x", padx=16, pady=(0, 12))

        # ── Nav Section Label ─────────────────────────────────────
        ctk.CTkLabel(
            self,
            text="NAVIGATION",
            font=FONTS["badge"],
            text_color=THEME["text_muted"],
        ).pack(anchor="w", padx=20, pady=(0, 6))

        # ── Nav Items ─────────────────────────────────────────────
        nav_items = list(_NAV_ITEMS)

        # Admin check
        if self.current_user:
            role = getattr(self.current_user, "role", "")
            role_val = getattr(role, "value", str(role))
            is_admin = "admin" in str(role_val).lower() or "admin" in str(role).lower()
            if is_admin:
                nav_items.append(("admin", "📊", "Admin Analytics"))

        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        nav_frame.pack(fill="x", padx=10)

        for key, icon, label in nav_items:
            btn = ctk.CTkButton(
                nav_frame,
                text=f"  {icon}  {label}",
                font=FONTS["body"],
                anchor="w",
                height=40,
                corner_radius=SHAPE["small"],
                fg_color="transparent",
                text_color=THEME["text_secondary"],
                hover_color=THEME["bg_card_hover"],
                command=lambda k=key: self.set_active(k),
            )
            btn.pack(fill="x", pady=2)
            self.buttons[key] = btn

        # ── Spacer ────────────────────────────────────────────────
        ctk.CTkFrame(self, fg_color="transparent").pack(fill="both", expand=True)

        # ── Divider ────────────────────────────────────────────────
        ctk.CTkFrame(self, height=1, fg_color=THEME["border"]).pack(fill="x", padx=16, pady=(0, 8))

        # ── User Pill ─────────────────────────────────────────────
        pill = ctk.CTkFrame(
            self,
            fg_color=THEME["bg_card"],
            corner_radius=SHAPE["medium"],
            border_width=1,
            border_color=THEME["border"],
        )
        pill.pack(fill="x", padx=12, pady=(0, 16))

        row = ctk.CTkFrame(pill, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=10)

        # Avatar circle
        user_name = "Traveler"
        user_email = ""
        if self.current_user:
            user_name = getattr(self.current_user, "full_name", None) or getattr(self.current_user, "email", "Traveler")
            user_email = getattr(self.current_user, "email", "")

        initial = (user_name[0] if user_name else "T").upper()
        avatar = ctk.CTkLabel(
            row,
            text=initial,
            font=FONTS["body_lg"],
            fg_color=THEME["primary"],
            text_color=THEME["on_primary"],
            corner_radius=SHAPE["full"],
            width=36,
            height=36,
        )
        avatar.pack(side="left", padx=(0, 10))

        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(
            info,
            text=user_name[:22],
            font=FONTS["body_sm"],
            text_color=THEME["text_primary"],
            anchor="w",
        ).pack(anchor="w")
        if user_email:
            ctk.CTkLabel(
                info,
                text=user_email[:26],
                font=FONTS["caption"],
                text_color=THEME["text_muted"],
                anchor="w",
            ).pack(anchor="w")

        ctk.CTkButton(
            pill,
            text="🚪  Log Out",
            font=FONTS["badge"],
            height=28,
            corner_radius=SHAPE["small"],
            fg_color=THEME["danger_bg"],
            hover_color=THEME["danger"],
            text_color=THEME["danger"],
            border_width=1,
            border_color=THEME["danger"],
            command=lambda: self.navigate_callback("logout"),
        ).pack(fill="x", padx=12, pady=(0, 10))

        # Set default active
        self.set_active("dashboard", notify=False)

    # ──────────────────────────────────────────────────────────────
    def set_active(self, tab_key: str, notify: bool = True):
        self.active_tab = tab_key
        for k, btn in self.buttons.items():
            if k == tab_key:
                btn.configure(
                    fg_color=THEME["primary_container"],
                    text_color=THEME["on_primary_container"],
                    border_width=1,
                    border_color=THEME["primary"],
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=THEME["text_secondary"],
                    border_width=0,
                )
        if notify:
            self.navigate_callback(tab_key)
