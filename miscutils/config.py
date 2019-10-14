from __future__ import annotations

from typing import Any

from maybe import Maybe
from pathmagic import PathLike, File, Dir
from miscutils import NameSpaceDict

from .misc import executed_within_user_tree


class Config:
    """
    A config class that abstracts away the process of creating, reading from, and writing to, a json config file within an OS-appropriate appdata dir.
    The directory itself can be accessed through the 'Config.appdata' attribute.
    The data held by the config file can be accessed through 'Config.data' attribute, holding a special kind of dictionary that allows its items to be accessed through attribute access.
    Any changes made to this dictionary will not be persisted until Config.save() is called. Config.save() is automatically called upon exiting when this class is used as a context manager.
    This class is intended to be subclassed and can be used simply by providing the 'Config.app_name' (string) and 'Config.default' (dict) class attributes.
    Alternatively, this class can be used directly and these can be provided as constructor arguments instead.
    """
    app_name: str = None
    default: dict = None

    def __init__(self, app_name: str = None, default: dict = None, systemwide: bool = None) -> None:
        if app_name is not None:
            self.app_name = app_name

        if default is not None:
            self.default = default

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
        """Clear the data in the config file."""
        self.data = None

    def import_(self, path: PathLike) -> None:
        """Import the config file at the given path."""
        file = File.from_pathlike(path)

        if file.extension != "json":
            raise TypeError(f"Config file to import must be type 'json'.")

        self.data = file.contents

    def export(self, path: PathLike) -> None:
        """Export the config file to the given path."""
        self.file.copy(path)

    def export_to(self, path: PathLike) -> None:
        """Export the config file to the given directory, keeping its name ('config.json')."""
        self.file.copy_to(path)

    def start(self) -> File:
        """Initialize the config file with the default application for json files."""
        return self.file.start()

    def save(self) -> None:
        """Persist the changes to the 'Config.data' attribute to the config file."""
        self.file.contents = self.data
