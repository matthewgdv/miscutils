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
            return f"{repr(self.cls)}[{repr(self.param)}]"

        def __call__(self, *args, **kwargs) -> T:
            ret = self.cls(*args, **kwargs)
            ret.parametrize(self.param)
            return ret

    def __class_getitem__(cls, param: Any) -> ParametrizableMixin.ParametrizedProxy:
        return cls.ParametrizedProxy(cls=cls, param=param)

    def __getitem__(self, param) -> ParametrizableMixin:
        self.parametrize(param)
        return self

    def parametrize(self, param: Any) -> ParametrizableMixin:
        raise NotImplementedError
