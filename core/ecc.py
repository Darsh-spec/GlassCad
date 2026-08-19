"""
Common ECC interface so encoder/decoder/pipeline can swap Reed-Solomon and
BCH without caring about the underlying library differences. RS corrects
byte-level errors; BCH corrects bit-level errors -- offering both lets you
genuinely compare which suits a given noise pattern better.
"""
from reedsolo import RSCodec, ReedSolomonError
import bchlib

# BCH parameters: m=12 -> block size 2^12-1 = 4095 bits (~511 bytes), t=16
# means it can correct up to 16 bit-errors per block. These are reasonable
# general-purpose defaults; real tuning would be noise-pattern-specific.
BCH_M = 12
BCH_T = 16


class ECCScheme:
    """Abstract shape both schemes implement: encode(bytes)->bytes,
    decode(bytes)->(bytes, errors_corrected_or_None_on_failure)."""
    name = "abstract"

    def encode(self, data: bytes) -> bytes:
        raise NotImplementedError

    def decode(self, data: bytes):
        raise NotImplementedError


class ReedSolomonScheme(ECCScheme):
    name = "reed_solomon"

    def __init__(self, ecc_bytes: int):
        self.ecc_bytes = ecc_bytes
        self.rsc = RSCodec(ecc_bytes)

    def encode(self, data: bytes) -> bytes:
        return bytes(self.rsc.encode(data))

    def decode(self, data: bytes):
        try:
            decoded_msg, decoded_msgecc, errata_pos = self.rsc.decode(data)
            return bytes(decoded_msg), (len(errata_pos) if errata_pos else 0)
        except Exception as e:
            return None, None  # signals failure; caller checks for None


class BCHScheme(ECCScheme):
    name = "bch"

    def __init__(self, m: int = BCH_M, t: int = BCH_T):
        self.bch = bchlib.BCH(t, m=m)
        # bytes of actual data payload this BCH config can protect per block
        self.data_bytes_per_block = self.bch.n // 8 - self.bch.ecc_bytes

    def encode(self, data: bytes) -> bytes:
        out = bytearray()
        block_size = self.data_bytes_per_block
        for i in range(0, len(data), block_size):
            chunk = data[i:i + block_size]
            padded = chunk.ljust(block_size, b"\x00")
            ecc = self.bch.encode(padded)
            out += padded + ecc
        return bytes(out)

    def decode(self, data: bytes):
        block_size = self.data_bytes_per_block
        full_block = block_size + self.bch.ecc_bytes
        recovered = bytearray()
        total_errors = 0
        for i in range(0, len(data), full_block):
            block = bytearray(data[i:i + full_block])
            if len(block) < full_block:
                break
            payload = block[:block_size]
            ecc = block[block_size:]
            n_errors = self.bch.decode(payload, ecc)
            if n_errors < 0:
                return None, None  # uncorrectable block -> whole decode fails
            self.bch.correct(payload, ecc)
            recovered += payload
            total_errors += max(0, n_errors)
        return bytes(recovered), total_errors


def get_scheme(name: str, ecc_bytes: int = 32):
    if name == "bch":
        return BCHScheme()
    return ReedSolomonScheme(ecc_bytes)