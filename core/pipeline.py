"""
Ties encoder -> [optional encryption] -> noise -> decoder -> gmem together
into one callable pipeline, returning a stats dict the GUI can display.
"""
import time
import hashlib
from core.encoder import encode_file, RS_ECC_BYTES
from core.noise import apply_noise, NoiseConfig
from core.decoder import decode_grid
from core.gmem import export_gmem
from core.crypto import encrypt_bytes, decrypt_bytes


def run_pipeline(raw_bytes: bytes, filename: str, noise_cfg: NoiseConfig,
                  ecc_bytes: int = RS_ECC_BYTES, password: str | None = None,
                  geometry: str = "grid", ecc_scheme: str = "reed_solomon") -> dict:
    t0 = time.time()

    salt = None
    payload_source = raw_bytes
    encrypted = False
    if password:
        payload_source, salt = encrypt_bytes(raw_bytes, password)
        encrypted = True

    grid = encode_file(payload_source, ecc_bytes=ecc_bytes, geometry=geometry, ecc_scheme=ecc_scheme)
    t_encode = time.time()

    noisy_grid = apply_noise(grid, noise_cfg)
    t_noise = time.time()

    result = decode_grid(noisy_grid, original_bytes=None, ecc_bytes=ecc_bytes)
    t_decode = time.time()

    recovered_final = None
    recovered_exact = False
    decrypt_error = None
    if result.success:
        if encrypted:
            try:
                recovered_final = decrypt_bytes(result.recovered_bytes, password, salt)
            except Exception as e:
                decrypt_error = str(e)
        else:
            recovered_final = result.recovered_bytes
        if recovered_final is not None:
            recovered_exact = (recovered_final == raw_bytes)

    original_sha256 = hashlib.sha256(raw_bytes).hexdigest()
    recovered_sha256 = hashlib.sha256(recovered_final).hexdigest() if recovered_final else None

    gmem_text = export_gmem(grid, filename, ecc_bytes)
    total_voxels = grid.width * grid.height * grid.layers
    density = grid.original_len / total_voxels if total_voxels else 0.0

    return {
        "filename": filename,
        "original_len": grid.original_len,
        "payload_len": grid.payload_len,
        "grid_dims": (grid.width, grid.height, grid.layers),
        "total_voxels": total_voxels,
        "density_bytes_per_voxel": density,
        "geometry": grid.geometry,
        "ecc_scheme": grid.ecc_scheme,
        "decode_success": result.success,
        "recovered_exact": recovered_exact,
        "ecc_errors_corrected": result.ecc_errors_detected,
        "error_message": result.error_message or decrypt_error,
        "encrypted": encrypted,
        "original_sha256": original_sha256,
        "recovered_sha256": recovered_sha256,
        "sha256_match": (original_sha256 == recovered_sha256) if recovered_sha256 else False,
        "timing_ms": {
            "encode": round((t_encode - t0) * 1000, 2),
            "noise": round((t_noise - t_encode) * 1000, 2),
            "decode": round((t_decode - t_noise) * 1000, 2),
        },
        "gmem_text": gmem_text,
        "clean_grid": grid,
        "noisy_grid": noisy_grid,
    }