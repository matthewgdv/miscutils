from __future__ import annotations

import os
import sys
import time
import warnings
from typing import Any, Callable

from maybe import Maybe
from pathmagic import Dir, PathLike

from .commandline import CommandLine


class SysTrayApp:
    def __init__(self, hover_text: str = "Placeholder program description.", icon: PathLike = None, default_menu_index: int = 0, on_quit: Callable = None) -> None:
        from infi.systray import SysTrayIcon
        from miscutils import resources

        icon = Maybe(icon).else_(resources.f.python_icon)
        on_quit = Maybe(on_quit).else_(SysTrayApp._kill)

        self.tray = SysTrayIcon(icon=os.fspath(icon), hover_text=hover_text, on_quit=on_quit, default_menu_index=default_menu_index)

    def __enter__(self) -> SysTrayApp:
        CommandLine.hide_console()
        return self.tray.__enter__()

    def __exit__(self, ex_type: Any, ex_value: Any, ex_traceback: Any) -> None:
        CommandLine.show_console()
        self.tray.__exit__(ex_type, ex_value, ex_traceback)

    @staticmethod
    def _kill(systray: Any) -> None:
        CommandLine.show_console()
        raise KeyboardInterrupt("The app was closed using the system tray's 'quit' option.")


class Timer:
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
        return type(self)()

    def __enter__(self) -> Timer:
        return self

    def __exit__(self, ex_type: Any, value: Any, trace: Any) -> None:
        print(self)


class Supressor:
    def __enter__(self) -> Supressor:
        self.stdout, self.filters = sys.stdout, warnings.filters.copy()  # type: ignore
        sys.stdout = open(os.devnull, "w")

        warnings.filterwarnings("ignore")

        return self

    def __exit__(self, ex_type: Any, ex_value: Any, ex_traceback: Any) -> None:
        sys.stdout.close()
        sys.stdout = self.stdout

        warnings.filters = self.filters  # type: ignore


class PrintRedirector:
    def __init__(self, outfile: PathLike = None, append: bool = False, openfile: bool = True) -> None:
        self.outfile = Dir.from_pathlike(outfile) if outfile is not None else matt.path.Dir.from_desktop().newfile("print_redirection.txt")
        self.append, self.openfile = append, openfile

    def __enter__(self) -> PrintRedirector:
        self.stdout = sys.stdout
        sys.stdout = open(self.outfile, "a" if self.append else "w")  # type: ignore
        return self

    def __exit__(self, ex_type: Any, ex_value: Any, ex_traceback: Any) -> None:
        sys.stdout.close()
        sys.stdout = self.stdout
        if self.openfile:
            self.outfile.open()


class NullContext:
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
