from __future__ import annotations


class SingletonMeta(type):
    def __call__(cls) -> Singleton:
        if cls._instance_ is None:
            cls._instance_ = super().__call__()

        return cls._instance_


class Singleton(metaclass=SingletonMeta):
    """A singleton class that will always return the same object from its constuctor. Intended to be subclassed."""
    _instance_ = None

    def __repr__(self) -> str:
        return type(self).__name__
