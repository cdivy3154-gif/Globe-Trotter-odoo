"""
Phase 9c — Admin Dashboard Screen
Features:
  - Access guard: redirects non-admin users
  - 4 platform MetricCards: Users, Trips, Cities, Activities
  - Top cities bar chart
  - Users table (email, name, role, trips count, joined)
  - All Trips table (name, owner email, stops, visibility, date)
  - Role badge highlight
"""
import customtkinter as ctk
from app.ui.theme import THEME, FONTS, SHAPE, LAYOUT
from app.ui.components.header import Header
from app.ui.components.cards import MetricCard, EmptyState
from app.services.admin_service import AdminService

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    _HAS_MPL = True
except ImportError:
    _HAS_MPL = False


def _pct_bar(parent, value: float, maximum: float, color: str, label=""):
    row = ctk.CTkFrame(parent, fg_color="transparent")
    row.pack(fill="x", pady=3)
    row.grid_columnconfigure(1, weight=1)
    ctk.CTkLabel(row, text=label, font=FONTS["body_sm"], text_color=THEME["text_secondary"], width=140, anchor="w").grid(row=0, column=0, sticky="w")
    bg = ctk.CTkFrame(row, height=8, fg_color=THEME["bg_input"], corner_radius=SHAPE["full"])
    bg.grid(row=0, column=1, sticky="ew", padx=8)
    pct = min(value / maximum, 1.0) if maximum > 0 else 0
    if pct > 0:
        ctk.CTkFrame(bg, height=8, fg_color=color, corner_radius=SHAPE["full"]).place(relx=0, rely=0, relwidth=pct, relheight=1)
    ctk.CTkLabel(row, text=str(int(value)), font=FONTS["body_sm"], text_color=THEME["text_primary"], width=40, anchor="e").grid(row=0, column=2)


