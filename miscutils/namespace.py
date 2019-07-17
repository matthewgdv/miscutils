from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

from maybe import Maybe


class BaseNameSpace(ABC):
    def __init__(self, mappings: Dict[str, Any] = None, recursive: bool = True) -> None:
        self.__dict__.update(Maybe(mappings).else_({}))

        if recursive:
            for key, val in vars(self).items():
                if isinstance(val, dict):
                    self[key] = type(self)(mappings=val, recursive=recursive)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({', '.join([f'{attr}={repr(val)}' for attr, val in self])})"

    def __len__(self) -> int:
        return len([item for item in self])

    @abstractmethod
    def __getitem__(self, name: str) -> None:
        pass

    @abstractmethod
    def __setitem__(self, name: str, val: Any) -> None:
        pass

    @abstractmethod
    def __delitem__(self, name: str) -> None:
        pass

    @abstractmethod
    def __iter__(self) -> None:
        pass

    @abstractmethod
    def __next__(self) -> None:
        pass

    @abstractmethod
    def __contains__(self, other: Any) -> None:
        pass

    def to_dict(self, recursive: bool = True) -> dict:
        return {key: (val.to_dict(recursive=recursive) if recursive and isinstance(val, type(self)) else val) for key, val in self}


class NameSpace(BaseNameSpace):
    def __getitem__(self, name: str) -> Any:
        return getattr(self, name)

    def __setitem__(self, name: str, val: Any) -> None:
        setattr(self, name, val)

    def __delitem__(self, name: str) -> None:
        self.__delattr__(name)

    def __iter__(self) -> NameSpace:
        self.__iter = iter({name: val for name, val in vars(self).items() if not name.startswith("_")}.items())
        return self

    def __next__(self) -> Any:
        return next(self.__iter)

    def __contains__(self, other: Any) -> bool:
        return other in set(vars(self).keys())


class NameSpaceObject(BaseNameSpace):
    def __getitem__(self, name: str) -> Any:
        if name in self:
            return getattr(self, name)
        else:
            raise KeyError(f"Key '{name}' is not in {self}.")

    def __setitem__(self, name: str, val: Any) -> None:
        if name.startswith("_"):
            raise NameError(f"Cannot assign keys that start with '_' to {type(self).__name__}.")
        else:
            setattr(self, name, val)

    def __delitem__(self, name: str) -> None:
        if name in self:
            self.__delattr__(name)
        else:
            raise KeyError(f"Key '{name}' is not in {self}.")

    def __iter__(self) -> NameSpaceObject:
        self.__iter = iter(self.__namespace_attributes().items())
        return self

    def __next__(self) -> Any:
        return next(self.__iter)

    def __contains__(self, other: Any) -> bool:
        return other in set(self.__namespace_attributes().keys())

    def _clear(self) -> None:
        for name in self.__namespace_attributes().keys():
            del self[name]

    def __namespace_attributes(self) -> dict:
        return {key: val for key, val in vars(self).items() if not key.startswith("_")}
