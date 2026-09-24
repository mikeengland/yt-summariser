from yt_summariser.transcript.models import Segment

SYSTEM_PROMPT = """You summarise YouTube video transcripts. Each transcript line starts with a timestamp marker like [02:05].
Reply in exactly this Markdown format and nothing else:

## TL;DR
<2-3 sentences>

## Key points
- <a key point> [02:05]

Give 5-10 key points. End each key point with the marker of the moment in the transcript it
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

MERGE_SYSTEM_PROMPT = """You are given bullet-point notes from consecutive parts of one YouTube video,
with timestamp markers like [02:05]. Merge them into a single summary. Reply in exactly this Markdown format:

## TL;DR
<2-3 sentences>

## Key points
- <a key point> [02:05]

Give 5-10 key points, keeping the timestamp markers from the notes."""
