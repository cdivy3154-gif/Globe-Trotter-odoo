"""
Phase 7 — Budget & Financial Intelligence Screen
Features:
  - Trip selector dropdown (persists across refresh)
  - 4 summary MetricCards: Planned / Activities / Accommodation / Remaining
  - Category breakdown bar chart (Matplotlib, no GUI thread issues)
  - Per-stop cost table with progress bar fill %
  - Per-category pie chart
  - Over-budget warning banner
  - Day-by-day cost table
  - Navigate → Itinerary Builder CTA
"""
import customtkinter as ctk
from app.ui.theme import THEME, FONTS, SHAPE, LAYOUT, MPL_STYLE, format_money, get_currency_symbol
from app.ui.components.header import Header
from app.ui.components.cards import MetricCard, EmptyState
from app.services.trip_service import TripService

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    _HAS_MPL = True
except ImportError:
    _HAS_MPL = False


def _pct_bar(parent, value: float, maximum: float, color: str):
    """Draw a thin filled progress bar inside a CTkFrame."""
    pct = min(value / maximum, 1.0) if maximum > 0 else 0
    bg = ctk.CTkFrame(parent, height=6, fg_color=THEME["bg_input"], corner_radius=SHAPE["full"])
    bg.pack(fill="x", pady=(4, 2))
    if pct > 0:
        ctk.CTkFrame(bg, height=6, fg_color=color, corner_radius=SHAPE["full"]).place(
            relx=0, rely=0, relwidth=pct, relheight=1.0
        )


