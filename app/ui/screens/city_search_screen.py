"""
Phase 6a — City Search / Directory Screen
Features:
  - Searchable city grid (name, country, region)
  - Region chip filter bar (All, Europe, Asia, Americas…)
  - Cost index range slider visual
  - 3-column CityCard grid with save-toggle + plan CTA
  - Add City modal (admin-only or open)
  - City detail popover on card click
"""
import customtkinter as ctk
from app.ui.theme import THEME, FONTS, SHAPE, LAYOUT
from app.ui.components.header import Header
from app.ui.components.cards import CityCard, EmptyState
from app.services.city_service import CityService
from app.schemas.city import CitySearchParams, CityCreate
from app.core.exceptions import AppException

_REGIONS = ["All Regions", "Europe", "Asia", "North America", "South America",
            "Middle East", "Africa", "Oceania", "Southeast Asia", "Central Asia"]

_REGION_ICONS = {
    "All Regions": "🌍",  "Europe": "🏰", "Asia": "🗼",
    "North America": "🗽", "South America": "🌴", "Middle East": "🕌",
    "Africa": "🦁", "Oceania": "🦘", "Southeast Asia": "🏯", "Central Asia": "🏔️",
}


def _mk_entry(parent, placeholder="", val="") -> ctk.CTkEntry:
    e = ctk.CTkEntry(
        parent,
        placeholder_text=placeholder,
        height=LAYOUT["input_height"],
        font=FONTS["body"],
        fg_color=THEME["bg_input"],
        border_color=THEME["border"],
        border_width=1,
        corner_radius=SHAPE["small"],
        text_color=THEME["text_primary"],
        placeholder_text_color=THEME["text_muted"],
    )
    if val:
        e.insert(0, val)
    e.bind("<FocusIn>",  lambda _: e.configure(border_color=THEME["border_focus"]))
    e.bind("<FocusOut>", lambda _: e.configure(border_color=THEME["border"]))
    return e


