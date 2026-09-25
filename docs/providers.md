# Providers

Pick one with `--provider`. There is no default and no config file: flags and environment variables
only. If a required variable is missing the tool exits with code 1 and a one-line error.

## claude

- Environment: `ANTHROPIC_API_KEY` (required)
- Model: `--model`, default `claude-sonnet-5`

```console
export ANTHROPIC_API_KEY=sk-ant-...
yts URL -o vault --provider claude
```

Without the key:

```
error: --provider claude needs ANTHROPIC_API_KEY to be set. Export it first, e.g. `export ANTHROPIC_API_KEY=...`.
```

## openai

- Environment: `OPENAI_API_KEY` (required), `OPENAI_BASE_URL` (optional)
- Model: `--model`, default `gpt-6-luna`
- Any OpenAI-compatible server works via `OPENAI_BASE_URL` or `--base-url`.

```console
export OPENAI_API_KEY=sk-...
yts URL -o vault --provider openai
```

Without the key:

```
error: --provider openai needs OPENAI_API_KEY to be set. Export it first, e.g. `export OPENAI_API_KEY=...`.
```

## ollama

- Environment: none required. `OLLAMA_HOST` (optional, default `http://localhost:11434`)
- Model: `--model` is **required**, e.g. `llama3.2`
- `--base-url` overrides the full endpoint (default `<OLLAMA_HOST>/v1`).

```console
ollama pull llama3.2
yts URL -o vault --provider ollama --model llama3.2
```

Without a model:

```
error: --model is required for --provider ollama (e.g. --model llama3).
```

Thinking is turned off for Ollama requests (`reasoning_effort: none`): summarising doesn't need it, and on
thinking models such as `gemma4:12b` it made runs about 6x slower.

### Context windows and long videos

Ollama's default context window is **4096 tokens**, even though models like `gemma4:12b` support far
more, and its OpenAI-compatible endpoint (which this tool uses) ignores per-request window settings
(checked with Ollama 0.34). So the window has to be set on the server, and the tool's budget has to
match it.

The tool's default Ollama budget is **12,000 estimated tokens**, which assumes a 16k window. Transcripts
within the budget go in as one request. Longer ones are split into chunks (map), the chunk notes are
condensed in groups that each fit the budget until they fit (reduce), and the final summary is written
from those notes.

```console
OLLAMA_CONTEXT_LENGTH=16384 ollama serve      # quit the menu-bar app first
yts URL -o vault --provider ollama --model gemma4:12b
```

Measured on a 16 GB M1 Pro with `gemma4:12b` (8.4 GB loaded at 16k context), a 21-minute video took
2m29s as one request versus 3m22s chunked at the old 2,500-token budget, with better timestamp coverage.

To use a different window, pass `--max-context-tokens` at about 75% of it (2500 for the default 4096
window, 24000 for 32k). If the window is smaller than the budget, the model's response is cut off and
the tool stops with an error telling you to lower `--max-context-tokens` or raise Ollama's window.

## Retries

HTTP 429 and 5xx responses are retried up to 3 times with exponential backoff (1s, 2s, 4s).
Other errors (for example a 401 from a bad key) fail immediately.
