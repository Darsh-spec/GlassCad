"""
Optional AES encryption layer, applied BEFORE ECC/voxel mapping.
Uses Fernet (AES-128-CBC + HMAC) with a password-derived key via PBKDF2.
The salt is NOT secret and travels with the .gmem file; the password never does.
"""
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

PBKDF2_ITERATIONS = 390_000


def _derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt,
                      iterations=PBKDF2_ITERATIONS)
    return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))


def encrypt_bytes(data: bytes, password: str) -> tuple[bytes, bytes]:
    """Returns (ciphertext, salt). Salt is safe to store/share."""
    salt = os.urandom(16)
    key = _derive_key(password, salt)
    ciphertext = Fernet(key).encrypt(data)
    return ciphertext, salt


def decrypt_bytes(ciphertext: bytes, password: str, salt: bytes) -> bytes:
    key = _derive_key(password, salt)
    return Fernet(key).decrypt(ciphertext)