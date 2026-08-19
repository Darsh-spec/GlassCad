import zlib
import math
from dataclasses import dataclass
from core.ecc import get_scheme

RS_ECC_BYTES = 32  # parity bytes per 255-byte block (Reed-Solomon only); higher = more resilient

@dataclass
class VoxelGrid:
    width: int
    height: int
    layers: int
    data: bytearray
    payload_len: int
    original_len: int
    geometry: str = "grid"     # "grid" or "hex" -- see core/geometry.py
    ecc_scheme: str = "reed_solomon"  # "reed_solomon" or "bch" -- see core/ecc.py

def _pick_grid_dims(n_bytes: int):
    side = max(1, math.ceil(n_bytes ** (1 / 3)))
    width = height = side
    layers = math.ceil(n_bytes / (width * height))
    return width, height, layers

def encode_file(raw_bytes: bytes, ecc_bytes: int = RS_ECC_BYTES,
                 geometry: str = "grid", ecc_scheme: str = "reed_solomon") -> VoxelGrid:
    """Compress, ECC-protect, and lay out raw_bytes into a 3D voxel grid.
    `geometry` selects the 2D per-layer spatial arrangement (grid or hex).
    `ecc_scheme` selects reed_solomon (byte-level correction) or bch
    (bit-level correction) -- see core/ecc.py for the tradeoff."""
    compressed = zlib.compress(raw_bytes, level=9)

    scheme = get_scheme(ecc_scheme, ecc_bytes)
    protected = scheme.encode(compressed)

    width, height, layers = _pick_grid_dims(len(protected))
    total_voxels = width * height * layers

    data = bytearray(total_voxels)
    data[: len(protected)] = protected

    return VoxelGrid(width, height, layers, data, len(protected), len(raw_bytes),
                      geometry, ecc_scheme)