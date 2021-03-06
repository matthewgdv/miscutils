from typing import Any, Callable
from functools import wraps


class PostInitMeta(type):
    _post_init_registry: dict[Any, int] = {}

    def post_init_soon(cls, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            instance = args[0]
            cls._post_init_registry[instance] = cls._post_init_registry.get(instance, 0) + 1

            ret = func(*args, **kwargs)

            if ref := (cls._post_init_registry[instance] - 1):
                cls._post_init_registry[instance] = ref
            else:
                del cls._post_init_registry[instance]
                instance.__post_init__()

            return ret
        return wrapper

    def __init__(cls, name: str, bases: tuple, namesapce: dict) -> None:
        cls.__init__ = cls.post_init_soon(cls.__init__)
