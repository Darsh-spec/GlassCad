"""
GlassCAD core decoder + verifier.
Reverses encoder.py: voxel grid -> ECC-corrected bytes -> decompressed -> original file.
Works with either Reed-Solomon or BCH via the core.ecc abstraction.
"""
import zlib
from dataclasses import dataclass
from core.encoder import VoxelGrid, RS_ECC_BYTES
from core.ecc import get_scheme


@dataclass
class DecodeResult:
    success: bool
    recovered_bytes: bytes | None
    bytes_match_original: bool
    error_message: str | None
    ecc_errors_detected: int | None


def decode_grid(grid: VoxelGrid, original_bytes: bytes | None = None,
                 ecc_bytes: int = RS_ECC_BYTES) -> DecodeResult:
    """Attempt to recover the original file from a (possibly noisy) VoxelGrid.
    Uses whichever ECC scheme the grid itself was encoded with (grid.ecc_scheme)."""
    protected = bytes(grid.data[: grid.payload_len])

    scheme = get_scheme(getattr(grid, "ecc_scheme", "reed_solomon"), ecc_bytes)

    decoded_msg, errors = scheme.decode(protected)
    if decoded_msg is None:
        return DecodeResult(
            success=False,
            recovered_bytes=None,
            bytes_match_original=False,
            error_message=f"ECC decode failed (too much corruption for {scheme.name})",
            ecc_errors_detected=None,
        )

    try:
        recovered = zlib.decompress(bytes(decoded_msg))
    except zlib.error as e:
        return DecodeResult(
            success=False,
            recovered_bytes=None,
            bytes_match_original=False,
            error_message=f"Decompression failed after ECC correction: {e}",
            ecc_errors_detected=errors,
        )

    matches = (recovered == original_bytes) if original_bytes is not None else None
    return DecodeResult(
        success=True,
        recovered_bytes=recovered,
        bytes_match_original=bool(matches),
        error_message=None,
        ecc_errors_detected=errors,
    )