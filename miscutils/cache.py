from __future__ import annotations

from typing import Any

from maybe import Maybe
from subtypes import DateTime
from pathmagic import PathLike

from .serializer import Serializer


class Cache:
    """A cache class that abstracts away the process of persisting python objects to the filesystem using a dict-like interface (common dict methods and item access)."""

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

    def __enter__(self) -> Cache:
        return self

    def __exit__(self, ex_type: Any, ex_value: Any, ex_traceback: Any) -> None:
        if ex_type is None:
            self._save()

    def get(self, key: str, fallback: Any = None) -> Any:
        """Get a given item from the cache by its key. Returns the fallback (default None) if the key cannot be found."""
        return self.contents.data.get(key, fallback)

    def put(self, key: str, val: Any) -> None:
        """Put an item into the cache with the given key."""
        with self:
            self.contents.data[key] = val

    def pop(self, key: str, fallback: Any = None) -> Any:
        """Return an item from the cache by its key and simultaneously remove it from the cache. Returns the fallback (default None) if the key cannot be found."""
        with self:
            return self.contents.data.pop(key, fallback)

    def setdefault(self, key: str, default: Any) -> Any:
        """Return an item from the cache by its key. If the key cannot be found, the default value will be added to the cache under that key, and then returned."""
        with self:
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
