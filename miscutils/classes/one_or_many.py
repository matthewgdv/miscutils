from __future__ import annotations

from typing import Optional, Type, Any, Callable, Union

from maybe import Maybe
from subtypes import Enum

from ..functions import class_name


class OneOrMany:
    class IfTypeNotMatches(Enum):
        RAISE = COERCE = IGNORE = Enum.Auto()

    def __init__(self, of_type: Union[Type[Any], tuple[Type[Any], ...]] = None) -> None:
        self._dtype: Optional[Type[Any]] = None
        self._on_type_mismatch = OneOrMany.IfTypeNotMatches.RAISE
        self._coerce_callback: Callable = self._dtype
        self._dtype_name: Optional[Union[str, list[str]]] = None

        if of_type is not None:
            self.of_type(dtype=of_type)

    def __call__(self, candidate: Any) -> list:
        return self.to_list(candidate=candidate)

    def of_type(self, dtype: Union[Type[Any], tuple[Type[Any], ...]]) -> OneOrMany:
        self._dtype = dtype
        self._dtype_name = class_name(self._dtype) if not isinstance(self._dtype, tuple) else [class_name(dtype) for dtype in self._dtype]
        return self

    def if_type_not_matches(self, respond_with: OneOrMany.IfTypeNotMatches) -> OneOrMany:
        self._on_type_mismatch = respond_with
        return self

    def coerce_with(self, callback: Callable) -> OneOrMany:
        self._coerce_callback = callback
        return self

    def to_list(self, candidate: Any) -> list[Any]:
        as_list = list(candidate) if isinstance(candidate, (list, set, tuple, dict)) else [candidate]

        if self._dtype is not None:
            for index, item in enumerate(as_list):
                if not isinstance(item, self._dtype):
                    if self._on_type_mismatch == self.IfTypeNotMatches.RAISE:
                        raise TypeError(f"Object: {repr(item)} has type '{class_name(item)}'. Expected type(s): {repr(self._dtype_name)}.")
                    elif self._on_type_mismatch == self.IfTypeNotMatches.COERCE:
                        coerced = self._coerce_callback(item)
                        if isinstance(coerced, self._dtype):
                            as_list[index] = coerced
                        else:
                            raise TypeError(f"Attempted to coerce object: {repr(item)} of type '{class_name(item)}' to type(s) {repr(self._dtype_name)} using '{Maybe(self._coerce_callback).else_(self._dtype)}' as a callback, but returned {repr(coerced)} of type '{class_name(coerced)}'.")
                    elif self._on_type_mismatch == self.IfTypeNotMatches.IGNORE:
                        continue
                    else:
                        self.IfTypeNotMatches(self._on_type_mismatch)

        return as_list

    def to_one(self, candidate: Any) -> Any:
        as_list = self.to_list(candidate=candidate)
        if len(as_list) == 1:
            return as_list[0]
        else:
            raise ValueError(f"Expected an iterable with one value from {candidate}, got {len(as_list)}.")

    def to_one_or_none(self, candidate: Any) -> Any:
        as_list = self.to_list(candidate=candidate)
        if not len(as_list):
            return None
        elif len(as_list) == 1:
            return as_list[0]
        else:
            raise ValueError(f"Expected an iterable with one value or empty from {candidate}, got {len(as_list)}.")
