from __future__ import annotations

import contextlib
import functools
import traceback
from types import FunctionType
from typing import Dict, Any, Type, cast, TypeVar, Callable
import inspect

from maybe import Maybe
from subtypes import DateTime
from pathmagic import Dir, File

from .misc import Counter
from .context import Timer
from .log import PrintLog

# TODO: Fix bug causing print statements to fail when carried out from certain scopes (such as from within Script.__init__() itself or inner classes)
# TODO: Allow script objects to recursively wrap inner classes with profiling and logging

FuncSig = TypeVar("FuncSig", bound=Callable)


class ScriptProfiler:
    def __init__(self, log: PrintLog = None, verbose: bool = False) -> None:
        self.log, self.verbose, self.stack = log, verbose, Counter()

    def __call__(self, func: FuncSig = None) -> FuncSig:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            timer, context = Timer(), Maybe(self.log).else_(contextlib.nullcontext())
            positional, keyword = ', '.join([repr(arg) for arg in args[1:]]), ', '.join([f'{name}={repr(val)}' for name, val in kwargs.items()])
            arguments = f"{positional}{f', ' if positional and keyword else ''}{keyword}"

            with context(to_console=self.verbose):
                print(f"{self.prefix}{func.__name__}({arguments}) starting...")

            self.stack.increment()

            with context(to_console=True):
                ret = func(*args, **kwargs)

            self.stack.decrement()

            with context(to_console=self.verbose):
                print(f"{self.prefix}{func.__name__} finished in {timer} seconds, returning: {repr(ret)}. {f'State of the script object is now: {args[0]}' if isinstance(args[0], Script) else ''}")

            return ret
        return cast(FuncSig, wrapper)

    @property
    def prefix(self) -> str:
        return f"{DateTime.now().logformat()} - {'    '*int(Maybe(self.stack).else_(0))}"


class ScriptMeta(type):
    def __new__(mcs, name: str, bases: Any, namespace: dict) -> Type[Script]:
        if name == "Script":
            return type.__new__(mcs, name, bases, namespace)
        else:
            profiler = ScriptProfiler(verbose=namespace.get("verbose", False))

            for attr, val in namespace.items():
                if isinstance(val, FunctionType):
                    if attr == "__init__":
                        namespace[attr] = mcs._constructor_wrapper(profiler(val))
                    else:
                        namespace[attr] = profiler(val)

            cls = cast(Type[Script], type.__new__(mcs, name, bases, namespace))
            cls.name, cls._profiler = File(inspect.getfile(cls)).prename, profiler

            return cls

    @staticmethod
    def _constructor_wrapper(func: FuncSig) -> FuncSig:
        @functools.wraps(func)
        def wrapper(self: Script, run_mode: str = "smart", **arguments: Any) -> None:
            self.run_mode, self.arguments = run_mode, arguments

            now = DateTime.now()
            logs_dir = (Dir.from_home() if Dir.from_cwd() < Dir.from_home() else Dir.from_root()).newdir("Python").newdir("logs")
            log_path = logs_dir.newdir(now.isoformat_date()).newdir(self.name).newfile(f"[{now.hour}h {now.minute}m {now.second}s {now.microsecond}ms]", "txt")
            self.log = PrintLog(log_path)

            self._profiler.log = self.log

            exception = None

            try:
                func(self)
            except Exception as ex:
                exception = ex
                self.log.to_console = False
                self.log.write(traceback.format_exc())

            self.log.file.newrename(self.log.file.prename, "pkl").contents = self

            if exception is not None:
                raise exception

        return cast(FuncSig, wrapper)


class Script(metaclass=ScriptMeta):
    name: str
    run_mode: str
    arguments: Dict[str, Any]
    log: PrintLog

    def __repr__(self) -> str:
        return f"{type(self).__name__}({', '.join([f'{attr}={repr(val)}' for attr, val in self.__dict__.items() if not attr.startswith('_')])})"
