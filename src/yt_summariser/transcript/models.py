from dataclasses import dataclass


@dataclass(frozen=True)
class Segment:
    start: float
    text: str
