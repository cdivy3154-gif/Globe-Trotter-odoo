"""
Reusable card components for GlobeTrotter.
MetricCard, TripCard, CityCard, ActivityCatalogCard, EmptyState
"""
import customtkinter as ctk
from datetime import datetime, timezone
from app.ui.theme import THEME, FONTS, LAYOUT, SHAPE, format_money, get_currency_symbol


# ── Utility ───────────────────────────────────────────────────────

def _bind_hover(widget, normal_color: str, hover_color: str, border_normal: str = "", border_hover: str = ""):
    """Attach enter/leave hover effect to any CTkFrame."""
    def _enter(_):
        kw = {"fg_color": hover_color}
        if border_hover:
            kw["border_color"] = border_hover
        widget.configure(**kw)

    def _leave(_):
        kw = {"fg_color": normal_color}
        if border_normal:
            kw["border_color"] = border_normal
        widget.configure(**kw)

    widget.bind("<Enter>", _enter)
    widget.bind("<Leave>", _leave)


def _trip_status(trip) -> tuple[str, str]:
    """Return (label, color) for trip status chip."""
    now = datetime.now(timezone.utc)
    try:
        start = trip.start_date if trip.start_date.tzinfo else trip.start_date.replace(tzinfo=timezone.utc)
        end   = trip.end_date   if trip.end_date.tzinfo   else trip.end_date.replace(tzinfo=timezone.utc)
    except Exception:
        return "Unknown", THEME["text_muted"]

    if now < start:
        return "Upcoming", THEME["status_upcoming"]
    elif now > end:
        return "Past", THEME["status_past"]
    else:
        return "Ongoing", THEME["status_ongoing"]


# ══════════════════════════════════════════════════════════════════
#   MetricCard
# ══════════════════════════════════════════════════════════════════
class MetricCard(ctk.CTkFrame):
    def __init__(self, master, title: str, value: str, icon: str = "📈", subtitle: str = "", accent_color: str = "", **kwargs):
        super().__init__(
            master,
            fg_color=THEME["bg_card"],
            corner_radius=SHAPE["medium"],
            border_width=1,
            border_color=THEME["border"],
            **kwargs,
        )
        _bind_hover(self, THEME["bg_card"], THEME["bg_card_hover"], THEME["border"], THEME["border_focus"])

        # Accent top stripe
        color = accent_color or THEME["primary"]
        ctk.CTkFrame(self, height=3, fg_color=color, corner_radius=0).pack(fill="x", side="top")

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=(10, 14))

        top_row = ctk.CTkFrame(inner, fg_color="transparent")
        top_row.pack(fill="x")
        ctk.CTkLabel(top_row, text=title.upper(), font=FONTS["badge"], text_color=THEME["text_muted"]).pack(side="left")
        ctk.CTkLabel(top_row, text=icon, font=FONTS["icon_md"]).pack(side="right")

        ctk.CTkLabel(inner, text=value, font=FONTS["title_xl"], text_color=THEME["text_primary"], anchor="w").pack(anchor="w", pady=(4, 0))

        if subtitle:
            ctk.CTkLabel(inner, text=subtitle, font=FONTS["body_sm"], text_color=THEME["text_secondary"], anchor="w").pack(anchor="w", pady=(2, 0))


