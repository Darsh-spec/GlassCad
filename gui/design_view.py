import os
import customtkinter as ctk
from gui import theme


def _human_size(n):
    for unit in ["B", "KB", "MB", "GB"]:
        if n < 1024:
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


class DesignView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        ctk.CTkLabel(self, text="INPUT DATA", font=theme.FONT_LABEL_BOLD,
                     text_color=theme.TEXT_DIM).pack(anchor="w", pady=(0, 12))

        self.drop_frame = ctk.CTkFrame(self, fg_color=theme.PANEL, corner_radius=theme.RADIUS,
                                        border_width=1, border_color=theme.BORDER, height=180)
        self.drop_frame.pack(fill="x")
        self.drop_frame.pack_propagate(False)

        self.empty_label = ctk.CTkLabel(
            self.drop_frame, text="No file selected\n\nChoose a file to simulate its storage",
            font=theme.FONT_SUB, text_color=theme.TEXT_DIM, justify="center")
        self.empty_label.pack(expand=True)

        self.browse_btn = ctk.CTkButton(
            self, text="Choose File", fg_color=theme.ACCENT, hover_color="#349aa8",
            text_color="#0b0c0e", font=theme.FONT_LABEL_BOLD, height=36,
            command=self.controller.choose_file)
        self.browse_btn.pack(anchor="w", pady=(14, 0))

    def show_selected(self, filepath, size_bytes):
        for w in self.drop_frame.winfo_children():
            w.destroy()

        name = os.path.basename(filepath)
        ext = (os.path.splitext(name)[1] or "FILE").lstrip(".").upper()

        card = ctk.CTkFrame(self.drop_frame, fg_color="transparent")
        card.pack(expand=True)
        ctk.CTkLabel(card, text=name, font=theme.FONT_LABEL_BOLD,
                     text_color=theme.TEXT).pack(pady=(0, 4))
        ctk.CTkLabel(card, text=f"{ext} • {_human_size(size_bytes)}",
                     font=theme.FONT_SUB, text_color=theme.TEXT_DIM).pack()