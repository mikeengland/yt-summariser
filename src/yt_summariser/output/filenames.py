import glob
import re
from dataclasses import dataclass
from pathlib import Path

MAX_TITLE_LENGTH = 120
_SUFFIXES = {"summary": ".md", "transcript": ".transcript.md"}


@dataclass(frozen=True)
class Combination:
    video_id: str
    source: str
    provider: str
    model: str


@dataclass(frozen=True)
class OutputPlan:
    path: Path
    skipped: bool = False


def sanitise_title(title: str) -> str:
    title = title.replace(":", " -").replace("/", "-").replace("\\", "-")
    title = re.sub(r'[*?"<>|]', "", title)
    title = re.sub(r"\s+", " ", title).strip()
    return title[:MAX_TITLE_LENGTH].rstrip()


def plan_output_path(
    out_dir: Path,
    title: str,
    combo: Combination,
    force: bool = False,
    kind: str = "summary",
) -> OutputPlan:
    base = sanitise_title(title)
    suffix = _SUFFIXES[kind]
    for candidate in _candidates(out_dir, base, suffix):
        if _read_combination(candidate) == combo:
            return OutputPlan(candidate, skipped=not force)
    plain = out_dir / f"{base}{suffix}"
    if not plain.exists():
        return OutputPlan(plain)
    stem = f"{base} [{combo.source} · {combo.provider}-{combo.model}]"
    if (out_dir / f"{stem}{suffix}").exists():
        stem = f"{stem} ({combo.video_id})"
    return OutputPlan(out_dir / f"{stem}{suffix}")


def _candidates(out_dir: Path, base: str, suffix: str) -> list[Path]:
    plain = out_dir / f"{base}{suffix}"
    long_names = sorted(out_dir.glob(f"{glob.escape(base)} [[]*[]]{glob.escape(suffix)}"))
    return ([plain] if plain.exists() else []) + long_names


def _read_combination(path: Path) -> Combination | None:
    lines = path.read_text().splitlines()
    if not lines or lines[0] != "---":
        return None
    fields: dict[str, str] = {}
    for line in lines[1:]:
        if line == "---":
            break
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    try:
        return Combination(
            fields["video_id"],
            fields["transcript_source"],
            fields["provider"],
            fields["model"],
        )
    except KeyError:
        return None
