from __future__ import annotations

import io
from functools import total_ordering
import os
import sys
import time
import warnings
from typing import Any, Optional

import pyinstrument

from maybe import Maybe
from pathmagic import Dir, PathLike


class Profiler(pyinstrument.Profiler):
    """A subclass of pyinstrument.Profiler with a better __str__ method."""

    def __str__(self) -> str:
        return self.output_text(unicode=True, color=True)


@total_ordering
class Timer:
    """
    A timer that begins on instanciation and can be converted to a string, int, or float. It can be reset by calling it.
    When used as a context manager, resets on entering and prints on exiting.
    """

    def __init__(self) -> None:
        self.start = time.time()

    def __repr__(self) -> str:
        return f"{type(self).__name__}(seconds={int(self)})"

    def __str__(self) -> str:
        return str(float(self))

    def __int__(self) -> int:
        return int(float(self))

    def __float__(self) -> float:
        return time.time() - self.start

    def __call__(self) -> Timer:
        self.start = time.time()
        return self

    def __enter__(self) -> Timer:
        return self()

    def __exit__(self, ex_type: Any, value: Any, trace: Any) -> None:
        print(self)

    def __eq__(self, other: Any) -> bool:
        return int(self) == other

    def __lt__(self, other: Any) -> bool:
        return float(self) < other


class Supressor:
    """Context manager that suppresses all output to sys.stdout while in scope."""

    def __enter__(self) -> Supressor:
        self.stdout, self.filters = sys.stdout, warnings.filters.copy()
        sys.stdout = open(os.devnull, "w")

        warnings.filterwarnings("ignore")

        return self

    def __exit__(self, ex_type: Any, ex_value: Any, ex_traceback: Any) -> None:
        sys.stdout.close()
        sys.stdout = self.stdout

        warnings.filters = self.filters


class FilePrintRedirector:
    """Context manager that redirects sys.stdout to the given file while in scope. Optionally opens the file on exiting."""

    def __init__(self, outfile: PathLike = None, append: bool = False, openfile: bool = True) -> None:
        self.outfile = Dir.from_pathlike(outfile) if outfile is not None else Dir.from_desktop().new_file("print_redirection.txt")
        self.append, self.openfile = append, openfile

    def __str__(self) -> str:
        return self.outfile.content

    def __enter__(self) -> FilePrintRedirector:
        self.stdout = sys.stdout
        sys.stdout = open(self.outfile, "a" if self.append else "w")
        return self

    def __exit__(self, ex_type: Any, ex_value: Any, ex_traceback: Any) -> None:
        sys.stdout.close()
        sys.stdout = self.stdout
        if self.openfile:
            self.outfile.start()


class StreamPrintRedirector:
    """Context manager that redirects sys.stdout to the given stream while in scope."""

    def __init__(self, stream: io.StringIO = None) -> None:
        self.stream = Maybe(stream).else_(io.StringIO())
        self.data: Optional[str] = None

    def __str__(self) -> str:
        return self.data

    def __enter__(self) -> StreamPrintRedirector:
        self.stdout = sys.stdout
        sys.stdout = self.stream
        return self

    def __exit__(self, ex_type: Any, ex_value: Any, ex_traceback: Any) -> None:
        self.stream.seek(0)
        self.data = self.stream.read()
        self.stream.close()
        sys.stdout = self.stdout


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
