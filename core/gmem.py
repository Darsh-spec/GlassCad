import json
import base64
from core.encoder import VoxelGrid

GMEM_VERSION = "0.1"

def export_gmem(grid: VoxelGrid, source_filename: str, ecc_bytes: int) -> str:
    doc = {
        "gmem_version": GMEM_VERSION,
        "source_filename": source_filename,
        "geometry": {"type": grid.geometry, "width": grid.width,
                      "height": grid.height, "layers": grid.layers},
        "encoding": {"voxel_bits": 8, "compression": "zlib",
                      "ecc_scheme": "reed_solomon", "ecc_parity_bytes": ecc_bytes},
        "payload": {"payload_len": grid.payload_len,
                     "original_len": grid.original_len,
                     "data_b64": base64.b64encode(bytes(grid.data)).decode("ascii")},
    }
    return json.dumps(doc, indent=2)

def import_gmem(gmem_text: str):
    doc = json.loads(gmem_text)
    geo = doc["geometry"]
    payload = doc["payload"]
    data = bytearray(base64.b64decode(payload["data_b64"]))
    grid = VoxelGrid(geo["width"], geo["height"], geo["layers"], data,
                      payload["payload_len"], payload["original_len"],
                      geometry=geo.get("type", "grid"))
    return grid, doc