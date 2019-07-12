from __future__ import annotations

import base64
import copy
import os
from typing import Any
import pickle

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import dill
from pathmagic import Dir

from .singleton import Singleton


class Lost(Singleton):
    def __len__(self) -> int:
        return 0

    def __iter__(self) -> Lost:
        return self

    def __next__(self) -> Any:
        return next(iter([]))

    def __getattr__(self, name: str) -> Lost:
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(name)
        else:
            return self


class LostObject:
    def __init__(self, obj: Any) -> None:
        self.repr = repr(obj)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.repr})"

    def __getattr__(self, name: str) -> Lost:
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(name)
        else:
            return Lost()


class Serializer:
    def __init__(self, file: os.PathLike) -> None:
        self.file = file

    def __repr__(self) -> str:
        return f"{type(self).__name__}({', '.join([f'{attr}={repr(val)}' for attr, val in self.__dict__.items() if not attr.startswith('_')])})"

    def serialize(self, obj: Any, **kwargs: Any) -> None:
        try:
            with open(self.file, "wb") as filehandle:
                dill.dump(obj, filehandle, **kwargs)
        except TypeError:
            cleaned_object = self.serializable_copy(obj)
            with open(self.file, "wb") as filehandle:
                dill.dump(cleaned_object, filehandle, **kwargs)

    def deserialize(self, **kwargs: Any) -> Any:
        try:
            with open(self.file, "rb") as filehandle:
                return dill.load(filehandle, **kwargs)
        except EOFError:
            return None

    @staticmethod
    def serializable_copy(item: Any) -> Any:
        seen = {id(item)}

        def recursively_strip_invalid(obj) -> Any:
            seen.add(id(obj))
            if Serializer._is_pickleable(obj):
                return obj
            else:
                if Serializer._is_endpoint(obj):
                    return LostObject(obj)
                else:
                    try:
                        shallow_copy = copy.copy(obj)
                    except TypeError:
                        return LostObject(obj)
                    else:
                        all_attributes_serializable = True
                        for key, val in vars(shallow_copy).items():
                            if not Serializer._is_pickleable(val):
                                try:
                                    dill.dumps(val)
                                except pickle.PicklingError:
                                    setattr(shallow_copy, key, LostObject(val))
                                except TypeError:
                                    setattr(shallow_copy, key, LostObject(val) if id(val) in seen else recursively_strip_invalid(val))
                                finally:
                                    all_attributes_serializable = False

                        return LostObject(obj) if all_attributes_serializable else shallow_copy

        try:
            initial_copy = copy.copy(item)
        except TypeError:
            return LostObject(item)
        else:
            return recursively_strip_invalid(initial_copy)

    @staticmethod
    def _is_pickleable(item: Any) -> bool:
        try:
            dill.dumps(item)
            return True
        except Exception:
            return False

    @staticmethod
    def _is_endpoint(item: Any) -> bool:
        return not hasattr(item, "__dict__") or type(item).__setattr__ is not object.__setattr__


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
