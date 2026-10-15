"""Security manager: password hashing, Fernet encryption, database encryption."""

import hashlib
import os
import tempfile
import bcrypt
from base64 import urlsafe_b64encode
from cryptography.fernet import Fernet, InvalidToken
from utils.constants import BCRYPT_ROUNDS, PBKDF2_ITERATIONS, SALT_LENGTH


class SecurityManager:
    """Handles all security operations: passwords, encryption, DB file protection."""

    def __init__(self):
        self._fernet: Fernet | None = None
        self._temp_db_path: str | None = None
        self._salt: bytes | None = None

    def hash_password(self, password: str) -> str:
        return bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt(rounds=BCRYPT_ROUNDS),
        ).decode("utf-8")

    def verify_password(self, password: str, hashed: str) -> bool:
        try:
            return bcrypt.checkpw(
                password.encode("utf-8"),
                hashed.encode("utf-8"),
            )
        except Exception:
            return False

    def generate_salt(self) -> bytes:
        return os.urandom(SALT_LENGTH)

    def derive_fernet_key(self, password: str, salt: bytes) -> Fernet:
        key = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            PBKDF2_ITERATIONS,
        )
        fernet_key = urlsafe_b64encode(key[:32])
        self._fernet = Fernet(fernet_key)
        self._salt = salt
        return self._fernet

    def encrypt_string(self, plaintext: str) -> str:
        if not self._fernet:
            raise RuntimeError("Fernet key not derived. Call derive_fernet_key first.")
        return self._fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")

    def decrypt_string(self, encrypted: str) -> str:
        if not self._fernet:
            raise RuntimeError("Fernet key not derived. Call derive_fernet_key first.")
        try:
            return self._fernet.decrypt(encrypted.encode("utf-8")).decode("utf-8")
        except InvalidToken:
            raise ValueError("Decryption failed. Wrong password or corrupted data.")

    def encrypt_database(self, db_path: str, encrypted_path: str):
        if not self._fernet:
            raise RuntimeError("Fernet key not derived.")
        with open(db_path, "rb") as f:
            data = f.read()
        encrypted = self._fernet.encrypt(data)
        with open(encrypted_path, "wb") as f:
            f.write(encrypted)

    def decrypt_database(self, encrypted_path: str) -> str:
        if not self._fernet:
            raise RuntimeError("Fernet key not derived.")
        with open(encrypted_path, "rb") as f:
            encrypted_data = f.read()
        try:
            decrypted = self._fernet.decrypt(encrypted_data)
        except InvalidToken:
            raise ValueError("Database decryption failed. Wrong password.")

        temp_fd, temp_path = tempfile.mkstemp(suffix=".db", prefix="diday_")
        with os.fdopen(temp_fd, "wb") as f:
            f.write(decrypted)

        self._temp_db_path = temp_path
        return temp_path

    def get_temp_db_path(self) -> str | None:
        return self._temp_db_path

    def cleanup(self):
        if self._temp_db_path and os.path.exists(self._temp_db_path):
            try:
                size = os.path.getsize(self._temp_db_path)
                with open(self._temp_db_path, "wb") as f:
                    f.write(os.urandom(size))
                os.remove(self._temp_db_path)
            except OSError:
                pass
            self._temp_db_path = None