# ══════════════════════════════════════════════════════════════════
#   TripCard
# ══════════════════════════════════════════════════════════════════
class TripCard(ctk.CTkFrame):
    def __init__(self, master, trip, on_view=None, on_edit=None, on_delete=None, on_share=None, **kwargs):
        super().__init__(
            master,
            fg_color=THEME["bg_card"],
            corner_radius=SHAPE["medium"],
            border_width=1,
            border_color=THEME["border"],
            **kwargs,
        )
        self.trip    = trip
        self.on_view   = on_view
        self.on_edit   = on_edit
        self.on_delete = on_delete
        self.on_share  = on_share
        _bind_hover(self, THEME["bg_card"], THEME["bg_card_hover"], THEME["border"], THEME["border_focus"])
        self._build()

    def _build(self):
        # Status + visibility chips
        status_label, status_color = _trip_status(self.trip)
        is_public = (
            getattr(self.trip, "visibility", "") == "public"
            or str(getattr(getattr(self.trip, "visibility", None), "value", "")) == "public"
        )
        vis_label = "PUBLIC" if is_public else "PRIVATE"
        vis_color = THEME["status_public"] if is_public else THEME["border_light"]

        # ── Header ────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(14, 4))

        ctk.CTkLabel(hdr, text=self.trip.name, font=FONTS["title_sm"], text_color=THEME["text_primary"], anchor="w").pack(side="left", fill="x", expand=True)

        chips = ctk.CTkFrame(hdr, fg_color="transparent")
        chips.pack(side="right")
        ctk.CTkLabel(chips, text=f" {status_label} ", font=FONTS["badge"], fg_color=status_color, text_color="#000", corner_radius=SHAPE["full"]).pack(side="left", padx=2)
        ctk.CTkLabel(chips, text=f" {vis_label} ", font=FONTS["badge"], fg_color=vis_color, text_color="#000", corner_radius=SHAPE["full"]).pack(side="left", padx=2)

        # ── Meta info ─────────────────────────────────────────────
        try:
            s = self.trip.start_date.strftime("%b %d, %Y")
            e = self.trip.end_date.strftime("%b %d, %Y")
        except Exception:
            s = str(self.trip.start_date)[:10]
            e = str(self.trip.end_date)[:10]

        ctk.CTkLabel(self, text=f"📅  {s}  →  {e}", font=FONTS["body_sm"], text_color=THEME["text_secondary"], anchor="w").pack(fill="x", padx=16, pady=1)

        stops = len(getattr(self.trip, "stops", []))
        acts  = sum(len(getattr(s, "activities", [])) for s in getattr(self.trip, "stops", []))
        ctk.CTkLabel(self, text=f"📍 {stops} Destinations   ·   🎟️ {acts} Activities", font=FONTS["body_sm"], text_color=THEME["text_muted"], anchor="w").pack(fill="x", padx=16, pady=1)

        if self.trip.total_budget:
            curr_str = getattr(self.trip, "currency", "USD")
            formatted_budget = format_money(self.trip.total_budget, curr_str, decimals=0)
            ctk.CTkLabel(self, text=f"💰  Budget: {formatted_budget}", font=FONTS["body_sm"], text_color=THEME["success"], anchor="w").pack(fill="x", padx=16, pady=1)

        # ── Divider ────────────────────────────────────────────────
        ctk.CTkFrame(self, height=1, fg_color=THEME["border"]).pack(fill="x", padx=16, pady=(8, 0))

        # ── Buttons ───────────────────────────────────────────────
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=12, pady=10)

        if self.on_view:
            ctk.CTkButton(bar, text="Open", font=FONTS["body_sm"], height=30, corner_radius=SHAPE["small"], fg_color=THEME["primary"], hover_color=THEME["primary_hover"], command=lambda: self.on_view(self.trip)).pack(side="left", padx=2, expand=True, fill="x")
        if self.on_share:
            ctk.CTkButton(bar, text="Share", font=FONTS["body_sm"], height=30, width=56, corner_radius=SHAPE["small"], fg_color=THEME["bg_input"], hover_color=THEME["bg_card_hover"], text_color=THEME["text_secondary"], command=lambda: self.on_share(self.trip)).pack(side="left", padx=2)
        if self.on_delete:
            ctk.CTkButton(bar, text="🗑", font=FONTS["body_sm"], height=30, width=36, corner_radius=SHAPE["small"], fg_color=THEME["danger_bg"], hover_color=THEME["danger"], text_color=THEME["danger"], command=lambda: self.on_delete(self.trip)).pack(side="left", padx=2)


