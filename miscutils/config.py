from __future__ import annotations

from typing import Any

from maybe import Maybe
from pathmagic import PathLike, File, Dir
from miscutils import NameSpaceDict

from .misc import executed_within_user_tree


class Config:
    app_name: str = None
    default: dict = None

    def __init__(self, systemwide: bool = None) -> None:
        self.appdata = Dir.from_appdata(app_name=self.app_name, app_author="pythondata", systemwide=Maybe(systemwide).else_(not executed_within_user_tree()))
        self.file = self.appdata.new_file(name="config", extension="json")
        self.data: NameSpaceDict = Maybe(self.file.contents).else_(NameSpaceDict(self.default or {}))

    def __repr__(self) -> str:
        return f"{type(self).__name__}({', '.join([f'{attr}={repr(val)}' for attr, val in self.__dict__.items() if not attr.startswith('_')])})"

    def __enter__(self) -> Config:
        return self

    def __exit__(self, ex_type: Any, ex_value: Any, ex_traceback: Any) -> None:
        if ex_type is None:
            self.save()

    def clear(self) -> None:
        self.data = None
        self.save()

    def save(self) -> None:
        self.file.contents = self.data

    def import_(self, path: PathLike) -> None:
        file = File.from_pathlike(path)

        if file.extension != "json":
            raise TypeError(f"Config file to import must be type 'json'.")

        self.data = file.contents

    def export(self, path: PathLike) -> None:
        self.file.copy(path)

    def export_to(self, path: PathLike) -> None:
        self.file.copy_to(path)

    def open(self) -> File:
        return self.file.open()
