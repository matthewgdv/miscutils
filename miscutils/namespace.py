from __future__ import annotations

from typing import Any, Dict

from maybe import Maybe


class NameSpace:
    def __init__(self, mappings: Dict[str, Any] = None) -> None:
        self.__dict__.update(Maybe(mappings).else_({}))

    def __repr__(self) -> str:
        return f"{type(self).__name__}({', '.join([f'{attr}={repr(val)}' for attr, val in self.__dict__.items() if not attr.startswith('_')])})"

    def __getitem__(self, name: str) -> Any:
        return getattr(self, name)

    def __setitem__(self, name: str, val: Any) -> None:
        setattr(self, name, val)

    def __delitem__(self, name: str) -> None:
        self.__delattr__(name)

    def __len__(self) -> int:
        return len([item for item in self])

    def __iter__(self) -> NameSpace:
        self.__iter = iter({name: val for name, val in vars(self).items() if not name.startswith("_")}.items())
        return self

    def __next__(self) -> Any:
        return next(self.__iter)

    def __contains__(self, other: Any) -> bool:
        return other in set(vars(self).keys())

    def _clear_namespace(self) -> None:
        to_delete = [key for key in vars(self).keys() if not key.startswith("_")]
        for name in to_delete:
            del self[name]
