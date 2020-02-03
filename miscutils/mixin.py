from __future__ import annotations

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


class StreamReplacerMixin:
    stream: TextIO

    def __enter__(self) -> StreamReplacerMixin:
        self.stream = sys.stdout
        sys.stdout = self
        return self

    def __exit__(self, ex_type: Any, ex_value: Any, ex_traceback: Any) -> None:
        sys.stdout = self.stream

    def write(self, text: str) -> None:
        self.stream.write(text)

    def flush(self) -> None:
        self.stream.flush()

    def close(self) -> None:
        self.stream.close()
