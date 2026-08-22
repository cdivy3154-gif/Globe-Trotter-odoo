import customtkinter as ctk
from app.ui.theme import THEME, FONTS
from app.services.auth_service import AuthService
from app.core.exceptions import AppException


class LoginScreen(ctk.CTkFrame):
    def __init__(self, master, on_login_success, session_factory, **kwargs):
        super().__init__(master, fg_color=THEME["bg_dark"], **kwargs)
        self.on_login_success = on_login_success
        self.session_factory = session_factory
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Center Card Container
        card = ctk.CTkFrame(
            self,
            fg_color=THEME["bg_card"],
            corner_radius=16,
            border_width=1,
            border_color=THEME["border"],
            width=440,
        )
        card.grid(row=0, column=0, padx=20, pady=40)
        card.grid_propagate(True)

        # Brand Header
        brand_frame = ctk.CTkFrame(card, fg_color="transparent")
        brand_frame.pack(fill="x", padx=30, pady=(30, 16))

        logo = ctk.CTkLabel(
            brand_frame,
            text="🌍 GlobeTrotter",
            font=FONTS["title_xl"],
            text_color=THEME["primary"],
        )
        logo.pack()

        subtitle = ctk.CTkLabel(
            brand_frame,
            text="Empowering Personalized Multi-City Travel Planning",
            font=FONTS["body"],
            text_color=THEME["text_secondary"],
            wraplength=360,
        )
        subtitle.pack(pady=(4, 0))

        # Tabview for Login / Signup / Reset
        self.tabview = ctk.CTkTabview(
            card,
            fg_color=THEME["bg_card"],
            segmented_button_selected_color=THEME["primary"],
            segmented_button_selected_hover_color=THEME["primary_hover"],
            segmented_button_unselected_color=THEME["bg_input"],
            segmented_button_unselected_hover_color=THEME["bg_card_hover"],
            height=340,
        )
        self.tabview.pack(fill="both", expand=True, padx=24, pady=(0, 24))

        self.tab_login = self.tabview.add("Log In")
        self.tab_signup = self.tabview.add("Create Account")
        self.tab_reset = self.tabview.add("Forgot Password")

        self._build_login_tab()
        self._build_signup_tab()
        self._build_reset_tab()

        # Status / Error banner
        self.status_label = ctk.CTkLabel(
            card,
            text="",
            font=FONTS["body_sm"],
            text_color=THEME["danger"],
            wraplength=380,
        )
        self.status_label.pack(fill="x", padx=24, pady=(0, 20))

    def _build_login_tab(self):
        tab = self.tab_login
        tab.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(tab, text="Email Address", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w", padx=10, pady=(12, 2))
        self.login_email = ctk.CTkEntry(tab, placeholder_text="e.g. demo@globetrotter.com", height=38, font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"])
        self.login_email.insert(0, "demo@globetrotter.com")
        self.login_email.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkLabel(tab, text="Password", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w", padx=10, pady=(4, 2))
        self.login_pass = ctk.CTkEntry(tab, placeholder_text="Enter password", show="*", height=38, font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"])
        self.login_pass.insert(0, "traveler123")
        self.login_pass.pack(fill="x", padx=10, pady=(0, 16))

        login_btn = ctk.CTkButton(
            tab,
            text="Log In to GlobeTrotter",
            font=FONTS["body_lg"],
            height=40,
            corner_radius=8,
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            command=self._handle_login,
        )
        login_btn.pack(fill="x", padx=10, pady=(6, 10))

        demo_admin_btn = ctk.CTkButton(
            tab,
            text="Quick Log In as Admin",
            font=FONTS["body_sm"],
            height=30,
            corner_radius=6,
            fg_color=THEME["border"],
            hover_color=THEME["bg_card_hover"],
            text_color=THEME["text_secondary"],
            command=self._quick_login_admin,
        )
        demo_admin_btn.pack(fill="x", padx=10, pady=2)

    def _build_signup_tab(self):
        tab = self.tab_signup
        tab.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(tab, text="Full Name", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w", padx=10, pady=(8, 2))
        self.signup_name = ctk.CTkEntry(tab, placeholder_text="e.g. Jane Doe", height=36, font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"])
        self.signup_name.pack(fill="x", padx=10, pady=(0, 8))

        ctk.CTkLabel(tab, text="Email Address", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w", padx=10, pady=(4, 2))
        self.signup_email = ctk.CTkEntry(tab, placeholder_text="name@example.com", height=36, font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"])
        self.signup_email.pack(fill="x", padx=10, pady=(0, 8))

        ctk.CTkLabel(tab, text="Password (min 6 characters)", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w", padx=10, pady=(4, 2))
        self.signup_pass = ctk.CTkEntry(tab, placeholder_text="Create secure password", show="*", height=36, font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"])
        self.signup_pass.pack(fill="x", padx=10, pady=(0, 14))

        signup_btn = ctk.CTkButton(
            tab,
            text="Create New Account",
            font=FONTS["body_lg"],
            height=38,
            corner_radius=8,
            fg_color=THEME["accent"],
            hover_color=THEME["accent_hover"],
            command=self._handle_signup,
        )
        signup_btn.pack(fill="x", padx=10, pady=(4, 6))

    def _build_reset_tab(self):
        tab = self.tab_reset
        tab.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(tab, text="Account Email", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w", padx=10, pady=(12, 2))
        self.reset_email = ctk.CTkEntry(tab, placeholder_text="Registered email address", height=38, font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"])
        self.reset_email.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkLabel(tab, text="New Password", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w", padx=10, pady=(4, 2))
        self.reset_new_pass = ctk.CTkEntry(tab, placeholder_text="Enter new password", show="*", height=38, font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"])
        self.reset_new_pass.pack(fill="x", padx=10, pady=(0, 16))

        reset_btn = ctk.CTkButton(
            tab,
            text="Reset Password",
            font=FONTS["body_lg"],
            height=38,
            corner_radius=8,
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            command=self._handle_reset,
        )
        reset_btn.pack(fill="x", padx=10, pady=(4, 8))

    def _show_message(self, text: str, is_error: bool = True):
        color = THEME["danger"] if is_error else THEME["success"]
        self.status_label.configure(text=text, text_color=color)

    def _handle_login(self):
        email = self.login_email.get().strip()
        pwd = self.login_pass.get()
        if not email or not pwd:
            self._show_message("Please enter both email and password")
            return

        try:
            with self.session_factory() as session:
                service = AuthService(session)
                user = service.login(email, pwd)
                self._show_message("Login successful!", is_error=False)
                self.on_login_success(user)
        except AppException as e:
            self._show_message(str(e.detail))
        except Exception as ex:
            self._show_message(f"Error during login: {str(ex)}")

    def _quick_login_admin(self):
        self.login_email.delete(0, "end")
        self.login_email.insert(0, "admin@globetrotter.com")
        self.login_pass.delete(0, "end")
        self.login_pass.insert(0, "admin123")
        self._handle_login()

    def _handle_signup(self):
        name = self.signup_name.get().strip()
        email = self.signup_email.get().strip()
        pwd = self.signup_pass.get()

        if not email or not pwd:
            self._show_message("Email and password are required")
            return
        if len(pwd) < 6:
            self._show_message("Password must be at least 6 characters")
            return

        try:
            with self.session_factory() as session:
                service = AuthService(session)
                user = service.signup(email=email, password=pwd, full_name=name)
                session.commit()
                self._show_message("Account created! Logging you in...", is_error=False)
                self.on_login_success(user)
        except AppException as e:
            self._show_message(str(e.detail))
        except Exception as ex:
            self._show_message(f"Registration error: {str(ex)}")

    def _handle_reset(self):
        email = self.reset_email.get().strip()
        new_pwd = self.reset_new_pass.get()
        if not email or not new_pwd:
            self._show_message("Email and new password are required")
            return

        try:
            with self.session_factory() as session:
                service = AuthService(session)
                service.reset_password(email, new_pwd)
                session.commit()
                self._show_message("Password reset! You can now log in.", is_error=False)
                self.tabview.set("Log In")
                self.login_email.delete(0, "end")
                self.login_email.insert(0, email)
                self.login_pass.delete(0, "end")
        except AppException as e:
            self._show_message(str(e.detail))
        except Exception as ex:
            self._show_message(f"Password reset error: {str(ex)}")
