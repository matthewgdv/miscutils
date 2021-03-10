from __future__ import annotations

from copy import copy, deepcopy
from typing import Any, Generic, TypeVar


T = TypeVar("T")


class ReprMixin:
    def __repr__(self) -> str:
        return f"{type(self).__name__}({', '.join([f'{attr}={repr(val)}' for attr, val in self.__dict__.items() if not attr.startswith('_')])})"


class CopyMixin:
    def copy(self) -> CopyMixin:
        return copy(self)

    def deepcopy(self) -> CopyMixin:
        return deepcopy(self)


class ParametrizableMixin:
    class ParametrizedProxy(Generic[T]):
        def __init__(self, cls: T, param: Any) -> None:
            self.cls, self.param = cls, param

        def __repr__(self) -> str:
            return f"{repr(self.cls)}[{repr(self.params)}]"

        def __call__(self, *args, **kwargs) -> T:
            return self.cls(*args, **kwargs).parametrize(self.param)

    def __class_getitem__(cls, item: Any) -> ParametrizableMixin.ParametrizedProxy:
        return cls.ParametrizedProxy(cls=cls, param=item)

    def __getitem__(self, param) -> ParametrizableMixin:
        self.parametrize(param)
        return self

    def parametrize(self, param: Any) -> ParametrizableMixin:
        raise NotImplementedError
