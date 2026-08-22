"""
Phase 2 — Login & Auth Screen
Two-panel layout:
  Left  → Brand splash (gradient dots, globe emoji, tagline, feature pills)
  Right → TabView: Log In / Create Account / Reset Password

Features:
  - Password strength bar on signup
  - Inline field validation + red/green helper text
  - Loading spinner (button text swap) during auth
  - Remember-me pre-fill for demo credentials
  - Quick Admin Login shortcut
"""
import threading
import customtkinter as ctk
from app.ui.theme import THEME, FONTS, SHAPE, LAYOUT
from app.services.auth_service import AuthService
from app.core.exceptions import AppException

# ── Feature bullets shown on the left splash panel ───────────────
_FEATURES = [
    ("✈️", "Plan multi-city itineraries in minutes"),
    ("💰", "Smart budget tracking & cost alerts"),
    ("📅", "Visual calendar & timeline view"),
    ("🔗", "Share & clone community trips"),
    ("🏙️", "Global city directory with cost index"),
    ("📊", "Analytics & trip insights"),
]


def _pw_strength(pw: str) -> tuple[int, str, str]:
    """Returns (score 0-4, label, color)."""
    s = 0
    if len(pw) >= 6:  s += 1
    if len(pw) >= 10: s += 1
    if any(c.isdigit() for c in pw):   s += 1
    if any(not c.isalnum() for c in pw): s += 1
    labels = {0: "Too short", 1: "Weak", 2: "Fair", 3: "Good", 4: "Strong"}
    colors = {
        0: THEME["danger"],
        1: THEME["danger"],
        2: THEME["warning"],
        3: THEME["accent"],
        4: THEME["success"],
    }
    return s, labels[s], colors[s]


