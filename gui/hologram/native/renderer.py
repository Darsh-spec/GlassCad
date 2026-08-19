"""
Builds GPU buffers from the real simulation result JSON (grid_dims + points
with real status: 0=unchanged, 1=missing, 2=corrupted). No random geometry --
every point/line comes directly from the backend's actual voxel data.
"""
import numpy as np
import moderngl

COLOR_HEALTHY = (0.44, 0.85, 0.91)
COLOR_MISSING = (0.88, 0.40, 0.37)
COLOR_CORRUPT = (0.88, 0.66, 0.31)


class HologramRenderer:
    def __init__(self, ctx: moderngl.Context, data: dict, shader_dir: str):
        self.ctx = ctx
        self.data = data
        self.points_prog = self._load_prog(shader_dir, "points")
        self.lines_prog = self._load_prog(shader_dir, "lines")

        W, H, L = data["grid_dims"]
        self.scale = 70.0 / max(W, H, L)
        self.spacing = 16.0

        by_layer = {}
        for p in data["points"]:
            by_layer.setdefault(p["z"], []).append(p)
        layer_keys = sorted(by_layer.keys())

        max_layers = 6
        step = max(1, len(layer_keys) // max_layers)
        shown = layer_keys[::step][:max_layers]

        self.layers = []
        for i, z in enumerate(shown):
            pts = by_layer[z]
            target_y = (i - (len(shown) - 1) / 2) * self.spacing
            self.layers.append(self._build_layer(pts, W, H, target_y, delay=i * 0.45))

        self.boundary = self._build_boundary_box(W, H)

        self.total_voxels = data["total_voxels"]
        self.grid_dims = (W, H, L)
        self.num_layers_shown = len(shown)

    def _load_prog(self, shader_dir, name):
        with open(f"{shader_dir}/{name}.vert") as f:
            vert = f.read()
        with open(f"{shader_dir}/{name}.frag") as f:
            frag = f.read()
        return self.ctx.program(vertex_shader=vert, fragment_shader=frag)

    def _build_layer(self, pts, W, H, target_y, delay):
        cx, cy = W / 2, H / 2
        by_xy = {(p["x"], p["y"]): p for p in pts}

        pos, col = [], []
        for p in pts:
            x0, y0 = (p["x"] - cx) * self.scale, (p["y"] - cy) * self.scale
            pos.extend([x0, 0.0, y0])
            c = (COLOR_MISSING if p["status"] == 1 else
                 COLOR_CORRUPT if p["status"] == 2 else COLOR_HEALTHY)
            col.extend(c)

        line_pos = []
        for p in pts:
            x0, y0 = (p["x"] - cx) * self.scale, (p["y"] - cy) * self.scale
            right = by_xy.get((p["x"] + 1, p["y"]))
            down = by_xy.get((p["x"], p["y"] + 1))
            if right:
                line_pos.extend([x0, 0.0, y0, (right["x"]-cx)*self.scale, 0.0, (right["y"]-cy)*self.scale])
            if down:
                line_pos.extend([x0, 0.0, y0, (down["x"]-cx)*self.scale, 0.0, (down["y"]-cy)*self.scale])

        pos_arr = np.array(pos, dtype='f4')
        col_arr = np.array(col, dtype='f4')
        line_arr = np.array(line_pos, dtype='f4') if line_pos else np.zeros(0, dtype='f4')

        pos_vbo = self.ctx.buffer(pos_arr.tobytes())
        col_vbo = self.ctx.buffer(col_arr.tobytes())
        point_vao = self.ctx.vertex_array(
            self.points_prog,
            [(pos_vbo, '3f', 'in_position'), (col_vbo, '3f', 'in_color')]
        )
        n_line_verts = len(line_arr) // 3
        if n_line_verts:
            line_vbo = self.ctx.buffer(line_arr.tobytes())
            line_vao = self.ctx.vertex_array(self.lines_prog, [(line_vbo, '3f', 'in_position')])
        else:
            line_vao = None

        return {
            "point_vao": point_vao, "line_vao": line_vao,
            "n_points": len(pos_arr) // 3, "target_y": target_y, "delay": delay,
        }

    def _build_boundary_box(self, W, H):
        """One translucent box enclosing the whole stack -- reads as 'contained in glass'."""
        half_x = W * self.scale / 2 * 1.1
        half_z = H * self.scale / 2 * 1.1
        half_y = self.spacing * (len(self.layers) - 1) / 2 + self.spacing * 0.8

        corners = [
            (-half_x, -half_y, -half_z), (half_x, -half_y, -half_z),
            (half_x, -half_y, half_z), (-half_x, -half_y, half_z),
            (-half_x, half_y, -half_z), (half_x, half_y, -half_z),
            (half_x, half_y, half_z), (-half_x, half_y, half_z),
        ]
        edges = [
            (0,1),(1,2),(2,3),(3,0),
            (4,5),(5,6),(6,7),(7,4),
            (0,4),(1,5),(2,6),(3,7),
        ]
        line_pos = []
        for a, b in edges:
            line_pos.extend(corners[a])
            line_pos.extend(corners[b])

        arr = np.array(line_pos, dtype='f4')
        vbo = self.ctx.buffer(arr.tobytes())
        vao = self.ctx.vertex_array(self.lines_prog, [(vbo, '3f', 'in_position')])
        return {"vao": vao, "n_verts": len(arr) // 3}

    def draw(self, mvp_bytes_fn, build_t):
        """build_t: seconds since hologram opened, drives the fade/rise animation."""
        self.ctx.enable(moderngl.PROGRAM_POINT_SIZE)
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE

        layer_start, layer_dur = 1.8, 2.6
        for i, layer in enumerate(self.layers):
            delay = layer_start + i * (layer_dur / max(1, len(self.layers)))
            p = max(0.0, min(1.0, (build_t - delay) / 0.9))
            eased = 1 - (1 - p) ** 3
            y_offset = layer["target_y"] - 40 * (1 - eased)
            alpha = eased * 0.95

            model = np.identity(4)
            model[1, 3] = y_offset
            mvp = mvp_bytes_fn(model)

            if alpha > 0.01:
                self.points_prog['mvp'].write(mvp)
                self.points_prog['point_size'].value = 7.0
                self.points_prog['alpha'].value = alpha
                layer["point_vao"].render(moderngl.POINTS, vertices=layer["n_points"])

                if layer["line_vao"] is not None and build_t > 4.6:
                    line_alpha = min(1.0, (build_t - 4.6) / 1.0) * 0.5
                    self.lines_prog['mvp'].write(mvp)
                    self.lines_prog['line_color'].value = (0.18, 0.39, 0.44)
                    self.lines_prog['alpha'].value = line_alpha
                    layer["line_vao"].render(moderngl.LINES)

        # draw the glass boundary once, fading in with the last layer
        boundary_alpha = min(1.0, max(0.0, (build_t - 5.0) / 1.0)) * 0.35
        if boundary_alpha > 0.01:
            model = np.identity(4)
            self.lines_prog['mvp'].write(mvp_bytes_fn(model))
            self.lines_prog['line_color'].value = (0.3, 0.65, 0.72)
            self.lines_prog['alpha'].value = boundary_alpha
            self.boundary["vao"].render(moderngl.LINES, vertices=self.boundary["n_verts"])