# ══════════════════════════════════════════════════════════════════
class CitySearchScreen(ctk.CTkScrollableFrame):
    def __init__(self, master, navigate_callback, session_factory, current_user, **kwargs):
        super().__init__(
            master,
            fg_color=THEME["bg_dark"],
            scrollbar_button_color=THEME["border"],
            scrollbar_button_hover_color=THEME["border_light"],
            **kwargs,
        )
        self.navigate_callback  = navigate_callback
        self.session_factory    = session_factory
        self.current_user       = current_user
        self.search_query       = ""
        self.selected_region    = "All Regions"
        self.saved_city_ids: set = set()
        self.grid_columnconfigure(0, weight=1)
        self.refresh()

    # ─────────────────────────────────────────────────────────────
    def refresh(self):
        for w in self.winfo_children():
            w.destroy()

        # Fetch saved set
        with self.session_factory() as session:
            saved = CityService(session).get_saved_destinations(self.current_user.id)
            self.saved_city_ids = {s.city_id for s in saved}

        Header(
            self,
            title="Global City Directory 🏙️",
            subtitle="Discover destinations, browse cost index, bookmark favourites, and launch trip plans.",
            action_button=("➕  Add City", self._open_add_city_modal, THEME["bg_input"]),
            breadcrumb=["Dashboard", "City Directory"],
        ).pack(fill="x", padx=20, pady=(18, 10))

        # ── Filter card ───────────────────────────────────────────
        filter_card = ctk.CTkFrame(
            self,
            fg_color=THEME["bg_card"],
            corner_radius=SHAPE["medium"],
            border_width=1,
            border_color=THEME["border"],
        )
        filter_card.pack(fill="x", padx=20, pady=(0, 10))

        inner = ctk.CTkFrame(filter_card, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=14)
        inner.grid_columnconfigure(0, weight=1)

        # Search row
        search_row = ctk.CTkFrame(inner, fg_color="transparent")
        search_row.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        search_row.grid_columnconfigure(0, weight=1)

        self._search_e = _mk_entry(search_row, "🔍  Search cities by name or country...", self.search_query)
        self._search_e.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self._search_e.bind("<Return>", lambda _: self._do_search())

        ctk.CTkButton(
            search_row,
            text="Search",
            font=FONTS["body_sm"],
            height=LAYOUT["input_height"],
            width=80,
            corner_radius=SHAPE["small"],
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            command=self._do_search,
        ).grid(row=0, column=1)

        # Region chip bar
        chip_row = ctk.CTkFrame(inner, fg_color="transparent")
        chip_row.grid(row=1, column=0, sticky="ew")

        for region in _REGIONS:
            icon    = _REGION_ICONS.get(region, "🌐")
            active  = region == self.selected_region
            fg      = THEME["primary"] if active else THEME["bg_input"]
            tc      = THEME["on_primary"] if active else THEME["text_secondary"]
            ctk.CTkButton(
                chip_row,
                text=f"{icon} {region}",
                font=FONTS["badge"],
                height=28,
                corner_radius=SHAPE["full"],
                fg_color=fg,
                hover_color=THEME["primary_hover"],
                text_color=tc,
                border_width=0 if active else 1,
                border_color=THEME["border"],
                command=lambda r=region: self._set_region(r),
            ).pack(side="left", padx=(0, 5), pady=2)

        # ── Results ───────────────────────────────────────────────
        self._render_results()

    # ─────────────────────────────────────────────────────────────
    def _render_results(self):
        if hasattr(self, "_results_frame") and self._results_frame.winfo_exists():
            self._results_frame.destroy()

        # Fetch with filters
        params = CitySearchParams(
            query=self.search_query or None,
            region=None if self.selected_region == "All Regions" else self.selected_region,
            limit=60,
        )
        with self.session_factory() as session:
            cities, total = CityService(session).search_cities(params)

        self._results_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._results_frame.pack(fill="x", padx=20, pady=(4, 24))

        # Count label
        ctk.CTkLabel(
            self._results_frame,
            text=f"{total} cities found" if total else f"{len(cities)} cities",
            font=FONTS["body_sm"],
            text_color=THEME["text_muted"],
            anchor="w",
        ).pack(fill="x", pady=(0, 8))

        if not cities:
            EmptyState(
                self._results_frame,
                icon="🏙️",
                title="No cities match your search",
                message="Try a different name, country, or remove the region filter.",
                action_label="Clear Filter",
                action_cmd=self._clear_filters,
            ).pack(fill="x")
            return

        grid = ctk.CTkFrame(self._results_frame, fg_color="transparent")
        grid.pack(fill="x")
        grid.grid_columnconfigure((0, 1, 2), weight=1)

        for i, city in enumerate(cities):
            r, c = divmod(i, 3)
            CityCard(
                grid,
                city=city,
                is_saved=city.id in self.saved_city_ids,
                on_plan=lambda ct: self.navigate_callback("create_trip", city_id=ct.id),
                on_save=lambda ct: self._toggle_save(ct),
            ).grid(row=r, column=c, padx=4, pady=5, sticky="ew")

    # ─────────────────────────────────────────────────────────────
    def _set_region(self, region: str):
        self.selected_region = region
        self.refresh()

    def _do_search(self):
        self.search_query = self._search_e.get().strip()
        self._render_results()

    def _clear_filters(self):
        self.search_query    = ""
        self.selected_region = "All Regions"
        self.refresh()

    def _toggle_save(self, city):
        with self.session_factory() as session:
            CityService(session).toggle_save_destination(self.current_user.id, city.id)
            session.commit()
        if city.id in self.saved_city_ids:
            self.saved_city_ids.discard(city.id)
        else:
            self.saved_city_ids.add(city.id)
        self._render_results()

    # ─────────────────────────────────────────────────────────────
    # ADD CITY MODAL
    # ─────────────────────────────────────────────────────────────
    def _open_add_city_modal(self):
        win = ctk.CTkToplevel(self)
        win.title("Add New City")
        win.geometry("520x560")
        win.configure(fg_color=THEME["bg_card"])
        win.grab_set()
        win.focus()

        ctk.CTkFrame(win, height=4, fg_color=THEME["primary"]).pack(fill="x")
        ctk.CTkLabel(win, text="🏙️  Add New City", font=FONTS["title_md"], text_color=THEME["text_primary"]).pack(anchor="w", padx=24, pady=(20, 4))

        def lbl(text):
            ctk.CTkLabel(win, text=text, font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w", padx=24, pady=(10, 2))

        lbl("City Name  *")
        name_e = _mk_entry(win, "e.g. Barcelona")
        name_e.pack(fill="x", padx=24, pady=(0, 4))

        lbl("Country  *")
        country_e = _mk_entry(win, "e.g. Spain")
        country_e.pack(fill="x", padx=24, pady=(0, 4))

        # Country + Region row
        cr_row = ctk.CTkFrame(win, fg_color="transparent")
        cr_row.pack(fill="x", padx=24, pady=(0, 4))
        cr_row.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(cr_row, text="Region", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).grid(row=0, column=0, sticky="w", padx=(0, 8))
        ctk.CTkLabel(cr_row, text="Cost Index (0–100)", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).grid(row=0, column=1, sticky="w", padx=(8, 0))

        region_cb = ctk.CTkComboBox(cr_row, values=_REGIONS[1:], height=LAYOUT["input_height"], font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"], text_color=THEME["text_primary"])
        region_cb.set("Europe")
        region_cb.grid(row=1, column=0, sticky="ew", padx=(0, 8))

        cost_e = _mk_entry(cr_row, "e.g. 55")
        cost_e.insert(0, "50")
        cost_e.grid(row=1, column=1, sticky="ew", padx=(8, 0))

        lbl("Timezone (optional)")
        tz_e = _mk_entry(win, "e.g. Europe/Madrid")
        tz_e.pack(fill="x", padx=24, pady=(0, 4))

        lbl("Description (optional)")
        desc_box = ctk.CTkTextbox(win, height=70, font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"], border_width=1, text_color=THEME["text_primary"])
        desc_box.pack(fill="x", padx=24, pady=(0, 4))

        err = ctk.CTkLabel(win, text="", font=FONTS["body_sm"], text_color=THEME["danger"])
        err.pack(fill="x", padx=24, pady=4)

        def save():
            name_val    = name_e.get().strip()
            country_val = country_e.get().strip()
            if not name_val or not country_val:
                err.configure(text="City name and country are required")
                return
            try:
                cost_idx = int(cost_e.get().strip() or 50)
                with self.session_factory() as session:
                    CityService(session).create_city(
                        CityCreate(
                            name=name_val,
                            country=country_val,
                            region=region_cb.get(),
                            cost_index=cost_idx,
                            timezone=tz_e.get().strip() or None,
                            description=desc_box.get("1.0", "end-1c").strip() or None,
                        )
                    )
                    session.commit()
                win.destroy()
                self.refresh()
            except AppException as ex:
                err.configure(text=str(ex.detail))
            except Exception as ex:
                err.configure(text=f"Error: {ex}")

        ctk.CTkButton(win, text="Save City", font=FONTS["body_lg"], height=LAYOUT["btn_height"], corner_radius=SHAPE["small"], fg_color=THEME["primary"], hover_color=THEME["primary_hover"], command=save).pack(fill="x", padx=24, pady=(4, 16))
