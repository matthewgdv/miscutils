from __future__ import annotations

import io
from functools import total_ordering
import os
import sys
import time
import warnings
from typing import Any, Optional, Callable, Sequence

import pyinstrument

from maybe import Maybe
from pathmagic import Dir, PathLike

from .mixin import StreamReplacerMixin


class Printer(StreamReplacerMixin):
    def __init__(self, formatter: Callable[[str], str]) -> None:
        self.formatter = formatter

    def write(self, text: str) -> None:
        self.stream.write(self.formatter(text))

    @classmethod
    def from_indentation(cls, level: int = 1, indentation_token: str = " "*4) -> Printer:
        return cls(formatter=lambda text: f"{indentation_token*level}{text}")


class Profiler(pyinstrument.Profiler):
    """A subclass of pyinstrument.Profiler with a better __str__ method."""

    def __str__(self) -> str:
        return self.output_text(unicode=True, color=True)


@total_ordering
class Timer:
    """
    A timer that begins on instanciation and can be converted to a string, int, or float. It can be reset by calling it.
    When used as a context manager, upon exiting sets a Timer.period attribute indicating the timer's value at point of exit. Entering does not reset the timer.
    """

    def __init__(self, timeout: int = None, retry_delay: int = None) -> None:
        self.period: float = None
        self.timeout, self.retry_delay = timeout, retry_delay
        self.start = time.time()

    def __repr__(self) -> str:
        return f"{type(self).__name__}(seconds={int(self)})"

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


class Supressor(StreamReplacerMixin):
    """Context manager that suppresses all output to sys.stdout while in scope."""

    def __enter__(self) -> Supressor:
        super().__enter__()

        self.filters = warnings.filters.copy()
        warnings.filterwarnings("ignore")

        return self

    def __exit__(self, ex_type: Any, ex_value: Any, ex_traceback: Any) -> None:
        super().__exit__(ex_type=ex_type, ex_value=ex_value, ex_traceback=ex_traceback)
        warnings.filters = self.filters

    def write(self, text: str) -> None:
        pass


class FilePrintRedirector(StreamReplacerMixin):
    """Context manager that redirects sys.stdout to the given file while in scope. Optionally opens the file on exiting."""

    def __init__(self, outfile: PathLike = None, append: bool = False, openfile: bool = True) -> None:
        self.outfile = Dir.from_pathlike(outfile) if outfile is not None else Dir.from_desktop().new_file("print_redirection", "txt")
        self.append, self.openfile = append, openfile

        if not append:
            self.outfile.content = None

    def __str__(self) -> str:
        return self.outfile.content

    def __enter__(self) -> FilePrintRedirector:
        super().__enter__()
        self.out = open(self.outfile, "a" if self.append else "w")
        return self

    def __exit__(self, ex_type: Any, ex_value: Any, ex_traceback: Any) -> None:
        super().__exit__(ex_type=ex_type, ex_value=ex_value, ex_traceback=ex_traceback)
        self.out.close()

        if self.openfile:
            self.outfile.start()

    def write(self, text: str) -> None:
        self.out.write(text)


class StreamPrintRedirector(StreamReplacerMixin):
    """Context manager that redirects sys.stdout to the given stream while in scope."""

    def __init__(self, stream: io.StringIO = None) -> None:
        self.out = Maybe(stream).else_(io.StringIO())
        self.data: Optional[str] = None

    def __str__(self) -> str:
        return self.data

    def __exit__(self, ex_type: Any, ex_value: Any, ex_traceback: Any) -> None:
        super().__exit__(ex_type=ex_type, ex_value=ex_value, ex_traceback=ex_traceback)
        self.out.close()

    def write(self, text: str) -> None:
        self.data += text
        self.out.write(text)


class NullContext:
    """Context manager that does nothing. Attributes can be set and accessed and it can be called and it will only ever return itself without doing anything."""

    def __bool__(self) -> bool:
        return False

    def __getattr__(self, attr: str) -> NullContext:
        return self

    def __setattr__(self, name: str, val: Any) -> None:
        pass

    def __call__(self, *args: Any, **kwargs: Any) -> NullContext:
        return self

    def __enter__(self) -> NullContext:
        return self

    def __exit__(self, ex_type: Any, ex_value: Any, ex_traceback: Any) -> None:
        pass
