import time
from collections.abc import Callable

from yt_summariser.providers.http import ProviderError, post_json

CUT_OFF_MESSAGE = (
    "The model's response was cut off because the prompt and answer did not fit its context "
    "window. Lower --max-context-tokens. For Ollama, also raise its window, "
    "e.g. OLLAMA_CONTEXT_LENGTH=16384 ollama serve (the default is 4096)."
)


class OpenAICompatibleProvider:
    def __init__(
        self,
        base_url: str,
        api_key: str | None,
        model: str,
        sleep: Callable[[float], None] = time.sleep,
        extra_body: dict | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.sleep = sleep
        self.extra_body = extra_body or {}

    def complete(self, system: str, prompt: str) -> str:
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        reply = post_json(
            f"{self.base_url}/chat/completions",
            headers,
            {
                "model": self.model,
                **self.extra_body,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
            },
            self.sleep,
        )
        choice = reply["choices"][0]
        if choice.get("finish_reason") == "length":
            raise ProviderError(CUT_OFF_MESSAGE)
        return choice["message"]["content"]
