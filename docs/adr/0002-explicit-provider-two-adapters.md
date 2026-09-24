---
status: accepted
---
# Require an explicit provider; two adapters cover three providers

Summaries can come from Claude, OpenAI or a local Ollama model, chosen with a required `--provider` flag: no default and no config file, so credentials and behaviour are never implicit. Missing env vars (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`) fail with an error naming the variable. OpenAI and Ollama share one adapter because Ollama exposes an OpenAI-compatible API (`OPENAI_BASE_URL`, `OLLAMA_HOST` and `--base-url` select the endpoint); Claude has its own adapter. `--model` has defaults for claude and openai but is required for ollama, since local models vary.

## Considered Options

- A default provider from a config file: less typing, but more to document and a hidden source of surprising cost or data flow.
- A separate adapter per provider: more code with no benefit for OpenAI-compatible servers.
