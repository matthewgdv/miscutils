from __future__ import annotations

from functools import total_ordering
from typing import Optional, cast
from math import inf as infinity

from subtypes import Enum


@total_ordering
class Version:
    """Version class with comparison operators, string conversion using a customizable wildcard, and attribute control."""
    class Update(Enum):
        MAJOR = MINOR = MICRO = Enum.Auto()

    inf = cast(int, infinity)

    def __init__(self, major: int, minor: int, micro: int, wildcard: str = None) -> None:
        self.major, self.minor, self.micro, self.wildcard = major, minor, micro, wildcard

    def __repr__(self) -> str:
        major = self.wildcard if (val := self.major) is None else val
        minor = self.wildcard if (val := self.minor) is None else val
        micro = self.wildcard if (val := self.micro) is None else val
        return f"{type(self).__name__}(major={repr(major)}, minor={repr(minor)}, micro={repr(micro)})"

    def __str__(self) -> str:
        major = self.wildcard if (val := self.major) is None else val
        minor = self.wildcard if (val := self.minor) is None else val
        micro = self.wildcard if (val := self.micro) is None else val
        return f"{major}.{minor}.{micro}"

    def __eq__(self, other: Version) -> bool:
        return (self._major, self._minor, self._micro) == (other._major, other._minor, other._micro)

    def __lt__(self, other: Version) -> bool:
        return (self._major, self._minor, self._micro) < (other._major, other._minor, other._micro)

    @property
    def major(self) -> Optional[int]:
        """The major version number."""
        return None if self._major == self.inf else self._major

    @major.setter
    def major(self, val: Optional[int]) -> None:
        self._major = self.inf if val is None else val

    @property
    def minor(self) -> Optional[int]:
        """The minor version number."""
        return None if self._minor == self.inf else self._minor

    @minor.setter
    def minor(self, val: Optional[int]) -> None:
        self._minor = self.inf if val is None else val

    @property
    def micro(self) -> Optional[int]:
        """The micro version number."""
        return None if self._micro == self.inf else self._micro

    @micro.setter
    def micro(self, val: Optional[int]) -> None:
        self._micro = self.inf if val is None else val

    def increment_major(self, magnitude: int = 1) -> Version:
        self.major += magnitude
        self.minor = self.micro = 0
        return self

    def increment_minor(self, magnitude: int) -> Version:
        self.minor += magnitude
        self.micro = 0
        return self

    def increment_micro(self, magnitude: int) -> Version:
        self.micro += magnitude
        return self

    def increment(self, magnitude: Update) -> Version:
        self.Update[magnitude].map_to({
            self.Update.MAJOR: self.increment_major,
            self.Update.MINOR: self.increment_minor,
            self.Update.MICRO: self.increment_micro,
        })(magnitude=magnitude)

        return self

    def copy(self) -> Version:
        return type(self)(self.major, self.minor, self.micro, wildcard=self.wildcard)

    @classmethod
    def from_string(cls, text: str, wildcard: str = None) -> Version:
        text = text.strip()
        text = text[1:] if text.lower().startswith("v") else text

        if (dots := text.count(".")) == 2:
            major, minor, micro = text.split(".")
        elif dots == 1:
            major, minor = text.split(".")
            micro = wildcard
        else:
            raise ValueError(f"{text} is not a valid version string")

        if wildcard is not None:
            major = None if major == wildcard else int(major)
            minor = None if minor == wildcard else int(minor)
            micro = None if micro == wildcard else int(micro)

        return cls(major=major, minor=minor, micro=micro, wildcard=wildcard)
