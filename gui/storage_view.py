import customtkinter as ctk
from gui import theme


class LabeledSlider(ctk.CTkFrame):
    def __init__(self, parent, label, from_, to_, initial, fmt="{:.2f}%", on_change=None):
        super().__init__(parent, fg_color="transparent")
        self.fmt = fmt
        self.on_change = on_change

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x")
        ctk.CTkLabel(top, text=label, font=theme.FONT_LABEL, text_color=theme.TEXT).pack(side="left")
        self.value_label = ctk.CTkLabel(top, text=fmt.format(initial * 100),
                                         font=theme.FONT_MONO, text_color=theme.ACCENT)
        self.value_label.pack(side="right")

        self.var = ctk.DoubleVar(value=initial)
        self.slider = ctk.CTkSlider(self, from_=from_, to=to_, variable=self.var,
                                     progress_color=theme.ACCENT, button_color=theme.ACCENT,
                                     command=self._changed)
        self.slider.pack(fill="x", pady=(8, 0))

        self.hint = ctk.CTkLabel(self, text="", font=theme.FONT_SUB, text_color=theme.TEXT_DIM)
        self.hint.pack(anchor="w", pady=(4, 0))
        self._changed(initial)

    def _changed(self, val):
        val = float(val)
        self.value_label.configure(text=self.fmt.format(val * 100))
        if val < 0.03:
            hint = "Low"
        elif val < 0.10:
            hint = "Moderate"
        else:
            hint = "High — may exceed ECC's correction budget"
        self.hint.configure(text=hint)
        if self.on_change:
            self.on_change(val)

    def get(self):
        return self.var.get()

    def set_value(self, v):
        self.var.set(v)
        self._changed(v)


class ECCSchemeSelector(ctk.CTkFrame):
    """Reed-Solomon vs BCH picker. RS corrects whole-byte errors and suits
    'burst' damage (e.g. a whole voxel lost). BCH corrects individual bits
    and can be more efficient against scattered single-bit noise, but has
    a smaller error budget against byte-level damage like missing voxels."""

    def __init__(self, parent, initial="reed_solomon"):
        super().__init__(parent, fg_color="transparent")
        self.value = ctk.StringVar(value=initial)

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x")
        self.rs_btn = ctk.CTkButton(
            row, text="Reed-Solomon", width=140, fg_color=theme.ACCENT_DIM,
            text_color=theme.ACCENT, hover_color=theme.PANEL_ALT,
            command=lambda: self._select("reed_solomon"))
        self.rs_btn.pack(side="left", padx=(0, 8))
        self.bch_btn = ctk.CTkButton(
            row, text="BCH", width=100, fg_color="transparent",
            text_color=theme.TEXT_DIM, hover_color=theme.PANEL_ALT,
            command=lambda: self._select("bch"))
        self.bch_btn.pack(side="left")

        self.desc = ctk.CTkLabel(
            self, text="", font=theme.FONT_SUB, text_color=theme.TEXT_DIM,
            wraplength=280, justify="left")
        self.desc.pack(anchor="w", pady=(8, 0))
        self._select(initial)

    def _select(self, value):
        self.value.set(value)
        if value == "reed_solomon":
            self.rs_btn.configure(fg_color=theme.ACCENT_DIM, text_color=theme.ACCENT)
            self.bch_btn.configure(fg_color="transparent", text_color=theme.TEXT_DIM)
            self.desc.configure(
                text="Corrects whole-byte errors — well suited to burst damage "
                     "like a fully missing voxel. Same scheme used in CDs and QR codes.")
        else:
            self.bch_btn.configure(fg_color=theme.ACCENT_DIM, text_color=theme.ACCENT)
            self.rs_btn.configure(fg_color="transparent", text_color=theme.TEXT_DIM)
            self.desc.configure(
                text="Corrects individual bit errors — more efficient against scattered "
                     "single-bit noise, but a smaller error budget against whole missing voxels.")

    def get(self):
        return self.value.get()


