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
more. Prompt and answer must both fit, so by default the tool splits Ollama transcripts into chunks of
about 2,500 tokens (map), condenses the chunk notes in groups that each fit the budget until the
combined notes fit (reduce), and then writes the final summary from those notes. This works everywhere
but is slower and gives less specific results than one request over the whole transcript.

If your machine has the memory, raise Ollama's window and tell the tool to use it. Measured on a
16 GB M1 Pro with `gemma4:12b` (8.4 GB loaded at 16k context), a 21-minute video went from 3m22s
chunked to 2m29s as one request, with better timestamp coverage:

```console
OLLAMA_CONTEXT_LENGTH=16384 ollama serve      # quit the menu-bar app first
yts URL -o vault --provider ollama --model gemma4:12b --max-context-tokens 12000
```

Keep `--max-context-tokens` comfortably below the window (about 75%) to leave room for the prompt and
the answer. If a response is cut off, the tool stops with an error telling you to lower it.

## Retries

HTTP 429 and 5xx responses are retried up to 3 times with exponential backoff (1s, 2s, 4s).
Other errors (for example a 401 from a bad key) fail immediately.