# ══════════════════════════════════════════════════════════════════
class AdminScreen(ctk.CTkScrollableFrame):
    def __init__(self, master, navigate_callback, session_factory, current_user, **kwargs):
        super().__init__(
            master, fg_color=THEME["bg_dark"],
            scrollbar_button_color=THEME["border"],
            scrollbar_button_hover_color=THEME["border_light"],
            **kwargs,
        )
        self.navigate_callback = navigate_callback
        self.session_factory   = session_factory
        self.current_user      = current_user
        self.grid_columnconfigure(0, weight=1)
        self.refresh()

    # ─────────────────────────────────────────────────────────────
    def refresh(self):
        for w in self.winfo_children():
            w.destroy()

        role = getattr(self.current_user, "role", "")
        role_val = getattr(role, "value", str(role))
        is_admin = "admin" in str(role_val).lower() or "admin" in str(role).lower()

        if not is_admin:
            Header(self, title="Admin Panel 📊", breadcrumb=["Dashboard", "Admin"]).pack(fill="x", padx=20, pady=(18, 10))
            EmptyState(self, icon="🚫", title="Access Denied", message="Admin privileges required to view this page.").pack(fill="x", padx=20, pady=40)
            return

        with self.session_factory() as session:
            svc     = AdminService(session)
            stats   = svc.get_stats()
            users   = svc.list_users(limit=100)
            trips   = svc.list_all_trips(limit=100)

        Header(
            self,
            title="Admin & Platform Analytics 📊",
            subtitle="Monitor user growth, popular destinations, activity trends, and all platform data.",
            breadcrumb=["Dashboard", "Admin"],
        ).pack(fill="x", padx=20, pady=(18, 10))

        # ── Metric cards ──────────────────────────────────────────
        mrow = ctk.CTkFrame(self, fg_color="transparent")
        mrow.pack(fill="x", padx=20, pady=(0, 10))
        mrow.grid_columnconfigure((0, 1, 2, 3), weight=1)

        for i, (title, val, icon, color) in enumerate([
            ("Total Users",      str(stats.total_users),      "👤",  THEME["primary"]),
            ("Total Trips",      str(stats.total_trips),      "✈️",  THEME["accent"]),
            ("Cities",           str(stats.total_cities),     "🏙️",  THEME["info"]),
            ("Activities",       str(stats.total_activities), "🎟️",  THEME["chart_3"]),
        ]):
            MetricCard(mrow, title=title, value=val, icon=icon, subtitle="platform-wide", accent_color=color).grid(
                row=0, column=i, padx=(0 if i == 0 else 6, 6 if i < 3 else 0), sticky="ew"
            )

        # ── Top cities chart ──────────────────────────────────────
        top_cities = getattr(stats, "top_cities", []) or []
        if top_cities:
            self._build_top_cities(top_cities)

        # ── Users table ───────────────────────────────────────────
        self._build_users_table(users)

        # ── Trips table ───────────────────────────────────────────
        self._build_trips_table(trips)

    # ─────────────────────────────────────────────────────────────
    def _build_top_cities(self, top_cities):
        sec = ctk.CTkFrame(self, fg_color=THEME["bg_card"], corner_radius=SHAPE["medium"], border_width=1, border_color=THEME["border"])
        sec.pack(fill="x", padx=20, pady=(0, 10))
        ctk.CTkFrame(sec, height=3, fg_color=THEME["accent"], corner_radius=0).pack(fill="x")
        ctk.CTkLabel(sec, text="🏆  Top Destinations by Stop Count", font=FONTS["title_sm"], text_color=THEME["text_primary"]).pack(anchor="w", padx=20, pady=(14, 8))

        max_cnt = max((c.stop_count for c in top_cities), default=1)
        bar_area = ctk.CTkFrame(sec, fg_color="transparent")
        bar_area.pack(fill="x", padx=20, pady=(0, 14))

        colors = [THEME["chart_1"], THEME["chart_2"], THEME["chart_3"], THEME["chart_4"], THEME["chart_5"]]
        for i, city in enumerate(top_cities[:10]):
            name = f"{city.city_name}, {city.country}" if hasattr(city, "country") else city.city_name
            _pct_bar(bar_area, float(city.stop_count), float(max_cnt), colors[i % 5], label=name[:22])

    # ─────────────────────────────────────────────────────────────
    def _build_users_table(self, users: list):
        sec = ctk.CTkFrame(self, fg_color=THEME["bg_card"], corner_radius=SHAPE["medium"], border_width=1, border_color=THEME["border"])
        sec.pack(fill="x", padx=20, pady=(0, 10))
        ctk.CTkFrame(sec, height=3, fg_color=THEME["primary"], corner_radius=0).pack(fill="x")
        ctk.CTkLabel(sec, text=f"👤  All Users  ({len(users)})", font=FONTS["title_sm"], text_color=THEME["text_primary"]).pack(anchor="w", padx=20, pady=(14, 6))

        # Column headers
        cols = ["Email", "Full Name", "Role", "Joined"]
        hdr = ctk.CTkFrame(sec, fg_color=THEME["bg_input"], corner_radius=SHAPE["extra_small"])
        hdr.pack(fill="x", padx=20, pady=(0, 4))
        for j, col in enumerate(cols):
            hdr.grid_columnconfigure(j, weight=1)
            ctk.CTkLabel(hdr, text=col, font=FONTS["badge"], text_color=THEME["text_muted"]).grid(row=0, column=j, padx=12, pady=6, sticky="w")

        for i, user in enumerate(users):
            bg = "transparent" if i % 2 == 0 else THEME["bg_input"]
            row = ctk.CTkFrame(sec, fg_color=bg, corner_radius=SHAPE["extra_small"])
            row.pack(fill="x", padx=20, pady=1)
            for j, (weight,) in enumerate([(1,)] * 4):
                row.grid_columnconfigure(j, weight=1)

            ctk.CTkLabel(row, text=user.email, font=FONTS["body_sm"], text_color=THEME["text_secondary"]).grid(row=0, column=0, padx=12, pady=5, sticky="w")
            ctk.CTkLabel(row, text=user.full_name or "—", font=FONTS["body_sm"], text_color=THEME["text_primary"]).grid(row=0, column=1, padx=12, pady=5, sticky="w")
            role_str = str(getattr(user, "role", "user") or "user")
            role_val  = getattr(user.role, "value", role_str) if hasattr(user.role, "value") else role_str
            is_admin  = role_val.lower() == "admin"
            ctk.CTkLabel(row, text=role_val.title(), font=FONTS["badge"], fg_color=THEME["primary"] if is_admin else THEME["bg_card"], text_color=THEME["on_primary"] if is_admin else THEME["text_muted"], corner_radius=SHAPE["full"]).grid(row=0, column=2, padx=12, pady=5, sticky="w")
            joined = getattr(user, "created_at", None)
            joined_str = joined.strftime("%b %d, %Y") if joined else "—"
            ctk.CTkLabel(row, text=joined_str, font=FONTS["body_sm"], text_color=THEME["text_muted"]).grid(row=0, column=3, padx=12, pady=5, sticky="w")

        ctk.CTkFrame(sec, height=12, fg_color="transparent").pack()

    # ─────────────────────────────────────────────────────────────
    def _build_trips_table(self, trips: list):
        sec = ctk.CTkFrame(self, fg_color=THEME["bg_card"], corner_radius=SHAPE["medium"], border_width=1, border_color=THEME["border"])
        sec.pack(fill="x", padx=20, pady=(0, 24))
        ctk.CTkFrame(sec, height=3, fg_color=THEME["chart_4"], corner_radius=0).pack(fill="x")
        ctk.CTkLabel(sec, text=f"✈️  All Trips  ({len(trips)})", font=FONTS["title_sm"], text_color=THEME["text_primary"]).pack(anchor="w", padx=20, pady=(14, 6))

        cols = ["Trip Name", "Owner", "Stops", "Visibility", "Start Date"]
        hdr = ctk.CTkFrame(sec, fg_color=THEME["bg_input"], corner_radius=SHAPE["extra_small"])
        hdr.pack(fill="x", padx=20, pady=(0, 4))
        for j, col in enumerate(cols):
            hdr.grid_columnconfigure(j, weight=1)
            ctk.CTkLabel(hdr, text=col, font=FONTS["badge"], text_color=THEME["text_muted"]).grid(row=0, column=j, padx=12, pady=6, sticky="w")

        for i, trip in enumerate(trips):
            bg  = "transparent" if i % 2 == 0 else THEME["bg_input"]
            row = ctk.CTkFrame(sec, fg_color=bg, corner_radius=SHAPE["extra_small"])
            row.pack(fill="x", padx=20, pady=1)
            for j in range(5):
                row.grid_columnconfigure(j, weight=1)

            ctk.CTkLabel(row, text=trip.name[:30], font=FONTS["body_sm"], text_color=THEME["text_primary"]).grid(row=0, column=0, padx=12, pady=5, sticky="w")
            owner = getattr(trip, "user", None)
            owner_email = owner.email if owner else "—"
            ctk.CTkLabel(row, text=owner_email[:24], font=FONTS["body_sm"], text_color=THEME["text_muted"]).grid(row=0, column=1, padx=12, pady=5, sticky="w")
            ctk.CTkLabel(row, text=str(len(trip.stops)), font=FONTS["body_sm"], text_color=THEME["text_secondary"]).grid(row=0, column=2, padx=12, pady=5, sticky="w")

            vis = str(getattr(trip, "visibility", "") or "")
            vis_val = getattr(trip.visibility, "value", vis) if hasattr(trip.visibility, "value") else vis
            is_pub  = vis_val.lower() == "public"
            ctk.CTkLabel(row, text=vis_val.title(), font=FONTS["badge"], fg_color=THEME["success_bg"] if is_pub else THEME["bg_card"], text_color=THEME["success"] if is_pub else THEME["text_muted"], corner_radius=SHAPE["full"]).grid(row=0, column=3, padx=12, pady=5, sticky="w")

            try:
                date_str = trip.start_date.strftime("%b %d, %Y")
            except Exception:
                date_str = "—"
            ctk.CTkLabel(row, text=date_str, font=FONTS["body_sm"], text_color=THEME["text_muted"]).grid(row=0, column=4, padx=12, pady=5, sticky="w")

        ctk.CTkFrame(sec, height=12, fg_color="transparent").pack()
