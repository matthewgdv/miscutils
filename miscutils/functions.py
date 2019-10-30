from __future__ import annotations

import ast
import inspect
import os
import sys
from typing import Optional, Any, Callable

from pathmagic import Dir


def is_running_in_ipython() -> bool:
    """Returns True if run from within a jupyter ipython interactive session, else False."""
    try:
        assert __IPYTHON__  # type: ignore
        return True
    except (NameError, AttributeError):
        return False


def executed_within_user_tree() -> bool:
    """Returns True if the '__main__' module is within the branches of the current user's filesystem tree, else False."""
    main_dir = sys.modules["__main__"]._dh[0] if is_running_in_ipython() else sys.modules["__main__"].__file__
    return Dir.from_home() > os.path.abspath(main_dir)


def issubclass_safe(candidate: Any, ancestor: Any) -> bool:
    """Returns True the candidate is a subclass of the ancestor, else False. Will return false instead of raising TypeError if the candidate is not a class."""
    try:
        return issubclass(candidate, ancestor)
    except TypeError:
        return False


def beep() -> None:
    """Cross-platform implementation for producing a beeping sound. Only works on windows when used in an interactive IPython session (jupyter notebook)."""
    if is_running_in_ipython():
        import winsound
        winsound.Beep(frequency=440, duration=2*1000)
    else:
        print("\a")


def get_short_lambda_source(lambda_func: Callable) -> Optional[str]:
    """Return the source of a (short) lambda function. If it's impossible to obtain, return None."""
    try:
        source_lines, _ = inspect.getsourcelines(lambda_func)
    except (IOError, TypeError):
        return None

    if len(source_lines) != 1:
        return None

    source_text = os.linesep.join(source_lines).strip()

    source_ast = ast.parse(source_text)
    lambda_node = next((node for node in ast.walk(source_ast) if isinstance(node, ast.Lambda)), None)
    if lambda_node is None:
        return None

    lambda_text = source_text[lambda_node.col_offset:]
    lambda_body_text = source_text[lambda_node.body.col_offset:]
    min_length = len('lambda:_')
    while len(lambda_text) > min_length:
        try:
            code = compile(lambda_body_text, '<unused filename>', 'eval')

            if len(code.co_code) == len(lambda_func.__code__.co_code):
                return lambda_text
        except SyntaxError:
            pass
        lambda_text = lambda_text[:-1]
        lambda_body_text = lambda_body_text[:-1]

    return None
