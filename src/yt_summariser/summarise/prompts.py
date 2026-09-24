from yt_summariser.transcript.models import Segment

SYSTEM_PROMPT = """You summarise YouTube video transcripts. The transcript has [mm:ss] markers.
Reply in exactly this Markdown format and nothing else:

## TL;DR
<2-3 sentences>

## Key points
- <a key point> [mm:ss]

Give 5-10 key points. End each key point with the [mm:ss] (or [h:mm:ss]) marker of the moment
in the transcript it comes from. Only cite markers that appear in the transcript."""


def format_timestamp(seconds: float) -> str:
    total = int(seconds)
    hours, rest = divmod(total, 3600)
    minutes, secs = divmod(rest, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def format_transcript(segments: list[Segment]) -> str:
    return "\n".join(f"[{format_timestamp(s.start)}] {s.text}" for s in segments)

CHUNK_SYSTEM_PROMPT = """You are given one part of a longer YouTube video transcript with [mm:ss] markers.
List its key points as Markdown bullets, each ending with the [mm:ss] (or [h:mm:ss]) marker of the
moment it comes from. Only cite markers that appear in the text."""

MERGE_SYSTEM_PROMPT = """You are given bullet-point notes from consecutive parts of one YouTube video,
with [mm:ss] markers. Merge them into a single summary. Reply in exactly this Markdown format:

## TL;DR
<2-3 sentences>

## Key points
- <a key point> [mm:ss]

Give 5-10 key points, keeping the [mm:ss] markers from the notes."""
