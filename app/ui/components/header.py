"""
Header component — page title bar with optional subtitle, breadcrumb, and action button.
"""
import customtkinter as ctk
from app.ui.theme import THEME, FONTS, LAYOUT, SHAPE


class Header(ctk.CTkFrame):
    """Top-of-screen header with title, subtitle, optional breadcrumb and CTA button."""

    def __init__(
        self,
        master,
        title: str,
        subtitle: str = "",
        action_button: tuple | None = None,   # (label, command, color)
        breadcrumb: list[str] | None = None,  # ["Dashboard", "My Trips"]
        **kwargs,
    ):
        super().__init__(
            master,
            fg_color=THEME["bg_card"],
            corner_radius=SHAPE["medium"],
            border_width=1,
            border_color=THEME["border"],
            **kwargs,
        )

        self.grid_columnconfigure(0, weight=1)

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="x", padx=LAYOUT["pad_lg"], pady=(16, 14))
        inner.grid_columnconfigure(0, weight=1)

        # ── Breadcrumb ────────────────────────────────────────────
        if breadcrumb and len(breadcrumb) > 1:
            bc_frame = ctk.CTkFrame(inner, fg_color="transparent")
            bc_frame.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))
            for i, crumb in enumerate(breadcrumb):
                ctk.CTkLabel(
                    bc_frame,
                    text=crumb,
                    font=FONTS["caption"],
                    text_color=THEME["text_muted"] if i < len(breadcrumb) - 1 else THEME["primary"],
                ).pack(side="left")
                if i < len(breadcrumb) - 1:
                    ctk.CTkLabel(
                        bc_frame, text=" › ", font=FONTS["caption"], text_color=THEME["text_muted"]
                    ).pack(side="left")

        # ── Title Row ─────────────────────────────────────────────
        title_row = ctk.CTkFrame(inner, fg_color="transparent")
        title_row.grid(row=1, column=0, sticky="ew")
        title_row.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            title_row,
            text=title,
            font=FONTS["title_lg"],
            text_color=THEME["text_primary"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        # ── Action Button ─────────────────────────────────────────
        if action_button:
            lbl, cmd, color = action_button
            ctk.CTkButton(
                title_row,
                text=lbl,
                font=FONTS["body_lg"],
                height=LAYOUT["btn_height_sm"],
                corner_radius=SHAPE["small"],
                fg_color=color,
                hover_color=THEME["primary_hover"] if color == THEME["primary"] else THEME["accent_hover"],
                command=cmd,
            ).grid(row=0, column=1, sticky="e", padx=(12, 0))

        # ── Subtitle ──────────────────────────────────────────────
        if subtitle:
            ctk.CTkLabel(
                inner,
                text=subtitle,
                font=FONTS["body"],
                text_color=THEME["text_secondary"],
                anchor="w",
                wraplength=700,
                justify="left",
            ).grid(row=2, column=0, sticky="w", pady=(4, 0))

        # ── Accent underline bar ──────────────────────────────────
        bar = ctk.CTkFrame(self, height=3, fg_color=THEME["primary"], corner_radius=0)
        bar.pack(fill="x", side="bottom")
