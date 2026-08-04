import base64
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from django.conf import settings


class CredentialCipher:
    def __init__(self, key: bytes):
        self._aes = AESGCM(key)

    def encrypt(self, plain: str) -> str:
        nonce = os.urandom(12)
        ct = self._aes.encrypt(nonce, plain.encode(), None)
        return base64.b64encode(nonce + ct).decode()   # 与 decrypt 的 b64decode 配对

    def decrypt(self, blob: str) -> str:
        raw = base64.b64decode(blob)
        return self._aes.decrypt(raw[:12], raw[12:], None).decode()

    @staticmethod
    def mask(plain: str) -> str:
        return f"{plain[:3]}****{plain[-3:]}" if len(plain) > 8 else "****"


cipher = CredentialCipher(settings.MODEL_CREDENTIAL_KEY)
