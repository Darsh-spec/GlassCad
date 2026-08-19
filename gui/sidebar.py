import customtkinter as ctk
from gui import theme

NAV_ITEMS = ["Design", "Storage", "Simulation", "Results", "Export"]


class Sidebar(ctk.CTkFrame):
    def __init__(self, parent, on_navigate):
        super().__init__(parent, width=170, fg_color=theme.PANEL, corner_radius=0)
        self.on_navigate = on_navigate
        self.buttons = {}

        ctk.CTkLabel(self, text="GlassCAD", font=theme.FONT_HEADER,
                     text_color=theme.TEXT).pack(anchor="w", padx=20, pady=(24, 2))
        ctk.CTkLabel(self, text="Optical Storage Engine", font=theme.FONT_SUB,
                     text_color=theme.TEXT_DIM).pack(anchor="w", padx=20, pady=(0, 24))

        for item in NAV_ITEMS:
            btn = ctk.CTkButton(
                self, text=item, anchor="w", fg_color="transparent",
                text_color=theme.TEXT_DIM, hover_color=theme.PANEL_ALT,
                font=theme.FONT_NAV, corner_radius=theme.RADIUS, height=34,
                command=lambda i=item: self.on_navigate(i),
            )
            btn.pack(fill="x", padx=10, pady=2)
            self.buttons[item] = btn

        self.set_active("Design")

    def set_active(self, name):
        for item, btn in self.buttons.items():
            if item == name:
                btn.configure(fg_color=theme.ACCENT_DIM, text_color=theme.ACCENT)
            else:
                btn.configure(fg_color="transparent", text_color=theme.TEXT_DIM)