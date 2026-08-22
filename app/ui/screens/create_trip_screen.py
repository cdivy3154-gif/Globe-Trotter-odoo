"""
Phase 4a — Create Trip Screen
3-step wizard:
  Step 1: Trip Name, Description, Visibility
  Step 2: Date Range (tkcalendar pickers), Budget, Currency
  Step 3: Optional first city stop + Cover Photo
Creates trip → auto-navigates to itinerary_builder.
"""
import customtkinter as ctk
from datetime import datetime, timedelta, UTC
from tkinter import filedialog
from tkcalendar import DateEntry
from app.ui.theme import THEME, FONTS, SHAPE, LAYOUT
from app.ui.components.header import Header
from app.services.trip_service import TripService
from app.services.city_service import CityService
from app.services.upload_service import UploadService
from app.schemas.trip import TripCreate, StopCreate
from app.schemas.city import CitySearchParams
from app.core.exceptions import AppException

_CURRENCIES = ["USD ($)", "EUR (€)", "GBP (£)", "JPY (¥)", "INR (₹)", "AUD (A$)", "CAD (C$)"]


def _entry(parent, placeholder="", show="") -> ctk.CTkEntry:
    e = ctk.CTkEntry(
        parent,
        placeholder_text=placeholder,
        show=show,
        height=LAYOUT["input_height"],
        font=FONTS["body"],
        fg_color=THEME["bg_input"],
        border_color=THEME["border"],
        border_width=1,
        corner_radius=SHAPE["small"],
        text_color=THEME["text_primary"],
        placeholder_text_color=THEME["text_muted"],
    )
    e.bind("<FocusIn>",  lambda _: e.configure(border_color=THEME["border_focus"]))
    e.bind("<FocusOut>", lambda _: e.configure(border_color=THEME["border"]))
    return e


