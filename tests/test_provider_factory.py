import pytest

from yt_summariser.providers.factory import make_provider
from yt_summariser.providers.http import ProviderError


def test_claude_without_api_key_names_the_missing_variable():
    with pytest.raises(ProviderError) as error:
        make_provider("claude", model=None, env={})

    assert "ANTHROPIC_API_KEY" in str(error.value)


def test_openai_without_api_key_names_the_missing_variable():
    with pytest.raises(ProviderError) as error:
        make_provider("openai", model=None, env={})

    assert "OPENAI_API_KEY" in str(error.value)


def test_claude_uses_documented_default_model():
    provider = make_provider("claude", model=None, env={"ANTHROPIC_API_KEY": "k"})

    assert provider.model == "claude-sonnet-5"
    assert provider.api_key == "k"


def test_openai_honours_base_url_from_environment():
    env = {"OPENAI_API_KEY": "k", "OPENAI_BASE_URL": "http://proxy.local/v1"}

    provider = make_provider("openai", model=None, env=env)

    assert provider.base_url == "http://proxy.local/v1"


def test_ollama_requires_an_explicit_model():
    with pytest.raises(ProviderError, match="--model is required for --provider ollama"):
        make_provider("ollama", model=None, env={})


def test_ollama_needs_no_api_key_and_defaults_to_local_endpoint():
    provider = make_provider("ollama", model="llama3", env={})

    assert provider.model == "llama3"
    assert provider.api_key is None
    assert provider.base_url == "http://localhost:11434/v1"


def test_ollama_base_url_prefers_flag_over_environment():
    env = {"OLLAMA_HOST": "http://gpu-box:11434"}

    from_env = make_provider("ollama", model="m", env=env)
    from_flag = make_provider("ollama", model="m", env=env, base_url="http://other:1234/v1")

    assert from_env.base_url == "http://gpu-box:11434/v1"
    assert from_flag.base_url == "http://other:1234/v1"


def test_openai_uses_documented_default_model():
    provider = make_provider("openai", model=None, env={"OPENAI_API_KEY": "k"})

    assert provider.model == "gpt-6-luna"


def test_ollama_requests_turn_thinking_off():
    from fake_server import FakeServer

    reply = {"choices": [{"message": {"content": "ok"}}]}
    with FakeServer([(200, reply)]) as server:
        provider = make_provider("ollama", model="gemma4:12b", env={}, base_url=server.url)

        provider.complete(system="s", prompt="p")

    assert server.requests[0]["body"]["reasoning_effort"] == "none"


def test_openai_requests_do_not_send_reasoning_settings():
    from fake_server import FakeServer

    reply = {"choices": [{"message": {"content": "ok"}}]}
    with FakeServer([(200, reply)]) as server:
        provider = make_provider("openai", model=None, env={"OPENAI_API_KEY": "k"}, base_url=server.url)

        provider.complete(system="s", prompt="p")

    assert "reasoning_effort" not in server.requests[0]["body"]
