"""
Phase 9b — Profile Screen
Features:
  - Avatar display (initials fallback with primary circle)
  - Editable: Full Name, Language preference
  - Change Password (current → new → confirm)
  - Stats row: Total Trips, Countries visited, Activities planned, Member since
  - Danger zone: Delete Account
"""
import customtkinter as ctk
from tkinter import messagebox, filedialog

from app.ui.theme import THEME, FONTS, SHAPE, LAYOUT
from app.ui.components.header import Header
from app.ui.components.cards import MetricCard
from app.services.auth_service import AuthService
from app.services.trip_service import TripService
from app.core.exceptions import AppException


_LANGUAGES = ["English", "Hindi", "Spanish", "French", "German", "Arabic", "Japanese", "Portuguese", "Chinese", "Italian"]


def _mk_entry(parent, placeholder="", show="", val="") -> ctk.CTkEntry:
    e = ctk.CTkEntry(
        parent, placeholder_text=placeholder, show=show,
        height=LAYOUT["input_height"], font=FONTS["body"],
        fg_color=THEME["bg_input"], border_color=THEME["border"],
        border_width=1, corner_radius=SHAPE["small"],
        text_color=THEME["text_primary"],
    )
    if val:
        e.insert(0, val)
    e.bind("<FocusIn>",  lambda _: e.configure(border_color=THEME["border_focus"]))
    e.bind("<FocusOut>", lambda _: e.configure(border_color=THEME["border"]))
    return e


