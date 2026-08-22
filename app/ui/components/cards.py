import customtkinter as ctk
from datetime import datetime
from app.ui.theme import THEME, FONTS


class MetricCard(ctk.CTkFrame):
    def __init__(self, master, title: str, value: str, icon: str = "📈", subtitle: str = "", **kwargs):
        super().__init__(master, fg_color=THEME["bg_card"], corner_radius=12, border_width=1, border_color=THEME["border"], **kwargs)
        self.grid_columnconfigure(0, weight=1)

        top_row = ctk.CTkFrame(self, fg_color="transparent")
        top_row.pack(fill="x", padx=16, pady=(14, 4))

        ctk.CTkLabel(top_row, text=title.upper(), font=FONTS["badge"], text_color=THEME["text_muted"]).pack(side="left")
        ctk.CTkLabel(top_row, text=icon, font=FONTS["title_md"]).pack(side="right")

        val_label = ctk.CTkLabel(self, text=value, font=FONTS["title_xl"], text_color=THEME["text_primary"])
        val_label.pack(anchor="w", padx=16, pady=(0, 2))

        if subtitle:
            sub_label = ctk.CTkLabel(self, text=subtitle, font=FONTS["body_sm"], text_color=THEME["text_secondary"])
            sub_label.pack(anchor="w", padx=16, pady=(0, 12))
        else:
            ctk.CTkFrame(self, height=6, fg_color="transparent").pack()


class TripCard(ctk.CTkFrame):
    def __init__(self, master, trip, on_view=None, on_edit=None, on_delete=None, on_share=None, **kwargs):
        super().__init__(master, fg_color=THEME["bg_card"], corner_radius=12, border_width=1, border_color=THEME["border"], **kwargs)
        self.trip = trip
        self.on_view = on_view
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.on_share = on_share
        self._build_ui()

    def _build_ui(self):
        self.pack_propagate(False)

        # Header with trip name and visibility badge
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(14, 6))

        title_lbl = ctk.CTkLabel(header, text=self.trip.name, font=FONTS["title_md"], text_color=THEME["text_primary"], anchor="w")
        title_lbl.pack(side="left", fill="x", expand=True)

        is_public = getattr(self.trip, "visibility", "") == "public" or getattr(getattr(self.trip, "visibility", None), "value", "") == "public"
        badge_bg = THEME["info"] if is_public else THEME["border"]
        badge_txt = "PUBLIC" if is_public else "PRIVATE"
        badge = ctk.CTkLabel(header, text=f" {badge_txt} ", font=FONTS["badge"], fg_color=badge_bg, text_color=THEME["text_primary"], corner_radius=4)
        badge.pack(side="right")

        # Date & Stops Info
        s_date = self.trip.start_date.strftime("%b %d, %Y") if hasattr(self.trip.start_date, "strftime") else str(self.trip.start_date)[:10]
        e_date = self.trip.end_date.strftime("%b %d, %Y") if hasattr(self.trip.end_date, "strftime") else str(self.trip.end_date)[:10]
        dates_lbl = ctk.CTkLabel(self, text=f"🗓️  {s_date}  ➔  {e_date}", font=FONTS["body_sm"], text_color=THEME["text_secondary"], anchor="w")
        dates_lbl.pack(fill="x", padx=16, pady=2)

        stops_count = len(getattr(self.trip, "stops", []))
        total_acts = sum(len(getattr(s, "activities", [])) for s in getattr(self.trip, "stops", []))
        meta_lbl = ctk.CTkLabel(self, text=f"📍  {stops_count} Destinations   •   🎟️ {total_acts} Activities", font=FONTS["body_sm"], text_color=THEME["text_muted"], anchor="w")
        meta_lbl.pack(fill="x", padx=16, pady=2)

        # Budget highlight
        if self.trip.total_budget:
            budg_lbl = ctk.CTkLabel(self, text=f"💰  Budget: ${float(self.trip.total_budget):,.2f}", font=FONTS["body_sm"], text_color=THEME["success"], anchor="w")
            budg_lbl.pack(fill="x", padx=16, pady=2)

        # Action Buttons
        btn_bar = ctk.CTkFrame(self, fg_color="transparent")
        btn_bar.pack(fill="x", padx=14, pady=(10, 12), side="bottom")

        if self.on_view:
            v_btn = ctk.CTkButton(btn_bar, text="Open Plan", font=FONTS["body_sm"], height=30, fg_color=THEME["primary"], hover_color=THEME["primary_hover"], command=lambda: self.on_view(self.trip))
            v_btn.pack(side="left", padx=2, expand=True, fill="x")

        if self.on_share:
            s_btn = ctk.CTkButton(btn_bar, text="Share", font=FONTS["body_sm"], height=30, width=54, fg_color=THEME["border"], hover_color=THEME["bg_card_hover"], command=lambda: self.on_share(self.trip))
            s_btn.pack(side="left", padx=2)

        if self.on_delete:
            d_btn = ctk.CTkButton(btn_bar, text="🗑️", font=FONTS["body_sm"], height=30, width=34, fg_color=THEME["danger_bg"], hover_color=THEME["danger"], command=lambda: self.on_delete(self.trip))
            d_btn.pack(side="left", padx=2)


