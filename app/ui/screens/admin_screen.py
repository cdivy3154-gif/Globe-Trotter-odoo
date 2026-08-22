import customtkinter as ctk
from app.ui.theme import THEME, FONTS
from app.ui.components.header import Header
from app.ui.components.cards import MetricCard
from app.services.admin_service import AdminService


class AdminScreen(ctk.CTkScrollableFrame):
    def __init__(self, master, navigate_callback, session_factory, current_user, **kwargs):
        super().__init__(master, fg_color=THEME["bg_dark"], **kwargs)
        self.navigate_callback = navigate_callback
        self.session_factory = session_factory
        self.current_user = current_user
        self.grid_columnconfigure(0, weight=1)
        self.refresh()

    def refresh(self):
        for widget in self.winfo_children():
            widget.destroy()

        header = Header(
            self,
            title="Admin & Platform Analytics 📊",
            subtitle="Monitor user growth, popular destinations, activity trends, and system itineraries.",
        )
        header.pack(fill="x", padx=20, pady=(15, 10))

        # Fetch Admin Stats
        stats = None
        users_list = []
        all_trips = []
        with self.session_factory() as session:
            admin_service = AdminService(session)
            stats = admin_service.get_stats()
            users_list = admin_service.list_users(limit=50)
            all_trips = admin_service.list_all_trips(limit=50)

        # Overview Metrics Grid
        metrics_row = ctk.CTkFrame(self, fg_color="transparent")
        metrics_row.pack(fill="x", padx=20, pady=(0, 15))
        metrics_row.grid_columnconfigure((0, 1, 2, 3), weight=1)

        m1 = MetricCard(metrics_row, title="Registered Users", value=str(stats.total_users), icon="👥", subtitle="Platform accounts")
        m1.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        m2 = MetricCard(metrics_row, title="Total Trips", value=str(stats.total_trips), icon="✈️", subtitle="Created journeys")
        m2.grid(row=0, column=1, padx=8, sticky="ew")

        m3 = MetricCard(metrics_row, title="Catalog Cities", value=str(stats.total_cities), icon="🏙️", subtitle="Global directory")
        m3.grid(row=0, column=2, padx=8, sticky="ew")

        m4 = MetricCard(metrics_row, title="Catalog Activities", value=str(stats.total_activities), icon="🎟️", subtitle="Available experiences")
        m4.grid(row=0, column=3, padx=(8, 0), sticky="ew")

        # Two Column Analytics Box: Top Cities + Top Categories
        two_col = ctk.CTkFrame(self, fg_color="transparent")
        two_col.pack(fill="x", padx=20, pady=(0, 20))
        two_col.grid_columnconfigure((0, 1), weight=1)

        # Left: Top Destinations
        top_c_card = ctk.CTkFrame(two_col, fg_color=THEME["bg_card"], corner_radius=12, border_width=1, border_color=THEME["border"])
        top_c_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        ctk.CTkLabel(top_c_card, text="🏆 Most Popular Destination Cities", font=FONTS["title_md"], text_color=THEME["text_primary"]).pack(anchor="w", padx=16, pady=(16, 10))

        if stats.top_cities:
            for idx, c in enumerate(stats.top_cities):
                r = ctk.CTkFrame(top_c_card, fg_color=THEME["bg_input"], corner_radius=6)
                r.pack(fill="x", padx=16, pady=3)
                r_in = ctk.CTkFrame(r, fg_color="transparent")
                r_in.pack(fill="x", padx=10, pady=6)
                ctk.CTkLabel(r_in, text=f"#{idx+1}  {c.city_name}, {c.country}", font=FONTS["body_lg"], text_color=THEME["text_primary"]).pack(side="left")
                ctk.CTkLabel(r_in, text=f"{c.trip_count} stops booked", font=FONTS["body_sm"], text_color=THEME["info"]).pack(side="right")
        else:
            ctk.CTkLabel(top_c_card, text="No destination stops recorded yet.", font=FONTS["body_sm"], text_color=THEME["text_muted"]).pack(padx=16, pady=20, anchor="w")

        ctk.CTkFrame(top_c_card, height=10, fg_color="transparent").pack()

        # Right: Top Activities
        top_a_card = ctk.CTkFrame(two_col, fg_color=THEME["bg_card"], corner_radius=12, border_width=1, border_color=THEME["border"])
        top_a_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        ctk.CTkLabel(top_a_card, text="📈 Top Activity Categories", font=FONTS["title_md"], text_color=THEME["text_primary"]).pack(anchor="w", padx=16, pady=(16, 10))

        if stats.top_activities:
            for idx, a in enumerate(stats.top_activities):
                r = ctk.CTkFrame(top_a_card, fg_color=THEME["bg_input"], corner_radius=6)
                r.pack(fill="x", padx=16, pady=3)
                r_in = ctk.CTkFrame(r, fg_color="transparent")
                r_in.pack(fill="x", padx=10, pady=6)
                ctk.CTkLabel(r_in, text=f"🏷️  {a.activity_type.upper()}", font=FONTS["body_lg"], text_color=THEME["text_primary"]).pack(side="left")
                ctk.CTkLabel(r_in, text=f"{a.count} entries", font=FONTS["body_sm"], text_color=THEME["success"]).pack(side="right")
        else:
            ctk.CTkLabel(top_a_card, text="No activity data recorded yet.", font=FONTS["body_sm"], text_color=THEME["text_muted"]).pack(padx=16, pady=20, anchor="w")

        ctk.CTkFrame(top_a_card, height=10, fg_color="transparent").pack()

        # User Management Table Section
        u_card = ctk.CTkFrame(self, fg_color=THEME["bg_card"], corner_radius=12, border_width=1, border_color=THEME["border"])
        u_card.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkLabel(u_card, text="👥 User Accounts Directory", font=FONTS["title_md"], text_color=THEME["text_primary"]).pack(anchor="w", padx=16, pady=(16, 10))

        # Table Header
        tbl_hdr = ctk.CTkFrame(u_card, fg_color=THEME["bg_sidebar"], corner_radius=6)
        tbl_hdr.pack(fill="x", padx=16, pady=(0, 4))
        tbl_hdr.grid_columnconfigure((0, 1, 2, 3), weight=1)

        ctk.CTkLabel(tbl_hdr, text="NAME", font=FONTS["badge"], text_color=THEME["text_muted"]).grid(row=0, column=0, sticky="w", padx=10, pady=6)
        ctk.CTkLabel(tbl_hdr, text="EMAIL", font=FONTS["badge"], text_color=THEME["text_muted"]).grid(row=0, column=1, sticky="w", padx=10, pady=6)
        ctk.CTkLabel(tbl_hdr, text="ROLE", font=FONTS["badge"], text_color=THEME["text_muted"]).grid(row=0, column=2, sticky="w", padx=10, pady=6)
        ctk.CTkLabel(tbl_hdr, text="TRIPS PLANNED", font=FONTS["badge"], text_color=THEME["text_muted"]).grid(row=0, column=3, sticky="e", padx=10, pady=6)

        for u in users_list:
            row = ctk.CTkFrame(u_card, fg_color=THEME["bg_input"], corner_radius=4)
            row.pack(fill="x", padx=16, pady=2)
            row.grid_columnconfigure((0, 1, 2, 3), weight=1)

            ctk.CTkLabel(row, text=u.full_name or "—", font=FONTS["body"]).grid(row=0, column=0, sticky="w", padx=10, pady=6)
            ctk.CTkLabel(row, text=u.email, font=FONTS["body"]).grid(row=0, column=1, sticky="w", padx=10, pady=6)

            role_col = THEME["accent"] if u.role.lower() == "admin" else THEME["info"]
            ctk.CTkLabel(row, text=u.role.upper(), font=FONTS["badge"], text_color=role_col).grid(row=0, column=2, sticky="w", padx=10, pady=6)
            ctk.CTkLabel(row, text=str(u.trip_count), font=FONTS["body"]).grid(row=0, column=3, sticky="e", padx=10, pady=6)

        ctk.CTkFrame(u_card, height=12, fg_color="transparent").pack()
