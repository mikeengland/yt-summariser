from yt_summariser.transcript.models import Segment

DETAIL_LEVELS = ("brief", "standard", "detailed")

# (TL;DR length, number of key points) for each detail level.
_DETAIL = {
    "brief": ("1 sentence", "3-5"),
    "standard": ("2-3 sentences", "5-10"),
    "detailed": ("a paragraph of 4-6 sentences", "10-20"),
}

# Videos shorter than these many seconds default to brief and standard respectively.
_BRIEF_UNDER = 10 * 60
_STANDARD_UNDER = 60 * 60


def detail_for_duration(seconds: int) -> str:
    if seconds <= 0:
        return "standard"  # unknown duration
    if seconds < _BRIEF_UNDER:
        return "brief"
    if seconds < _STANDARD_UNDER:
        return "standard"
    return "detailed"


def system_prompt(detail: str) -> str:
    tldr, points = _DETAIL[detail]
    return f"""You summarise YouTube video transcripts. Each transcript line starts with a timestamp marker like [02:05].
Reply in exactly this Markdown format and nothing else:

## TL;DR
<{tldr}>

## Key points
- <a key point> [02:05]

Give {points} key points. End each key point with the marker of the moment in the transcript it
comes from, copied exactly, e.g. [02:05] or [1:02:05]. Only cite markers that appear in the transcript."""


def format_timestamp(seconds: float) -> str:
    total = int(seconds)
    hours, rest = divmod(total, 3600)
    minutes, secs = divmod(rest, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def format_transcript(segments: list[Segment]) -> str:
    return "\n".join(f"[{format_timestamp(s.start)}] {s.text}" for s in segments)

CHUNK_SYSTEM_PROMPT = """You are given one part of a longer YouTube video transcript with timestamp markers like [02:05].
List its key points as Markdown bullets, each ending with the marker (e.g. [02:05]) of the
moment it comes from. Only cite markers that appear in the text."""



def merge_system_prompt(detail: str) -> str:
    tldr, points = _DETAIL[detail]
    return f"""You are given bullet-point notes from consecutive parts of one YouTube video,
with timestamp markers like [02:05]. Merge them into a single summary. Reply in exactly this Markdown format:

## TL;DR
<{tldr}>

## Key points
- <a key point> [02:05]

Give {points} key points, keeping the timestamp markers from the notes."""
