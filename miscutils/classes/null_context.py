from __future__ import annotations

from typing import Any


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
