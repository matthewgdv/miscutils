from __future__ import annotations

import io
from functools import total_ordering
import time
import warnings
from typing import Any, Optional

import pyinstrument

from maybe import Maybe
from pathmagic import Dir, PathLike

from .mixin import StdOutReplacerMixin, StdErrReplacerMixin


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
        self.period: Optional[float] = None
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


class Supressor(StdOutReplacerMixin):
    """Context manager that suppresses all output to sys.stdout and all warnings while in scope."""

    def __init__(self):
        super().__init__()
        self.catch_warnings = warnings.catch_warnings()

    def __enter__(self) -> Supressor:
        super().__enter__()
        self.catch_warnings.__enter__()
        warnings.filterwarnings("ignore")
        return self

    def __exit__(self, ex_type: Any, ex_value: Any, ex_traceback: Any) -> None:
        super().__exit__(ex_type=ex_type, ex_value=ex_value, ex_traceback=ex_traceback)
        self.catch_warnings.__exit__(ex_type, ex_value, ex_traceback)

    def write(self, text: str) -> None:
        pass


class StdOutFileRedirector(StdOutReplacerMixin):
    """Context manager that redirects sys.stdout to the given file while in scope. Optionally opens the file on exiting."""

    def __init__(self, file: PathLike = None, append: bool = False, openfile: bool = True) -> None:
        self.file = Dir.from_pathlike(file) if file is not None else Dir.from_desktop().new_file("print_redirection", "txt")
        self.append, self.openfile = append, openfile

        if not append:
            self.file.content = None

    def __str__(self) -> str:
        return self.file.content

    def __enter__(self) -> StdOutFileRedirector:
        super().__enter__()
        self.out = open(self.file, "a" if self.append else "w")
        return self

    def __exit__(self, ex_type: Any, ex_value: Any, ex_traceback: Any) -> None:
        super().__exit__(ex_type=ex_type, ex_value=ex_value, ex_traceback=ex_traceback)
        self.out.close()

        if self.openfile:
            self.file.start()

    def write(self, text: str) -> None:
        self.out.write(text)


class BaseStreamRedirector:
    """Context manager that redirects sys.stdout to the given stream while in scope."""

    def __init__(self, stream: io.StringIO = None) -> None:
        self.out = stream if stream is not None else io.StringIO()
        self.data: Optional[str] = None

    def __str__(self) -> str:
        return self.data

    def __exit__(self, ex_type: Any, ex_value: Any, ex_traceback: Any) -> None:
        # noinspection PyUnresolvedReferences
        super().__exit__(ex_type, ex_value, ex_traceback)
        self.data = self.out.getvalue()
        self.out.close()

    def write(self, text: str) -> None:
        self.out.write(text)

    def flush(self) -> None:
        self.out.flush()

    def close(self) -> None:
        self.out.close()


class StdOutStreamRedirector(BaseStreamRedirector, StdOutReplacerMixin):
    pass


class StdErrStreamRedirector(BaseStreamRedirector, StdErrReplacerMixin):
    pass


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
