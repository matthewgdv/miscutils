from __future__ import annotations

import sys
import contextlib
import functools
from typing import Any, Collection, Set, Callable, cast, TypeVar
import ctypes

import colorama
import readchar
import cursor

from maybe import Maybe
from subtypes import Frame

from .misc import is_running_in_ipython

colorama.init()

FuncSig = TypeVar("FuncSig", bound=Callable)

# TODO: implement commandline interaction interface creation API


class Colorama:
    def __init__(self) -> None:
        self.colorama = colorama

    def __call__(self, func: FuncSig = None) -> FuncSig:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with type(self)():
                ret = func(*args, **kwargs)
            return ret

        return cast(FuncSig, wrapper)

    def __enter__(self) -> Colorama:
        self.previous = sys.stdout
        sys.stdout = CommandLine.DEFAULT_STDOUT
        colorama.init()
        return self

    def __exit__(self, ex_type: Any, ex_value: Any, ex_traceback: Any) -> None:
        colorama.deinit()
        sys.stdout = self.previous


class CommandLine:
    DEFAULT_STDOUT = sys.stdout
    SEP = "-"*150
    SEP2 = f"{'-'*150}\n{'-'*150}"

    @staticmethod
    def hide_console() -> None:
        ctypes.WinDLL("user32").ShowWindow(ctypes.WinDLL("kernel32").GetConsoleWindow(), 0)

    @staticmethod
    def show_console() -> None:
        ctypes.WinDLL("user32").ShowWindow(ctypes.WinDLL("kernel32").GetConsoleWindow(), 1)

    @staticmethod
    def clear_lines(num: int = 1) -> None:
        up_one, clear_current = "\033[A", "\033[2K"
        print(f"{up_one}{clear_current}" * num, end="")

    @staticmethod
    def offer_choices(choices: Collection, starting_choice: Any = None, multi_select: bool = False, desc: str = None, helptext: bool = True, display_repr: bool = True) -> Any:
        try:
            if is_running_in_ipython():
                return CommandLine.prompt_choices(choices, desc=desc)

            choices = list(choices)
            selected_index = 0 if starting_choice is None else choices.index(starting_choice)

            func = CommandLine._collect_choices if multi_select else CommandLine._collect_choice

            with cursor.HiddenCursor():
                result = func(choices=choices, starting_index=selected_index, desc=desc, helptext=helptext, display_repr=display_repr)

            print("")
            return result
        except KeyboardInterrupt:
            print("\n\nExiting...")
            sys.exit()

    @staticmethod
    def offer_yes_or_no(default: bool, yes_text: str = 'YES', no_text: str = 'NO', desc: str = None) -> bool:
        mappings = {yes_text: True, no_text: False}
        question = Maybe(desc).else_(f"[{yes_text}/{no_text}]")
        return mappings[CommandLine.offer_choices(mappings, starting_choice=yes_text if default else no_text, desc=question, display_repr=False, helptext=False)]

    @staticmethod
    def prompt_choices(choices: Collection, desc: str = None, fancy: bool = True) -> Any:
        if desc is not None:
            print(f"\n{desc}\n\n")

        df = Frame([(index + 1, key) for index, key in enumerate(choices)], columns=("number", "option"))
        print(df.to_ascii(fancy=fancy), end="\n\n")

        output, prompt = 0, f"Choose an option: 1-{len(choices)}. 'esc' to exit.\n"
        while output not in list(df.number):
            output = input(prompt).strip()
            if output in ["esc", "quit", "bye", "stop", "help"]:
                raise KeyboardInterrupt()
            else:
                output = int(output)

        choice, = df[df.number == output].option
        return choice

    @staticmethod
    def _collect_choice(choices: list, starting_index: int, desc: str, helptext: bool, display_repr: bool) -> Any:
        if helptext:
            print("Up/Down to navigate. Enter to choose and continue. Esc to exit.", end="\n\n")

        if desc is not None:
            print(desc, end="\n\n")

        output, current_index = None, starting_index
        while output is None:
            print("\n".join([f"{'[x]' if index == current_index else '[ ]'} {repr(choice) if display_repr else choice}" for index, choice in enumerate(choices)]))

            while True:
                keypress = readchar.readkey()
                if keypress == readchar.key.UP:
                    current_index = max(current_index - 1, 0)
                    break
                elif keypress == readchar.key.DOWN:
                    current_index = min(current_index + 1, len(choices) - 1)
                    break
                elif keypress == readchar.key.ENTER:
                    output = choices[current_index]
                    break
                elif keypress == readchar.key.ESC:
                    raise KeyboardInterrupt()

            if output is None:
                CommandLine.clear_lines(len(choices))

        return output

    @staticmethod
    def _collect_choices(choices: list, starting_index: int, desc: str, helptext: bool, display_repr: bool) -> Any:
        if helptext:
            print("Up/Down to navigate. Right to add a choice. Left to remove a choice. Enter to continue. Esc to exit.", end="\n\n")

        if desc is not None:
            print(desc, end="\n\n")

        current_index, finished = starting_index, False
        selected_indices: Set[int] = set()
        while not finished:
            print("\n".join([f"{'>' if index == current_index else ' '} {'[x]' if index in selected_indices else '[ ]'} {repr(choice) if display_repr else choice}" for index, choice in enumerate(choices)]))

            while True:
                keypress = readchar.readkey()
                if keypress == readchar.key.UP:
                    current_index = max(current_index - 1, 0)
                    break
                elif keypress == readchar.key.DOWN:
                    current_index = min(current_index + 1, len(choices) - 1)
                    break
                if keypress == readchar.key.RIGHT:
                    selected_indices.add(current_index)
                    break
                elif keypress == readchar.key.LEFT:
                    selected_indices.discard(current_index)
                    break
                elif keypress == readchar.key.ENTER:
                    finished = True
                    break
                elif keypress == readchar.key.ESC:
                    raise KeyboardInterrupt()

            if not finished:
                CommandLine.clear_lines(len(choices))

        return [choices[index] for index in selected_indices]

    @staticmethod
    @contextlib.contextmanager
    def surround_sep(lines: int = 1, length: int = 150) -> None:
        br = "\n"
        print(f"{br}{('-'*length + br)*lines}", end=br)
        try:
            yield
        finally:
            print(f"{br}{('-'*length + br)*lines}", end=br)

    @staticmethod
    def print_sep(text: str, lines: int = 1, length: int = 150) -> None:
        with CommandLine.surround_sep(lines=lines, length=length):
            print(text)
