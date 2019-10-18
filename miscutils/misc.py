from __future__ import annotations

import functools
import inspect
import os
import sys
from typing import Optional, Tuple, Dict, Any, cast
from math import inf as Infinity

from maybe import Maybe
from subtypes import Enum
from pathmagic import Dir

from .singleton import Singleton


def is_running_in_ipython() -> bool:
    """Returns True if run from within a jupyter ipython interactive session, else False."""
    try:
        assert __IPYTHON__  # type: ignore
        return True
    except (NameError, AttributeError):
        return False


def executed_within_user_tree() -> bool:
    """Returns True if the '__main__' module is within the branches of the current user's filesystem tree, else False."""
    main_dir = sys.modules["__main__"]._dh[0] if is_running_in_ipython() else sys.modules["__main__"].__file__
    return Dir.from_home() > os.path.abspath(main_dir)


def issubclass_safe(candidate: Any, ancestor: Any) -> bool:
    """Returns True the candidate is a subclass of the ancestor, else False. Will return false instead of raising TypeError if the candidate is not a class."""
    try:
        return issubclass(candidate, ancestor)
    except TypeError:
        return False


class Beep:
    """Cross-platform implementation for producing a beeping sound. Only works on windows when used in an interactive IPython session (jupyter notebook)."""

    def __init__(self) -> None:
        if is_running_in_ipython():
            import winsound
            winsound.Beep(frequency=440, duration=2*1000)
        else:
            print("\a")


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
