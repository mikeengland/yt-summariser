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
- Model: `--model`, default `gpt-5` (check this is a model your account can use)
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

Local models have small context windows. Transcripts over 6,000 estimated tokens are chunked
automatically; raise or lower that with `--max-context-tokens`.

## Retries

HTTP 429 and 5xx responses are retried up to 3 times with exponential backoff (1s, 2s, 4s).
Other errors (for example a 401 from a bad key) fail immediately.
