from __future__ import annotations

import base64
import contextlib
import copy
import os
from typing import Any, Iterator

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import dill
from pathmagic import Dir


class Serializer:
    def __init__(self, file: os.PathLike) -> None:
        self.file = file

    def serialize(self, obj: Any, **kwargs: Any) -> None:
        try:
            with open(self.file, "wb") as filehandle:
                dill.dump(obj, filehandle, **kwargs)
        except TypeError:
            cleaned_object = self.serializable_copy(obj)
            try:
                with open(self.file, "wb") as filehandle:
                    dill.dump(cleaned_object, filehandle, **kwargs)
            except TypeError:
                with self._temporarily_discard_unpicklable_class_attributes(cleaned_object):
                    with open(self.file, "wb") as filehandle:
                        dill.dump(cleaned_object, filehandle, **kwargs)

    def deserialize(self, **kwargs: Any) -> Any:
        try:
            with open(self.file, "rb") as filehandle:
                return dill.load(filehandle, **kwargs)
        except EOFError:
            return None

    @staticmethod
    def serializable_copy(obj: Any) -> Any:
        try:
            return dill.copy(obj)
        except TypeError:
            if not hasattr(obj, "__dict__"):
                return Serializer.LostObject(obj)
            else:
                try:
                    shallow_copy = copy.copy(obj)
                except TypeError:
                    return Serializer.LostObject(obj)
                else:
                    for key, val in vars(shallow_copy).items():
                        setattr(shallow_copy, key, Serializer.serializable_copy(val))
                    return shallow_copy

    @staticmethod
    @contextlib.contextmanager
    def _temporarily_discard_unpicklable_class_attributes(obj: Any) -> Iterator[None]:
        unpicklable_attrs = {}
        for key, val in obj.__class__.__dict__.items():
            try:
                dill.dumps(val)
            except TypeError:
                unpicklable_attrs[key] = val
                setattr(type(obj), key, Serializer.LostObject(val))

        yield

        for key, val in unpicklable_attrs.items():
            setattr(type(obj), key, val)

    class LostObject:
        def __init__(self, obj: Any) -> None:
            self.repr = repr(obj)

        def __repr__(self) -> str:
            return f"{type(self).__name__}({self.repr})"


class ByteSerializer:
    def __init__(self, contents: bytes = None) -> None:
        self.contents = contents

    def __call__(self, contents: bytes = None) -> ByteSerializer:
        self.contents = contents
        return self

    def serialize(self, obj: Any) -> None:
        self.contents = dill.dumps(obj)

    def deserialize(self) -> Any:
        return dill.loads(self.contents)


class Secrets:
    def __init__(self, file: os.PathLike) -> None:
        self.pw = Dir.from_home().newfile("secrets.txt")
        self.file_serializer, self.byte_serializer = Serializer(file), ByteSerializer()
        self.fernet = self._generate_fernet()

    def provide_new_password(self, key: str) -> None:
        self.pw.contents = key

    def encrypt(self, obj: Any) -> None:
        self.byte_serializer.serialize(obj)
        self.file_serializer.serialize(self.fernet.encrypt(self.byte_serializer.contents))

    def decrypt(self) -> Any:
        return self.byte_serializer(self.fernet.decrypt(self.file_serializer.deserialize())).deserialize()

    def _generate_fernet(self) -> Fernet:
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=b"", iterations=100000, backend=default_backend())
        key = base64.urlsafe_b64encode(kdf.derive(self.pw.contents.encode()))
        return Fernet(key)
