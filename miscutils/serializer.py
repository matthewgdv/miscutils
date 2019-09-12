from __future__ import annotations

import base64
from collections.abc import MutableSequence, Sequence, MutableMapping, Mapping, MutableSet, Iterable
import copy
import os
from typing import Any

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import dill

from pathmagic import Dir, PathLike

from .singleton import Singleton


class Lost(Singleton):
    def __len__(self) -> int:
        return 0

    def __iter__(self) -> Lost:
        return self

    def __next__(self) -> Any:
        raise StopIteration

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

    def __len__(self) -> int:
        return 0

    def __iter__(self) -> Lost:
        return self

    def __next__(self) -> Any:
        raise StopIteration

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
        self.file.path.write_bytes(self.to_bytes(obj=obj, **kwargs))

    def deserialize(self, **kwargs: Any) -> Any:
        try:
            return self.from_bytes(text=self.file.path.read_bytes(), **kwargs)
        except EOFError:
            return None

    def to_bytes(self, obj: Any, **kwargs: Any) -> None:
        try:
            return dill.dumps(obj, **kwargs)
        except Exception:
            cleaned_object = UnpickleableItemHelper(obj).serializable_copy()
            return dill.dumps(cleaned_object, **kwargs)

    def from_bytes(self, text: bytes, **kwargs: Any) -> Any:
        return dill.loads(text, **kwargs)


class UnpickleableItemHelper:
    def __init__(self, item: Any) -> None:
        self.item, self.copy, self.seen = item, None, {}

    def serializable_copy(self) -> Any:
        self.seen.clear()

        try:
            self.copy = copy.copy(self.item)
            self.seen[id(self.item)] = self.copy
            return self.recursively_strip_invalid(self.copy)
        except Exception:
            return LostObject(self.item)

    def recursively_strip_invalid(self, obj) -> Any:
        if obj is self.item:
            return self.copy

        if self.is_endpoint(obj):
            if id(obj) in self.seen:
                return self.seen[id(obj)]
            else:
                ret = obj if self.is_pickleable(obj) else LostObject(obj)
                self.seen[id(obj)] = ret
                return ret
        else:
            return self.handle_non_endpoint(obj)

    def handle_non_endpoint(self, obj):
        try:
            shallow_copy = obj if obj is self.copy else copy.copy(obj)
        except Exception:
            ret = LostObject(obj)
            self.seen[id(obj)] = ret
            return ret
        else:
            self.seen[id(obj)] = shallow_copy
            return self.handle_shallow_copy(shallow_copy)

    def handle_shallow_copy(self, obj):
        return self.handle_object(obj) if hasattr(obj, "__dict__") else self.handle_iterable(obj)

    def handle_object(self, obj):
        for key, val in vars(obj).items():
            setattr(obj, key, self.recursively_strip_invalid(val))

        return obj

    def handle_iterable(self, obj):
        if isinstance(obj, MutableMapping):
            new_dict = {self.recursively_strip_invalid(key): self.recursively_strip_invalid(val) for key, val in obj.items()}
            obj.clear()
            obj.update(new_dict)
        elif isinstance(obj, Mapping):
            new = type(obj)({self.recursively_strip_invalid(key): self.recursively_strip_invalid(val) for key, val in obj.items()})
            for key, val in self.seen.items():
                if val is obj:
                    self.seen[key] = new
                    break

            obj = new
        elif isinstance(obj, MutableSet):
            for val in obj:
                obj.remove(val)
                obj.add(self.recursively_strip_invalid(val))
        elif isinstance(obj, MutableSequence):
            for index, val in enumerate(obj):
                obj[index] = self.recursively_strip_invalid(val)
        elif isinstance(obj, Sequence):
            new = type(obj)([self.recursively_strip_invalid(val) for val in obj])
            for key, val in self.seen.items():
                if val is obj:
                    self.seen[key] = new
                    break

            obj = new

        return obj

    @staticmethod
    def is_pickleable(item: Any) -> bool:
        try:
            dill.dumps(item)
            return True
        except Exception:
            return False

    @staticmethod
    def is_endpoint(item: Any) -> bool:
        if hasattr(item, "__dict__"):
            return True if type(item).__setattr__ is not object.__setattr__ else False

        return False if isinstance(item, Iterable) and not isinstance(item, (str, bytes)) else True


class Secrets:
    def __init__(self, file: os.PathLike, key_path: PathLike = None, salt: bytes = b"") -> None:
        self.pw = Dir.from_home().newfile("secrets", "txt") if key_path is None else key_path
        self.serializer, self.salt = Serializer(file), salt
        self.fernet = self._generate_fernet()

    def provide_new_password(self, key: str) -> None:
        self.pw.contents = key

    def encrypt(self, obj: Any) -> None:
        self.serializer.file.path.write_bytes(self.fernet.encrypt(self.serializer.to_bytes(obj)))

    def decrypt(self) -> Any:
        return self.serializer.from_bytes(self.fernet.decrypt(self.serializer.file.path.read_bytes()))

    def _generate_fernet(self) -> Fernet:
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=self.salt, iterations=100000, backend=default_backend())
        key = base64.urlsafe_b64encode(kdf.derive(self.pw.contents.encode()))
        return Fernet(key)
