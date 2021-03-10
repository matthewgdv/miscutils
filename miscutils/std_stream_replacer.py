from __future__ import annotations

import io
import os
import sys
import warnings
from typing import Optional, TextIO, Any

from pathmagic import Dir, PathLike


class BaseReplacerMixin:
    stream: TextIO = open(os.devnull, mode="w", encoding="utf-8", errors="ignore")

    def __enter__(self) -> BaseReplacerMixin:
        if self.target is not self:
            self.stream = self.target
            self.target = self

        return self

    def __exit__(self, ex_type: Any, ex_value: Any, ex_traceback: Any) -> None:
        if self.stream is not type(self).stream:
            self.target = self.stream
            del self.stream

    @property
    def target(self):
        raise NotImplementedError

    @target.setter
    def target(self):
        raise NotImplementedError

    def write(self, text: str) -> None:
        self.stream.write(text)

    def flush(self) -> None:
        self.stream.flush()

    def close(self) -> None:
        self.stream.close()


class StdOutReplacerMixin(BaseReplacerMixin):
    @property
    def target(self):
        return sys.stdout

    @target.setter
    def target(self, stream):
        sys.stdout = stream


class StdErrReplacerMixin(BaseReplacerMixin):
    @property
    def target(self):
        return sys.stderr

    @target.setter
    def target(self, stream):
        sys.stderr = stream


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


class BaseStreamRedirector(BaseReplacerMixin):
    """Context manager that redirects sys.stdout to the given stream while in scope."""

    def __init__(self, stream: io.StringIO = None) -> None:
        self.out = stream if stream is not None else io.StringIO()

    def __str__(self) -> str:
        return self.out.getvalue()

    def __exit__(self, ex_type: Any, ex_value: Any, ex_traceback: Any) -> None:
        super().__exit__(ex_type, ex_value, ex_traceback)

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
