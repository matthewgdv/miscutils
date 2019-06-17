from __future__ import annotations

import functools
import inspect
import os

from typing import Any, Optional, Tuple, Dict, cast

from maybe import Maybe
from subtypes import Str


def is_running_in_ipython() -> bool:
    try:
        assert __IPYTHON__  # type: ignore
        return True
    except (NameError, AttributeError):
        return False


class Beep:
    def __init__(self, duration: int = 2, frequency: int = 440) -> None:
        import winsound
        winsound.Beep(frequency=frequency, duration=duration*1000)


@functools.total_ordering
class Version:
    inf = cast(int, float("inf"))

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
        return int(self._major) if self._major != self.inf else None

    @major.setter
    def major(self, val: int) -> None:
        self._major = Maybe(val).else_(self.inf)

    @property
    def minor(self) -> Optional[int]:
        return int(self._minor) if self._minor != self.inf else None

    @minor.setter
    def minor(self, val: int) -> None:
        self._minor = Maybe(val).else_(self.inf)

    @property
    def micro(self) -> Optional[int]:
        return int(self._micro) if self._micro != self.inf else None

    @micro.setter
    def micro(self, val: int) -> None:
        self._micro = Maybe(val).else_(self.inf)


class Counter:
    def __init__(self, start_value: int = 0) -> None:
        self.value = start_value

    def __int__(self) -> int:
        return self.value

    def __iter__(self) -> Counter:
        return self

    def __next__(self) -> int:
        self.increment()
        return self.value

    def increment(self, amount: int = 1) -> None:
        self.value += amount

    def decrement(self, amount: int = 1) -> None:
        self.value -= amount


class EnVarsMeta(type):
    def __call__(self) -> Dict[str, str]:  # type: ignore
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


class EnVars(metaclass=EnVarsMeta):
    pass


class WhoCalledMe:
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


class NameSpace:
    def __init__(self, mappings: Dict[str, Any] = None) -> None:
        self._namespace = {}
        for key, val in Maybe(mappings).else_({}).items():
            self[key] = val

    def __repr__(self) -> str:
        return f"{type(self).__name__}({', '.join([f'{attr}={repr(val)}' for attr, val in self.__dict__.items() if not attr.startswith('_')])})"

    def __getitem__(self, key: str) -> Any:
        return self._namespace[key]

    def __setitem__(self, key: str, val: Any) -> None:
        self._namespace[key] = val
        setattr(self, Str(key).identifier(), val)

    def __setattr__(self, key: str, val: Any) -> None:
        super().__setattr__(key, val)
        if not key.startswith("_"):
            self._namespace[key] = val