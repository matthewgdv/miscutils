from __future__ import annotations

import base64
import functools
import inspect
import os
from typing import Optional, Tuple, List, Type, Any, Callable, cast, Union, Sequence, Dict
from math import inf as infinity

import numpy as np
from gender_guesser.detector import Detector as GenderDetector

from maybe import Maybe
from subtypes import Enum, cached_property

from .mixin import ReprMixin
from .functions import class_name


@functools.total_ordering
class Version:
    """Version class with comparison operators, string conversion using a customizable wildcard, and attribute control."""
    class Update(Enum):
        MAJOR, MINOR, MICRO = "major", "minor", "micro"

    inf = cast(int, infinity)

    def __init__(self, major: int, minor: int, micro: int, wildcard: str = None) -> None:
        self.wildcard = wildcard
        self.major, self.minor, self.micro = [magnitude if magnitude is None else int(magnitude) for magnitude in (major, minor, micro)]

    def __repr__(self) -> str:
        return f"{type(self).__name__}({', '.join([f'{size}={getattr(self, size)}' for size in ['major', 'minor', 'micro']])})"

    def __str__(self) -> str:
        return ".".join([str(getattr(self, size)) if getattr(self, f"_{size}") != self.inf else str(self.wildcard) for size in ["major", "minor", "micro"]])

    def __eq__(self, other: Version) -> bool:
        return (self._major, self._minor, self._micro) == (other._major, other._minor, other._micro)

    def __lt__(self, other: Version) -> bool:
        return (self._major, self._minor, self._micro) < (other._major, other._minor, other._micro)

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

    def increment(self, magnitude: Update) -> Version:
        self.Update(magnitude).map_to({
            self.Update.MAJOR: self.increment_major,
            self.Update.MINOR: self.increment_minor,
            self.Update.MICRO: self.increment_micro,
        })()

        return self

    def copy(self) -> Version:
        return type(self)(self.major, self.minor, self.micro, wildcard=self.wildcard)

    @classmethod
    def from_string(cls, text: str, wildcard: str = None) -> Version:
        text = text.strip()
        text = text[1:] if text.lower().startswith("v") else text
        major, minor, micro = text.split(".")

        if wildcard is not None:
            major, minor, micro = major if major != wildcard else None, minor if minor != wildcard else None, micro if micro != wildcard else None

        return cls(major=major, minor=minor, micro=micro, wildcard=wildcard)


class Coordinates:
    def __init__(self, x: int, y: int) -> None:
        self.array = np.array([x, y])

    def __repr__(self) -> str:
        return f"{type(self).__name__}(x={self.x}, y={self.y})"

    def __bool__(self) -> bool:
        return bool(self.x or self.y)

    def __eq__(self, other: Coordinates) -> bool:
        return self.x == other.x and self.y == other.y

    def __add__(self, other: Coordinates) -> Coordinates:
        x, y = self.array + (other.array if isinstance(other, Coordinates) else other)
        return type(self)(x, y)

    def __sub__(self, other: Coordinates) -> Coordinates:
        x, y = self.array - (other.array if isinstance(other, Coordinates) else other)
        return type(self)(x, y)

    def __mul__(self, other: Coordinates) -> Coordinates:
        x, y = self.array * (other.array if isinstance(other, Coordinates) else other)
        return type(self)(x, y)

    def __truediv__(self, other: Coordinates) -> Coordinates:
        x, y = self.array / (other.array if isinstance(other, Coordinates) else other)
        return type(self)(x, y)

    def __floordiv__(self, other: Coordinates) -> Coordinates:
        x, y = self.array // (other.array if isinstance(other, Coordinates) else other)
        return type(self)(x, y)

    def __mod__(self, other: Coordinates) -> Coordinates:
        x, y = self.array % (other.array if isinstance(other, Coordinates) else other)
        return type(self)(x, y)

    @property
    def x(self) -> int:
        return int(self.array[0])

    @x.setter
    def x(self, x: int) -> None:
        self.array[0] = x

    @property
    def y(self) -> int:
        return int(self.array[1])

    @y.setter
    def y(self, y: int) -> None:
        self.array[1] = y


class Counter:
    """Counter implementation that can have a limit set and can then be iterated over. Start value can also be set."""

    def __init__(self, start: int = 0, limit: int = infinity) -> None:
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


class PercentagePrinter:
    def __init__(self, iterable: Sequence, formatter: Callable[[Any], str] = lambda val: str(val), padding: str = " ", finished_text: str = "DONE", percent_formatter: Callable[[Union[int, float]], str] = lambda percent: f"[{percent:7.2%}]") -> None:
        self.iterable, self.formatter, self.finished_text, self.percent_formatter = iterable, formatter, finished_text, percent_formatter
        self.padding, self.size = padding, len(iterable)

    def __iter__(self) -> PercentagePrinter:
        self.index = 0
        return self

    def __next__(self) -> Any:
        if self.index >= self.size:
            print(f"{self.percent_formatter(1)}{self.padding}{self.finished_text}")
            raise StopIteration

        print(f"{self.percent_formatter(self.index/self.size)}{self.padding}{self.formatter(element := self.iterable[self.index])}")
        self.index += 1
        return element


