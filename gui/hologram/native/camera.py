"""Orbit camera + standard OpenGL matrix math, no external math dependency."""
import numpy as np


def normalize(v):
    n = np.linalg.norm(v)
    return v / n if n > 1e-8 else v


def look_at(eye, target, up):
    f = normalize(target - eye)
    s = normalize(np.cross(f, up))
    u = np.cross(s, f)
    M = np.identity(4, dtype='f8')
    M[0, :3] = s
    M[1, :3] = u
    M[2, :3] = -f
    M[0, 3] = -np.dot(s, eye)
    M[1, 3] = -np.dot(u, eye)
    M[2, 3] = np.dot(f, eye)
    return M


def perspective(fovy_deg, aspect, near, far):
    f = 1.0 / np.tan(np.radians(fovy_deg) / 2)
    M = np.zeros((4, 4), dtype='f8')
    M[0, 0] = f / aspect
    M[1, 1] = f
    M[2, 2] = (far + near) / (near - far)
    M[2, 3] = (2 * far * near) / (near - far)
    M[3, 2] = -1.0
    return M


class OrbitCamera:
    def __init__(self, target=(0, 0, 0), distance=170.0):
        self.target = np.array(target, dtype='f8')
        self.distance = distance
        self.yaw = 0.6
        self.pitch = 0.35
        self.min_dist = 60.0
        self.max_dist = 260.0
        self.auto_rotate = False
        self.dragging = False

    def eye(self):
        cy, sy = np.cos(self.yaw), np.sin(self.yaw)
        cp, sp = np.cos(self.pitch), np.sin(self.pitch)
        offset = np.array([sy * cp, sp, cy * cp]) * self.distance
        return self.target + offset

    def drag(self, dx, dy):
        self.yaw -= dx * 0.006
        self.pitch = np.clip(self.pitch + dy * 0.006, -1.4, 1.4)

    def zoom(self, delta):
        self.distance = np.clip(self.distance - delta * 8.0, self.min_dist, self.max_dist)

    def tick_auto_rotate(self, dt):
        if self.auto_rotate and not self.dragging:
            self.yaw += dt * 0.18

    def view_matrix(self):
        return look_at(self.eye(), self.target, np.array([0.0, 1.0, 0.0]))