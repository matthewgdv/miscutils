from __future__ import annotations

import os
import sys
from copy import copy, deepcopy
from typing import TextIO, Any


class ReprMixin:
    def __repr__(self) -> str:
        return f"{type(self).__name__}({', '.join([f'{attr}={repr(val)}' for attr, val in self.__dict__.items() if not attr.startswith('_')])})"


class CopyMixin:
    def copy(self) -> CopyMixin:
        return copy(self)

    def deepcopy(self) -> CopyMixin:
        return deepcopy(self)


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
