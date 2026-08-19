"""
Design-space explorer: runs the real pipeline across every combination of
geometry and ECC scheme (using the SAME file, noise settings, and ECC byte
count the user configured), then ranks the real results. No fabricated
scores -- every row is a genuine run_pipeline() call.
"""
from core.pipeline import run_pipeline
from core.noise import NoiseConfig

GEOMETRIES = ["grid", "hex"]
ECC_SCHEMES = ["reed_solomon", "bch"]


def run_design_space_search(raw_bytes: bytes, filename: str, noise_cfg: NoiseConfig,
                             ecc_bytes: int = 32, password: str | None = None):
    """Runs the real pipeline once per (geometry, ecc_scheme) combination.
    Returns a list of result dicts, each with an added 'config_label' field,
    sorted best-first by: success, then recovered_exact, then lower total
    time (faster), then higher density."""
    results = []
    for geometry in GEOMETRIES:
        for scheme in ECC_SCHEMES:
            r = run_pipeline(
                raw_bytes, filename, noise_cfg,
                ecc_bytes=ecc_bytes, password=password,
                geometry=geometry, ecc_scheme=scheme,
            )
            r["config_label"] = f"{geometry.capitalize()} + {'BCH' if scheme == 'bch' else 'Reed-Solomon'}"
            results.append(r)

    def sort_key(r):
        total_time = sum(r["timing_ms"].values())
        return (
            not r["decode_success"],       # False (0) sorts before True (1) -- success first
            not r["recovered_exact"],       # exact match first
            total_time,                     # then faster
            -r["density_bytes_per_voxel"],  # then higher density
        )

    results.sort(key=sort_key)
    return results