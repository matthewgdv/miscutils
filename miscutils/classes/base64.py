from __future__ import annotations

import base64


class Base64:
    def __init__(self, raw_bytes: bytes) -> None:
        self.bytes = raw_bytes

    def __bytes__(self) -> bytes:
        return self.bytes

    def to_utf8(self) -> str:
        return self.bytes.decode("utf-8")

    def to_b64(self) -> str:
        return base64.urlsafe_b64encode(self.bytes).decode("utf-8")

    @classmethod
    def from_utf8(cls, utf8: str) -> Base64:
        return cls(raw_bytes=utf8.encode("utf-8"))

    @classmethod
    def from_b64(cls, b64: str) -> Base64:
        return cls(raw_bytes=base64.urlsafe_b64decode(b64))