# ══════════════════════════════════════════════════════════════════
#   CityCard
# ══════════════════════════════════════════════════════════════════
class CityCard(ctk.CTkFrame):
    def __init__(self, master, city, on_plan=None, on_save=None, is_saved: bool = False, **kwargs):
        super().__init__(
            master,
            fg_color=THEME["bg_card"],
            corner_radius=SHAPE["medium"],
            border_width=1,
            border_color=THEME["border"],
            **kwargs,
        )
        self.city = city
        self.on_plan = on_plan
        self.on_save = on_save
        self.is_saved = is_saved
        _bind_hover(self, THEME["bg_card"], THEME["bg_card_hover"], THEME["border"], THEME["border_focus"])
        self._build()

    def _cost_color(self, idx: int) -> str:
        if idx <= 35:  return THEME["success"]
        if idx <= 65:  return THEME["warning"]
        return THEME["danger"]

    def _build(self):
        cost_idx = int(getattr(self.city, "cost_index", 50) or 50)
        pop_score = float(getattr(self.city, "popularity_score", 0.5) or 0.5)
        region = getattr(self.city, "region", "") or ""
        country = getattr(self.city, "country", "") or ""

        # ── Header ────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(14, 4))

        ctk.CTkLabel(hdr, text=self.city.name, font=FONTS["title_sm"], text_color=THEME["text_primary"], anchor="w").pack(side="left")

        # Cost badge
        ctk.CTkLabel(
            hdr,
            text=f" ${cost_idx} ",
            font=FONTS["badge"],
            fg_color=self._cost_color(cost_idx),
            text_color="#000",
            corner_radius=SHAPE["extra_small"],
        ).pack(side="right")

        # ── Country / Region ──────────────────────────────────────
        ctk.CTkLabel(self, text=f"🌐  {country}  ·  {region}", font=FONTS["body_sm"], text_color=THEME["text_secondary"], anchor="w").pack(fill="x", padx=16, pady=1)

        # ── Popularity bar ────────────────────────────────────────
        pop_pct = min(int(pop_score * 100), 100)
        bar_bg = ctk.CTkFrame(self, height=6, fg_color=THEME["bg_input"], corner_radius=SHAPE["full"])
        bar_bg.pack(fill="x", padx=16, pady=(4, 6))
        if pop_pct > 0:
            # simulate fill with a proportional inner frame
            bar_fill = ctk.CTkFrame(bar_bg, height=6, fg_color=THEME["primary"], corner_radius=SHAPE["full"])
            bar_fill.place(relx=0, rely=0, relwidth=pop_pct / 100, relheight=1.0)

        ctk.CTkLabel(self, text=f"⭐ Popularity: {pop_pct}%", font=FONTS["caption"], text_color=THEME["text_muted"], anchor="w").pack(fill="x", padx=16)

        # ── Divider ────────────────────────────────────────────────
        ctk.CTkFrame(self, height=1, fg_color=THEME["border"]).pack(fill="x", padx=16, pady=(8, 0))

        # ── Action Row ────────────────────────────────────────────
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=12, pady=10)

        if self.on_plan:
            ctk.CTkButton(bar, text="Plan Trip Here", font=FONTS["body_sm"], height=30, corner_radius=SHAPE["small"], fg_color=THEME["primary"], hover_color=THEME["primary_hover"], command=lambda: self.on_plan(self.city)).pack(side="left", padx=2, expand=True, fill="x")

        if self.on_save:
            star = "⭐" if self.is_saved else "☆"
            save_color = THEME["accent"] if self.is_saved else THEME["bg_input"]
            ctk.CTkButton(bar, text=star, font=FONTS["body_sm"], height=30, width=36, corner_radius=SHAPE["small"], fg_color=save_color, hover_color=THEME["accent_hover"], command=lambda: self.on_save(self.city)).pack(side="left", padx=2)


# ══════════════════════════════════════════════════════════════════
#   ActivityCatalogCard
# ══════════════════════════════════════════════════════════════════
_ACTIVITY_ICONS = {
    "sightseeing": "🏛️",
    "food":        "🍽️",
    "adventure":   "🧗",
    "cultural":    "🎭",
    "nature":      "🌿",
    "nightlife":   "🌙",
    "shopping":    "🛍️",
    "wellness":    "🧘",
    "transport":   "🚌",
    "other":       "📍",
}


