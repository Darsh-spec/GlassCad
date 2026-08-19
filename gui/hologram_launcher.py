"""
Builds a real-data JSON payload from a pipeline result and launches the
native PySide6/ModernGL hologram viewer as a separate OS process. Backend
logic (core.pipeline, core.noise, etc.) is never touched -- this only reads
the already-computed result dict and the existing voxel_status() helper.
"""
import os
import sys
import json
import tempfile
import subprocess
from core.visualize import voxel_status

HERE = os.path.dirname(os.path.abspath(__file__))
HOLOGRAM_DIR = os.path.join(HERE, "hologram")
HOLOGRAM_PROCESS = os.path.join(HOLOGRAM_DIR, "native", "native_hologram_process.py")


def _get_launch_command(tmp_path):
    """Picks the right way to launch the hologram viewer depending on
    whether we're running from source (dev) or as a PyInstaller-frozen
    .exe. When frozen, sys.executable points at the packaged app itself,
    not a real Python interpreter, so we must launch the sibling
    GlassCAD-Hologram.exe directly instead."""
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
        hologram_exe = os.path.join(base_dir, "GlassCAD-Hologram.exe")
        return [hologram_exe, tmp_path]
    else:
        return [sys.executable, HOLOGRAM_PROCESS, tmp_path]


def launch_hologram(result):
    clean = result["clean_grid"]
    noisy = result["noisy_grid"]

    # cap point count for responsiveness -- sample if the grid is huge
    xs, ys, zs, status = voxel_status(clean, noisy)
    max_points = 20000
    n = len(xs)
    if n > max_points:
        import random
        idx = sorted(random.sample(range(n), max_points))
        xs, ys, zs, status = xs[idx], ys[idx], zs[idx], status[idx]

    points = [
        {"x": int(xs[i]), "y": int(ys[i]), "z": int(zs[i]), "status": int(status[i])}
        for i in range(len(xs))
    ]

    payload = {
        "grid_dims": list(result["grid_dims"]),
        "total_voxels": result["total_voxels"],
        "density": result["density_bytes_per_voxel"],
        "ecc_errors": result["ecc_errors_corrected"],
        "recovered_exact": bool(result["recovered_exact"]),
        "timing": result["timing_ms"],
        "points": points,
    }

    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    json.dump(payload, tmp)
    tmp.close()

    # launch as a fully separate process -- avoids any Tkinter/Qt event-loop
    # conflict, especially on macOS, and correctly picks source-vs-frozen
    # launch command so this also works from a PyInstaller Windows build
    subprocess.Popen(_get_launch_command(tmp.name))