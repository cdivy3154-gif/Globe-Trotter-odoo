import customtkinter as ctk
from app.ui.theme import THEME, FONTS


class Header(ctk.CTkFrame):
    def __init__(self, master, title: str = "Dashboard", subtitle: str = "", action_button=None, **kwargs):
        super().__init__(master, fg_color="transparent", height=70, **kwargs)
        self.title_text = title
        self.subtitle_text = subtitle
        self.action_button = action_button
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        left_frame = ctk.CTkFrame(self, fg_color="transparent")
        left_frame.grid(row=0, column=0, sticky="w", padx=0, pady=10)

        self.title_label = ctk.CTkLabel(
            left_frame,
            text=self.title_text,
            font=FONTS["title_xl"],
            text_color=THEME["text_primary"],
        )
        self.title_label.pack(anchor="w")

        if self.subtitle_text:
            self.subtitle_label = ctk.CTkLabel(
                left_frame,
                text=self.subtitle_text,
                font=FONTS["body"],
                text_color=THEME["text_secondary"],
            )
            self.subtitle_label.pack(anchor="w")

        if self.action_button:
            text, command, color = self.action_button
            btn = ctk.CTkButton(
                self,
                text=text,
                font=FONTS["body_lg"],
                fg_color=color or THEME["primary"],
                hover_color=THEME["primary_hover"],
                height=38,
                corner_radius=8,
                command=command,
            )
            btn.grid(row=0, column=1, sticky="e", padx=10, pady=10)

    def set_title(self, title: str, subtitle: str = ""):
        self.title_label.configure(text=title)
        if hasattr(self, "subtitle_label") and subtitle:
            self.subtitle_label.configure(text=subtitle)
