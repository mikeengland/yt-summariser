from fake_server import FakeServer

from yt_summariser.providers.openai_compatible import OpenAICompatibleProvider

OPENAI_REPLY = {"choices": [{"message": {"content": "the summary"}}]}


def test_openai_compatible_adapter_sends_expected_request_and_returns_text():
    with FakeServer([(200, OPENAI_REPLY)]) as server:
        provider = OpenAICompatibleProvider(server.url, api_key="sk-test", model="gpt-x")

        text = provider.complete(system="be brief", prompt="summarise this")

    request = server.requests[0]
    assert text == "the summary"
    assert request["path"] == "/chat/completions"
    assert request["headers"]["Authorization"] == "Bearer sk-test"
    assert request["body"] == {
        "model": "gpt-x",
        "messages": [
            {"role": "system", "content": "be brief"},
            {"role": "user", "content": "summarise this"},
        ],
    }


def test_claude_adapter_sends_expected_request_and_returns_text():
    from yt_summariser.providers.claude import ClaudeProvider

    reply = {"content": [{"type": "text", "text": "claude summary"}]}
    with FakeServer([(200, reply)]) as server:
        provider = ClaudeProvider(api_key="ak-test", model="claude-x", base_url=server.url)

        text = provider.complete(system="be brief", prompt="summarise this")

    request = server.requests[0]
    assert text == "claude summary"
    assert request["path"] == "/v1/messages"
    assert request["headers"]["x-api-key"] == "ak-test"
    assert request["headers"]["anthropic-version"] == "2023-06-01"
    assert request["body"]["model"] == "claude-x"
    assert request["body"]["system"] == "be brief"
    assert request["body"]["messages"] == [{"role": "user", "content": "summarise this"}]
    assert request["body"]["max_tokens"] > 0


def test_transient_errors_are_retried_with_backoff_then_succeed():
    sleeps = []
    responses = [(429, {"error": "slow down"}), (503, {"error": "busy"}), (200, OPENAI_REPLY)]
    with FakeServer(responses) as server:
        provider = OpenAICompatibleProvider(
            server.url, api_key="k", model="m", sleep=sleeps.append
        )

        text = provider.complete(system="s", prompt="p")

    assert text == "the summary"
    assert len(server.requests) == 3
    assert sleeps == [1, 2]


def test_gives_up_after_three_retries_with_a_clear_error():
    import pytest

    from yt_summariser.providers.http import ProviderError

    with FakeServer([(503, {"error": "busy"})] * 4) as server:
        provider = OpenAICompatibleProvider(server.url, "k", "m", sleep=lambda s: None)

        with pytest.raises(ProviderError, match="503"):
            provider.complete(system="s", prompt="p")

    assert len(server.requests) == 4


def test_client_errors_are_not_retried():
    import pytest

    from yt_summariser.providers.http import ProviderError

    with FakeServer([(401, {"error": "bad key"})]) as server:
        provider = OpenAICompatibleProvider(server.url, "k", "m", sleep=lambda s: None)

        with pytest.raises(ProviderError, match="401"):
            provider.complete(system="s", prompt="p")

    assert len(server.requests) == 1


def test_response_cut_off_by_the_context_window_is_a_clear_error():
    import pytest

    from yt_summariser.providers.http import ProviderError

    cut_off = {"choices": [{"message": {"content": ""}, "finish_reason": "length"}]}
    with FakeServer([(200, cut_off)]) as server:
        provider = OpenAICompatibleProvider(server.url, "k", "m", sleep=lambda s: None)

        with pytest.raises(ProviderError) as error:
            provider.complete(system="s", prompt="p")

    assert str(error.value) == (
        "The model's response was cut off because the prompt and answer did not fit its context "
        "window. Lower --max-context-tokens. For Ollama, also raise its window, "
        "e.g. OLLAMA_CONTEXT_LENGTH=16384 ollama serve (the default is 4096)."
    )
