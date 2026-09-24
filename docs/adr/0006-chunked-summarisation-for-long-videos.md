---
status: accepted
---
# Summarise in one request when it fits, otherwise chunk and merge

Long talks can exceed a model's context, especially local Ollama models. The tool estimates tokens and sends the whole transcript in one request when it fits a per-provider budget (overridable with `--max-context-tokens`). Otherwise it splits on paragraph or time boundaries, summarises each chunk keeping its timestamps, then runs a final merge pass. Chunk summaries are cached so a failed run resumes instead of restarting. Failing on long videos and silently truncating were both rejected.
