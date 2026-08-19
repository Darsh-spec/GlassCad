"""
Voxel layout geometries. Both produce the same total voxel count for a given
(width, height) -- the difference is spatial arrangement within each layer,
not storage capacity. This is a real structural variant (relevant to future
physical writing/reading constraints like beam spacing), not a claimed
density improvement.
"""
import math


def grid_positions(width: int, height: int):
    """Standard square grid: (x, y) for x in [0,width), y in [0,height)."""
    return [(x, y) for y in range(height) for x in range(width)]


def hex_positions(width: int, height: int):
    """Hexagonal offset packing: odd rows shifted by 0.5 in X, like a
    honeycomb. Still returns exactly width*height positions -- same count,
    different spatial arrangement."""
    positions = []
    for y in range(height):
        offset = 0.5 if (y % 2 == 1) else 0.0
        for x in range(width):
            positions.append((x + offset, y))
    return positions


GEOMETRIES = {
    "grid": grid_positions,
    "hex": hex_positions,
}


def get_positions(width: int, height: int, geometry: str = "grid"):
    fn = GEOMETRIES.get(geometry, grid_positions)
    return fn(width, height)