class WindowsEnVars:
    """Helper class to permanently modify the user environment variables on Windows."""

    class Scope(Enum):
        SYSTEM, USER = "system", "user"

    # noinspection PyUnresolvedReferences,PyPackageRequirements
    def __init__(self, scope: WindowsEnVars.Scope = Scope.USER) -> None:
        import clr
        from System import Environment, EnvironmentVariableTarget

        Scope = type(self).Scope

        self._dotnet_setter_ = Environment.SetEnvironmentVariable
        self._scope_ = Scope(scope).map_to({Scope.USER: EnvironmentVariableTarget.User, Scope.SYSTEM: EnvironmentVariableTarget.Machine})

    def __call__(self) -> List[str]:
        return self.keys()

    def __getitem__(self, key: str) -> str:
        return os.environ[key]

    def __setitem__(self, key: str, val: str) -> None:
        os.environ[(key := str(key))] = (val := str(val))
        self._dotnet_setter_(key, val, self._scope_)

    def __getattr__(self, attr: str) -> str:
        if attr.startswith("_") and attr.endswith("_"):
            return super().__getattribute__(attr)
        else:
            return self[attr]

    def __setattr__(self, attr: str, val: str) -> None:
        if attr.startswith("_") and attr.endswith("_"):
            super().__setattr__(attr, val)
        else:
            self[attr] = val

    def keys(self) -> List[str]:
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

    def __init__(self, of_type: Union[Type[Any], Tuple[Type[Any], ...]] = None) -> None:
        self._dtype: Optional[Type[Any]] = None
        self._on_type_mismatch = OneOrMany.IfTypeNotMatches.RAISE
        self._coerce_callback: Callable = self._dtype
        self._dtype_name: Optional[Union[str, List[str]]] = None

        if of_type is not None:
            self.of_type(dtype=of_type)

    def __call__(self, candidate: Any) -> list:
        return self.to_list(candidate=candidate)

    def of_type(self, dtype: Union[Type[Any], Tuple[Type[Any], ...]]) -> OneOrMany:
        self._dtype = dtype
        self._dtype_name = class_name(self._dtype) if not isinstance(self._dtype, tuple) else [class_name(dtype) for dtype in self._dtype]
        return self

    def if_type_not_matches(self, respond_with: OneOrMany.IfTypeNotMatches) -> OneOrMany:
        self._on_type_mismatch = respond_with
        return self

    def coerce_with(self, callback: Callable) -> OneOrMany:
        self._coerce_callback = callback
        return self

    def to_list(self, candidate: Any) -> List[Any]:
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


class Base64:
    def __init__(self, raw_bytes: bytes) -> None:
        self.bytes = raw_bytes

    def __bytes__(self) -> bytes:
        return self.bytes

    def to_utf8(self) -> str:
        return self.bytes.decode("utf-8")

    def to_b64(self) -> str:
        return base64.urlsafe_b64encode(self.bytes).decode("utf-8")

    @classmethod
    def from_utf8(cls, utf8: str) -> Base64:
        return cls(raw_bytes=utf8.encode("utf-8"))

    @classmethod
    def from_b64(cls, b64: str) -> Base64:
        return cls(raw_bytes=base64.urlsafe_b64decode(b64))


class GenderMeta(type):
    Pronoun: Type[Gender.Pronoun]

    def from_name(cls, name: str) -> Gender:
        return cls._mappings.get(cls._detector.get_gender(name=name))

    @cached_property
    def male(cls) -> Gender:
        return cls(name="male", pronoun=cls.Pronoun(subjective="he", objective="him", possessive="his"))

    @cached_property
    def trans_masculine(cls) -> Gender:
        return cls(name="transmasculine", pronoun=cls.Pronoun(subjective="he", objective="him", possessive="his"))

    @cached_property
    def female(cls) -> Gender:
        return cls(name="female", pronoun=cls.Pronoun(subjective="she", objective="her", possessive="her"))

    @cached_property
    def trans_femenine(cls) -> Gender:
        return cls(name="transfemenine", pronoun=cls.Pronoun(subjective="she", objective="her", possessive="her"))

    @cached_property
    def non_binary(cls) -> Gender:
        return cls(name="nonbinary", pronoun=cls.Pronoun(subjective="they", objective="them", possessive="their"))

    @cached_property
    def other(cls) -> Gender:
        return cls(name="other")

    @cached_property
    def unknown(cls) -> Gender:
        return cls(name="unknown")

    @cached_property
    def _detector(cls) -> GenderDetector:
        return GenderDetector(case_sensitive=False)

    @cached_property
    def _mappings(cls) -> Dict[str, Gender]:
        return {
            "male": cls.male,
            "mostly_male": cls.male,
            "female": cls.female,
            "mostly_female": cls.female,
            "andy": cls.non_binary,
            "unknown": cls.unknown
        }


class Gender(ReprMixin, metaclass=GenderMeta):
    class Pronoun(ReprMixin):
        def __init__(self, subjective: str, objective: str, possessive: str) -> None:
            self.subjective, self.objective, self.possessive = subjective, objective, possessive

    def __init__(self, name: str, pronoun: Pronoun = None) -> None:
        self.name, self.pronoun = name, pronoun

