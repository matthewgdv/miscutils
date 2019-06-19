from __future__ import annotations

from typing import Any
import sys
import os
import getpass

from maybe import Maybe
from subtypes import DateTime
from pathmagic import File, Dir, PathLike


class Log:
    def __init__(self, logfile: PathLike, active: bool = True) -> None:
        self._path, self.user = logfile, getpass.getuser()
        self._active = self._initialized = False

        if active:
            self.activate()

    def __repr__(self) -> str:
        return f"{type(self).__name__}({', '.join([f'{attr}={repr(val)}' for attr, val in self.__dict__.items() if not attr.startswith('_')])})"

    @property
    def active(self) -> bool:
        return self._active

    @active.setter
    def active(self, val: bool) -> None:
        (self.activate if val else self.deactivate)()

    def activate(self) -> None:
        if not self._active:
            self.file = File(self._path)
            self.file.force_read = True
            if not self._initialized:
                self.file.append(f"{'-' * 200}\n" if self.file.contents else "")
                self.file.append(f"-- Process run by user: {self.user} at: {DateTime.now()}\n\n")
                self._initialized = True

            self._active = True

    def deactivate(self) -> None:
        if self._active:
            self._active = False

    def restart(self) -> None:
        self.active = False
        self.active = True

    def write(self, text: str, add_newlines: int = 2) -> None:
        if self._active:
            br = "\n"
            self.file.contents += f"{text}{br * add_newlines}"

    def write_delimiter(self, length: int = 200, add_newlines: int = 2) -> None:
        if self._active:
            br = "\n"
            self.file.contents += f"{'-' * length}{br * add_newlines}"

    def open(self) -> None:
        self.file.open()

    def opendir(self) -> None:
        self.file.opendir()

    @classmethod
    def from_details(cls, log_name: str, file_extension: str = "txt", log_dir: PathLike = None, active: bool = True) -> Log:
        default_log_dir = Dir.from_home().d.documents.newdir("Python").newdir("logs")
        today = DateTime.now().isoformat_date(dashes=False)
        logdir = Dir.from_pathlike(Maybe(log_dir).else_(default_log_dir))
        path = fR"{logdir}{os.sep}{log_name}Log{today}{file_extension if file_extension.startswith('.') else f'.{file_extension}'}"

        return cls(path, active=active)


class PrintLog(Log):
    initial = sys.stdout
    stack: Any = []

    def __init__(self, *args: Any, printing: bool = True, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.printing = printing

    def __call__(self, printing: bool) -> PrintLog:
        self.printing = printing
        return self

    def __enter__(self) -> PrintLog:
        self.stack.append(sys.stdout)
        sys.stdout = self
        return self

    def __exit__(self, ex_type: Any, ex_value: Any, ex_traceback: Any) -> None:
        sys.stdout = self.stack.pop(-1)

    def write(self, text: str) -> None:
        if self.printing:
            self.initial.write(text)

        try:
            super().write(text, add_newlines=0)
        except UnicodeEncodeError:
            pass

    def flush(self) -> None:
        self.initial.flush()
