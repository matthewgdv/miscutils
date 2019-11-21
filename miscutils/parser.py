from __future__ import annotations

from typing import Union, List, Tuple, Callable

from subtypes import Str


class NestedParser:
    def __repr__(self) -> str:
        return f"{type(self).__name__}(text={self.text}), children={len(self)}"

    def __str__(self) -> str:
        return self.text

    def __len__(self) -> int:
        return len(self.children)

    def __iter__(self) -> NestedParser:
        self.__iter = iter(self.children)
        return self

    def __next__(self) -> NestedParser:
        return next(self.__iter)

    def __getitem__(self, key: int) -> Union[List[NestedParser], NestedParser]:
        return self.children[key]

    def __init__(self, text: str, identifier_tags: Tuple[str, str] = ("(", ")"), ignore_between_tags: List[Tuple[str, str]] = None, parent: NestedParser = None) -> None:
        self.text = text[1:-1] if parent is not None else text
        self.parent = parent
        self.identifiers = identifier_tags
        self.ignore = ignore_between_tags

        self._starts = Str(self.text).find_all(self.identifiers[0], overlapping=False, not_within=self.ignore)
        self._ends = Str(self.text).find_all(self.identifiers[1], overlapping=False, not_within=self.ignore)

        outer_starts = []
        outer_ends = []
        counter = 0
        for index in range(len(self.text)):
            if index in self._starts:
                if not counter:
                    outer_starts.append(index)
                counter += 1
            if index in self._ends:
                counter -= 1
                if not counter:
                    outer_ends.append(index)
                if counter < 0:
                    raise ValueError(f"Mismatched identifiers in {self.text}. An instance of '{self.identifiers[1]}' closes without first opening with '{self.identifiers[0]}'")
        if counter:
            raise ValueError(f"Mismatched identifiers in {self.text}. An instance of '{self.identifiers[0]}' opens without later being closed by '{self.identifiers[1]}'")

        self.indices = [(first, second) for first, second in zip(outer_starts, outer_ends)]
        self.substrings = [self.text[start: end + 1] for start, end in self.indices]
        self.children = [NestedParser(substring, identifier_tags=identifier_tags, ignore_between_tags=ignore_between_tags, parent=self) for substring in self.substrings]

    def apply_outward(self, func: Callable) -> str:
        return "".join([char if char not in self.identifiers else "" for char in self.__apply_deeper(func)])

    def __apply_deeper(self, func: Callable) -> str:
        if self.children:
            mutated = [child.__apply_deeper(func) for child in self.children]
            mutable = Str(self.text)
            for index, (start, end) in enumerate(self.indices):
                mutable[start + 1:end] = mutated[index]
            return str(func(mutable))
        return str(func(self.text))

    def visualize(self, spacing: int = 150) -> None:
        def visualise_dict(tree: dict, spaces: int = 150, lvl: int = 1, title: bool = True) -> None:
            for key in sorted(tree):
                if title and key == sorted(tree)[0]:
                    print("{:<{spacing}} {:<15}".format("KEY", "DEPTH", spacing=spacing))
                    print("-" * (spacing + 10))

                indent = "  " * lvl
                print("{:<{spacing}} {:<15}".format(f"{indent}{key}", lvl, spacing=spacing))

                if type(tree[key]) == dict:
                    visualise_dict(tree[key], spaces=spaces, title=False, lvl=lvl + 1)

        return visualise_dict({self.text: self.__fetch_deeper()}, spaces=spacing)

    def __fetch_deeper(self) -> dict:
        if self.children is not None:
            content = {}
            for index, child in enumerate(self.children):
                content[child.text] = child.__fetch_deeper()
            return content
        else:
            return {}
