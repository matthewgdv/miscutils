from __future__ import annotations

from typing import Any, Callable, TypeVar, cast

from maybe import Maybe
from subtypes import DateTime
from pathmagic import PathLike
from .serializer import Serializer

FuncSig = TypeVar("FuncSig", bound=Callable)


def _serialize_cache(func: FuncSig) -> FuncSig:
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        instance = args[0]
        ret = func(*args, **kwargs)
        instance._save()
        return ret
    return cast(FuncSig, wrapper)


class Cache:
    def __init__(self, file: PathLike, days: int = None, hours: int = None, minutes: int = None) -> None:
        self.serializer = Serializer(file)
        self.expiry = None if all([val is None for val in (days, hours, minutes)]) else DateTime.now().delta(days=Maybe(days).else_(0), hours=Maybe(hours).else_(0), minutes=Maybe(minutes).else_(0))
        self.contents = self._get_contents()

    def __repr__(self) -> str:
        return f"{type(self).__name__}({', '.join([f'{attr}={repr(val)}' for attr, val in self.__dict__.items() if not attr.startswith('_')])})"

    def __bool__(self) -> bool:
        return self.serializer and DateTime.now() < self.expiry

    def __getitem__(self, key: str) -> Any:
        return self.get(key)

    def __setitem__(self, key: str, val: Any) -> None:
        self.put(key, val)

    def __delitem__(self, key: str) -> None:
        self.pop(key)

    def __contains__(self, name: str) -> bool:
        return name in self.contents.data

    def get(self, key: str, fallback: Any = None) -> Any:
        return self.contents.data.get(key, fallback)

    @_serialize_cache
    def put(self, key: str, val: Any) -> None:
        self.contents.data[key] = val

    @_serialize_cache
    def pop(self, key: str, fallback: Any = None) -> Any:
        return self.contents.data.pop(key, fallback)

    @_serialize_cache
    def setdefault(self, key: str, default: Any) -> Any:
        return self.contents.data.setdefault(key, default)

    def _save(self) -> None:
        self.serializer.serialize(self.contents)

    def _get_contents(self) -> None:
        contents = self.serializer.deserialize()
        if not contents:
            contents = Cache.Contents(expires_on=self.expiry)
            self.serializer.serialize(contents)

        return contents

    class Contents:
        def __init__(self, expires_on: DateTime) -> None:
            self.expiry = expires_on
            self.data: dict = {}

        def __repr__(self) -> str:
            return f"{type(self).__name__}({', '.join([f'{attr}={repr(val)}' for attr, val in self.data.items()])})"

        def __bool__(self) -> bool:
            return True if self.expiry is None else DateTime.now() < self.expiry
