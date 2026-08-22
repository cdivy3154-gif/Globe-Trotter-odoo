import customtkinter as ctk
from app.ui.theme import THEME, FONTS
from app.ui.components.header import Header
from app.ui.components.cards import MetricCard
from app.services.trip_service import TripService


class BudgetScreen(ctk.CTkScrollableFrame):
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

        user_trips = []
        with self.session_factory() as session:
            trip_service = TripService(session)
            user_trips = trip_service.list_trips(self.current_user.id, limit=50)

        if not user_trips:
            ctk.CTkLabel(self, text="💰 No trips available for budget analysis.", font=FONTS["title_md"]).pack(pady=40)
            ctk.CTkButton(self, text="➕ Create a Trip", command=lambda: self.navigate_callback("create_trip")).pack()
            return

        # If no trip selected, default to first
        selected_trip = None
        if self.trip_id:
            selected_trip = next((t for t in user_trips if t.id == self.trip_id), None)
        if not selected_trip:
            selected_trip = user_trips[0]
            self.trip_id = selected_trip.id

        header = Header(
            self,
            title="Trip Budget & Financial Intelligence 💰",
            subtitle="Automated cost estimations, category breakdowns, daily averages, and budget alerts.",
        )
        header.pack(fill="x", padx=20, pady=(15, 10))

        # Trip Selector Dropdown
        selector_frame = ctk.CTkFrame(self, fg_color=THEME["bg_card"], corner_radius=12, border_width=1, border_color=THEME["border"])
        selector_frame.pack(fill="x", padx=20, pady=(0, 15))

        s_inner = ctk.CTkFrame(selector_frame, fg_color="transparent")
        s_inner.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(s_inner, text="Select Trip to Analyze:", font=FONTS["body_lg"], text_color=THEME["text_primary"]).pack(side="left", padx=(0, 12))
        trip_names = [t.name for t in user_trips]
        self.trip_cb = ctk.CTkComboBox(
            s_inner,
            values=trip_names,
            height=36,
            width=280,
            font=FONTS["body"],
            fg_color=THEME["bg_input"],
            border_color=THEME["border"],
            command=self._on_trip_change,
        )
        self.trip_cb.set(selected_trip.name)
        self.trip_cb.pack(side="left")

        # Fetch Budget Breakdown
        breakdown = {}
        with self.session_factory() as session:
            trip_service = TripService(session)
            breakdown = trip_service.get_budget_breakdown(selected_trip.id, self.current_user.id)

        total_cost = breakdown.get("total", 0.0)
        target_budget = breakdown.get("total_budget") or 0.0
        avg_day = breakdown.get("average_per_day", 0.0)
        days_count = breakdown.get("days_count", 1)
        overbudget_days = breakdown.get("overbudget_days", [])

        # Top Financial Summary Metric Cards
        metrics_row = ctk.CTkFrame(self, fg_color="transparent")
        metrics_row.pack(fill="x", padx=20, pady=(0, 15))
        metrics_row.grid_columnconfigure((0, 1, 2, 3), weight=1)

        m1 = MetricCard(metrics_row, title="Est. Total Cost", value=f"${total_cost:,.2f}", icon="💵", subtitle="All expenses combined")
        m1.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        budg_str = f"${target_budget:,.2f}" if target_budget > 0 else "Not set"
        m2 = MetricCard(metrics_row, title="Target Budget", value=budg_str, icon="🎯", subtitle="Trip spending limit")
        m2.grid(row=0, column=1, padx=8, sticky="ew")

        m3 = MetricCard(metrics_row, title="Avg. Cost / Day", value=f"${avg_day:,.2f}", icon="📊", subtitle=f"Across {days_count} days")
        m3.grid(row=0, column=2, padx=8, sticky="ew")

        status_txt = "Under Budget ✅" if (target_budget == 0 or total_cost <= target_budget) else f"Exceeded by ${(total_cost - target_budget):,.0f} ⚠️"
        status_icon = "🟢" if (target_budget == 0 or total_cost <= target_budget) else "🔴"
        m4 = MetricCard(metrics_row, title="Budget Health", value=status_icon, icon="", subtitle=status_txt)
        m4.grid(row=0, column=3, padx=(8, 0), sticky="ew")

        # Overbudget Alert Banner (if any)
        if overbudget_days:
            alert_box = ctk.CTkFrame(self, fg_color=THEME["warning_bg"], corner_radius=10, border_width=1, border_color=THEME["warning"])
            alert_box.pack(fill="x", padx=20, pady=(0, 15))

            a_inner = ctk.CTkFrame(alert_box, fg_color="transparent")
            a_inner.pack(fill="x", padx=16, pady=12)

            ctk.CTkLabel(a_inner, text="⚠️ Overbudget Days Alert", font=FONTS["body_lg"], text_color=THEME["warning"]).pack(anchor="w")
            over_txt = f"Estimated daily expenses significantly exceed average budget during: {', '.join(overbudget_days)}. Consider adjusting high-cost activities or accommodations."
            ctk.CTkLabel(a_inner, text=over_txt, font=FONTS["body_sm"], text_color=THEME["text_primary"], wraplength=700).pack(anchor="w", pady=(2, 0))

        # Expense Categories Breakdown Card
        cat_card = ctk.CTkFrame(self, fg_color=THEME["bg_card"], corner_radius=12, border_width=1, border_color=THEME["border"])
        cat_card.pack(fill="x", padx=20, pady=(0, 20))

        c_hdr = ctk.CTkFrame(cat_card, fg_color="transparent")
        c_hdr.pack(fill="x", padx=20, pady=(16, 12))
        ctk.CTkLabel(c_hdr, text="Cost Breakdown by Category", font=FONTS["title_md"], text_color=THEME["text_primary"]).pack(side="left")

        categories = [
            ("🏨 Accommodation & Lodging", breakdown.get("accommodation", 0.0), THEME["primary"]),
            ("🍽️ Food & Dining", breakdown.get("meals", 0.0), THEME["accent"]),
            ("🎟️ Scheduled Activities & Tours", breakdown.get("activities", 0.0), THEME["success"]),
            ("🚗 Local Transit & Transport", breakdown.get("transport", 0.0), THEME["info"]),
        ]

        for label, amt, col in categories:
            self._render_expense_bar(cat_card, label, amt, total_cost, col)

        ctk.CTkFrame(cat_card, height=12, fg_color="transparent").pack()

    def _render_expense_bar(self, parent, label, amount, total_sum, color):
        pct = (amount / total_sum) if total_sum > 0 else 0.0

        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=6)

        t_frame = ctk.CTkFrame(row, fg_color="transparent")
        t_frame.pack(fill="x")

        ctk.CTkLabel(t_frame, text=label, font=FONTS["body_lg"], text_color=THEME["text_primary"]).pack(side="left")
        ctk.CTkLabel(t_frame, text=f"${amount:,.2f}  ({pct*100:.1f}%)", font=FONTS["body_lg"], text_color=THEME["text_primary"]).pack(side="right")

        progress = ctk.CTkProgressBar(row, height=10, corner_radius=5, fg_color=THEME["bg_input"], progress_color=color)
        progress.set(pct)
        progress.pack(fill="x", pady=(4, 2))

    def _on_trip_change(self, choice):
        with self.session_factory() as session:
            trip_service = TripService(session)
            trips = trip_service.list_trips(self.current_user.id, limit=50)
            chosen = next((t for t in trips if t.name == choice), None)
            if chosen:
                self.trip_id = chosen.id
        self.refresh()