# ══════════════════════════════════════════════════════════════════
class BudgetScreen(ctk.CTkScrollableFrame):
    def __init__(self, master, navigate_callback, session_factory, current_user, trip_id=None, **kwargs):
        super().__init__(
            master,
            fg_color=THEME["bg_dark"],
            scrollbar_button_color=THEME["border"],
            scrollbar_button_hover_color=THEME["border_light"],
            **kwargs,
        )
        self.navigate_callback = navigate_callback
        self.session_factory   = session_factory
        self.current_user      = current_user
        self.trip_id           = trip_id
        self.grid_columnconfigure(0, weight=1)
        self.refresh()

    # ─────────────────────────────────────────────────────────────
    def refresh(self):
        for w in self.winfo_children():
            w.destroy()

        with self.session_factory() as session:
            user_trips = TripService(session).list_trips(self.current_user.id, limit=50)

        if not user_trips:
            Header(self, title="Budget & Financial Intelligence 💰", breadcrumb=["Dashboard", "Budget"]).pack(fill="x", padx=20, pady=(18, 10))
            EmptyState(self, icon="💰", title="No trips yet", message="Create a trip to start tracking budget.", action_label="➕  Create Trip", action_cmd=lambda: self.navigate_callback("create_trip")).pack(fill="x", padx=20, pady=40)
            return

        # Default trip selection
        if self.trip_id:
            selected = next((t for t in user_trips if t.id == self.trip_id), user_trips[0])
        else:
            selected = user_trips[0]
        self.trip_id = selected.id

        # Get budget data
        with self.session_factory() as session:
            data = TripService(session).get_budget_breakdown(self.trip_id, self.current_user.id)
            full_trip = TripService(session).get_trip(self.trip_id, self.current_user.id)

        Header(
            self,
            title="Budget & Financial Intelligence 💰",
            subtitle="Automated cost estimations, category breakdowns, and budget alerts.",
            action_button=("✏️  Open Builder", lambda: self.navigate_callback("itinerary_builder", trip_id=self.trip_id), THEME["primary"]),
            breadcrumb=["Dashboard", "Budget"],
        ).pack(fill="x", padx=20, pady=(18, 10))

        # ── Trip selector ─────────────────────────────────────────
        sel_card = ctk.CTkFrame(self, fg_color=THEME["bg_card"], corner_radius=SHAPE["medium"], border_width=1, border_color=THEME["border"])
        sel_card.pack(fill="x", padx=20, pady=(0, 10))
        si = ctk.CTkFrame(sel_card, fg_color="transparent")
        si.pack(fill="x", padx=16, pady=12)
        si.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(si, text="Viewing Trip:", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).grid(row=0, column=0, padx=(0, 12))
        trip_names = [t.name for t in user_trips]
        trip_cb = ctk.CTkComboBox(si, values=trip_names, height=LAYOUT["input_height"], font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"], text_color=THEME["text_primary"], command=self._on_trip_change)
        trip_cb.set(selected.name)
        trip_cb.grid(row=0, column=1, sticky="ew")
        self._user_trips = user_trips

        # ── Over-budget warning ───────────────────────────────────
        total_planned = float(data.get("total_budget", 0) or 0)
        total_actual  = float(data.get("total_estimated_cost", 0) or 0)
        over          = total_planned > 0 and total_actual > total_planned
        curr          = data.get("currency") or getattr(full_trip, "currency", "USD") or "USD"

        if over:
            overage_str = format_money(total_actual - total_planned, curr, decimals=2)
            warn = ctk.CTkFrame(self, fg_color=THEME["danger_bg"], corner_radius=SHAPE["medium"], border_width=1, border_color=THEME["danger"])
            warn.pack(fill="x", padx=20, pady=(0, 10))
            ctk.CTkLabel(warn, text=f"⚠️  Over Budget by  {overage_str}  — review your activities or increase the trip budget.", font=FONTS["body_lg"], text_color=THEME["danger"], wraplength=900, justify="left").pack(padx=20, pady=14, anchor="w")

        # ── 4 Metric Cards ────────────────────────────────────────
        remaining = total_planned - total_actual
        self._metric_row(data, total_planned, total_actual, remaining, curr)

        # ── Category breakdown ────────────────────────────────────
        categories = data.get("by_category", {}) or {}
        if categories:
            self._category_section(categories, total_actual, curr)

        # ── Per-stop table ────────────────────────────────────────
        self._stop_table(full_trip, total_actual, curr)

        # ── Day-by-day table ──────────────────────────────────────
        daily = data.get("daily_breakdown", []) or []
        if daily:
            self._daily_table(daily, curr)

    # ─────────────────────────────────────────────────────────────
    def _metric_row(self, data, planned, actual, remaining, curr):
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(0, 10))
        row.grid_columnconfigure((0, 1, 2, 3), weight=1)

        act_cost = float(data.get("total_activities", 0) or 0)
        acc_cost  = float(data.get("total_accommodation", 0) or 0)

        cards = [
            ("Trip Budget", format_money(planned, curr, decimals=0) if planned else "—", "💼", "Planned allocation", THEME["primary"]),
            ("Activity Costs", format_money(act_cost, curr, decimals=2), "🎟️", "Booked activities", THEME["accent"]),
            ("Est. Accommodation", format_money(acc_cost, curr, decimals=2), "🏨", "Hotel estimate", THEME["info"]),
            ("Remaining", format_money(remaining, curr, decimals=2), "💰", "Budget left" if remaining >= 0 else "Over budget!", THEME["success"] if remaining >= 0 else THEME["danger"]),
        ]
        for i, (title, val, icon, sub, color) in enumerate(cards):
            MetricCard(row, title=title, value=val, icon=icon, subtitle=sub, accent_color=color).grid(
                row=0, column=i, padx=(0 if i == 0 else 6, 6 if i < 3 else 0), sticky="ew"
            )

    # ─────────────────────────────────────────────────────────────
    def _category_section(self, categories: dict, total: float, curr: str = "USD"):
        section = ctk.CTkFrame(self, fg_color=THEME["bg_card"], corner_radius=SHAPE["medium"], border_width=1, border_color=THEME["border"])
        section.pack(fill="x", padx=20, pady=(0, 10))
        ctk.CTkFrame(section, height=3, fg_color=THEME["accent"], corner_radius=0).pack(fill="x")
        ctk.CTkLabel(section, text="Cost by Category", font=FONTS["title_sm"], text_color=THEME["text_primary"]).pack(anchor="w", padx=20, pady=(14, 10))

        if _HAS_MPL and categories:
            self._draw_pie(section, categories)

        # Category bars
        bars = ctk.CTkFrame(section, fg_color="transparent")
        bars.pack(fill="x", padx=20, pady=(0, 16))

        colors = [THEME["chart_1"], THEME["chart_2"], THEME["chart_3"], THEME["chart_4"], THEME["chart_5"], THEME["chart_6"]]
        for idx, (cat, amt) in enumerate(sorted(categories.items(), key=lambda x: x[1], reverse=True)):
            color = colors[idx % len(colors)]
            pct   = (float(amt) / total * 100) if total > 0 else 0
            row   = ctk.CTkFrame(bars, fg_color="transparent")
            row.pack(fill="x", pady=3)
            row.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(row, text=cat.title(), font=FONTS["body_sm"], text_color=THEME["text_secondary"], width=120, anchor="w").grid(row=0, column=0, sticky="w")
            _pct_bar(row, float(amt), total, color)
            formatted_cat = format_money(amt, curr, decimals=2)
            ctk.CTkLabel(row, text=f"{formatted_cat}  ({pct:.1f}%)", font=FONTS["body_sm"], text_color=THEME["text_primary"], width=130, anchor="e").grid(row=0, column=2, sticky="e")

    def _draw_pie(self, parent, categories: dict):
        try:
            fig, ax = plt.subplots(figsize=(5, 3), facecolor=MPL_STYLE["bg"])
            ax.set_facecolor(MPL_STYLE["axes_bg"])
            labels  = list(categories.keys())
            values  = [float(v) for v in categories.values()]
            colors  = MPL_STYLE["colors"][:len(labels)]
            wedges, texts, autotexts = ax.pie(
                values, labels=None, colors=colors,
                autopct="%1.1f%%", startangle=90,
                pctdistance=0.8,
                wedgeprops={"edgecolor": MPL_STYLE["bg"], "linewidth": 2},
            )
            for t in autotexts:
                t.set_color(MPL_STYLE["text"])
                t.set_fontsize(8)
            ax.legend(
                wedges, [l.title() for l in labels],
                loc="center left", bbox_to_anchor=(1, 0, 0.5, 1),
                fontsize=8, framealpha=0,
                labelcolor=MPL_STYLE["text"],
            )
            plt.tight_layout()

            canvas = FigureCanvasTkAgg(fig, master=parent)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="x", padx=20, pady=(0, 8))
            plt.close(fig)
        except Exception:
            pass  # Graceful degradation — bars still render

    # ─────────────────────────────────────────────────────────────
    def _stop_table(self, trip, total_actual: float, curr: str = "USD"):
        if not trip.stops:
            return
        section = ctk.CTkFrame(self, fg_color=THEME["bg_card"], corner_radius=SHAPE["medium"], border_width=1, border_color=THEME["border"])
        section.pack(fill="x", padx=20, pady=(0, 10))
        ctk.CTkFrame(section, height=3, fg_color=THEME["primary"], corner_radius=0).pack(fill="x")
        ctk.CTkLabel(section, text="Cost per Destination", font=FONTS["title_sm"], text_color=THEME["text_primary"]).pack(anchor="w", padx=20, pady=(14, 6))

        for stop in trip.stops:
            stop_cost = sum(float(a.estimated_cost or 0) for a in stop.activities)
            city = stop.city.name if stop.city else "Stop"

            row = ctk.CTkFrame(section, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=4)
            row.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(row, text=f"📍 {city}", font=FONTS["body_sm"], text_color=THEME["text_secondary"], width=160, anchor="w").grid(row=0, column=0, sticky="w")

            bar_frame = ctk.CTkFrame(row, fg_color="transparent")
            bar_frame.grid(row=0, column=1, sticky="ew", padx=8)
            _pct_bar(bar_frame, stop_cost, total_actual or 1, THEME["primary"])

            ctk.CTkLabel(row, text=format_money(stop_cost, curr, decimals=2), font=FONTS["body_sm"], text_color=THEME["success"], width=90, anchor="e").grid(row=0, column=2, sticky="e")

        ctk.CTkFrame(section, height=12, fg_color="transparent").pack()

    # ─────────────────────────────────────────────────────────────
    def _daily_table(self, daily: list, curr: str = "USD"):
        section = ctk.CTkFrame(self, fg_color=THEME["bg_card"], corner_radius=SHAPE["medium"], border_width=1, border_color=THEME["border"])
        section.pack(fill="x", padx=20, pady=(0, 24))
        ctk.CTkFrame(section, height=3, fg_color=THEME["chart_2"], corner_radius=0).pack(fill="x")
        ctk.CTkLabel(section, text="Day-by-Day Cost Estimate", font=FONTS["title_sm"], text_color=THEME["text_primary"]).pack(anchor="w", padx=20, pady=(14, 6))

        # Column headers
        hdr = ctk.CTkFrame(section, fg_color=THEME["bg_input"], corner_radius=SHAPE["extra_small"])
        hdr.pack(fill="x", padx=20, pady=(0, 4))
        hdr.grid_columnconfigure((1, 2, 3), weight=1)
        for col, (txt, c) in enumerate([("Date", 0), ("Accommodation", 1), ("Activities", 2), ("Total", 3)]):
            ctk.CTkLabel(hdr, text=txt, font=FONTS["badge"], text_color=THEME["text_muted"]).grid(row=0, column=c, padx=12, pady=6, sticky="w")

        max_day_cost = max((float(d.get("total_day_cost", 0) or 0) for d in daily), default=1)

        for i, day in enumerate(daily):
            date_str = day["date"].strftime("%a, %b %d") if hasattr(day.get("date"), "strftime") else str(day.get("date", ""))[:10]
            acc   = float(day.get("accommodation", 0) or 0)
            acts  = float(day.get("activities", 0) or 0)
            total = float(day.get("total_day_cost", 0) or 0)
            over  = float(day.get("avg_daily_budget", 0) or 0) > 0 and total > float(day.get("avg_daily_budget", 0))

            bg = THEME["danger_bg"] if over else ("transparent" if i % 2 == 0 else THEME["bg_input"])
            row = ctk.CTkFrame(section, fg_color=bg, corner_radius=SHAPE["extra_small"])
            row.pack(fill="x", padx=20, pady=1)
            row.grid_columnconfigure((1, 2, 3), weight=1)

            ctk.CTkLabel(row, text=date_str, font=FONTS["body_sm"], text_color=THEME["text_secondary"], width=110).grid(row=0, column=0, padx=12, pady=5, sticky="w")
            ctk.CTkLabel(row, text=format_money(acc, curr, decimals=0), font=FONTS["body_sm"], text_color=THEME["text_muted"]).grid(row=0, column=1, padx=12, pady=5, sticky="w")
            ctk.CTkLabel(row, text=format_money(acts, curr, decimals=0), font=FONTS["body_sm"], text_color=THEME["text_muted"]).grid(row=0, column=2, padx=12, pady=5, sticky="w")
            ctk.CTkLabel(row, text=format_money(total, curr, decimals=0), font=FONTS["body_sm"], text_color=THEME["danger"] if over else THEME["success"]).grid(row=0, column=3, padx=12, pady=5, sticky="w")

        ctk.CTkFrame(section, height=12, fg_color="transparent").pack()

    # ─────────────────────────────────────────────────────────────
    def _on_trip_change(self, trip_name: str):
        t = next((t for t in self._user_trips if t.name == trip_name), None)
        if t:
            self.trip_id = t.id
            self.refresh()
