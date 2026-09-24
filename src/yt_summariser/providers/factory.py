from collections.abc import Mapping

from yt_summariser.providers.claude import ClaudeProvider
from yt_summariser.providers.http import ProviderError
from yt_summariser.providers.openai_compatible import OpenAICompatibleProvider

DEFAULT_CLAUDE_MODEL = "claude-sonnet-5"
DEFAULT_OPENAI_MODEL = "gpt-5"
DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"
DEFAULT_OLLAMA_HOST = "http://localhost:11434"


def _require(env: Mapping[str, str], name: str, provider: str) -> str:
    value = env.get(name)
    if not value:
        raise ProviderError(
            f"--provider {provider} needs {name} to be set. Export it first, "
            f"e.g. `export {name}=...`."
        )
    return value


def make_provider(name: str, model: str | None, env: Mapping[str, str], base_url: str | None = None):
    if name == "claude":
        key = _require(env, "ANTHROPIC_API_KEY", "claude")
        return ClaudeProvider(api_key=key, model=model or DEFAULT_CLAUDE_MODEL)
    if name == "openai":
        key = _require(env, "OPENAI_API_KEY", "openai")
        url = base_url or env.get("OPENAI_BASE_URL") or DEFAULT_OPENAI_BASE_URL
        return OpenAICompatibleProvider(url, key, model or DEFAULT_OPENAI_MODEL)
    if name == "ollama":
        if not model:
            raise ProviderError("--model is required for --provider ollama (e.g. --model llama3).")
        host = env.get("OLLAMA_HOST", DEFAULT_OLLAMA_HOST).rstrip("/")
        return OpenAICompatibleProvider(base_url or f"{host}/v1", None, model)
    raise ProviderError(f"Unknown provider: {name}")
