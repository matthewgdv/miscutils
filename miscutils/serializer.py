from __future__ import annotations

import base64
from collections.abc import Mapping, MutableSequence, Sequence
import copy
import os
from typing import Any
import pickle

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


class FutureObject:
    def __init__(self, id: int) -> None:
        self.id = id


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
        except TypeError:
            cleaned_object = UnpickleableItemHelper(obj).serializable_copy()
            return dill.dumps(cleaned_object, **kwargs)

    def from_bytes(self, text: bytes, **kwargs: Any) -> Any:
        return dill.loads(text, **kwargs)


class UnpickleableItemHelper:
    def __init__(self, item: Any) -> None:
        self.item, self.seen = item, {}

    def serializable_copy(self) -> Any:
        return self.recursively_strip_invalid(self.item)

    def recursively_strip_invalid(self, obj) -> Any:
        if self.is_pickleable(obj):
            self.seen[id(obj)] = obj
            return obj
        else:
            return self.handle_unpickleable(obj)

    def handle_unpickleable(self, obj):
        if self.is_endpoint(obj):
            ret = LostObject(obj)
            self.seen[id(obj)] = ret
            return ret
        else:
            return self.handle_non_endpoint(obj)

    def handle_non_endpoint(self, obj):
        try:
            shallow_copy = copy.copy(obj)
        except TypeError:
            ret = LostObject(obj)
            self.seen[id(obj)] = ret
            return ret
        else:
            self.seen[id(obj)] = shallow_copy
            return self.handle_shallow_copy(shallow_copy)

    def handle_shallow_copy(self, obj):
        if not hasattr(obj, "__dict__"):
            return self.handle_iterable(obj)
        else:
            return self.handle_object(obj)

    def handle_iterable(self, obj):
        if isinstance(obj, Mapping):
            obj.update({self.handle_item(key): self.handle_item(val) for key, val in obj.items()})
        elif isinstance(obj, MutableSequence):
            for index, val in enumerate(obj):
                obj[index] = self.handle_item(val)
        elif isinstance(obj, Sequence):
            new = type(obj)([self.handle_item(val) for val in obj])
            for key, val in self.seen.items():
                if val is obj:
                    self.seen[key] = new

            obj = new

        return obj

    def handle_object(self, obj):
        prior_items = set([id(item) for item in vars(obj).values()])
        for key, val in vars(obj).items():
            setattr(obj, key, self.handle_item(val))

        return LostObject(obj) if prior_items == set(id(item) for item in vars(obj).values()) else obj

    def handle_item(self, obj):
        try:
            dill.dumps(obj)
        except pickle.PicklingError:
            return LostObject(obj)
        except TypeError:
            return self.seen[id(obj)] if id(obj) in self.seen else self.recursively_strip_invalid(obj)
        else:
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
        return (not hasattr(item, "__dict__") or type(item).__setattr__ is not object.__setattr__) and (not hasattr(item, "__iter__") or isinstance(item, (str, bytes)))


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
