from yt_summariser.summarise.chunking import estimate_tokens, plan_chunks
from yt_summariser.summarise.parsing import Summary, parse_summary
from yt_summariser.summarise.prompts import (
    CHUNK_SYSTEM_PROMPT,
    MERGE_SYSTEM_PROMPT,
    SYSTEM_PROMPT,
    format_transcript,
)

ATTEMPTS = 2


def summarise(segments, provider, budget_tokens: int, language: str = "English") -> Summary:
    instruction = f"\n\nWrite the summary in {language}."
    transcript_text = format_transcript(segments)
    if estimate_tokens(transcript_text) <= budget_tokens:
        system, user = SYSTEM_PROMPT + instruction, transcript_text
    else:
        notes = [
            provider.complete(CHUNK_SYSTEM_PROMPT, format_transcript(chunk))
            for chunk in plan_chunks(segments, budget_tokens)
        ]
        notes = _reduce_until_it_fits(notes, provider, budget_tokens)
        system, user = MERGE_SYSTEM_PROMPT + instruction, "\n\n".join(notes)
    for _ in range(ATTEMPTS):
        summary = parse_summary(provider.complete(system, user))
        if summary.complete:
            break
    return summary


def _reduce_until_it_fits(notes: list[str], provider, budget_tokens: int) -> list[str]:
    """Condense groups of notes until the final merge prompt fits the context budget."""
    while len(notes) > 1 and sum(estimate_tokens(n) for n in notes) > budget_tokens:
        groups = _group_within_budget(notes, budget_tokens)
        if len(groups) == len(notes):
            break  # notes too big to combine; the final merge will surface any overflow
        notes = [provider.complete(CHUNK_SYSTEM_PROMPT, "\n\n".join(group)) for group in groups]
    return notes


def _group_within_budget(notes: list[str], budget_tokens: int) -> list[list[str]]:
    groups: list[list[str]] = []
    used = 0
    for note in notes:
        cost = estimate_tokens(note)
        if groups and used + cost <= budget_tokens:
            groups[-1].append(note)
            used += cost
        else:
            groups.append([note])
            used = cost
    return groups
