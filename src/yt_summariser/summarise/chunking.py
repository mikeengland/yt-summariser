from yt_summariser.transcript.models import Segment

CHARS_PER_TOKEN = 4


def estimate_tokens(text: str) -> int:
    return -(-len(text) // CHARS_PER_TOKEN)


def plan_chunks(segments: list[Segment], budget_tokens: int) -> list[list[Segment]]:
    chunks: list[list[Segment]] = []
    current: list[Segment] = []
    used = 0
    for segment in segments:
        cost = estimate_tokens(segment.text)
        if current and used + cost > budget_tokens:
            chunks.append(current)
            current, used = [], 0
        current.append(segment)
        used += cost
    if current:
        chunks.append(current)
    return chunks
