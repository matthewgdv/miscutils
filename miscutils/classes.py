from __future__ import annotations

import functools
import inspect
import os
from typing import Optional, Tuple, Dict, Collection, Type, Any, Callable, cast
from math import inf as Infinity

from maybe import Maybe
from subtypes import Enum, Singleton

from .functions import is_non_string_iterable


@functools.total_ordering
class Version:
    """Version class with comparison operators, string conversion using a customizable wildcard, and attribute control."""
    class Update(Enum):
        MAJOR, MINOR, MICRO = "major", "minor", "micro"

    inf = cast(int, Infinity)

    def __init__(self, major: int, minor: int, micro: int, wildcard: str = None) -> None:
        self.wildcard = wildcard
        self.major, self.minor, self.micro = major, minor, micro

    def __repr__(self) -> str:
        return f"{type(self).__name__}({', '.join([f'{size}={getattr(self, size)}' for size in ['major', 'minor', 'micro']])})"

    def __str__(self) -> str:
        return ".".join([str(getattr(self, size)) if getattr(self, f"_{size}") != self.inf else str(self.wildcard) for size in ["major", "minor", "micro"]])

    def __eq__(self, other: Tuple[int, int, int]) -> bool:  # type: ignore
        return (self._major, self._minor, self._micro) == other

    def __lt__(self, other: Tuple[int, int, int]) -> bool:
        return (self._major, self._minor, self._micro) < other

    @property
    def major(self) -> Optional[int]:
        """The major version number."""
        return int(self._major) if self._major != self.inf else None

    @major.setter
    def major(self, val: int) -> None:
        self._major = Maybe(val).else_(self.inf)

    @property
    def minor(self) -> Optional[int]:
        """The minor version number."""
        return int(self._minor) if self._minor != self.inf else None

    @minor.setter
    def minor(self, val: int) -> None:
        self._minor = Maybe(val).else_(self.inf)

    @property
    def micro(self) -> Optional[int]:
        """The micro version number."""
        return int(self._micro) if self._micro != self.inf else None

    @micro.setter
    def micro(self, val: int) -> None:
        self._micro = Maybe(val).else_(self.inf)

    def increment_major(self) -> Version:
        self.major += 1
        self.minor = self.micro = 0
        return self

    def increment_minor(self) -> Version:
        self.minor += 1
        self.micro = 0
        return self

    def increment_micro(self) -> Version:
        self.micro += 1
        return self


class Counter:
    """Counter implementation that can have a limit set and can then be iterated over. Start value can also be set."""

    def __init__(self, start: int = 0, limit: int = Infinity) -> None:
        self.start = self.value = start
        self.limit = limit

    def __str__(self) -> str:
        return str(self.value)

    def __int__(self) -> int:
        return self.value

    def __iter__(self) -> Counter:
        self.reset()
        return self

    def __next__(self) -> int:
        if self.value >= self.limit:
            raise StopIteration

        ret = self.value
        self.increment()
        return ret

    def increment(self, amount: int = 1) -> int:
        """Increment the counter by given amount."""
        self.value += amount
        return self.value

    def decrement(self, amount: int = 1) -> int:
        """Decrement the counter by given amount."""
        self.value -= amount
        return self.value

    def reset(self) -> int:
        """Reset the counter to the starting value."""
        self.value = self.start
        return self.value


class EnvironmentVariables(Singleton):
    """Helper class to permanently modify the user environment variables on Windows."""

    def __call__(self) -> Dict[str, str]:
        return self.keys()

    def __getitem__(self, key: str) -> str:
        return os.environ[key]

    def __setitem__(self, key: str, val: str) -> None:
        os.environ[str(key)] = str(val)
        os.system(f"SET {key} {val}")
        os.system(f"SETX {key} {val}")

    def __getattr__(self, attr: str) -> str:
        return self[attr]

    def __setattr__(self, attr: str, val: str) -> None:
        self[attr] = val

    def keys(self) -> list:
        return list(os.environ)


class WhoCalledMe:
    """Utility class to print the stack_trace from the location of its instanciation."""

    def __init__(self, full_trace: bool = True) -> None:
        self.stack = inspect.stack()

        if not full_trace:
            print(f"'{self.stack[1][3]}' called by: '{self.stack[2][3]}'")
        else:
            statement = f"'{self.stack[1][3]}'"
            for caller in self.stack[2:]:
                statement += f" <- '{caller[3]}'"
                if caller[3] == "run_code":
                    break

            print(statement)


class OneOrMany:
    class IfTypeNotMatches(Enum):
        RAISE, COERCE, IGNORE = "raise", "coerce", "ignore"

    def __init__(self, of_type: Type[Any] = None) -> None:
        self._candidate: Any = None
        self._dtype: Type[Any] = of_type
        self._collection_type: Type[Collection] = list
        self._on_type_mismatch = OneOrMany.IfTypeNotMatches.RAISE
        self._coerce_callback: Callable = None

    def __call__(self) -> Type[Collection]:
        return self.normalize()

    def of_type(self, dtype: Type[Any]) -> OneOrMany:
        self._dtype = dtype
        return self

    def to_collection_type(self, collection_type: Type[Collection]) -> OneOrMany:
        self._collection_type = collection_type
        return self

    def if_type_not_matches(self, respond_with: OneOrMany.IfTypeNotMatches) -> OneOrMany:
        self._on_type_mismatch = respond_with
        return self

    def coerce_with(self, callback: Callable) -> OneOrMany:
        self._coerce_callback = callback
        return self

    def normalize(self, candidate: Any) -> Type[Collection]:
        as_list = list(candidate) if is_non_string_iterable(candidate) else [candidate]

        if self._dtype is not None:
            for index, item in enumerate(as_list):
                if not isinstance(item, self._dtype):
                    if self._on_type_mismatch == OneOrMany.IfTypeNotMatches.RAISE:
                        raise TypeError(f"Object {repr(item)} has type '{type(item).__name__}'. Expected type '{self._dtype.__name__}'.")
                    elif self._on_type_mismatch == OneOrMany.IfTypeNotMatches.COERCE:
                        coerced = Maybe(self._coerce_callback).else_(self._dtype)(item)
                        if isinstance(coerced, self._dtype):
                            as_list[index] = coerced
                        else:
                            raise TypeError(f"Attempted to coerce object {repr(item)} of type '{type(item).__name__}' to type '{self._dtype.__name__}' using '{Maybe(self._coerce_callback).else_(self._dtype)}' as a callback, but returned {repr(coerced)} of type '{type(coerced).__name__}'.")
                    elif self._on_type_mismatch == OneOrMany.IfTypeNotMatches.IGNORE:
                        pass
                    else:
                        OneOrMany.IfTypeNotMatches.raise_if_not_a_member(self._on_type_mismatch)

        return self._collection_type(as_list)