class ECCControl(ctk.CTkFrame):
    def __init__(self, parent, initial=32, lo=4, hi=64):
        super().__init__(parent, fg_color="transparent")
        self.lo, self.hi = lo, hi
        self.value = ctk.IntVar(value=initial)

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x")
        ctk.CTkLabel(row, text="ECC parity bytes", font=theme.FONT_LABEL,
                     text_color=theme.TEXT).pack(side="left")
        self.value_label = ctk.CTkLabel(row, text=str(initial), font=theme.FONT_MONO,
                                         text_color=theme.ACCENT)
        self.value_label.pack(side="right")

        ctrl = ctk.CTkFrame(self, fg_color="transparent")
        ctrl.pack(fill="x", pady=(8, 0))
        ctk.CTkButton(ctrl, text="−", width=32, fg_color=theme.PANEL_ALT,
                      hover_color=theme.BORDER, command=self._dec).pack(side="left")
        self.bar = ctk.CTkProgressBar(ctrl, progress_color=theme.ACCENT)
        self.bar.pack(side="left", fill="x", expand=True, padx=10)
        ctk.CTkButton(ctrl, text="+", width=32, fg_color=theme.PANEL_ALT,
                      hover_color=theme.BORDER, command=self._inc).pack(side="left")

        self.note = ctk.CTkLabel(self, text="Higher ECC → more resilient to physical noise, "
                                  "but a larger payload footprint",
                     font=theme.FONT_SUB, text_color=theme.TEXT_DIM,
                     wraplength=280, justify="left")
        self.note.pack(anchor="w", pady=(6, 0))
        self._refresh()

    def _dec(self):
        self.value.set(max(self.lo, self.value.get() - 4))
        self._refresh()

    def _inc(self):
        self.value.set(min(self.hi, self.value.get() + 4))
        self._refresh()

    def _refresh(self):
        v = self.value.get()
        self.value_label.configure(text=str(v))
        self.bar.set((v - self.lo) / (self.hi - self.lo))

    def get(self):
        return self.value.get()

    def set_value(self, v):
        self.value.set(max(self.lo, min(self.hi, v)))
        self._refresh()

    def set_bch_mode(self, is_bch):
        """BCH ignores the parity-byte slider (it uses fixed internal
        parameters), so disable it and explain why when BCH is selected."""
        if is_bch:
            self.value_label.configure(text="fixed (BCH)")
            self.note.configure(
                text="BCH uses fixed internal parameters (not this slider) — "
                     "protection level is determined by the scheme itself.")
        else:
            self._refresh()
            self.note.configure(
                text="Higher ECC → more resilient to physical noise, "
                     "but a larger payload footprint")


class GeometrySelector(ctk.CTkFrame):
    """Grid vs Hex layout picker. Both produce identical total voxel/byte
    capacity -- this only changes the spatial arrangement within each layer,
    not how much data can be stored."""

    def __init__(self, parent, initial="grid"):
        super().__init__(parent, fg_color="transparent")
        self.value = ctk.StringVar(value=initial)

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x")
        self.grid_btn = ctk.CTkButton(
            row, text="Grid", width=120, fg_color=theme.ACCENT_DIM,
            text_color=theme.ACCENT, hover_color=theme.PANEL_ALT,
            command=lambda: self._select("grid"))
        self.grid_btn.pack(side="left", padx=(0, 8))
        self.hex_btn = ctk.CTkButton(
            row, text="Hex", width=120, fg_color="transparent",
            text_color=theme.TEXT_DIM, hover_color=theme.PANEL_ALT,
            command=lambda: self._select("hex"))
        self.hex_btn.pack(side="left")

        self.desc = ctk.CTkLabel(
            self, text="", font=theme.FONT_SUB, text_color=theme.TEXT_DIM,
            wraplength=280, justify="left")
        self.desc.pack(anchor="w", pady=(8, 0))
        self._select(initial)

    def _select(self, value):
        self.value.set(value)
        if value == "grid":
            self.grid_btn.configure(fg_color=theme.ACCENT_DIM, text_color=theme.ACCENT)
            self.hex_btn.configure(fg_color="transparent", text_color=theme.TEXT_DIM)
            self.desc.configure(
                text="Standard square layout — each voxel sits on a regular row/column.")
        else:
            self.hex_btn.configure(fg_color=theme.ACCENT_DIM, text_color=theme.ACCENT)
            self.grid_btn.configure(fg_color="transparent", text_color=theme.TEXT_DIM)
            self.desc.configure(
                text="Honeycomb-offset layout — alternating rows shifted, same total "
                     "voxel capacity, different spatial packing.")

    def get(self):
        return self.value.get()


