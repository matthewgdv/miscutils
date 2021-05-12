from __future__ import annotations

from functools import cached_property
from typing import Type

from gender_guesser.detector import Detector as GenderDetector

from ..mixin import ReprMixin


class GenderMeta(type):
    Pronoun: Type[Gender.Pronouns]

    def from_name(cls, name: str) -> Gender:
        return cls._mappings.get(cls._detector.get_gender(name=name))

    @cached_property
    def male(cls) -> Gender:
        return cls(name="male", pronoun=cls.Pronoun(subjective="he", objective="him", possessive="his"))

    @cached_property
    def female(cls) -> Gender:
        return cls(name="female", pronoun=cls.Pronoun(subjective="she", objective="her", possessive="her"))

    @cached_property
    def non_binary(cls) -> Gender:
        return cls(name="enby", pronoun=cls.Pronoun(subjective="they", objective="them", possessive="their"))

    @cached_property
    def unknown(cls) -> Gender:
        return cls(name="unknown")

    @cached_property
    def _detector(cls) -> GenderDetector:
        return GenderDetector(case_sensitive=False)

    @cached_property
    def _mappings(cls) -> dict[str, Gender]:
        return {
            "male": cls.male,
            "mostly_male": cls.male,
            "female": cls.female,
            "mostly_female": cls.female,
            "andy": cls.non_binary,
            "unknown": cls.unknown
        }


class Gender(ReprMixin, metaclass=GenderMeta):
    class Pronouns(ReprMixin):
        def __init__(self, subjective: str, objective: str, possessive: str) -> None:
            self.subjective, self.objective, self.possessive = subjective, objective, possessive

    def __init__(self, name: str, pronouns: Pronouns = None) -> None:
        self.name, self.pronouns = name, pronouns
