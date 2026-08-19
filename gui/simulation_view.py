import threading
import customtkinter as ctk
from gui import theme

STAGES = [
    "Reading input",
    "Compressing payload",
    "Applying ECC",
    "Mapping into storage volume",
    "Simulating physical noise",
    "Decoding",
    "Validating recovery",
]


class SimulationView(ctk.CTkFrame):
    """
    IMPORTANT HONESTY NOTE: the backend exposes a single run_pipeline() call,
    not per-stage hooks. The stage list below is a UX narration of what that
    one call is doing internally (which is all true, in that order) -- it is
    NOT claiming the backend reports these stages independently. We advance
    them on a timer while the real call runs in a background thread, and if
    the real call finishes before the animation, we snap straight to the
    final state instead of faking extra delay.
    """

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.stage_labels = []

        ctk.CTkLabel(self, text="SIMULATION", font=theme.FONT_LABEL_BOLD,
                     text_color=theme.TEXT_DIM).pack(anchor="w", pady=(0, 12))

        self.panel = ctk.CTkFrame(self, fg_color=theme.PANEL, corner_radius=theme.RADIUS,
                                   border_width=1, border_color=theme.BORDER)
        self.panel.pack(fill="x", pady=(0, 14))
        inner = ctk.CTkFrame(self.panel, fg_color="transparent")
        inner.pack(fill="x", padx=18, pady=18)

        for stage in STAGES:
            row = ctk.CTkFrame(inner, fg_color="transparent")
            row.pack(fill="x", pady=3)
            mark = ctk.CTkLabel(row, text="○", font=theme.FONT_MONO,
                                 text_color=theme.TEXT_DIM, width=20)
            mark.pack(side="left")
            lbl = ctk.CTkLabel(row, text=stage, font=theme.FONT_LABEL,
                                text_color=theme.TEXT_DIM)
            lbl.pack(side="left")
            self.stage_labels.append((mark, lbl))

        self.run_btn = ctk.CTkButton(
            self, text="RUN SIMULATION", fg_color=theme.ACCENT, hover_color="#349aa8",
            text_color="#0b0c0e", font=theme.FONT_LABEL_BOLD, height=40,
            command=self.start)
        self.run_btn.pack(fill="x")

        self.optimize_btn = ctk.CTkButton(
            self, text="RUN DESIGN-SPACE SEARCH", fg_color=theme.PANEL_ALT,
            hover_color=theme.BORDER, text_color=theme.TEXT,
            font=theme.FONT_LABEL_BOLD, height=36,
            command=self.start_optimizer)
        self.optimize_btn.pack(fill="x", pady=(8, 0))

        self.error_panel = None
        self.optimizer_panel = None
        self._stage_index = 0
        self._result = None
        self._error = None

    def _reset_stages(self):
        self._stage_index = 0
        for mark, lbl in self.stage_labels:
            mark.configure(text="○", text_color=theme.TEXT_DIM)
            lbl.configure(text_color=theme.TEXT_DIM)
        if self.error_panel:
            self.error_panel.destroy()
            self.error_panel = None

    def start(self):
        if not self.controller.raw_bytes:
            self.controller.show_toast("Choose a file first.", theme.WARNING)
            return

        self._reset_stages()
        self.run_btn.configure(state="disabled", text="RUNNING…")
        self._result = None
        self._error = None

        thread = threading.Thread(target=self._run_backend, daemon=True)
        thread.start()
        self._animate_stage()

    def _run_backend(self):
        try:
            if not self.controller.raw_bytes:
                self._error = "No file loaded — go to Design and choose a file first."
                return

            cfg = self.controller.storage_view.get_noise_config()
            ecc_bytes = self.controller.storage_view.get_ecc_bytes()
            password = self.controller.storage_view.get_password()
            geometry = self.controller.storage_view.get_geometry()
            ecc_scheme = self.controller.storage_view.get_ecc_scheme()
            from core.pipeline import run_pipeline
            result = run_pipeline(
                self.controller.raw_bytes,
                self.controller.filename,
                cfg,
                ecc_bytes=ecc_bytes,
                password=password,
                geometry=geometry,
                ecc_scheme=ecc_scheme,
            )
            self._result = result
        except MemoryError:
            self._error = "File too large for this prototype's memory limits — try a smaller file."
        except Exception as e:
            self._error = f"{type(e).__name__}: {e}"

    def _animate_stage(self):
        # advance one stage marker at a time; if the real call already
        # finished, stop narrating and jump straight to completion
        if self._stage_index < len(self.stage_labels):
            mark, lbl = self.stage_labels[self._stage_index]
            mark.configure(text="●", text_color=theme.ACCENT)
            lbl.configure(text_color=theme.TEXT)
            if self._stage_index > 0:
                prev_mark, prev_lbl = self.stage_labels[self._stage_index - 1]
                prev_mark.configure(text="✓", text_color=theme.SUCCESS)
            self._stage_index += 1

        if self._result is None and self._error is None:
            self.after(160, self._animate_stage)
        else:
            if self._stage_index >= len(self.stage_labels):
                last_mark, last_lbl = self.stage_labels[-1]
                last_mark.configure(text="✓", text_color=theme.SUCCESS)
            self.after(150, self._finish)

    def _finish(self):
        self.run_btn.configure(state="normal", text="RUN SIMULATION")
        if self._error:
            self._show_error(self._error)
        else:
            self.controller.on_simulation_complete(self._result)

    def _show_error(self, message):
        self.error_panel = ctk.CTkFrame(self.panel, fg_color="#2a1f1f",
                                         corner_radius=theme.RADIUS,
                                         border_width=1, border_color=theme.ERROR)
        self.error_panel.pack(fill="x", padx=18, pady=(0, 18))
        inner = ctk.CTkFrame(self.error_panel, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=12)
        ctk.CTkLabel(inner, text="SIMULATION ERROR", font=theme.FONT_LABEL_BOLD,
                     text_color=theme.ERROR).pack(anchor="w")
        ctk.CTkLabel(inner, text=message, font=theme.FONT_SUB, text_color=theme.TEXT_DIM,
                     wraplength=340, justify="left").pack(anchor="w", pady=(4, 0))

    def start_optimizer(self):
        if not self.controller.raw_bytes:
            self.controller.show_toast("Choose a file first.", theme.WARNING)
            return

        if self.optimizer_panel:
            self.optimizer_panel.destroy()
            self.optimizer_panel = None

        self.optimize_btn.configure(state="disabled", text="SEARCHING…")
        thread = threading.Thread(target=self._run_optimizer_backend, daemon=True)
        thread.start()

    def _run_optimizer_backend(self):
        try:
            cfg = self.controller.storage_view.get_noise_config()
            ecc_bytes = self.controller.storage_view.get_ecc_bytes()
            password = self.controller.storage_view.get_password()
            from core.optimizer import run_design_space_search
            results = run_design_space_search(
                self.controller.raw_bytes, self.controller.filename,
                cfg, ecc_bytes=ecc_bytes, password=password,
            )
            self.after(0, lambda: self._show_optimizer_results(results))
        except Exception as e:
            self.after(0, lambda: self._show_optimizer_error(f"{type(e).__name__}: {e}"))

    def _show_optimizer_results(self, results):
        self.optimize_btn.configure(state="normal", text="RUN DESIGN-SPACE SEARCH")

        self.optimizer_panel = ctk.CTkFrame(self.panel, fg_color=theme.PANEL_ALT,
                                             corner_radius=theme.RADIUS,
                                             border_width=1, border_color=theme.BORDER)
        self.optimizer_panel.pack(fill="x", padx=18, pady=(0, 18))
        inner = ctk.CTkFrame(self.optimizer_panel, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=12)

        ctk.CTkLabel(inner, text="DESIGN-SPACE SEARCH — real runs, ranked best first",
                     font=theme.FONT_LABEL_BOLD, text_color=theme.TEXT).pack(anchor="w", pady=(0, 10))

        for i, r in enumerate(results):
            row = ctk.CTkFrame(inner, fg_color=theme.PANEL if i == 0 else "transparent",
                                corner_radius=6)
            row.pack(fill="x", pady=2)
            inner_row = ctk.CTkFrame(row, fg_color="transparent")
            inner_row.pack(fill="x", padx=10, pady=6)

            rank_prefix = "★ BEST  " if i == 0 else f"{i+1}.  "
            status = "✓" if (r["decode_success"] and r["recovered_exact"]) else "✕"
            total_ms = sum(r["timing_ms"].values())

            ctk.CTkLabel(inner_row, text=f"{rank_prefix}{status}  {r['config_label']}",
                         font=theme.FONT_LABEL_BOLD, text_color=theme.TEXT).pack(anchor="w")
            ctk.CTkLabel(inner_row,
                         text=f"errors corrected: {r['ecc_errors_corrected']}   ·   "
                              f"time: {total_ms:.1f}ms   ·   density: {r['density_bytes_per_voxel']:.4f} B/voxel",
                         font=theme.FONT_SUB, text_color=theme.TEXT_DIM).pack(anchor="w")

    def _show_optimizer_error(self, message):
        self.optimize_btn.configure(state="normal", text="RUN DESIGN-SPACE SEARCH")
        self.optimizer_panel = ctk.CTkFrame(self.panel, fg_color="#2a1f1f",
                                             corner_radius=theme.RADIUS,
                                             border_width=1, border_color=theme.ERROR)
        self.optimizer_panel.pack(fill="x", padx=18, pady=(0, 18))
        inner = ctk.CTkFrame(self.optimizer_panel, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=12)
        ctk.CTkLabel(inner, text="SEARCH FAILED", font=theme.FONT_LABEL_BOLD,
                     text_color=theme.ERROR).pack(anchor="w")
        ctk.CTkLabel(inner, text=message, font=theme.FONT_SUB, text_color=theme.TEXT_DIM,
                     wraplength=340, justify="left").pack(anchor="w", pady=(4, 0))