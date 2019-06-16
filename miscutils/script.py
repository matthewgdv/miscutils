from __future__ import annotations

import contextlib
import functools
import inspect
import os
import traceback
from types import FunctionType
from typing import Dict, Any, Type, cast, TypeVar, Callable

from maybe import Maybe
from subtypes import Str, DateTime
from pathmagic import Dir

from .misc import Counter
from .context import Timer
from .log import PrintLog

FuncSig = TypeVar("FuncSig", bound=Callable)


class ScriptProfiler:
    def __init__(self, script: ScriptBase = None) -> None:
        self.script, self.stack = script, Counter()

    def __call__(self, func: FuncSig = None) -> FuncSig:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            timer, context = Timer(), Maybe(self.script).log.else_(contextlib.nullcontext())
            positional, keyword = ', '.join([repr(arg) for arg in args[1:]]), ', '.join([f'{name}={repr(val)}' for name, val in kwargs.items()])
            arguments = f"{positional}{f', ' if positional and keyword else ''}{keyword}"

            with context(printing=False):
                print(f"{self.prefix}{func.__name__}({arguments}) starting...")

            self.stack.increment()

            with context(printing=True):
                ret = func(*args, **kwargs)

            self.stack.decrement()

            with context(printing=False):
                print(f"{self.prefix}{func.__name__} finished in {timer} seconds, returning: {repr(ret)}. {f'State of the script object is now: {args[0]}' if isinstance(args[0], ScriptBase) else ''}")

            return ret
        return cast(FuncSig, wrapper)

    @property
    def prefix(self) -> str:
        return f"{DateTime.now().get_timestamp()} - {'    '*int(Maybe(self.stack).else_(0))}"


class ScriptMeta(type):
    def __new__(mcs, name: str, bases: Any, namespace: dict) -> Type[ScriptBase]:
        if name == "ScriptBase":
            return type.__new__(mcs, name, bases, namespace)
        else:
            profiler = ScriptProfiler(printing=False)

            for attr, val in namespace.items():
                if isinstance(val, FunctionType):
                    if attr == "__init__":
                        namespace[attr] = mcs._set_script_attributes_and_serialize(profiler(val))
                    else:
                        namespace[attr] = profiler(val)

            cls = cast(Type[ScriptBase], type.__new__(mcs, name, bases, namespace))
            cls._profiler = profiler

            try:
                cls.name = Str(os.path.basename(inspect.getfile(cls))).before_first(r"\.")
            except TypeError:
                cls.name = "LoadedScript"

            return cls

    @staticmethod
    def _set_script_attributes_and_serialize(func: FuncSig) -> FuncSig:
        @functools.wraps(func)
        def wrapper(self: ScriptBase, run_mode: str = "smart", **arguments: Any) -> None:
            self.name, self.run_mode, self.arguments = type(self).name, run_mode, arguments
            self._profiler.script = self

            now = DateTime.now()
            logs_dir = Dir.from_home().d.documents.newdir("Python").newdir("logs")
            log_path = logs_dir.newdir(now.isoformat_date(dashes=True)).newdir(self.name).newfile(f"{now.hour}h {now.minute}m {now.second}s {now.microsecond}ms.txt")
            self.log = PrintLog(log_path)

            exception = None

            try:
                func(self)
            except Exception as ex:
                exception = ex
                self.log.printing = False
                self.log.write(traceback.format_exc())

            self.log.file.newrename(f"{self.log.file.prename}.pkl").contents = self

            if exception is not None:
                raise exception

        return cast(FuncSig, wrapper)


class ScriptBase(metaclass=ScriptMeta):
    name: str
    run_mode: str
    arguments: Dict[str, Any]
    log: PrintLog
    _profiler: ScriptProfiler

    def __repr__(self) -> str:
        return f"{type(self).__name__}({', '.join([f'{attr}={repr(val)}' for attr, val in self.__dict__.items() if not attr.startswith('_')])})"