# ══════════════════════════════════════════════════════════════════
class ProfileScreen(ctk.CTkScrollableFrame):
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

        # Fresh user data + stats
        with self.session_factory() as session:
            trips = TripService(session).list_trips(self.current_user.id, limit=200)

        total_trips = len(trips)
        countries   = len({s.city.country for t in trips for s in t.stops if s.city})
        activities  = sum(len(s.activities) for t in trips for s in t.stops)

        Header(
            self,
            title="My Profile & Account ⚙️",
            subtitle="Manage your personal details, preferences, and account security.",
            action_button=("🚪  Log Out", lambda: self.navigate_callback("logout"), THEME["danger"]),
            breadcrumb=["Dashboard", "Profile"],
        ).pack(fill="x", padx=20, pady=(18, 10))

        # ── Stats row ─────────────────────────────────────────────
        stats_row = ctk.CTkFrame(self, fg_color="transparent")
        stats_row.pack(fill="x", padx=20, pady=(0, 10))
        stats_row.grid_columnconfigure((0, 1, 2, 3), weight=1)

        joined = getattr(self.current_user, "created_at", None)
        joined_str = joined.strftime("%b %Y") if joined else "—"

        for i, (title, val, icon, color) in enumerate([
            ("Total Trips",    str(total_trips), "✈️",  THEME["primary"]),
            ("Countries",      str(countries),   "🌍",  THEME["accent"]),
            ("Activities",     str(activities),  "🎟️",  THEME["info"]),
            ("Member Since",   joined_str,       "🗓️",  THEME["chart_3"]),
        ]):
            MetricCard(stats_row, title=title, value=val, icon=icon, subtitle="", accent_color=color).grid(
                row=0, column=i, padx=(0 if i == 0 else 6, 6 if i < 3 else 0), sticky="ew"
            )

        # ── Avatar + Name section ─────────────────────────────────
        prof_card = ctk.CTkFrame(self, fg_color=THEME["bg_card"], corner_radius=SHAPE["medium"], border_width=1, border_color=THEME["border"])
        prof_card.pack(fill="x", padx=20, pady=(0, 10))
        ctk.CTkFrame(prof_card, height=3, fg_color=THEME["primary"], corner_radius=0).pack(fill="x")

        body = ctk.CTkFrame(prof_card, fg_color="transparent")
        body.pack(fill="x", padx=24, pady=20)
        body.grid_columnconfigure(1, weight=1)

        # Avatar circle (initials)
        initials = "".join(p[0].upper() for p in (self.current_user.full_name or "GT").split()[:2])
        av = ctk.CTkLabel(
            body,
            text=initials,
            font=("Segoe UI", 26, "bold"),
            text_color=THEME["on_primary"],
            fg_color=THEME["primary"],
            corner_radius=50,
            width=80,
            height=80,
        )
        av.grid(row=0, column=0, rowspan=3, padx=(0, 20), sticky="n")

        ctk.CTkLabel(body, text=self.current_user.full_name or "GlobeTrotter User", font=FONTS["title_md"], text_color=THEME["text_primary"], anchor="w").grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(body, text=self.current_user.email, font=FONTS["body_sm"], text_color=THEME["text_secondary"], anchor="w").grid(row=1, column=1, sticky="w")
        role = getattr(self.current_user, "role", "user")
        ctk.CTkLabel(body, text=f"Role: {str(role).title()}", font=FONTS["badge"], fg_color=THEME["primary_container"], text_color=THEME["primary"], corner_radius=SHAPE["full"]).grid(row=2, column=1, sticky="w", pady=(4, 0))

        ctk.CTkButton(
            body,
            text="🚪  Log Out",
            font=FONTS["body_sm"],
            height=32,
            width=100,
            corner_radius=SHAPE["small"],
            fg_color=THEME["danger_bg"],
            hover_color=THEME["danger"],
            text_color=THEME["danger"],
            border_width=1,
            border_color=THEME["danger"],
            command=lambda: self.navigate_callback("logout"),
        ).grid(row=0, column=2, rowspan=2, sticky="e", padx=(10, 0))

        # ── Edit Profile form ─────────────────────────────────────
        form_card = ctk.CTkFrame(self, fg_color=THEME["bg_card"], corner_radius=SHAPE["medium"], border_width=1, border_color=THEME["border"])
        form_card.pack(fill="x", padx=20, pady=(0, 10))
        ctk.CTkFrame(form_card, height=3, fg_color=THEME["accent"], corner_radius=0).pack(fill="x")
        ctk.CTkLabel(form_card, text="✏️  Edit Profile", font=FONTS["title_sm"], text_color=THEME["text_primary"]).pack(anchor="w", padx=24, pady=(14, 4))

        form = ctk.CTkFrame(form_card, fg_color="transparent")
        form.pack(fill="x", padx=24, pady=(4, 16))
        form.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(form, text="Full Name", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).grid(row=0, column=0, sticky="w", padx=(0, 8))
        ctk.CTkLabel(form, text="Language Preference", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).grid(row=0, column=1, sticky="w", padx=(8, 0))

        name_e = _mk_entry(form, val=self.current_user.full_name or "")
        name_e.grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=(4, 0))

        lang_cb = ctk.CTkComboBox(form, values=_LANGUAGES, height=LAYOUT["input_height"], font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"], text_color=THEME["text_primary"])
        lang_pref = getattr(self.current_user, "language_pref", "English") or "English"
        lang_cb.set(lang_pref if lang_pref in _LANGUAGES else "English")
        lang_cb.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=(4, 0))

        prof_err = ctk.CTkLabel(form_card, text="", font=FONTS["body_sm"], text_color=THEME["danger"])
        prof_err.pack(fill="x", padx=24)

        def save_profile():
            nm = name_e.get().strip()
            if not nm:
                prof_err.configure(text="Full name cannot be empty")
                return
            try:
                with self.session_factory() as session:
                    AuthService(session).update_profile(
                        self.current_user.id,
                        full_name=nm,
                        language_pref=lang_cb.get(),
                    )
                    session.commit()
                self.current_user.full_name     = nm
                self.current_user.language_pref = lang_cb.get()
                prof_err.configure(text="✅  Profile updated successfully.", text_color=THEME["success"])
            except AppException as ex:
                prof_err.configure(text=str(ex.detail), text_color=THEME["danger"])
            except Exception as ex:
                prof_err.configure(text=str(ex), text_color=THEME["danger"])

        ctk.CTkButton(form_card, text="Save Profile", font=FONTS["body_lg"], height=LAYOUT["btn_height_sm"], width=140, corner_radius=SHAPE["small"], fg_color=THEME["primary"], hover_color=THEME["primary_hover"], command=save_profile).pack(anchor="w", padx=24, pady=(4, 16))

        # ── Change Password ───────────────────────────────────────
        pw_card = ctk.CTkFrame(self, fg_color=THEME["bg_card"], corner_radius=SHAPE["medium"], border_width=1, border_color=THEME["border"])
        pw_card.pack(fill="x", padx=20, pady=(0, 10))
        ctk.CTkFrame(pw_card, height=3, fg_color=THEME["chart_2"], corner_radius=0).pack(fill="x")
        ctk.CTkLabel(pw_card, text="🔒  Change Password", font=FONTS["title_sm"], text_color=THEME["text_primary"]).pack(anchor="w", padx=24, pady=(14, 4))

        pw_form = ctk.CTkFrame(pw_card, fg_color="transparent")
        pw_form.pack(fill="x", padx=24, pady=(4, 4))
        pw_form.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(pw_form, text="Current Password", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).grid(row=0, column=0, sticky="w", padx=(0, 8))
        ctk.CTkLabel(pw_form, text="New Password", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).grid(row=0, column=1, sticky="w", padx=(0, 8))
        ctk.CTkLabel(pw_form, text="Confirm New", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).grid(row=0, column=2, sticky="w")

        cur_pw  = _mk_entry(pw_form, placeholder="••••••••", show="•")
        new_pw  = _mk_entry(pw_form, placeholder="Min 6 chars", show="•")
        conf_pw = _mk_entry(pw_form, placeholder="Repeat new", show="•")
        cur_pw.grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=(4, 0))
        new_pw.grid(row=1, column=1, sticky="ew", padx=(0, 8), pady=(4, 0))
        conf_pw.grid(row=1, column=2, sticky="ew", pady=(4, 0))

        pw_err = ctk.CTkLabel(pw_card, text="", font=FONTS["body_sm"], text_color=THEME["danger"])
        pw_err.pack(fill="x", padx=24, pady=(4, 0))

        def do_change_pw():
            c = cur_pw.get()
            n = new_pw.get()
            cf = conf_pw.get()
            if not c or not n:
                pw_err.configure(text="All fields required", text_color=THEME["danger"])
                return
            if n != cf:
                pw_err.configure(text="New passwords do not match", text_color=THEME["danger"])
                return
            if len(n) < 6:
                pw_err.configure(text="New password must be at least 6 characters", text_color=THEME["danger"])
                return
            try:
                with self.session_factory() as session:
                    AuthService(session).change_password(self.current_user.id, c, n)
                    session.commit()
                cur_pw.delete(0, "end")
                new_pw.delete(0, "end")
                conf_pw.delete(0, "end")
                pw_err.configure(text="✅  Password changed successfully.", text_color=THEME["success"])
            except AppException as ex:
                pw_err.configure(text=str(ex.detail), text_color=THEME["danger"])
            except Exception as ex:
                pw_err.configure(text=str(ex), text_color=THEME["danger"])

        ctk.CTkButton(pw_card, text="Change Password", font=FONTS["body_lg"], height=LAYOUT["btn_height_sm"], width=160, corner_radius=SHAPE["small"], fg_color=THEME["chart_2"], hover_color=THEME["primary_hover"], command=do_change_pw).pack(anchor="w", padx=24, pady=(4, 16))

        # ── Danger zone ───────────────────────────────────────────
        danger_card = ctk.CTkFrame(self, fg_color=THEME["danger_bg"], corner_radius=SHAPE["medium"], border_width=1, border_color=THEME["danger"])
        danger_card.pack(fill="x", padx=20, pady=(0, 24))
        ctk.CTkLabel(danger_card, text="⚠️  Danger Zone", font=FONTS["title_sm"], text_color=THEME["danger"]).pack(anchor="w", padx=24, pady=(14, 4))
        ctk.CTkLabel(danger_card, text="Deleting your account is permanent. All trips, stops, activities and data will be removed.", font=FONTS["body_sm"], text_color=THEME["text_muted"], anchor="w", wraplength=700).pack(fill="x", padx=24, pady=(0, 10))

        def delete_account():
            if messagebox.askyesno("Delete Account", "This will permanently delete your account and ALL your trip data.\n\nAre you absolutely sure?"):
                pw = ctk.CTkInputDialog(text="Enter your password to confirm deletion:", title="Confirm Password")
                confirmed_pw = pw.get_input()
                if not confirmed_pw:
                    return
                try:
                    with self.session_factory() as session:
                        AuthService(session).delete_account(self.current_user.id, confirmed_pw)
                        session.commit()
                    messagebox.showinfo("Goodbye", "Your account has been deleted.")
                    self.navigate_callback("login")
                except Exception as ex:
                    messagebox.showerror("Error", str(ex))

        ctk.CTkButton(danger_card, text="🗑  Delete My Account", font=FONTS["body"], height=LAYOUT["btn_height_sm"], width=180, corner_radius=SHAPE["small"], fg_color="transparent", hover_color=THEME["danger"], text_color=THEME["danger"], border_width=1, border_color=THEME["danger"], command=delete_account).pack(anchor="w", padx=24, pady=(0, 16))
