import time
from collections.abc import Callable

from yt_summariser.providers.http import post_json

MAX_OUTPUT_TOKENS = 4096


class ClaudeProvider:
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str = "https://api.anthropic.com",
        sleep: Callable[[float], None] = time.sleep,
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.sleep = sleep

    def complete(self, system: str, prompt: str) -> str:
        reply = post_json(
            f"{self.base_url}/v1/messages",
            {"x-api-key": self.api_key, "anthropic-version": "2023-06-01"},
            {
                "model": self.model,
                "max_tokens": MAX_OUTPUT_TOKENS,
                "system": system,
                "messages": [{"role": "user", "content": prompt}],
            },
            self.sleep,
        )
        return reply["content"][0]["text"]
