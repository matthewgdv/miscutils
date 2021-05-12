from __future__ import annotations

import pyinstrument


class Profiler(pyinstrument.Profiler):
    """A subclass of pyinstrument.Profiler with a better __str__ method."""

    def __str__(self) -> str:
        return self.output_text(unicode=True, color=True)
