---
status: accepted
---
# Let the LLM cite timestamps, then validate them; keep partial summaries

The transcript is sent with inline `[mm:ss]` markers and the model cites them in each key point; the tool turns them into `youtu.be/ID?t=SECONDS` links. Models hallucinate timestamps, so every cited time is checked against the video's duration and invalid ones are dropped rather than emitted as broken links. If the output is malformed we retry once, then write whatever validates with a warning: a mostly good Summary beats none. Failed LLM calls (after retries) never leave a partial file.

## Considered Options

- Matching key points back to transcript segments after the fact: no hallucination risk, but fuzzy matching is brittle and adds a second failure mode.
