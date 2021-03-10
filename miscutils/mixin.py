from __future__ import annotations

from copy import copy, deepcopy


class ReprMixin:
    def __repr__(self) -> str:
        return f"{type(self).__name__}({', '.join([f'{attr}={repr(val)}' for attr, val in self.__dict__.items() if not attr.startswith('_')])})"


class CopyMixin:
    def copy(self) -> CopyMixin:
        return copy(self)

    def deepcopy(self) -> CopyMixin:
        return deepcopy(self)
