import os
import customtkinter as ctk
from tkinter import filedialog
from gui import theme
from gui.sidebar import Sidebar
from gui.design_view import DesignView
from gui.storage_view import StorageView
from gui.simulation_view import SimulationView
from gui.results_view import ResultsView
from gui.export_view import ExportView
from gui.hologram_launcher import launch_hologram

ctk.set_appearance_mode("dark")


class GlassCADApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("GlassCAD")
        self.geometry("980x680")
        self.minsize(860, 600)
        self.configure(fg_color=theme.BG)

        self.raw_bytes = None
        self.filepath = None
        self.filename = None
        self.last_result = None

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color=theme.BG, height=48, corner_radius=0)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.status_dot = ctk.CTkLabel(header, text="●  Simulation Ready",
                                        font=theme.FONT_SUB, text_color=theme.TEXT_DIM)
        self.status_dot.pack(side="right", padx=20, pady=12)

        # Sidebar
        self.sidebar = Sidebar(self, self.navigate)
        self.sidebar.grid(row=1, column=0, sticky="ns")

        # Main workspace (scrollable, so it survives smaller laptop screens)
        self.workspace = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.workspace.grid(row=1, column=1, sticky="nsew", padx=30, pady=20)

        # Status bar
        statusbar = ctk.CTkFrame(self, fg_color=theme.PANEL, height=28, corner_radius=0)
        statusbar.grid(row=2, column=0, columnspan=2, sticky="ew")
        ctk.CTkLabel(statusbar, text="GlassCAD v0.1", font=theme.FONT_SUB,
                     text_color=theme.TEXT_DIM).pack(side="left", padx=16, pady=4)
        ctk.CTkLabel(statusbar, text="Optical Storage Engine", font=theme.FONT_SUB,
                     text_color=theme.TEXT_DIM).pack(side="right", padx=16, pady=4)

        # Views
        self.design_view = DesignView(self.workspace, self)
        self.storage_view = StorageView(self.workspace, self)
        self.simulation_view = SimulationView(self.workspace, self)
        self.results_view = ResultsView(self.workspace, self)
        self.export_view = ExportView(self.workspace, self)

        self.views = {
            "Design": self.design_view,
            "Storage": self.storage_view,
            "Simulation": self.simulation_view,
            "Results": self.results_view,
            "Export": self.export_view,
        }
        self.navigate("Design")

    def navigate(self, name):
        for view in self.views.values():
            view.pack_forget()
        self.views[name].pack(fill="both", expand=True)
        self.sidebar.set_active(name)

    def choose_file(self):
        path = filedialog.askopenfilename()
        if not path:
            return

        try:
            with open(path, "rb") as f:
                data = f.read()
        except PermissionError:
            self.show_toast("Permission denied — can't read that file.", theme.ERROR)
            return
        except OSError as e:
            self.show_toast(f"Couldn't read file: {e.strerror or e}", theme.ERROR)
            return
        except Exception as e:
            self.show_toast(f"Unexpected error reading file: {e}", theme.ERROR)
            return

        if len(data) == 0:
            self.show_toast("That file is empty — choose a different one.", theme.WARNING)
            return

        MAX_SIZE = 50 * 1024 * 1024  # 50 MB safety cap for this prototype
        if len(data) > MAX_SIZE:
            self.show_toast(
                f"File is {len(data)/1_000_000:.1f} MB — over the 50 MB demo limit.",
                theme.WARNING)
            return

        self.filepath = path
        self.filename = os.path.basename(path)
        self.raw_bytes = data
        self.design_view.show_selected(path, len(self.raw_bytes))
        self.storage_view.apply_auto_recommendation(len(self.raw_bytes))
        self.status_dot.configure(text="●  File Loaded")

    def on_simulation_complete(self, result):
        self.last_result = result
        self.storage_view.set_volume(result["grid_dims"], result["total_voxels"])
        self.results_view.render(result)
        self.export_view.enable()

        if result["decode_success"] and result["recovered_exact"]:
            self.status_dot.configure(text="●  Simulation Successful", text_color=theme.SUCCESS)
            launch_hologram(result)
        else:
            self.status_dot.configure(text="●  Recovery Failed", text_color=theme.ERROR)

        self.navigate("Results")

    def save_gmem(self):
        if not self.last_result:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".gmem", filetypes=[("GlassCAD memory file", "*.gmem")])
        if not path:
            return
        try:
            with open(path, "w") as f:
                f.write(self.last_result["gmem_text"])
            self.show_toast(f"Saved to {os.path.basename(path)}", theme.SUCCESS)
        except OSError as e:
            self.show_toast(f"Couldn't save file: {e.strerror or e}", theme.ERROR)

    def show_toast(self, message, color):
        # lightweight, no extra dependency: reuse the header status label briefly
        prev_text = self.status_dot.cget("text")
        prev_color = self.status_dot.cget("text_color")
        self.status_dot.configure(text=f"●  {message}", text_color=color)
        self.after(2500, lambda: self.status_dot.configure(text=prev_text, text_color=prev_color))


if __name__ == "__main__":
    app = GlassCADApp()
    app.update_idletasks()
    app.after(50, lambda: app.geometry("981x680"))  # nudge size to force macOS to repaint
    app.mainloop()