from __future__ import annotations

from ..mixin import ReprMixin


class Pronoun(ReprMixin):
    def __init__(self, subjective: str, objective: str, possessive: str) -> None:
        self.subjective, self.objective, self.possessive = subjective, objective, possessive


class Gender(ReprMixin):
    def __init__(self, name: str, pronoun: Pronoun = None) -> None:
        self.name, self.pronoun = name, pronoun
