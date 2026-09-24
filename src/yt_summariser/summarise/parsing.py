import re
from dataclasses import dataclass, field


@dataclass
class Summary:
    tldr: str = ""
    points: list[str] = field(default_factory=list)

    @property
    def complete(self) -> bool:
        return bool(self.tldr and self.points)

    @property
    def usable(self) -> bool:
        return bool(self.tldr or self.points)

    def missing(self) -> list[str]:
        return [name for name, ok in (("TL;DR", self.tldr), ("key points", self.points)) if not ok]

    def to_markdown(self) -> str:
        parts = []
        if self.tldr:
            parts.append(f"## TL;DR\n{self.tldr}")
        if self.points:
            parts.append("## Key points\n" + "\n".join(f"- {p}" for p in self.points))
        return "\n\n".join(parts)


def parse_summary(text: str) -> Summary:
    tldr = re.search(r"^## TL;DR\s*\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    points = re.search(r"^## Key points\s*\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    bullets = re.findall(r"^\s*[-*] (.+)$", points.group(1), re.M) if points else []
    return Summary(tldr.group(1).strip() if tldr else "", [b.strip() for b in bullets])