class CityCard(ctk.CTkFrame):
    def __init__(self, master, city, on_add_to_trip=None, on_toggle_save=None, is_saved=False, **kwargs):
        super().__init__(master, fg_color=THEME["bg_card"], corner_radius=12, border_width=1, border_color=THEME["border"], **kwargs)
        self.city = city
        self.on_add_to_trip = on_add_to_trip
        self.on_toggle_save = on_toggle_save
        self.is_saved = is_saved
        self._build_ui()

    def _build_ui(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(14, 4))

        name_lbl = ctk.CTkLabel(hdr, text=f"{self.city.name}, {self.city.country}", font=FONTS["title_md"], text_color=THEME["text_primary"], anchor="w")
        name_lbl.pack(side="left", fill="x", expand=True)

        if self.on_toggle_save:
            save_icon = "⭐ Saved" if self.is_saved else "☆ Save"
            save_color = THEME["warning"] if self.is_saved else THEME["text_muted"]
            save_btn = ctk.CTkButton(hdr, text=save_icon, width=65, height=26, font=FONTS["badge"], fg_color="transparent", hover_color=THEME["bg_card_hover"], text_color=save_color, command=lambda: self.on_toggle_save(self.city))
            save_btn.pack(side="right")

        # Region & popularity
        region_text = f"📍 {self.city.region or 'Global'} • Cost Index: {self.city.cost_index}/100 • Popularity: {self.city.popularity_score}★"
        reg_lbl = ctk.CTkLabel(self, text=region_text, font=FONTS["body_sm"], text_color=THEME["text_secondary"], anchor="w")
        reg_lbl.pack(fill="x", padx=16, pady=2)

        # Description
        desc_txt = self.city.description or "A wonderful travel destination ready to be explored."
        if len(desc_txt) > 130:
            desc_txt = desc_txt[:127] + "..."
        desc_lbl = ctk.CTkLabel(self, text=desc_txt, font=FONTS["body_sm"], text_color=THEME["text_muted"], anchor="w", justify="left", wraplength=340)
        desc_lbl.pack(fill="x", padx=16, pady=(4, 8))

        # Bottom Bar
        b_frame = ctk.CTkFrame(self, fg_color="transparent")
        b_frame.pack(fill="x", padx=14, pady=(4, 12))

        cat_count = len(getattr(self.city, "activities_catalog", []))
        c_lbl = ctk.CTkLabel(b_frame, text=f"🎟️ {cat_count} catalog activities", font=FONTS["body_sm"], text_color=THEME["info"])
        c_lbl.pack(side="left")

        if self.on_add_to_trip:
            add_btn = ctk.CTkButton(b_frame, text="+ Add to Trip", font=FONTS["body_sm"], height=28, width=100, fg_color=THEME["primary"], hover_color=THEME["primary_hover"], command=lambda: self.on_add_to_trip(self.city))
            add_btn.pack(side="right")


class ActivityCard(ctk.CTkFrame):
    def __init__(self, master, activity, on_add=None, on_remove=None, **kwargs):
        super().__init__(master, fg_color=THEME["bg_card"], corner_radius=10, border_width=1, border_color=THEME["border"], **kwargs)
        self.activity = activity
        self.on_add = on_add
        self.on_remove = on_remove
        self._build_ui()

    def _build_ui(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=14, pady=(10, 2))

        act_type = getattr(self.activity, "activity_type", "sightseeing")
        if hasattr(act_type, "value"):
            act_type = act_type.value

        title = getattr(self.activity, "name", "Activity")
        t_lbl = ctk.CTkLabel(hdr, text=title, font=FONTS["body_lg"], text_color=THEME["text_primary"], anchor="w")
        t_lbl.pack(side="left", fill="x", expand=True)

        type_badge = ctk.CTkLabel(hdr, text=f" {act_type.upper()} ", font=FONTS["badge"], fg_color=THEME["border"], text_color=THEME["text_secondary"], corner_radius=4)
        type_badge.pack(side="right")

        # Details
        cost_val = getattr(self.activity, "avg_cost", None) or getattr(self.activity, "estimated_cost", None) or 0.0
        dur_val = getattr(self.activity, "duration_minutes", None)
        dur_str = f" • ⏱️ {dur_val} min" if dur_val else ""
        cur = getattr(self.activity, "currency", "USD")

        info_lbl = ctk.CTkLabel(self, text=f"💲 {cur} ${float(cost_val):,.2f}{dur_str}", font=FONTS["body_sm"], text_color=THEME["success"], anchor="w")
        info_lbl.pack(fill="x", padx=14, pady=2)

        desc = getattr(self.activity, "description", "") or ""
        if desc:
            if len(desc) > 110:
                desc = desc[:107] + "..."
            d_lbl = ctk.CTkLabel(self, text=desc, font=FONTS["body_sm"], text_color=THEME["text_muted"], anchor="w", justify="left")
            d_lbl.pack(fill="x", padx=14, pady=(0, 6))

        if self.on_add or self.on_remove:
            b_bar = ctk.CTkFrame(self, fg_color="transparent")
            b_bar.pack(fill="x", padx=14, pady=(2, 8))
            if self.on_add:
                ctk.CTkButton(b_bar, text="+ Add to Stop", font=FONTS["body_sm"], height=26, fg_color=THEME["primary"], hover_color=THEME["primary_hover"], command=lambda: self.on_add(self.activity)).pack(side="right")
            if self.on_remove:
                ctk.CTkButton(b_bar, text="Remove", font=FONTS["body_sm"], height=26, fg_color=THEME["danger_bg"], hover_color=THEME["danger"], command=lambda: self.on_remove(self.activity)).pack(side="right")
