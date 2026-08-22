import customtkinter as ctk
from tkinter import filedialog, messagebox
from app.ui.theme import THEME, FONTS
from app.ui.components.header import Header
from app.services.auth_service import AuthService
from app.services.city_service import CityService
from app.services.upload_service import UploadService


class ProfileScreen(ctk.CTkScrollableFrame):
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
            title="User Profile & Settings 👤",
            subtitle="Manage your personal traveler details, credentials, and saved destinations.",
        )
        header.pack(fill="x", padx=20, pady=(15, 10))

        # ---------------- Section 1: Profile Information ----------------
        prof_card = ctk.CTkFrame(self, fg_color=THEME["bg_card"], corner_radius=12, border_width=1, border_color=THEME["border"])
        prof_card.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkLabel(prof_card, text="Personal Details", font=FONTS["title_md"], text_color=THEME["text_primary"]).pack(anchor="w", padx=20, pady=(16, 8))

        # Email (Readonly)
        ctk.CTkLabel(prof_card, text="Account Email", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w", padx=20, pady=(4, 2))
        email_lbl = ctk.CTkEntry(prof_card, height=36, font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"])
        email_lbl.insert(0, self.current_user.email)
        email_lbl.configure(state="disabled")
        email_lbl.pack(fill="x", padx=20, pady=(0, 10))

        # Full Name
        ctk.CTkLabel(prof_card, text="Full Name", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w", padx=20, pady=(4, 2))
        self.name_entry = ctk.CTkEntry(prof_card, height=36, font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"])
        self.name_entry.insert(0, self.current_user.full_name or "")
        self.name_entry.pack(fill="x", padx=20, pady=(0, 10))

        # Language Preference
        ctk.CTkLabel(prof_card, text="Preferred Language", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w", padx=20, pady=(4, 2))
        self.lang_cb = ctk.CTkComboBox(prof_card, values=["English (en)", "Spanish (es)", "French (fr)", "German (de)", "Japanese (ja)", "Hindi (hi)"], height=36, font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"])
        self.lang_cb.set("English (en)")
        self.lang_cb.pack(fill="x", padx=20, pady=(0, 16))

        # Save Button
        save_btn = ctk.CTkButton(prof_card, text="Update Profile Information", height=38, font=FONTS["body_lg"], fg_color=THEME["primary"], hover_color=THEME["primary_hover"], command=self._handle_update_profile)
        save_btn.pack(anchor="w", padx=20, pady=(0, 20))

        # ---------------- Section 2: Change Password ----------------
        pwd_card = ctk.CTkFrame(self, fg_color=THEME["bg_card"], corner_radius=12, border_width=1, border_color=THEME["border"])
        pwd_card.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkLabel(pwd_card, text="Security & Password", font=FONTS["title_md"], text_color=THEME["text_primary"]).pack(anchor="w", padx=20, pady=(16, 8))

        ctk.CTkLabel(pwd_card, text="Current Password", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w", padx=20, pady=(4, 2))
        self.curr_pwd_entry = ctk.CTkEntry(pwd_card, show="*", height=36, font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"])
        self.curr_pwd_entry.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(pwd_card, text="New Password (min 6 characters)", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w", padx=20, pady=(4, 2))
        self.new_pwd_entry = ctk.CTkEntry(pwd_card, show="*", height=36, font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"])
        self.new_pwd_entry.pack(fill="x", padx=20, pady=(0, 16))

        pwd_btn = ctk.CTkButton(pwd_card, text="Change Password", height=38, font=FONTS["body_lg"], fg_color=THEME["accent"], hover_color=THEME["accent_hover"], command=self._handle_change_password)
        pwd_btn.pack(anchor="w", padx=20, pady=(0, 20))

        # ---------------- Section 3: Saved / Favorite Destinations ----------------
        saved_card = ctk.CTkFrame(self, fg_color=THEME["bg_card"], corner_radius=12, border_width=1, border_color=THEME["border"])
        saved_card.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkLabel(saved_card, text="⭐ Saved Destinations", font=FONTS["title_md"], text_color=THEME["text_primary"]).pack(anchor="w", padx=20, pady=(16, 8))

        saved_dests = []
        with self.session_factory() as session:
            city_service = CityService(session)
            saved_dests = city_service.get_saved_destinations(self.current_user.id)

        if saved_dests:
            for s in saved_dests:
                c = s.city
                if not c:
                    continue
                r_frame = ctk.CTkFrame(saved_card, fg_color=THEME["bg_input"], corner_radius=6, border_width=1, border_color=THEME["border"])
                r_frame.pack(fill="x", padx=20, pady=4)

                r_inner = ctk.CTkFrame(r_frame, fg_color="transparent")
                r_inner.pack(fill="x", padx=12, pady=8)

                ctk.CTkLabel(r_inner, text=f"📍 {c.name}, {c.country} ({c.region or 'Global'})", font=FONTS["body_lg"], text_color=THEME["text_primary"]).pack(side="left")

                # Action buttons: Plan Trip with this city, or remove
                r_btns = ctk.CTkFrame(r_inner, fg_color="transparent")
                r_btns.pack(side="right")

                ctk.CTkButton(r_btns, text="Plan Trip", height=28, width=75, font=FONTS["body_sm"], fg_color=THEME["primary"], hover_color=THEME["primary_hover"], command=lambda city_id=c.id: self.navigate_callback("create_trip", city_id=city_id)).pack(side="left", padx=4)
                ctk.CTkButton(r_btns, text="Remove", height=28, width=65, font=FONTS["body_sm"], fg_color=THEME["danger_bg"], hover_color=THEME["danger"], command=lambda city_id=c.id: self._remove_saved(city_id)).pack(side="left")
            ctk.CTkFrame(saved_card, height=12, fg_color="transparent").pack()
        else:
            ctk.CTkLabel(saved_card, text="You haven't bookmarked any cities yet. Explore the City Directory to save favorites.", font=FONTS["body_sm"], text_color=THEME["text_muted"]).pack(padx=20, pady=(0, 20), anchor="w")

    def _handle_update_profile(self):
        new_name = self.name_entry.get().strip()
        lang = self.lang_cb.get().split("(")[-1].rstrip(")")
        try:
            with self.session_factory() as session:
                service = AuthService(session)
                updated = service.update_profile(self.current_user.id, full_name=new_name, language_pref=lang)
                session.commit()
                self.current_user = updated
            messagebox.showinfo("Saved", "Profile information updated successfully!")
        except Exception as ex:
            messagebox.showerror("Error", f"Failed to update profile: {str(ex)}")

    def _handle_change_password(self):
        curr_p = self.curr_pwd_entry.get()
        new_p = self.new_pwd_entry.get()
        if not curr_p or not new_p:
            messagebox.showwarning("Missing Fields", "Please enter both current and new password.")
            return

        try:
            with self.session_factory() as session:
                service = AuthService(session)
                service.change_password(self.current_user.id, curr_p, new_p)
                session.commit()
            self.curr_pwd_entry.delete(0, "end")
            self.new_pwd_entry.delete(0, "end")
            messagebox.showinfo("Success", "Password updated successfully!")
        except Exception as ex:
            messagebox.showerror("Error", f"Password change failed: {str(ex)}")

    def _remove_saved(self, city_id):
        with self.session_factory() as session:
            service = CityService(session)
            service.toggle_save_destination(self.current_user.id, city_id)
            session.commit()
        self.refresh()
