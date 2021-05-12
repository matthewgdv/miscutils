from __future__ import annotations

from functools import total_ordering
from typing import Optional, Any
import time


@total_ordering
class Timer:
    """
    A timer that begins on instanciation and can be converted to a string, int, or float. It can be reset by calling it.
    When used as a context manager, upon exiting sets a Timer.period attribute indicating the timer's value at point of exit. Entering does not reset the timer.
    """

    def __init__(self, timeout: float = None, retry_delay: float = None) -> None:
        self.period: Optional[float] = None
        self.timeout, self.retry_delay = timeout, retry_delay
        self.start = time.time()

    def __repr__(self) -> str:
        return f"{type(self).__name__}(seconds={float(self)})"

    def __str__(self) -> str:
        return str(float(self))

    def __bool__(self) -> bool:
        return self.timeout is None or self < self.timeout

    def __iter__(self) -> Timer:
        self._fresh = True
        return self

    def __next__(self) -> float:
        if self.timeout is None:
            raise RuntimeError(f"Cannot iterate over a {type(self).__name__} that does not have a timeout set.")

        if float(self) + (self.retry_delay or 0) > self.timeout:
            raise StopIteration

        if self._fresh:
            self._fresh = False
        elif self.retry_delay is not None:
            time.sleep(self.retry_delay)

        return float(self)

    def __int__(self) -> int:
        return int(float(self))

    def __float__(self) -> float:
        return time.time() - self.start

    def __call__(self) -> Timer:
        self.start = time.time()
        return self

    def __enter__(self) -> Timer:
        self.period = None
        return self

    def __exit__(self, ex_type: Any, value: Any, trace: Any) -> None:
        self.period = float(self)

    def __eq__(self, other: Any) -> bool:
        return int(self) == other

    def __lt__(self, other: Any) -> bool:
        return float(self) < other
