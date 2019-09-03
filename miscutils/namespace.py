from __future__ import annotations

from typing import Any
from collections.abc import Mapping, MutableSequence, Sequence


class NameSpace:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if len(args) > 1:
            raise TypeError(f"{type(self).__name__} only accepts a single positional argument (of type collections.Mapping).")
        else:
            mappings = {} if not len(args) else args[0]

        self.__dict__.update({**mappings, **kwargs})

    def __repr__(self) -> str:
        return f"{type(self).__name__}({', '.join([f'{attr}={repr(val)}' for attr, val in self])})"

    def __len__(self) -> int:
        return len([item for item in self])

    def __getitem__(self, name: str) -> Any:
        return getattr(self, name)

    def __setitem__(self, name: str, val: Any) -> None:
        setattr(self, name, val)

    def __delitem__(self, name: str) -> None:
        self.__delattr__(name)

    def __iter__(self) -> NameSpace:
        return iter({name: val for name, val in vars(self).items() if not name.startswith("_")}.items())

    def __contains__(self, other: Any) -> bool:
        return other in set(vars(self).keys())

    def _clear(self) -> None:
        for name, item in self:
            del self[name]


class NameSpaceDict(dict):
    dict_fields = {attr for attr in dir(dict()) if not attr.startswith("_")}

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        invalid_fields = self.dict_fields.intersection(set(dict(*args, **kwargs).keys()))
        if invalid_fields:
            raise NameError(f"Cannot assign attributes that shadow dict methods: {', '.join([attr for attr in invalid_fields])}")

        super().__init__(*args, **kwargs)

        self.__dict__.update(self)

        for key, val in self.items():
            if isinstance(val, Mapping):
                self[key] = type(self)(val)
            elif isinstance(val, (str, bytes)):
                pass
            elif isinstance(val, MutableSequence):
                for index, item in enumerate(val):
                    if isinstance(item, Mapping):
                        val[index] = type(self)(item)
            elif isinstance(val, Sequence):
                try:
                    self[key] = type(val)([type(self)(item) if isinstance(item, Mapping) else item for item in val])
                except Exception:
                    self[key] = tuple(type(self)(item) if isinstance(item, Mapping) else item for item in val)

    def __getitem__(self, name: str) -> Any:
        return super().__getitem__(name)

    def __setitem__(self, name: str, val: Any) -> None:
        if name in self.dict_fields:
            raise NameError(f"Cannot assign attribute that shadows dict method dict.{name}().")

        setattr(self, name, val)
        super().__setitem__(name, val)

    def __delitem__(self, name: str) -> None:
        self.__delattr__(name)
        super().__delitem__(name)

    def __setattr__(self, name, val) -> None:
        super().__setattr__(name, val)
        super().__setitem__(name, val)