class ActivityCatalogCard(ctk.CTkFrame):
    def __init__(self, master, activity, on_add=None, **kwargs):
        super().__init__(
            master,
            fg_color=THEME["bg_card"],
            corner_radius=SHAPE["medium"],
            border_width=1,
            border_color=THEME["border"],
            **kwargs,
        )
        self.activity = activity
        self.on_add = on_add
        _bind_hover(self, THEME["bg_card"], THEME["bg_card_hover"], THEME["border"], THEME["border_focus"])
        self._build()

    def _build(self):
        act_type = str(getattr(self.activity, "activity_type", "other") or "other").lower()
        icon = _ACTIVITY_ICONS.get(act_type, "📍")
        avg_cost = float(getattr(self.activity, "avg_cost", 0) or 0)
        duration = int(getattr(self.activity, "duration_minutes", 0) or 0)
        city_name = getattr(getattr(self.activity, "city", None), "name", "") or ""

        # ── Header ────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=14, pady=(12, 4))

        ctk.CTkLabel(hdr, text=icon, font=FONTS["icon_md"]).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(hdr, text=self.activity.name, font=FONTS["body_lg"], text_color=THEME["text_primary"], anchor="w", wraplength=180).pack(side="left", fill="x", expand=True)

        # ── Chips row ─────────────────────────────────────────────
        chips = ctk.CTkFrame(self, fg_color="transparent")
        chips.pack(fill="x", padx=14, pady=2)

        ctk.CTkLabel(chips, text=f" {act_type.title()} ", font=FONTS["badge"], fg_color=THEME["primary_container"], text_color=THEME["on_primary_container"], corner_radius=SHAPE["extra_small"]).pack(side="left", padx=(0, 4))
        if avg_cost > 0:
            cost_str = format_money(avg_cost, getattr(self.activity, "currency", "USD"), decimals=0)
            ctk.CTkLabel(chips, text=f" {cost_str} ", font=FONTS["badge"], fg_color=THEME["success_bg"], text_color=THEME["success"], corner_radius=SHAPE["extra_small"]).pack(side="left", padx=2)
        if duration > 0:
            hrs = duration // 60
            mins = duration % 60
            dur_str = f"{hrs}h" if not mins else (f"{hrs}h {mins}m" if hrs else f"{mins}m")
            ctk.CTkLabel(chips, text=f" {dur_str} ", font=FONTS["badge"], fg_color=THEME["bg_input"], text_color=THEME["text_secondary"], corner_radius=SHAPE["extra_small"]).pack(side="left", padx=2)

        if city_name:
            ctk.CTkLabel(self, text=f"📍 {city_name}", font=FONTS["caption"], text_color=THEME["text_muted"], anchor="w").pack(fill="x", padx=14, pady=(2, 6))

        # ── Add button ────────────────────────────────────────────
        if self.on_add:
            ctk.CTkFrame(self, height=1, fg_color=THEME["border"]).pack(fill="x", padx=14)
            ctk.CTkButton(
                self,
                text="+ Add to Trip",
                font=FONTS["body_sm"],
                height=28,
                corner_radius=SHAPE["extra_small"],
                fg_color=THEME["bg_input"],
                hover_color=THEME["primary"],
                text_color=THEME["text_secondary"],
                command=lambda: self.on_add(self.activity),
            ).pack(fill="x", padx=14, pady=8)


# ══════════════════════════════════════════════════════════════════
#   EmptyState
# ══════════════════════════════════════════════════════════════════
class EmptyState(ctk.CTkFrame):
    def __init__(self, master, icon: str = "🗺️", title: str = "Nothing here yet", message: str = "", action_label: str = "", action_cmd=None, **kwargs):
        super().__init__(
            master,
            fg_color=THEME["bg_card"],
            corner_radius=SHAPE["large"],
            border_width=1,
            border_color=THEME["border"],
            **kwargs,
        )
        ctk.CTkLabel(self, text=icon, font=FONTS["display"]).pack(pady=(32, 8))
        ctk.CTkLabel(self, text=title, font=FONTS["title_md"], text_color=THEME["text_primary"]).pack()
        if message:
            ctk.CTkLabel(self, text=message, font=FONTS["body_sm"], text_color=THEME["text_secondary"], wraplength=380, justify="center").pack(pady=(4, 0))
        if action_label and action_cmd:
            ctk.CTkButton(
                self,
                text=action_label,
                font=FONTS["body_lg"],
                height=LAYOUT["btn_height"],
                corner_radius=SHAPE["small"],
                fg_color=THEME["primary"],
                hover_color=THEME["primary_hover"],
                command=action_cmd,
            ).pack(pady=(20, 32))
        else:
            ctk.CTkFrame(self, height=32, fg_color="transparent").pack()
