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
        system, user = MERGE_SYSTEM_PROMPT + instruction, "\n\n".join(notes)
    for _ in range(ATTEMPTS):
        summary = parse_summary(provider.complete(system, user))
        if summary.complete:
            break
    return summary
