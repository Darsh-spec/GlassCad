"""
Builds per-voxel status arrays so the GUI can show a 3D view of what
survived noise, what got corrupted, and what ECC still recovered.
"""
import numpy as np

def voxel_status(clean_grid, noisy_grid):
    """
    Returns (xs, ys, zs, status) arrays for plotting.
    status: 0 = unchanged, 1 = missing (zeroed), 2 = corrupted (changed, nonzero)
    """
    w, h, l = clean_grid.width, clean_grid.height, clean_grid.layers
    clean = np.frombuffer(bytes(clean_grid.data), dtype=np.uint8).reshape(l, h, w)
    noisy = np.frombuffer(bytes(noisy_grid.data), dtype=np.uint8).reshape(l, h, w)

    xs, ys, zs, status = [], [], [], []
    for z in range(l):
        for y in range(h):
            for x in range(w):
                c, n = clean[z, y, x], noisy[z, y, x]
                if c == n:
                    s = 0
                elif n == 0 and c != 0:
                    s = 1  # missing
                else:
                    s = 2  # corrupted
                xs.append(x); ys.append(y); zs.append(z); status.append(s)
    return np.array(xs), np.array(ys), np.array(zs), np.array(status)