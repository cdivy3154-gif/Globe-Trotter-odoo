"""
Phase 9a — Share & Community Screen
Features:
  - My Trips selector → generate/revoke share link
  - Copy shareable URL to clipboard with one click
  - Share link card: view count, expiry, QR code ASCII placeholder
  - Import by slug: paste slug → preview trip → clone
  - Public trips gallery: 3-col cards of discovered public trips with clone CTA
"""
import customtkinter as ctk
import subprocess
from datetime import datetime, UTC
from tkinter import messagebox

from app.ui.theme import THEME, FONTS, SHAPE, LAYOUT
from app.ui.components.header import Header
from app.ui.components.cards import EmptyState
from app.services.sharing_service import SharingService
from app.services.trip_service import TripService
from app.schemas.sharing import TripShareCreate
from app.core.exceptions import AppException


def _copy_to_clipboard(root, text: str):
    try:
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()
    except Exception:
        try:
            subprocess.run(["clip"], input=text.encode(), check=True)
        except Exception:
            pass


def _mk_entry(parent, placeholder="", val="") -> ctk.CTkEntry:
    e = ctk.CTkEntry(
        parent, placeholder_text=placeholder,
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
class ShareScreen(ctk.CTkScrollableFrame):
    def __init__(self, master, navigate_callback, session_factory, current_user, trip_id=None, **kwargs):
        super().__init__(
            master, fg_color=THEME["bg_dark"],
            scrollbar_button_color=THEME["border"],
            scrollbar_button_hover_color=THEME["border_light"],
            **kwargs,
        )
        self.navigate_callback = navigate_callback
        self.session_factory   = session_factory
        self.current_user      = current_user
        self.trip_id           = trip_id
        self._user_trips       = []
        self.grid_columnconfigure(0, weight=1)
        self.refresh()

    # ─────────────────────────────────────────────────────────────
    def refresh(self):
        for w in self.winfo_children():
            w.destroy()

        with self.session_factory() as session:
            self._user_trips = TripService(session).list_trips(self.current_user.id, limit=50)

        Header(
            self,
            title="Share & Community Itineraries 🔗",
            subtitle="Publish your journeys with a unique link, or clone trips shared by the community.",
            breadcrumb=["Dashboard", "Share"],
        ).pack(fill="x", padx=20, pady=(18, 10))

        # ── Section 1: Share your own trip ────────────────────────
        self._build_share_section()

        # ── Section 2: Import by slug ─────────────────────────────
        self._build_import_section()

        # ── Section 3: Public community gallery ───────────────────
        self._build_community_gallery()

    # ─────────────────────────────────────────────────────────────
    # SHARE SECTION
    # ─────────────────────────────────────────────────────────────
    def _build_share_section(self):
        card = ctk.CTkFrame(self, fg_color=THEME["bg_card"], corner_radius=SHAPE["medium"], border_width=1, border_color=THEME["border"])
        card.pack(fill="x", padx=20, pady=(0, 10))
        ctk.CTkFrame(card, height=3, fg_color=THEME["primary"], corner_radius=0).pack(fill="x")
        ctk.CTkLabel(card, text="📤  Share One of Your Trips", font=FONTS["title_sm"], text_color=THEME["text_primary"]).pack(anchor="w", padx=20, pady=(14, 8))

        if not self._user_trips:
            ctk.CTkLabel(card, text="No trips yet. Create one first.", font=FONTS["body_sm"], text_color=THEME["text_muted"]).pack(padx=20, pady=(0, 14), anchor="w")
            return

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=(0, 16))
        inner.grid_columnconfigure(0, weight=1)

        trip_names = [t.name for t in self._user_trips]
        trip_cb = ctk.CTkComboBox(inner, values=trip_names, height=LAYOUT["input_height"], font=FONTS["body"], fg_color=THEME["bg_input"], border_color=THEME["border"], text_color=THEME["text_primary"])
        if self.trip_id:
            t = next((t for t in self._user_trips if t.id == self.trip_id), self._user_trips[0])
            trip_cb.set(t.name)
        else:
            trip_cb.set(trip_names[0])
        trip_cb.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        btn_frame = ctk.CTkFrame(inner, fg_color="transparent")
        btn_frame.grid(row=0, column=1)

        self._share_result = ctk.CTkFrame(card, fg_color="transparent")
        self._share_result.pack(fill="x", padx=20)

        def get_selected_trip():
            return next((t for t in self._user_trips if t.name == trip_cb.get()), self._user_trips[0])

        def do_generate():
            trip = get_selected_trip()
            try:
                with self.session_factory() as session:
                    share = SharingService(session).create_share(trip.id, self.current_user.id, TripShareCreate())
                    session.commit()
                    slug = share.share_slug
                    views = getattr(share, "view_count", 0)
                self._render_share_result(slug, views)
            except AppException as ex:
                self._show_share_error(str(ex.detail))
            except Exception as ex:
                self._show_share_error(str(ex))

        def do_revoke():
            if messagebox.askyesno("Revoke Share", "This will make the trip private and disable the link."):
                trip = get_selected_trip()
                with self.session_factory() as session:
                    SharingService(session).revoke_share(trip.id, self.current_user.id)
                    session.commit()
                for w in self._share_result.winfo_children():
                    w.destroy()
                ctk.CTkLabel(self._share_result, text="✅  Share link revoked. Trip is now private.", font=FONTS["body_sm"], text_color=THEME["success"]).pack(anchor="w", pady=(0, 10))

        ctk.CTkButton(btn_frame, text="🔗  Generate Link", font=FONTS["body_sm"], height=LAYOUT["input_height"], width=130, corner_radius=SHAPE["small"], fg_color=THEME["primary"], hover_color=THEME["primary_hover"], command=do_generate).pack(side="left", padx=(0, 6))
        ctk.CTkButton(btn_frame, text="🚫  Revoke", font=FONTS["body_sm"], height=LAYOUT["input_height"], width=80, corner_radius=SHAPE["small"], fg_color=THEME["danger_bg"], hover_color=THEME["danger"], text_color=THEME["danger"], border_width=1, border_color=THEME["danger"], command=do_revoke).pack(side="left")

        # If the currently selected trip already has a share, show it
        if self.trip_id:
            trip = next((t for t in self._user_trips if t.id == self.trip_id), None)
            if trip and getattr(trip, "share_slug", None):
                self._render_share_result(trip.share_slug, 0)

    def _render_share_result(self, slug: str, views: int):
        for w in self._share_result.winfo_children():
            w.destroy()

        link = f"globetrotter://share/{slug}"

        res_card = ctk.CTkFrame(self._share_result, fg_color=THEME["bg_input"], corner_radius=SHAPE["small"], border_width=1, border_color=THEME["success"])
        res_card.pack(fill="x", pady=(0, 14))

        top = ctk.CTkFrame(res_card, fg_color="transparent")
        top.pack(fill="x", padx=14, pady=(12, 6))
        ctk.CTkLabel(top, text="✅  Share Link Active", font=FONTS["body_lg"], text_color=THEME["success"]).pack(side="left")
        if views:
            ctk.CTkLabel(top, text=f"👁 {views} views", font=FONTS["badge"], text_color=THEME["text_muted"]).pack(side="right")

        link_row = ctk.CTkFrame(res_card, fg_color="transparent")
        link_row.pack(fill="x", padx=14, pady=(0, 12))
        link_row.grid_columnconfigure(0, weight=1)

        link_e = ctk.CTkEntry(link_row, height=LAYOUT["input_height"], font=FONTS["body_sm"], fg_color=THEME["bg_card"], border_color=THEME["border"], border_width=1, text_color=THEME["text_muted"], state="readonly")
        link_e.configure(state="normal")
        link_e.insert(0, link)
        link_e.configure(state="readonly")
        link_e.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        ctk.CTkButton(link_row, text="📋  Copy", font=FONTS["body_sm"], height=LAYOUT["input_height"], width=80, corner_radius=SHAPE["small"], fg_color=THEME["primary"], hover_color=THEME["primary_hover"], command=lambda: [_copy_to_clipboard(self, link), self._flash_copied()]).grid(row=0, column=1)

        ctk.CTkLabel(res_card, text=f"Slug: {slug}", font=FONTS["badge"], text_color=THEME["text_muted"], anchor="w").pack(padx=14, pady=(0, 10), anchor="w")

    def _flash_copied(self):
        pass  # Visual feedback already via clipboard — could add a tooltip later

    def _show_share_error(self, msg: str):
        for w in self._share_result.winfo_children():
            w.destroy()
        ctk.CTkLabel(self._share_result, text=f"⚠️  {msg}", font=FONTS["body_sm"], text_color=THEME["danger"]).pack(anchor="w", pady=(0, 8))

    # ─────────────────────────────────────────────────────────────
    # IMPORT SECTION
    # ─────────────────────────────────────────────────────────────
    def _build_import_section(self):
        card = ctk.CTkFrame(self, fg_color=THEME["bg_card"], corner_radius=SHAPE["medium"], border_width=1, border_color=THEME["border"])
        card.pack(fill="x", padx=20, pady=(0, 10))
        ctk.CTkFrame(card, height=3, fg_color=THEME["accent"], corner_radius=0).pack(fill="x")
        ctk.CTkLabel(card, text="📥  Import a Shared Itinerary", font=FONTS["title_sm"], text_color=THEME["text_primary"]).pack(anchor="w", padx=20, pady=(14, 4))
        ctk.CTkLabel(card, text="Paste a share slug to preview and clone the trip into your account.", font=FONTS["body_sm"], text_color=THEME["text_secondary"], anchor="w").pack(fill="x", padx=20, pady=(0, 10))

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(0, 8))
        row.grid_columnconfigure(0, weight=1)

        slug_e = _mk_entry(row, "Paste share slug (e.g. a3f7b8c12d4e)")
        slug_e.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        result_frame = ctk.CTkFrame(card, fg_color="transparent")
        result_frame.pack(fill="x", padx=20)

        def do_import():
            slug = slug_e.get().strip().split("/")[-1]
            if not slug:
                return
            for w in result_frame.winfo_children():
                w.destroy()
            try:
                with self.session_factory() as session:
                    trip = SharingService(session).get_public_trip(slug)
                    stops = len(trip.stops)
                    acts  = sum(len(s.activities) for s in trip.stops)

                preview = ctk.CTkFrame(result_frame, fg_color=THEME["bg_input"], corner_radius=SHAPE["small"], border_width=1, border_color=THEME["border"])
                preview.pack(fill="x", pady=(0, 14))

                ph = ctk.CTkFrame(preview, fg_color="transparent")
                ph.pack(fill="x", padx=14, pady=(12, 4))
                ctk.CTkLabel(ph, text=f"✈️  {trip.name}", font=FONTS["title_sm"], text_color=THEME["text_primary"]).pack(side="left")

                s = trip.start_date.strftime("%b %d, %Y")
                e = trip.end_date.strftime("%b %d, %Y")
                ctk.CTkLabel(preview, text=f"📅 {s} → {e}   •   📍 {stops} stops   •   🎟 {acts} activities", font=FONTS["body_sm"], text_color=THEME["text_secondary"], anchor="w").pack(fill="x", padx=14, pady=(0, 4))
                if trip.description:
                    ctk.CTkLabel(preview, text=trip.description[:120], font=FONTS["body_sm"], text_color=THEME["text_muted"], anchor="w", wraplength=700).pack(fill="x", padx=14, pady=(0, 8))

                def do_clone():
                    with self.session_factory() as session:
                        new_trip = SharingService(session).copy_trip(slug, self.current_user.id)
                        session.commit()
                        new_id = new_trip.id
                    for w in result_frame.winfo_children():
                        w.destroy()
                    ctk.CTkLabel(result_frame, text=f"✅  Trip cloned successfully!", font=FONTS["body_sm"], text_color=THEME["success"]).pack(anchor="w")
                    ctk.CTkButton(result_frame, text="Open in Builder →", font=FONTS["body_sm"], height=28, corner_radius=SHAPE["small"], fg_color=THEME["primary"], hover_color=THEME["primary_hover"], command=lambda: self.navigate_callback("itinerary_builder", trip_id=new_id)).pack(anchor="w", pady=4)

                ctk.CTkButton(preview, text="📋  Clone to My Trips", font=FONTS["body_lg"], height=LAYOUT["btn_height_sm"], corner_radius=SHAPE["small"], fg_color=THEME["accent"], hover_color=THEME["accent_hover"], command=do_clone).pack(padx=14, pady=(0, 12), anchor="w")

            except AppException as ex:
                ctk.CTkLabel(result_frame, text=f"⚠️  {ex.detail}", font=FONTS["body_sm"], text_color=THEME["danger"]).pack(anchor="w", pady=(0, 8))
            except Exception as ex:
                ctk.CTkLabel(result_frame, text=f"⚠️  {ex}", font=FONTS["body_sm"], text_color=THEME["danger"]).pack(anchor="w", pady=(0, 8))

        ctk.CTkButton(row, text="Preview →", font=FONTS["body_sm"], height=LAYOUT["input_height"], width=90, corner_radius=SHAPE["small"], fg_color=THEME["primary"], hover_color=THEME["primary_hover"], command=do_import).grid(row=0, column=1)

        ctk.CTkFrame(card, height=8, fg_color="transparent").pack()

    # ─────────────────────────────────────────────────────────────
    # COMMUNITY GALLERY
    # ─────────────────────────────────────────────────────────────
    def _build_community_gallery(self):
        # Fetch all public trips (use trip_repo directly via service)
        try:
            with self.session_factory() as session:
                from app.repositories import TripRepository
                repo   = TripRepository(session)
                public = repo.list_public(limit=12) if hasattr(repo, "list_public") else []
        except Exception:
            public = []

        if not public:
            return

        section = ctk.CTkFrame(self, fg_color=THEME["bg_card"], corner_radius=SHAPE["medium"], border_width=1, border_color=THEME["border"])
        section.pack(fill="x", padx=20, pady=(0, 24))
        ctk.CTkFrame(section, height=3, fg_color=THEME["chart_3"], corner_radius=0).pack(fill="x")
        ctk.CTkLabel(section, text="🌍  Community Itineraries", font=FONTS["title_sm"], text_color=THEME["text_primary"]).pack(anchor="w", padx=20, pady=(14, 8))

        grid = ctk.CTkFrame(section, fg_color="transparent")
        grid.pack(fill="x", padx=20, pady=(0, 16))
        grid.grid_columnconfigure((0, 1, 2), weight=1)

        for i, trip in enumerate(public):
            r, c = divmod(i, 3)
            cell = ctk.CTkFrame(grid, fg_color=THEME["bg_input"], corner_radius=SHAPE["small"], border_width=1, border_color=THEME["border"])
            cell.grid(row=r, column=c, padx=4, pady=4, sticky="ew")

            ctk.CTkLabel(cell, text=f"✈️  {trip.name}", font=FONTS["body_lg"], text_color=THEME["text_primary"], anchor="w", wraplength=200).pack(fill="x", padx=12, pady=(12, 2))
            stops = len(trip.stops)
            acts  = sum(len(s.activities) for s in trip.stops)
            ctk.CTkLabel(cell, text=f"📍 {stops} stops  •  🎟 {acts} activities", font=FONTS["badge"], text_color=THEME["text_muted"], anchor="w").pack(fill="x", padx=12)

            if trip.share_slug:
                ctk.CTkButton(cell, text="📋  Clone", font=FONTS["badge"], height=28, corner_radius=SHAPE["extra_small"], fg_color=THEME["accent"], hover_color=THEME["accent_hover"], command=lambda slug=trip.share_slug: self._quick_clone(slug)).pack(anchor="w", padx=12, pady=(8, 12))

    def _quick_clone(self, slug: str):
        try:
            with self.session_factory() as session:
                SharingService(session).copy_trip(slug, self.current_user.id)
                session.commit()
            messagebox.showinfo("Cloned!", "Trip has been cloned to My Trips.")
            self.navigate_callback("my_trips")
        except Exception as ex:
            messagebox.showerror("Error", str(ex))
