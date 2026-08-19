import customtkinter as ctk
from gui import theme
from gui.hologram_launcher import launch_hologram


class StatCard(ctk.CTkFrame):
    def __init__(self, parent, label, value):
        super().__init__(parent, fg_color=theme.PANEL_ALT, corner_radius=theme.RADIUS,
                          border_width=1, border_color=theme.BORDER)
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(padx=16, pady=12, anchor="w")
        ctk.CTkLabel(inner, text=label, font=theme.FONT_SUB,
                     text_color=theme.TEXT_DIM).pack(anchor="w")
        ctk.CTkLabel(inner, text=value, font=theme.FONT_MONO_BIG,
                     text_color=theme.TEXT).pack(anchor="w", pady=(2, 0))


class ResultsView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        ctk.CTkLabel(self, text="RESULTS", font=theme.FONT_LABEL_BOLD,
                     text_color=theme.TEXT_DIM).pack(anchor="w", pady=(0, 12))

        self.status_label = ctk.CTkLabel(self, text="No simulation run yet",
                                          font=theme.FONT_MONO_BIG, text_color=theme.TEXT_DIM)
        self.status_label.pack(anchor="w", pady=(0, 16))

        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True)

    def render(self, result):
        for w in self.body.winfo_children():
            w.destroy()

        success = result["decode_success"] and result["recovered_exact"]
        if success:
            self.status_label.configure(text="✓ SIMULATION SUCCESSFUL", text_color=theme.SUCCESS)
        elif result["decode_success"]:
            self.status_label.configure(text="⚠ RECOVERED BUT NOT EXACT", text_color=theme.WARNING)
        else:
            self.status_label.configure(text="✕ RECOVERY FAILED", text_color=theme.ERROR)

        grid = ctk.CTkFrame(self.body, fg_color="transparent")
        grid.pack(fill="x")
        grid.grid_columnconfigure((0, 1), weight=1)

        w, h, l = result["grid_dims"]
        scheme_labels = {"reed_solomon": "Reed-Solomon", "bch": "BCH"}
        cards = [
            ("Original Data", f"{result['original_len']:,} B"),
            ("Encoded Payload", f"{result['payload_len']:,} B"),
            ("Storage Volume", f"{w}×{h}×{l}"),
            ("Total Voxels", f"{result['total_voxels']:,}"),
            ("Storage Density", f"{result['density_bytes_per_voxel']:.4f} B/voxel"),
            ("Voxel Geometry", result.get("geometry", "grid").capitalize()),
            ("ECC Scheme", scheme_labels.get(result.get("ecc_scheme", "reed_solomon"), "Reed-Solomon")),
            ("ECC Errors Corrected",
             str(result['ecc_errors_corrected']) if result['ecc_errors_corrected'] is not None else "—"),
            ("Encryption", "AES enabled" if result.get("encrypted") else "None"),
            ("SHA-256 Match", "✓ Verified" if result.get("sha256_match") else "✗ Mismatch"),
        ]
        for i, (label, value) in enumerate(cards):
            card = StatCard(grid, label, value)
            card.grid(row=i // 2, column=i % 2, sticky="ew", padx=6, pady=6)

        timing_panel = ctk.CTkFrame(self.body, fg_color=theme.PANEL, corner_radius=theme.RADIUS,
                                     border_width=1, border_color=theme.BORDER)
        timing_panel.pack(fill="x", pady=(14, 0))
        inner = ctk.CTkFrame(timing_panel, fg_color="transparent")
        inner.pack(fill="x", padx=18, pady=14)
        ctk.CTkLabel(inner, text="PERFORMANCE", font=theme.FONT_LABEL_BOLD,
                     text_color=theme.TEXT).pack(anchor="w", pady=(0, 8))
        t = result["timing_ms"]
        total = round(sum(t.values()), 2)
        for k, v in [("Encoding", t["encode"]), ("Noise", t["noise"]),
                     ("Decoding", t["decode"]), ("Total", total)]:
            row = ctk.CTkFrame(inner, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=k, font=theme.FONT_LABEL, text_color=theme.TEXT_DIM).pack(side="left")
            ctk.CTkLabel(row, text=f"{v} ms", font=theme.FONT_MONO, text_color=theme.TEXT).pack(side="right")

        holo_btn = ctk.CTkButton(
            self.body, text="Enter Hologram View", fg_color=theme.ACCENT,
            hover_color="#349aa8", text_color="#0b0c0e", font=theme.FONT_LABEL_BOLD,
            height=38, command=lambda: launch_hologram(result))
        holo_btn.pack(fill="x", pady=(14, 0))

        if result["error_message"]:
            err = ctk.CTkFrame(self.body, fg_color="#2a1f1f", corner_radius=theme.RADIUS,
                                border_width=1, border_color=theme.ERROR)
            err.pack(fill="x", pady=(14, 0))
            inner2 = ctk.CTkFrame(err, fg_color="transparent")
            inner2.pack(fill="x", padx=14, pady=12)
            ctk.CTkLabel(inner2, text=result["error_message"], font=theme.FONT_SUB,
                         text_color=theme.ERROR, wraplength=340, justify="left").pack(anchor="w")