"""QOpenGLWidget hosting the ModernGL hologram renderer, with orbit-drag and
scroll-zoom mouse interaction, and floating Qt label overlays (layer labels,
legend, dims, status) projected/positioned around the real 3D model -- no
HTML/browser involved anywhere."""
import os
import time
import numpy as np
import moderngl
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QLabel, QWidget
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtGui import QSurfaceFormat

from renderer import HologramRenderer
from camera import OrbitCamera, perspective

HERE = os.path.dirname(os.path.abspath(__file__))
SHADER_DIR = os.path.join(HERE, "shaders")


class HologramView(QOpenGLWidget):
    def __init__(self, data, parent=None):
        fmt = QSurfaceFormat()
        fmt.setVersion(3, 3)
        fmt.setProfile(QSurfaceFormat.CoreProfile)
        fmt.setSamples(4)
        QSurfaceFormat.setDefaultFormat(fmt)
        super().__init__(parent)

        self.data = data
        self.camera = OrbitCamera()
        self.ctx = None
        self.renderer = None
        self.start_time = time.time()
        self.build_done = False
        self.last_mouse = None

        # --- top-left explainer subtitle: what am I looking at ---
        self.subtitle_label = QLabel(self)
        self.subtitle_label.setStyleSheet(
            "color:#8fb8c0; font-size:10px; background:transparent;")
        self.subtitle_label.setText(
            "Each dot = 1 byte of your file, placed at its real position inside the simulated glass"
        )
        self.subtitle_label.adjustSize()

        self.status_label = QLabel(self)
        self.status_label.setStyleSheet(
            "color:#4fe08a; font-size:18px; letter-spacing:2px; background:transparent;")
        self.status_label.hide()

        self.dims_label = QLabel(self)
        self.dims_label.setStyleSheet(
            "color:#cfe8ee; font-size:11px; background:rgba(10,14,16,0.55);"
            "border:1px solid #1c3a42; border-radius:3px; padding:6px 9px;")
        self.dims_label.setText(
            f"STORAGE VOLUME — the full simulated glass block\n"
            f"{data['grid_dims'][0]} × {data['grid_dims'][1]} × {data['grid_dims'][2]} voxel positions\n"
            f"{data['total_voxels']:,} total voxels · showing 6 of {data['grid_dims'][2]} depth layers"
        )
        self.dims_label.adjustSize()

        # one label per shown layer, with its REAL depth index + short caption
        self.layer_labels = []
        by_layer_z = sorted(set(p["z"] for p in data["points"]))
        max_layers = 6
        step = max(1, len(by_layer_z) // max_layers)
        shown_z = by_layer_z[::step][:max_layers]
        total_layers = data["grid_dims"][2]
        for z in shown_z:
            lbl = QLabel(self)
            lbl.setStyleSheet(
                "color:#9fd4dd; font-size:9px; background:rgba(10,14,16,0.4);"
                "border:1px solid #1c3a42; border-radius:2px; padding:3px 7px;")
            lbl.setText(f"DEPTH {z}/{total_layers} — one flat slice through the glass")
            lbl.adjustSize()
            self.layer_labels.append(lbl)

        # legend explaining voxel color meaning
        self.legend_label = QLabel(self)
        self.legend_label.setStyleSheet(
            "color:#cfe8ee; font-size:10px; background:rgba(10,14,16,0.55);"
            "border:1px solid #1c3a42; border-radius:3px; padding:6px 9px;")
        self.legend_label.setTextFormat(Qt.RichText)
        self.legend_label.setText(
            'VOXEL STATUS<br>'
            '<span style="color:#70d8e8;">●</span> intact — read back correctly<br>'
            '<span style="color:#e0665f;">●</span> missing — lost, recovered by ECC<br>'
            '<span style="color:#e0a94f;">●</span> corrupted — damaged, recovered by ECC'
        )
        self.legend_label.adjustSize()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(16)

    def initializeGL(self):
        self.ctx = moderngl.create_context()
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.renderer = HologramRenderer(self.ctx, self.data, SHADER_DIR)

    def resizeGL(self, w, h):
        self.ctx.viewport = (0, 0, w, h)

    def paintGL(self):
        # QOpenGLWidget renders into its own internal FBO (especially with
        # multisampling enabled) -- ModernGL's context needs to be told to
        # target that exact FBO explicitly, or everything draws into a
        # buffer Qt never actually displays.
        fbo = self.ctx.detect_framebuffer(self.defaultFramebufferObject())
        fbo.use()
        self.ctx.clear(0.02, 0.024, 0.031)

        t = time.time() - self.start_time

        if t >= 5.8 and not self.build_done:
            self.build_done = True
            self.camera.auto_rotate = True
            self._show_status()

        self.camera.tick_auto_rotate(1 / 60)

        proj = perspective(50, max(self.width(), 1) / max(self.height(), 1), 0.1, 3000)
        view = self.camera.view_matrix()

        def mvp_bytes(model):
            mvp = proj @ view @ model
            return mvp.T.astype('f4').tobytes()

        self.renderer.draw(mvp_bytes, t)
        self._position_labels()

    def _show_status(self):
        d = self.data
        if d.get("recovered_exact"):
            self.status_label.setText("✓  DATA RECOVERED — EXACT MATCH  (every byte read back correctly)")
            self.status_label.setStyleSheet(
                "color:#4fe08a; font-size:16px; letter-spacing:1px; background:transparent;")
        else:
            self.status_label.setText("✕  RECOVERY FAILED  (damage exceeded what the error correction could fix)")
            self.status_label.setStyleSheet(
                "color:#e0665f; font-size:16px; letter-spacing:1px; background:transparent;")
        self.status_label.adjustSize()
        self.status_label.show()

    def _position_labels(self):
        w, h = self.width(), self.height()
        self.status_label.move(w // 2 - self.status_label.width() // 2, h - 60)
        self.dims_label.move(24, 60)
        self.subtitle_label.move(24, 116)
        self.legend_label.move(w - self.legend_label.width() - 24, 24)

        n = len(self.layer_labels)
        for i, lbl in enumerate(self.layer_labels):
            y = 140 + i * ((h - 260) // max(1, n - 1)) if n > 1 else h // 2
            lbl.move(w - lbl.width() - 24, y)
            lbl.show()

    def mousePressEvent(self, e):
        self.last_mouse = e.position()
        self.camera.dragging = True

    def mouseReleaseEvent(self, e):
        self.last_mouse = None
        self.camera.dragging = False

    def mouseMoveEvent(self, e):
        if self.last_mouse is not None:
            dx = e.position().x() - self.last_mouse.x()
            dy = e.position().y() - self.last_mouse.y()
            self.camera.drag(dx, dy)
            self.last_mouse = e.position()

    def wheelEvent(self, e):
        self.camera.zoom(e.angleDelta().y() / 60.0)