def _label(parent, text):
    ctk.CTkLabel(parent, text=text, font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w", padx=0, pady=(8, 2))


# ══════════════════════════════════════════════════════════════════
class CreateTripScreen(ctk.CTkScrollableFrame):
    def __init__(self, master, navigate_callback, session_factory, current_user, initial_city_id=None, **kwargs):
        super().__init__(
            master,
            fg_color=THEME["bg_dark"],
            scrollbar_button_color=THEME["border"],
            scrollbar_button_hover_color=THEME["border_light"],
            **kwargs,
        )
        self.navigate_callback   = navigate_callback
        self.session_factory     = session_factory
        self.current_user        = current_user
        self.initial_city_id     = initial_city_id
        self.selected_cover_path = None
        self.cities              = []
        self._step               = 1   # 1, 2, or 3

        # Load city list once
        with self.session_factory() as session:
            self.cities, _ = CityService(session).search_cities(CitySearchParams(limit=200))

        self._build_ui()

    # ─────────────────────────────────────────────────────────────
    def _build_ui(self):
        Header(
            self,
            title="Plan a New Journey 🚀",
            subtitle="Design your multi-city trip step by step.",
            breadcrumb=["Dashboard", "Plan New Trip"],
        ).pack(fill="x", padx=20, pady=(18, 12))

        # Step indicator
        self._step_bar = ctk.CTkFrame(self, fg_color="transparent")
        self._step_bar.pack(fill="x", padx=20, pady=(0, 16))
        self._render_step_bar()

        # Main form card
        self._card = ctk.CTkFrame(
            self,
            fg_color=THEME["bg_card"],
            corner_radius=SHAPE["large"],
            border_width=1,
            border_color=THEME["border"],
        )
        self._card.pack(fill="x", padx=20, pady=(0, 24))

        ctk.CTkFrame(self._card, height=4, fg_color=THEME["primary"], corner_radius=0).pack(fill="x")

        self._form_area = ctk.CTkFrame(self._card, fg_color="transparent")
        self._form_area.pack(fill="both", padx=32, pady=24)

        # Error / status label
        self._err = ctk.CTkLabel(self._card, text="", font=FONTS["body_sm"], text_color=THEME["danger"], wraplength=600)
        self._err.pack(fill="x", padx=32, pady=(0, 8))

        # Nav buttons
        self._nav_bar = ctk.CTkFrame(self._card, fg_color=THEME["bg_surface2"], corner_radius=0)
        self._nav_bar.pack(fill="x", side="bottom")

        self._render_step()

    # ─────────────────────────────────────────────────────────────
    # STEP BAR
    # ─────────────────────────────────────────────────────────────
    def _render_step_bar(self):
        for w in self._step_bar.winfo_children():
            w.destroy()

        steps = [
            (1, "Trip Details"),
            (2, "Dates & Budget"),
            (3, "First Stop"),
        ]
        for i, (num, lbl) in enumerate(steps):
            active = num == self._step
            done   = num < self._step

            col = THEME["primary"] if active else (THEME["success"] if done else THEME["border"])
            fg  = THEME["on_primary"] if active else (THEME["success"] if done else THEME["text_muted"])

            pip = ctk.CTkLabel(
                self._step_bar,
                text=f" ✓ " if done else f" {num} ",
                font=FONTS["badge"],
                fg_color=col,
                text_color=fg,
                corner_radius=SHAPE["full"],
                width=28,
                height=28,
            )
            pip.pack(side="left")

            ctk.CTkLabel(
                self._step_bar,
                text=lbl,
                font=FONTS["body_sm"],
                text_color=THEME["text_primary"] if active else THEME["text_muted"],
            ).pack(side="left", padx=(6, 0))

            if i < len(steps) - 1:
                ctk.CTkFrame(self._step_bar, height=1, width=40, fg_color=THEME["border"]).pack(side="left", padx=12)

    # ─────────────────────────────────────────────────────────────
    # RENDER CURRENT STEP FORM
    # ─────────────────────────────────────────────────────────────
    def _render_step(self):
        for w in self._form_area.winfo_children():
            w.destroy()
        for w in self._nav_bar.winfo_children():
            w.destroy()
        self._err.configure(text="")
        self._render_step_bar()

        if self._step == 1:
            self._build_step1()
        elif self._step == 2:
            self._build_step2()
        elif self._step == 3:
            self._build_step3()

        self._build_nav()

    # ─────────────────────────────────────────────────────────────
    # STEP 1 — Trip identity
    # ─────────────────────────────────────────────────────────────
    def _build_step1(self):
        f = self._form_area
        ctk.CTkLabel(f, text="Step 1: Trip Identity", font=FONTS["title_sm"], text_color=THEME["primary"]).pack(anchor="w", pady=(0, 12))

        _label(f, "Trip Name  *")
        self._name = _entry(f, "e.g. Grand European Summer, Tokyo & Kyoto Express")
        if hasattr(self, "_s1_name"):
            self._name.insert(0, self._s1_name)
        self._name.pack(fill="x")

        _label(f, "Description & Notes")
        self._desc = ctk.CTkTextbox(
            f,
            height=90,
            font=FONTS["body"],
            fg_color=THEME["bg_input"],
            border_color=THEME["border"],
            border_width=1,
            text_color=THEME["text_primary"],
        )
        self._desc.pack(fill="x", pady=(0, 4))
        if hasattr(self, "_s1_desc"):
            self._desc.insert("1.0", self._s1_desc)

        _label(f, "Visibility")
        self._visibility = ctk.CTkSegmentedButton(
            f,
            values=["Private 🔒", "Public 🌐"],
            font=FONTS["body_sm"],
            fg_color=THEME["bg_input"],
            selected_color=THEME["primary"],
            selected_hover_color=THEME["primary_hover"],
            unselected_color=THEME["bg_input"],
            unselected_hover_color=THEME["bg_card_hover"],
            text_color=THEME["text_secondary"],
        )
        self._visibility.set(getattr(self, "_s1_vis", "Private 🔒"))
        self._visibility.pack(anchor="w", pady=(0, 4))

    def _validate_step1(self) -> bool:
        name = self._name.get().strip()
        if not name:
            self._err.configure(text="⚠  Trip name is required")
            return False
        self._s1_name = name
        self._s1_desc = self._desc.get("1.0", "end-1c").strip()
        self._s1_vis  = self._visibility.get()
        return True

    # ─────────────────────────────────────────────────────────────
    # STEP 2 — Dates & Budget
    # ─────────────────────────────────────────────────────────────
    def _build_step2(self):
        f = self._form_area
        ctk.CTkLabel(f, text="Step 2: Dates & Budget", font=FONTS["title_sm"], text_color=THEME["primary"]).pack(anchor="w", pady=(0, 12))

        dates_row = ctk.CTkFrame(f, fg_color="transparent")
        dates_row.pack(fill="x")
        dates_row.grid_columnconfigure((0, 1), weight=1)

        # Start Date (tkcalendar)
        s_col = ctk.CTkFrame(dates_row, fg_color="transparent")
        s_col.grid(row=0, column=0, sticky="ew", padx=(0, 12))
        ctk.CTkLabel(s_col, text="Start Date  *", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w")
        self._start_cal = DateEntry(
            s_col,
            font=("Segoe UI", 12),
            background=THEME["primary"],
            foreground="white",
            borderwidth=1,
            date_pattern="yyyy-mm-dd",
        )
        if hasattr(self, "_s2_start"):
            self._start_cal.set_date(self._s2_start)
        else:
            self._start_cal.set_date(datetime.now().date())
        self._start_cal.pack(fill="x", pady=(4, 0))

        # End Date
        e_col = ctk.CTkFrame(dates_row, fg_color="transparent")
        e_col.grid(row=0, column=1, sticky="ew", padx=(12, 0))
        ctk.CTkLabel(e_col, text="End Date  *", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w")
        self._end_cal = DateEntry(
            e_col,
            font=("Segoe UI", 12),
            background=THEME["primary"],
            foreground="white",
            borderwidth=1,
            date_pattern="yyyy-mm-dd",
        )
        if hasattr(self, "_s2_end"):
            self._end_cal.set_date(self._s2_end)
        else:
            self._end_cal.set_date((datetime.now() + timedelta(days=7)).date())
        self._end_cal.pack(fill="x", pady=(4, 0))

        # Budget + Currency
        budget_row = ctk.CTkFrame(f, fg_color="transparent")
        budget_row.pack(fill="x", pady=(16, 0))
        budget_row.grid_columnconfigure(0, weight=1)
        budget_row.grid_columnconfigure(1, weight=0)

        ctk.CTkLabel(budget_row, text="Total Budget", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).grid(row=0, column=0, sticky="w", padx=(0, 8))
        ctk.CTkLabel(budget_row, text="Currency", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).grid(row=0, column=1, sticky="w", padx=(8, 0))

        self._budget = _entry(budget_row, "e.g. 2500")
        if hasattr(self, "_s2_budget"):
            self._budget.insert(0, self._s2_budget)
        self._budget.grid(row=1, column=0, sticky="ew", padx=(0, 8))

        self._currency = ctk.CTkComboBox(
            budget_row,
            values=_CURRENCIES,
            width=130,
            height=LAYOUT["input_height"],
            font=FONTS["body"],
            fg_color=THEME["bg_input"],
            border_color=THEME["border"],
            text_color=THEME["text_primary"],
        )
        self._currency.set(getattr(self, "_s2_currency", "USD ($)"))
        self._currency.grid(row=1, column=1, sticky="ew", padx=(8, 0))

    def _validate_step2(self) -> bool:
        try:
            s = self._start_cal.get_date()
            e = self._end_cal.get_date()
        except Exception:
            self._err.configure(text="⚠  Please select valid dates")
            return False

        if s > e:
            self._err.configure(text="⚠  Start date cannot be after end date")
            return False

        budget_str = self._budget.get().strip()
        if budget_str:
            try:
                v = float(budget_str)
                if v < 0:
                    raise ValueError
            except ValueError:
                self._err.configure(text="⚠  Budget must be a positive number")
                return False

        self._s2_start    = s
        self._s2_end      = e
        self._s2_budget   = budget_str
        self._s2_currency = self._currency.get()
        return True

    # ─────────────────────────────────────────────────────────────
    # STEP 3 — First Stop + Cover Photo
    # ─────────────────────────────────────────────────────────────
    def _build_step3(self):
        f = self._form_area
        ctk.CTkLabel(f, text="Step 3: First Stop & Cover (Optional)", font=FONTS["title_sm"], text_color=THEME["primary"]).pack(anchor="w", pady=(0, 12))

        _label(f, "First Destination City")
        city_names = ["(Select later in builder)"] + [f"{c.name}, {c.country}" for c in self.cities]
        self._city_combo = ctk.CTkComboBox(
            f,
            values=city_names,
            height=LAYOUT["input_height"],
            font=FONTS["body"],
            fg_color=THEME["bg_input"],
            border_color=THEME["border"],
            text_color=THEME["text_primary"],
        )
        if self.initial_city_id:
            for c in self.cities:
                if c.id == self.initial_city_id:
                    self._city_combo.set(f"{c.name}, {c.country}")
                    break
        elif hasattr(self, "_s3_city"):
            self._city_combo.set(self._s3_city)
        else:
            self._city_combo.set("(Select later in builder)")
        self._city_combo.pack(fill="x")

        # Cover photo
        ctk.CTkLabel(f, text="Cover Photo", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w", pady=(16, 4))

        cover_row = ctk.CTkFrame(f, fg_color=THEME["bg_input"], corner_radius=SHAPE["small"], border_width=1, border_color=THEME["border"])
        cover_row.pack(fill="x")

        self._cover_lbl = ctk.CTkLabel(
            cover_row,
            text="🖼️  No file chosen",
            font=FONTS["body_sm"],
            text_color=THEME["text_muted"],
            anchor="w",
        )
        self._cover_lbl.pack(side="left", padx=14, pady=10, fill="x", expand=True)
        if hasattr(self, "_s3_cover") and self._s3_cover:
            fn = self._s3_cover.replace("\\", "/").split("/")[-1]
            self._cover_lbl.configure(text=f"✅  {fn}", text_color=THEME["success"])

        ctk.CTkButton(
            cover_row,
            text="Browse...",
            font=FONTS["body_sm"],
            height=32,
            width=90,
            corner_radius=SHAPE["extra_small"],
            fg_color=THEME["border"],
            hover_color=THEME["bg_card_hover"],
            command=self._pick_cover,
        ).pack(side="right", padx=10, pady=10)

        # Summary card
        summary = ctk.CTkFrame(f, fg_color=THEME["primary_container"], corner_radius=SHAPE["medium"])
        summary.pack(fill="x", pady=(20, 0))
        ctk.CTkLabel(summary, text="Trip Summary", font=FONTS["body_lg"], text_color=THEME["primary"]).pack(anchor="w", padx=16, pady=(12, 4))

        name = getattr(self, "_s1_name", "—")
        s    = getattr(self, "_s2_start", "—")
        e    = getattr(self, "_s2_end",   "—")
        bud  = getattr(self, "_s2_budget", "—") or "—"
        cur  = getattr(self, "_s2_currency", "USD ($)")

        lines = [
            f"✈️  {name}",
            f"📅  {s}  →  {e}",
            f"💰  Budget: {bud} {cur.split()[0]}",
        ]
        for line in lines:
            ctk.CTkLabel(summary, text=line, font=FONTS["body"], text_color=THEME["on_primary_container"]).pack(anchor="w", padx=16)
        ctk.CTkFrame(summary, height=12, fg_color="transparent").pack()

    def _pick_cover(self):
        path = filedialog.askopenfilename(
            title="Select Cover Photo",
            filetypes=[("Image Files", "*.jpg *.jpeg *.png *.webp"), ("All Files", "*.*")],
        )
        if path:
            self._s3_cover = path
            fn = path.replace("\\", "/").split("/")[-1]
            self._cover_lbl.configure(text=f"✅  {fn}", text_color=THEME["success"])

    # ─────────────────────────────────────────────────────────────
    # NAV BUTTONS
    # ─────────────────────────────────────────────────────────────
    def _build_nav(self):
        bar = self._nav_bar

        if self._step > 1:
            ctk.CTkButton(
                bar,
                text="← Back",
                font=FONTS["body_lg"],
                height=LAYOUT["btn_height"],
                width=120,
                corner_radius=SHAPE["small"],
                fg_color=THEME["bg_card"],
                hover_color=THEME["bg_card_hover"],
                border_width=1,
                border_color=THEME["border"],
                text_color=THEME["text_secondary"],
                command=self._go_back,
            ).pack(side="left", padx=20, pady=14)

        ctk.CTkButton(
            bar,
            text="Cancel",
            font=FONTS["body_sm"],
            height=LAYOUT["btn_height_sm"],
            width=80,
            corner_radius=SHAPE["small"],
            fg_color="transparent",
            hover_color=THEME["bg_card"],
            text_color=THEME["text_muted"],
            command=lambda: self.navigate_callback("dashboard"),
        ).pack(side="left", padx=(0, 8), pady=14)

        next_text = "Next →" if self._step < 3 else "🚀  Create Trip"
        next_color = THEME["primary"] if self._step < 3 else THEME["accent"]
        ctk.CTkButton(
            bar,
            text=next_text,
            font=FONTS["body_lg"],
            height=LAYOUT["btn_height"],
            corner_radius=SHAPE["small"],
            fg_color=next_color,
            hover_color=THEME["primary_hover"],
            command=self._go_next,
        ).pack(side="right", padx=20, pady=14)

    def _go_back(self):
        self._step -= 1
        self._render_step()

    def _go_next(self):
        self._err.configure(text="")
        if self._step == 1:
            if not self._validate_step1():
                return
            self._step = 2
            self._render_step()
        elif self._step == 2:
            if not self._validate_step2():
                return
            self._step = 3
            self._render_step()
        elif self._step == 3:
            self._s3_city  = self._city_combo.get()
            if not hasattr(self, "_s3_cover"):
                self._s3_cover = None
            self._create_trip()

    # ─────────────────────────────────────────────────────────────
    # CREATE
    # ─────────────────────────────────────────────────────────────
    def _create_trip(self):
        try:
            s_dt = datetime.combine(self._s2_start, datetime.min.time()).replace(tzinfo=UTC)
            e_dt = datetime.combine(self._s2_end,   datetime.min.time()).replace(tzinfo=UTC)
            bud  = float(self._s2_budget) if self._s2_budget else None

            cover_saved = None
            if self._s3_cover:
                try:
                    cover_saved = UploadService().save_image(self._s3_cover)
                except Exception:
                    pass

            with self.session_factory() as session:
                ts = TripService(session)
                cs = CityService(session)

                new_trip = ts.create_trip(
                    self.current_user.id,
                    TripCreate(
                        name=self._s1_name,
                        description=self._s1_desc or None,
                        start_date=s_dt,
                        end_date=e_dt,
                        total_budget=bud,
                        cover_photo_path=cover_saved,
                    ),
                )

                # Optionally add first city stop
                city_val = self._s3_city
                if city_val and city_val != "(Select later in builder)":
                    selected = next(
                        (c for c in self.cities if f"{c.name}, {c.country}" == city_val),
                        None,
                    )
                    if selected:
                        ts.add_stop(
                            new_trip.id,
                            self.current_user.id,
                            StopCreate(
                                city_id=selected.id,
                                arrival_date=s_dt,
                                departure_date=e_dt,
                            ),
                        )

                session.commit()
                trip_id = new_trip.id

            self.navigate_callback("itinerary_builder", trip_id=trip_id)

        except AppException as ex:
            self._err.configure(text=str(ex.detail))
        except Exception as ex:
            self._err.configure(text=f"Error: {ex}")
