import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.pipeline import run_pipeline
from core.noise import NoiseConfig

def run_case(label, raw_bytes, filename, noise_cfg):
    r = run_pipeline(raw_bytes, filename, noise_cfg)
    print(f"\n=== {label} ===")
    print(f"  file: {r['filename']} ({r['original_len']} bytes)")
    print(f"  grid: {r['grid_dims']} ({r['total_voxels']} voxels)")
    print(f"  decode_success: {r['decode_success']}")
    print(f"  recovered_exact: {r['recovered_exact']}")
    print(f"  ecc_errors_corrected: {r['ecc_errors_corrected']}")
    print(f"  timing_ms: {r['timing_ms']}")
    if r["error_message"]:
        print(f"  error: {r['error_message']}")

if __name__ == "__main__":
    sample = b"GlassCAD v0.1 test payload. " * 200 + b"Round trip check."

    run_case("No noise", sample, "sample.txt", NoiseConfig())
    run_case("Light noise (2% missing)", sample, "sample.txt",
              NoiseConfig(missing_voxel_rate=0.02, seed=42))
    run_case("Moderate noise (5% missing + 2% corrupted)", sample, "sample.txt",
              NoiseConfig(missing_voxel_rate=0.05, bit_corruption_rate=0.02, seed=42))
    run_case("Heavy noise (15% missing) — expect failure", sample, "sample.txt",
              NoiseConfig(missing_voxel_rate=0.15, seed=42))