# ══════════════════════════════════════════════════════════════════
class LoginScreen(ctk.CTkFrame):
    def __init__(self, master, on_login_success, session_factory, **kwargs):
        super().__init__(master, fg_color=THEME["bg_dark"], **kwargs)
        self.on_login_success = on_login_success
        self.session_factory  = session_factory
        self._loading = False

        self.grid_columnconfigure(0, weight=3)   # left splash
        self.grid_columnconfigure(1, weight=4)   # right form
        self.grid_rowconfigure(0, weight=1)

        self._build_left()
        self._build_right()

    # ─────────────────────────────────────────────────────────────
    # LEFT PANEL — brand splash
    # ─────────────────────────────────────────────────────────────
    def _build_left(self):
        left = ctk.CTkFrame(
            self,
            fg_color=THEME["primary_container"],
            corner_radius=0,
        )
        left.grid(row=0, column=0, sticky="nsew")
        left.grid_rowconfigure(1, weight=1)
        left.grid_columnconfigure(0, weight=1)

        # Dot-grid decoration (simulated with small frames)
        dots = ctk.CTkFrame(left, fg_color="transparent")
        dots.grid(row=0, column=0, padx=40, pady=(50, 0), sticky="w")
        for r in range(4):
            for c in range(8):
                alpha = THEME["primary_dim"] if (r + c) % 2 == 0 else THEME["border"]
                ctk.CTkFrame(dots, width=6, height=6, fg_color=alpha, corner_radius=SHAPE["full"]).grid(row=r, column=c, padx=4, pady=4)

        # Globe + wordmark
        center = ctk.CTkFrame(left, fg_color="transparent")
        center.grid(row=1, column=0, padx=40, sticky="nsew")
        center.grid_rowconfigure(0, weight=1)
        center.grid_columnconfigure(0, weight=1)

        inner = ctk.CTkFrame(center, fg_color="transparent")
        inner.grid(row=0, column=0)

        ctk.CTkLabel(inner, text="🌍", font=(FONTS["display"][0], 64)).pack(pady=(0, 8))

        ctk.CTkLabel(
            inner,
            text="GlobeTrotter",
            font=(FONTS["display"][0], 36, "bold"),
            text_color=THEME["primary"],
        ).pack()

        ctk.CTkLabel(
            inner,
            text="Personalized Multi-City Travel Planning",
            font=FONTS["body_lg"],
            text_color=THEME["on_primary_container"],
        ).pack(pady=(4, 32))

        # Feature pills
        for icon, label in _FEATURES:
            row = ctk.CTkFrame(inner, fg_color=THEME["bg_card"], corner_radius=SHAPE["full"])
            row.pack(fill="x", pady=4, ipady=6, ipadx=12)
            ctk.CTkLabel(row, text=icon, font=FONTS["body_lg"]).pack(side="left", padx=(12, 8))
            ctk.CTkLabel(row, text=label, font=FONTS["body"], text_color=THEME["text_secondary"]).pack(side="left")

        # Bottom tagline
        ctk.CTkLabel(
            left,
            text="Dream it. Plan it. Live it.",
            font=(*FONTS["body_sm"][:2], "italic"),
            text_color=THEME["text_muted"],
        ).grid(row=2, column=0, pady=(16, 40))

    # ─────────────────────────────────────────────────────────────
    # RIGHT PANEL — auth forms
    # ─────────────────────────────────────────────────────────────
    def _build_right(self):
        right = ctk.CTkScrollableFrame(
            self,
            fg_color=THEME["bg_dark"],
            corner_radius=0,
            scrollbar_button_color=THEME["border"],
            scrollbar_button_hover_color=THEME["border_light"],
        )
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(0, weight=1)

        # Centered card
        card = ctk.CTkFrame(
            right,
            fg_color=THEME["bg_card"],
            corner_radius=SHAPE["large"],
            border_width=1,
            border_color=THEME["border"],
        )
        card.grid(row=0, column=0, padx=60, pady=60, sticky="nsew")

        # Accent top bar
        ctk.CTkFrame(card, height=4, fg_color=THEME["primary"], corner_radius=0).pack(fill="x", side="top")

        # ── Welcome text ──────────────────────────────────────────
        head = ctk.CTkFrame(card, fg_color="transparent")
        head.pack(fill="x", padx=32, pady=(28, 4))
        ctk.CTkLabel(head, text="Welcome back 👋", font=FONTS["title_lg"], text_color=THEME["text_primary"]).pack(anchor="w")
        ctk.CTkLabel(head, text="Sign in to continue your journey", font=FONTS["body"], text_color=THEME["text_secondary"]).pack(anchor="w", pady=(2, 0))

        # ── TabView ───────────────────────────────────────────────
        self.tabview = ctk.CTkTabview(
            card,
            fg_color=THEME["bg_card"],
            segmented_button_fg_color=THEME["bg_input"],
            segmented_button_selected_color=THEME["primary"],
            segmented_button_selected_hover_color=THEME["primary_hover"],
            segmented_button_unselected_color=THEME["bg_input"],
            segmented_button_unselected_hover_color=THEME["bg_card_hover"],
            text_color=THEME["text_secondary"],
            text_color_disabled=THEME["text_muted"],
        )
        self.tabview.pack(fill="both", expand=True, padx=24, pady=(8, 0))

        self._tab_login  = self.tabview.add("Log In")
        self._tab_signup = self.tabview.add("Sign Up")
        self._tab_reset  = self.tabview.add("Reset")

        self._build_login_tab()
        self._build_signup_tab()
        self._build_reset_tab()

        # ── Status banner ─────────────────────────────────────────
        self.status_label = ctk.CTkLabel(
            card,
            text="",
            font=FONTS["body_sm"],
            text_color=THEME["danger"],
            wraplength=380,
        )
        self.status_label.pack(fill="x", padx=32, pady=(4, 20))

    # ─────────────────────────────────────────────────────────────
    # LOG IN TAB
    # ─────────────────────────────────────────────────────────────
    def _build_login_tab(self):
        tab = self._tab_login
        tab.grid_columnconfigure(0, weight=1)

        self._field_label(tab, "Email Address")
        self.login_email = self._entry(tab, placeholder="demo@globetrotter.com")
        self.login_email.insert(0, "demo@globetrotter.com")
        self.login_email.pack(fill="x", padx=10, pady=(0, 12))

        self._field_label(tab, "Password")
        self.login_pass = self._entry(tab, placeholder="Enter password", show="*")
        self.login_pass.insert(0, "traveler123")
        self.login_pass.pack(fill="x", padx=10, pady=(0, 6))

        # Error hint for login
        self.login_hint = ctk.CTkLabel(tab, text="", font=FONTS["caption"], text_color=THEME["danger"], anchor="w")
        self.login_hint.pack(fill="x", padx=10, pady=(0, 14))

        self.login_btn = ctk.CTkButton(
            tab,
            text="Log In to GlobeTrotter",
            font=FONTS["body_lg"],
            height=LAYOUT["btn_height"],
            corner_radius=SHAPE["small"],
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            command=self._handle_login,
        )
        self.login_btn.pack(fill="x", padx=10, pady=(0, 6))

        # Divider
        div = ctk.CTkFrame(tab, fg_color="transparent")
        div.pack(fill="x", padx=10, pady=4)
        ctk.CTkFrame(div, height=1, fg_color=THEME["border"]).pack(fill="x", pady=4)
        ctk.CTkLabel(div, text="Quick Access", font=FONTS["caption"], text_color=THEME["text_muted"]).pack()

        # Admin quick login
        ctk.CTkButton(
            tab,
            text="⚡  Quick Login as Admin",
            font=FONTS["body_sm"],
            height=LAYOUT["btn_height_sm"],
            corner_radius=SHAPE["small"],
            fg_color=THEME["bg_input"],
            hover_color=THEME["bg_card_hover"],
            border_width=1,
            border_color=THEME["border"],
            text_color=THEME["text_secondary"],
            command=self._quick_login_admin,
        ).pack(fill="x", padx=10, pady=(4, 12))

    # ─────────────────────────────────────────────────────────────
    # SIGN UP TAB
    # ─────────────────────────────────────────────────────────────
    def _build_signup_tab(self):
        tab = self._tab_signup
        tab.grid_columnconfigure(0, weight=1)

        self._field_label(tab, "Full Name")
        self.signup_name = self._entry(tab, placeholder="e.g. Jane Doe")
        self.signup_name.pack(fill="x", padx=10, pady=(0, 10))

        self._field_label(tab, "Email Address")
        self.signup_email = self._entry(tab, placeholder="name@example.com")
        self.signup_email.pack(fill="x", padx=10, pady=(0, 10))

        self._field_label(tab, "Password")
        self.signup_pass = self._entry(tab, placeholder="Min 6 characters", show="*")
        self.signup_pass.pack(fill="x", padx=10, pady=(0, 4))
        self.signup_pass.bind("<KeyRelease>", self._update_pw_strength)

        # Password strength bar
        strength_row = ctk.CTkFrame(tab, fg_color="transparent")
        strength_row.pack(fill="x", padx=10, pady=(0, 4))

        self._pw_bars: list[ctk.CTkFrame] = []
        bar_track = ctk.CTkFrame(strength_row, fg_color="transparent")
        bar_track.pack(side="left", fill="x", expand=True)
        for _ in range(4):
            b = ctk.CTkFrame(bar_track, height=4, fg_color=THEME["border"], corner_radius=SHAPE["full"])
            b.pack(side="left", fill="x", expand=True, padx=2)
            self._pw_bars.append(b)

        self.pw_strength_label = ctk.CTkLabel(strength_row, text="", font=FONTS["caption"], text_color=THEME["text_muted"], width=56)
        self.pw_strength_label.pack(side="left", padx=(6, 0))

        self._field_label(tab, "Confirm Password")
        self.signup_confirm = self._entry(tab, placeholder="Repeat password", show="*")
        self.signup_confirm.pack(fill="x", padx=10, pady=(0, 4))
        self.confirm_hint = ctk.CTkLabel(tab, text="", font=FONTS["caption"], text_color=THEME["danger"], anchor="w")
        self.confirm_hint.pack(fill="x", padx=10, pady=(0, 10))

        self.signup_btn = ctk.CTkButton(
            tab,
            text="Create My Account",
            font=FONTS["body_lg"],
            height=LAYOUT["btn_height"],
            corner_radius=SHAPE["small"],
            fg_color=THEME["accent"],
            hover_color=THEME["accent_hover"],
            command=self._handle_signup,
        )
        self.signup_btn.pack(fill="x", padx=10, pady=(0, 12))

    # ─────────────────────────────────────────────────────────────
    # RESET TAB
    # ─────────────────────────────────────────────────────────────
    def _build_reset_tab(self):
        tab = self._tab_reset
        tab.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            tab,
            text="Enter your registered email and a new password.",
            font=FONTS["body_sm"],
            text_color=THEME["text_secondary"],
            wraplength=340,
            justify="left",
        ).pack(anchor="w", padx=10, pady=(12, 10))

        self._field_label(tab, "Registered Email")
        self.reset_email = self._entry(tab, placeholder="your@email.com")
        self.reset_email.pack(fill="x", padx=10, pady=(0, 10))

        self._field_label(tab, "New Password")
        self.reset_new_pass = self._entry(tab, placeholder="Min 6 characters", show="*")
        self.reset_new_pass.pack(fill="x", padx=10, pady=(0, 16))

        ctk.CTkButton(
            tab,
            text="Reset Password",
            font=FONTS["body_lg"],
            height=LAYOUT["btn_height"],
            corner_radius=SHAPE["small"],
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            command=self._handle_reset,
        ).pack(fill="x", padx=10, pady=(0, 12))

    # ─────────────────────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────────────────────
    def _field_label(self, parent, text: str):
        ctk.CTkLabel(parent, text=text, font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w", padx=10, pady=(6, 2))

    def _entry(self, parent, placeholder: str = "", show: str = "") -> ctk.CTkEntry:
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

    def _show_message(self, text: str, is_error: bool = True):
        color = THEME["danger"] if is_error else THEME["success"]
        self.status_label.configure(text=text, text_color=color)

    def _set_loading(self, btn: ctk.CTkButton, loading: bool, default_text: str):
        self._loading = loading
        if loading:
            btn.configure(text="⏳  Please wait...", state="disabled", fg_color=THEME["primary_dim"])
        else:
            btn.configure(text=default_text, state="normal", fg_color=THEME["primary"])

    # ─────────────────────────────────────────────────────────────
    # PASSWORD STRENGTH
    # ─────────────────────────────────────────────────────────────
    def _update_pw_strength(self, _=None):
        pw = self.signup_pass.get()
        score, label, color = _pw_strength(pw)
        for i, bar in enumerate(self._pw_bars):
            bar.configure(fg_color=color if i < score else THEME["border"])
        self.pw_strength_label.configure(text=label, text_color=color)

        # Confirm match check
        confirm = self.signup_confirm.get()
        if confirm:
            match = pw == confirm
            self.confirm_hint.configure(
                text="" if match else "Passwords don't match",
                text_color=THEME["success"] if match else THEME["danger"],
            )

    # ─────────────────────────────────────────────────────────────
    # AUTH HANDLERS
    # ─────────────────────────────────────────────────────────────
    def _handle_login(self):
        if self._loading:
            return
        email = self.login_email.get().strip()
        pwd   = self.login_pass.get()

        if not email:
            self.login_hint.configure(text="Email is required")
            return
        if not pwd:
            self.login_hint.configure(text="Password is required")
            return
        self.login_hint.configure(text="")

        self._set_loading(self.login_btn, True, "Log In to GlobeTrotter")

        def _do():
            try:
                with self.session_factory() as session:
                    user = AuthService(session).login(email, pwd)
                self.after(0, lambda: self._on_auth_ok(user))
            except AppException as ex:
                self.after(0, lambda: self._on_auth_err(str(ex.detail), self.login_btn, "Log In to GlobeTrotter"))
            except Exception as ex:
                self.after(0, lambda: self._on_auth_err(f"Login error: {ex}", self.login_btn, "Log In to GlobeTrotter"))

        threading.Thread(target=_do, daemon=True).start()

    def _handle_signup(self):
        if self._loading:
            return
        name    = self.signup_name.get().strip()
        email   = self.signup_email.get().strip()
        pwd     = self.signup_pass.get()
        confirm = self.signup_confirm.get()

        if not email:
            self._show_message("Email is required")
            return
        if len(pwd) < 6:
            self._show_message("Password must be at least 6 characters")
            return
        if pwd != confirm:
            self._show_message("Passwords do not match")
            return

        self._set_loading(self.signup_btn, True, "Create My Account")

        def _do():
            try:
                with self.session_factory() as session:
                    user = AuthService(session).signup(email=email, password=pwd, full_name=name)
                    session.commit()
                self.after(0, lambda: self._on_auth_ok(user))
            except AppException as ex:
                self.after(0, lambda: self._on_auth_err(str(ex.detail), self.signup_btn, "Create My Account"))
            except Exception as ex:
                self.after(0, lambda: self._on_auth_err(f"Registration error: {ex}", self.signup_btn, "Create My Account"))

        threading.Thread(target=_do, daemon=True).start()

    def _handle_reset(self):
        email   = self.reset_email.get().strip()
        new_pwd = self.reset_new_pass.get()
        if not email or not new_pwd:
            self._show_message("Email and new password are required")
            return
        try:
            with self.session_factory() as session:
                AuthService(session).reset_password(email, new_pwd)
                session.commit()
            self._show_message("Password reset! You can now log in.", is_error=False)
            self.tabview.set("Log In")
            self.login_email.delete(0, "end")
            self.login_email.insert(0, email)
            self.login_pass.delete(0, "end")
        except AppException as ex:
            self._show_message(str(ex.detail))
        except Exception as ex:
            self._show_message(f"Reset error: {ex}")

    def _quick_login_admin(self):
        self.login_email.delete(0, "end")
        self.login_email.insert(0, "admin@globetrotter.com")
        self.login_pass.delete(0, "end")
        self.login_pass.insert(0, "admin123")
        self._handle_login()

    def _on_auth_ok(self, user):
        self._loading = False
        self._show_message("✅ Success! Loading your dashboard...", is_error=False)
        self.after(300, lambda: self.on_login_success(user))

    def _on_auth_err(self, msg: str, btn: ctk.CTkButton, default_text: str):
        self._loading = False
        btn.configure(text=default_text, state="normal", fg_color=THEME["primary"])
        self._show_message(msg)
