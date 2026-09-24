import time
from collections.abc import Callable

import httpx

MAX_RETRIES = 3


class ProviderError(Exception):
    pass


def post_json(
    url: str,
    headers: dict[str, str],
    body: dict,
    sleep: Callable[[float], None] = time.sleep,
) -> dict:
    for attempt in range(MAX_RETRIES + 1):
        response = httpx.post(url, headers=headers, json=body, timeout=300)
        if response.status_code == 429 or response.status_code >= 500:
            if attempt < MAX_RETRIES:
                sleep(2**attempt)
                continue
        if response.status_code >= 400:
            raise ProviderError(f"Provider returned HTTP {response.status_code}: {response.text}")
        return response.json()
    raise AssertionError("unreachable")
