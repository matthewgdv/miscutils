from __future__ import annotations

from math import inf as infinity


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

    def increment(self, amount: int = 1) -> Counter:
        """Increment the counter by given amount."""
        self.value += amount
        return self

    def decrement(self, amount: int = 1) -> Counter:
        """Decrement the counter by given amount."""
        self.value -= amount
        return self

    def reset(self) -> Counter:
        """Reset the counter to the starting value."""
        self.value = self.start
        return self