class StorageView(ctk.CTkFrame):
    """Noise + ECC scheme/parity + geometry + optional encryption
    configuration, plus a conceptual volume preview. All values auto-
    configure to sensible, file-size-aware defaults the moment a file is
    chosen (see apply_auto_recommendation), but every control stays fully
    manually adjustable afterward."""

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        ctk.CTkLabel(self, text="STORAGE CONFIGURATION", font=theme.FONT_LABEL_BOLD,
                     text_color=theme.TEXT_DIM).pack(anchor="w", pady=(0, 12))

        noise_panel = ctk.CTkFrame(self, fg_color=theme.PANEL, corner_radius=theme.RADIUS,
                                    border_width=1, border_color=theme.BORDER)
        noise_panel.pack(fill="x", pady=(0, 14))
        inner = ctk.CTkFrame(noise_panel, fg_color="transparent")
        inner.pack(fill="x", padx=18, pady=16)
        ctk.CTkLabel(inner, text="Physical Noise", font=theme.FONT_LABEL_BOLD,
                     text_color=theme.TEXT).pack(anchor="w", pady=(0, 10))
        self.missing_slider = LabeledSlider(inner, "Missing voxel rate", 0, 0.3, 0.0)
        self.missing_slider.pack(fill="x", pady=(0, 14))
        self.corrupt_slider = LabeledSlider(inner, "Bit corruption rate", 0, 0.3, 0.0)
        self.corrupt_slider.pack(fill="x")

        ecc_panel = ctk.CTkFrame(self, fg_color=theme.PANEL, corner_radius=theme.RADIUS,
                                  border_width=1, border_color=theme.BORDER)
        ecc_panel.pack(fill="x", pady=(0, 14))
        inner2 = ctk.CTkFrame(ecc_panel, fg_color="transparent")
        inner2.pack(fill="x", padx=18, pady=16)
        ctk.CTkLabel(inner2, text="Error Correction", font=theme.FONT_LABEL_BOLD,
                     text_color=theme.TEXT).pack(anchor="w", pady=(0, 10))
        self.ecc_scheme_selector = ECCSchemeSelector(inner2)
        self.ecc_scheme_selector.pack(fill="x", pady=(0, 14))
        self.ecc_control = ECCControl(inner2)
        self.ecc_control.pack(fill="x")

        self.auto_note = ctk.CTkLabel(
            inner2, text="", font=theme.FONT_SUB, text_color=theme.ACCENT,
            wraplength=280, justify="left")

        # wire scheme toggle to disable/relabel the parity slider for BCH
        self.ecc_scheme_selector.rs_btn.configure(
            command=lambda: self._on_ecc_scheme_change("reed_solomon"))
        self.ecc_scheme_selector.bch_btn.configure(
            command=lambda: self._on_ecc_scheme_change("bch"))

        geometry_panel = ctk.CTkFrame(self, fg_color=theme.PANEL, corner_radius=theme.RADIUS,
                                       border_width=1, border_color=theme.BORDER)
        geometry_panel.pack(fill="x", pady=(0, 14))
        inner5 = ctk.CTkFrame(geometry_panel, fg_color="transparent")
        inner5.pack(fill="x", padx=18, pady=16)
        ctk.CTkLabel(inner5, text="Voxel Geometry", font=theme.FONT_LABEL_BOLD,
                     text_color=theme.TEXT).pack(anchor="w", pady=(0, 10))
        self.geometry_selector = GeometrySelector(inner5)
        self.geometry_selector.pack(fill="x")

        crypto_panel = ctk.CTkFrame(self, fg_color=theme.PANEL, corner_radius=theme.RADIUS,
                                     border_width=1, border_color=theme.BORDER)
        crypto_panel.pack(fill="x", pady=(0, 14))
        inner4 = ctk.CTkFrame(crypto_panel, fg_color="transparent")
        inner4.pack(fill="x", padx=18, pady=16)
        ctk.CTkLabel(inner4, text="Encryption (optional)", font=theme.FONT_LABEL_BOLD,
                     text_color=theme.TEXT).pack(anchor="w", pady=(0, 8))
        ctk.CTkLabel(inner4, text="AES, applied before error correction. Leave blank to skip.",
                     font=theme.FONT_SUB, text_color=theme.TEXT_DIM,
                     wraplength=280, justify="left").pack(anchor="w", pady=(0, 8))
        self.password_var = ctk.StringVar(value="")
        self.password_entry = ctk.CTkEntry(inner4, textvariable=self.password_var,
                                            placeholder_text="Password (optional)", show="•")
        self.password_entry.pack(fill="x")

        vol_panel = ctk.CTkFrame(self, fg_color=theme.PANEL, corner_radius=theme.RADIUS,
                                  border_width=1, border_color=theme.BORDER)
        vol_panel.pack(fill="x")
        inner3 = ctk.CTkFrame(vol_panel, fg_color="transparent")
        inner3.pack(fill="x", padx=18, pady=16)
        ctk.CTkLabel(inner3, text="Storage Volume", font=theme.FONT_LABEL_BOLD,
                     text_color=theme.TEXT).pack(anchor="w", pady=(0, 6))
        self.vol_label = ctk.CTkLabel(
            inner3, text="Grid dimensions appear here after Run\n(computed from your actual file, not estimated)",
            font=theme.FONT_SUB, text_color=theme.TEXT_DIM, justify="left")
        self.vol_label.pack(anchor="w")

    def _on_ecc_scheme_change(self, value):
        self.ecc_scheme_selector._select(value)
        self.ecc_control.set_bch_mode(value == "bch")

    def apply_auto_recommendation(self, file_size_bytes):
        """Auto-configures ECC + noise sliders to sensible, demo-ready
        defaults based purely on the chosen file's real size. Every value
        set here remains manually adjustable afterward -- nothing is locked.

        IMPORTANT: a file splits into many independent RS blocks (a ~500KB
        file is ~2000 blocks). Even a noise rate that's safe on AVERAGE can,
        by pure statistical variance, cause a small number of individual
        blocks to exceed the correction ceiling -- and with thousands of
        blocks, that's likely unless the margin is large. These rates carry
        real statistical margin (not just the average) so the default run
        reliably succeeds across all blocks, not just most. These are tuned
        for Reed-Solomon; BCH is a smaller error budget against missing
        voxels specifically, worth noting if switching schemes manually."""
        if file_size_bytes < 100_000:
            ecc, missing, corrupt = 16, 0.0015, 0.0015
            reason = "small file — light protection, safe across all blocks"
        elif file_size_bytes < 5_000_000:
            ecc, missing, corrupt = 32, 0.005, 0.005
            reason = "medium file — balanced protection, safe across all blocks"
        else:
            ecc, missing, corrupt = 48, 0.01, 0.01
            reason = "larger file — extra ECC headroom, safe across all blocks"

        self.ecc_control.set_value(ecc)
        self.missing_slider.set_value(missing)
        self.corrupt_slider.set_value(corrupt)

        self.auto_note.configure(
            text=f"Auto-configured ({reason}). Drag any control to override.")
        self.auto_note.pack(anchor="w", pady=(6, 0))

    def set_volume(self, dims, total_voxels):
        w, h, l = dims
        self.vol_label.configure(
            text=f"{w} × {h} × {l}\n{total_voxels:,} voxels",
            font=theme.FONT_MONO, text_color=theme.ACCENT)

    def get_noise_config(self):
        from core.noise import NoiseConfig
        return NoiseConfig(
            missing_voxel_rate=self.missing_slider.get(),
            bit_corruption_rate=self.corrupt_slider.get(),
            seed=42,
        )

    def get_ecc_bytes(self):
        return self.ecc_control.get()

    def get_ecc_scheme(self):
        return self.ecc_scheme_selector.get()

    def get_geometry(self):
        return self.geometry_selector.get()

    def get_password(self):
        pw = self.password_var.get().strip()
        return pw if pw else None