import customtkinter as ctk
from app.ui.theme import THEME, FONTS
from app.ui.components.header import Header
from app.services.sharing_service import SharingService
from app.services.trip_service import TripService
from app.schemas.sharing import TripShareCreate
from tkinter import messagebox


class ShareScreen(ctk.CTkScrollableFrame):
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

        header = Header(
            self,
            title="Share & Explore Community Itineraries 🔗",
            subtitle="Publish your journeys with unique share links, or clone trips shared by friends.",
        )
        header.pack(fill="x", padx=20, pady=(15, 10))

        # ---------------- Section 1: Share Your Own Trip ----------------
        share_box = ctk.CTkFrame(self, fg_color=THEME["bg_card"], corner_radius=12, border_width=1, border_color=THEME["border"])
        share_box.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkLabel(share_box, text="Share One of Your Trips", font=FONTS["title_md"], text_color=THEME["text_primary"]).pack(anchor="w", padx=20, pady=(16, 6))

        user_trips = []
        with self.session_factory() as session:
            trip_service = TripService(session)
            user_trips = trip_service.list_trips(self.current_user.id, limit=50)

        if user_trips:
            s_row = ctk.CTkFrame(share_box, fg_color="transparent")
            s_row.pack(fill="x", padx=20, pady=(4, 12))

            trip_names = [t.name for t in user_trips]
            self.trip_cb = ctk.CTkComboBox(s_row, values=trip_names, height=36, width=280, font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"], command=self._on_trip_select)
            
            selected_trip = next((t for t in user_trips if t.id == self.trip_id), user_trips[0])
            self.trip_id = selected_trip.id
            self.trip_cb.set(selected_trip.name)
            self.trip_cb.pack(side="left", padx=(0, 10))

            # Check if currently shared
            is_shared = bool(selected_trip.share_slug)
            if is_shared:
                slug_text = f"Public Slug: {selected_trip.share_slug}"
                ctk.CTkLabel(share_box, text=f"🌐 {slug_text}", font=FONTS["body_lg"], text_color=THEME["success"]).pack(anchor="w", padx=20, pady=(0, 4))
                
                btn_row = ctk.CTkFrame(share_box, fg_color="transparent")
                btn_row.pack(fill="x", padx=20, pady=(6, 16))

                ctk.CTkButton(btn_row, text="📋 Copy Share Slug", height=32, font=FONTS["body_sm"], fg_color=THEME["primary"], hover_color=THEME["primary_hover"], command=lambda: self._copy_to_clipboard(selected_trip.share_slug)).pack(side="left", padx=(0, 8))
                ctk.CTkButton(btn_row, text="Revoke Sharing", height=32, font=FONTS["body_sm"], fg_color=THEME["danger_bg"], hover_color=THEME["danger"], command=lambda: self._revoke_sharing(selected_trip.id)).pack(side="left")
            else:
                ctk.CTkLabel(share_box, text="🔒 This trip is currently Private.", font=FONTS["body"], text_color=THEME["text_secondary"]).pack(anchor="w", padx=20, pady=(0, 8))
                ctk.CTkButton(share_box, text="🌐 Publish & Generate Share Link", height=36, font=FONTS["body_lg"], fg_color=THEME["accent"], hover_color=THEME["accent_hover"], command=lambda: self._generate_share(selected_trip.id)).pack(anchor="w", padx=20, pady=(0, 16))
        else:
            ctk.CTkLabel(share_box, text="No trips created yet to share.", font=FONTS["body_sm"], text_color=THEME["text_muted"]).pack(padx=20, pady=(0, 16), anchor="w")

        # ---------------- Section 2: Clone / Copy Shared Trip ----------------
        copy_box = ctk.CTkFrame(self, fg_color=THEME["bg_card"], corner_radius=12, border_width=1, border_color=THEME["border"])
        copy_box.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkLabel(copy_box, text="Clone a Shared Trip", font=FONTS["title_md"], text_color=THEME["text_primary"]).pack(anchor="w", padx=20, pady=(16, 4))
        ctk.CTkLabel(copy_box, text="Paste any 12-character Trip Share Slug to import its destinations and itinerary into your account.", font=FONTS["body_sm"], text_color=THEME["text_secondary"]).pack(anchor="w", padx=20, pady=(0, 10))

        c_row = ctk.CTkFrame(copy_box, fg_color="transparent")
        c_row.pack(fill="x", padx=20, pady=(0, 16))

        self.slug_input = ctk.CTkEntry(c_row, placeholder_text="e.g. 7f89a1b2c3d4", height=38, width=280, font=FONTS["code"], fg_color=THEME["bg_input"], border_color=THEME["border"])
        self.slug_input.pack(side="left", padx=(0, 10))

        ctk.CTkButton(c_row, text="📥 Preview & Clone Trip", height=38, font=FONTS["body_lg"], fg_color=THEME["primary"], hover_color=THEME["primary_hover"], command=self._handle_clone_trip).pack(side="left")

    def _on_trip_select(self, choice):
        with self.session_factory() as session:
            trip_service = TripService(session)
            trips = trip_service.list_trips(self.current_user.id, limit=50)
            chosen = next((t for t in trips if t.name == choice), None)
            if chosen:
                self.trip_id = chosen.id
        self.refresh()

    def _generate_share(self, trip_id):
        try:
            with self.session_factory() as session:
                sharing_service = SharingService(session)
                share = sharing_service.create_share(trip_id, self.current_user.id)
                session.commit()
            messagebox.showinfo("Published!", f"Trip shared successfully!\nShare Slug: {share.share_slug}")
            self.refresh()
        except Exception as ex:
            messagebox.showerror("Error", f"Failed to share trip: {str(ex)}")

    def _revoke_sharing(self, trip_id):
        try:
            with self.session_factory() as session:
                sharing_service = SharingService(session)
                sharing_service.revoke_share(trip_id, self.current_user.id)
                session.commit()
            messagebox.showinfo("Revoked", "Trip is now private again.")
            self.refresh()
        except Exception as ex:
            messagebox.showerror("Error", f"Failed to revoke share: {str(ex)}")

    def _copy_to_clipboard(self, slug):
        self.clipboard_clear()
        self.clipboard_append(slug)
        messagebox.showinfo("Copied", f"Share slug '{slug}' copied to clipboard!")

    def _handle_clone_trip(self):
        slug = self.slug_input.get().strip()
        if not slug:
            messagebox.showwarning("Missing Slug", "Please enter a valid trip share slug.")
            return

        try:
            with self.session_factory() as session:
                sharing_service = SharingService(session)
                cloned = sharing_service.copy_trip(slug, self.current_user.id)
                session.commit()
                cloned_id = cloned.id

            messagebox.showinfo("Trip Cloned!", f"Successfully cloned trip as '{cloned.name}'!\nRedirecting to itinerary builder.")
            self.navigate_callback("itinerary_builder", trip_id=cloned_id)
        except Exception as ex:
            messagebox.showerror("Clone Failed", f"Could not clone trip: {str(ex)}")
