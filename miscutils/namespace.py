from __future__ import annotations

from typing import Any, Dict

from maybe import Maybe
from subtypes import Str


class NameSpace:
    def __init__(self, mappings: Dict[str, Any] = None) -> None:
        self._namespace = {}
        self._update_namespace(mappings)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({', '.join([f'{attr}={repr(val)}' for attr, val in self.__dict__.items() if not attr.startswith('_')])})"

    def __getitem__(self, name: str) -> Any:
        return self._namespace[name]

    def __setitem__(self, name: str, val: Any) -> None:
        self._add_to_namespace(name, val)

    def __delitem__(self, name: str) -> None:
        self._remove_from_namespace(name)

    def __setattr__(self, name: str, val: Any) -> None:
        if name.startswith("_"):
            super().__setattr__(name, val)
        else:
            self._add_to_namespace(name, val)

    def __delattr__(self, name: str) -> None:
        self._remove_from_namespace(name)

    def __len__(self) -> int:
        return len(self._namespace)

    def __iter__(self) -> NameSpace:
        self.__iter = self._namespace.values()
        return self

    def __next__(self) -> Any:
        return next(self.__iter)

    def __contains__(self, other: Any) -> bool:
        return other in set(self._namespace.keys())

    def _add_to_namespace(self, name: Any, val: Any) -> None:
        super().__setattr__(Str(name).identifier(), val)
        self._namespace[name] = val

    def _update_namespace(self, mappings: Dict[str, Any]) -> None:
        for key, val in Maybe(mappings).else_({}).items():
            self[key] = val

    def _remove_from_namespace(self, name: str) -> None:
        super().__delattr__(name)
        self._namespace.pop(name)

    def _clear_namespace(self) -> None:
        for name in list(self._namespace):
            del self[name]
