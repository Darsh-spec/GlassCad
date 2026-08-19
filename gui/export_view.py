import customtkinter as ctk
from gui import theme


class ExportView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        ctk.CTkLabel(self, text="EXPORT", font=theme.FONT_LABEL_BOLD,
                     text_color=theme.TEXT_DIM).pack(anchor="w", pady=(0, 12))

        self.panel = ctk.CTkFrame(self, fg_color=theme.PANEL, corner_radius=theme.RADIUS,
                                   border_width=1, border_color=theme.BORDER)
        self.panel.pack(fill="x")
        inner = ctk.CTkFrame(self.panel, fg_color="transparent")
        inner.pack(fill="x", padx=18, pady=18)

        ctk.CTkLabel(inner, text="GlassCAD Memory File", font=theme.FONT_LABEL_BOLD,
                     text_color=theme.TEXT).pack(anchor="w")
        self.status = ctk.CTkLabel(inner, text="Run a simulation first.",
                                    font=theme.FONT_SUB, text_color=theme.TEXT_DIM)
        self.status.pack(anchor="w", pady=(4, 14))

        self.export_btn = ctk.CTkButton(
            inner, text="Export .GMEM", fg_color=theme.ACCENT, hover_color="#349aa8",
            text_color="#0b0c0e", font=theme.FONT_LABEL_BOLD, height=38,
            command=self.controller.save_gmem, state="disabled")
        self.export_btn.pack(anchor="w")

    def enable(self):
        self.status.configure(text="Simulation data is ready to export.")
        self.export_btn.configure(state="normal")