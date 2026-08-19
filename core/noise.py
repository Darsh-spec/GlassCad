import random
from dataclasses import dataclass
from core.encoder import VoxelGrid

@dataclass
class NoiseConfig:
    missing_voxel_rate: float = 0.0
    read_noise_std: float = 0.0
    bit_corruption_rate: float = 0.0
    seed: int = None

def apply_noise(grid: VoxelGrid, cfg: NoiseConfig) -> VoxelGrid:
    rng = random.Random(cfg.seed)
    noisy = bytearray(grid.data)

    for i in range(len(noisy)):
        if cfg.missing_voxel_rate and rng.random() < cfg.missing_voxel_rate:
            noisy[i] = 0
            continue
        if cfg.bit_corruption_rate and rng.random() < cfg.bit_corruption_rate:
            noisy[i] = rng.randint(0, 255)
            continue
        if cfg.read_noise_std:
            jitter = int(rng.gauss(0, cfg.read_noise_std))
            noisy[i] = max(0, min(255, noisy[i] + jitter))

    return VoxelGrid(grid.width, grid.height, grid.layers, noisy,
                      grid.payload_len, grid.original_len,
                      grid.geometry, grid.ecc_scheme)