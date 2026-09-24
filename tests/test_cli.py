import io

from fake_server import FakeServer
from fakes import INFO, MANUAL, FakeWhisper, FakeYouTube

from yt_summariser.cli import run

GOOD_REPLY = {
    "choices": [
        {
            "message": {
                "content": (
                    "## TL;DR\nRust is fast and safe.\n\n"
                    "## Key points\n- No garbage collector [02:05]\n- Ownership rules [05:00]\n"
                )
            }
        }
    ]
}


def invoke(argv, server_url=None, youtube=None, whisper=None, env=None, cache_dir=None, tmp=None):
    stdout, stderr = io.StringIO(), io.StringIO()
    args = list(argv)
    if server_url:
        args += ["--provider", "ollama", "--model", "m", "--base-url", server_url]
    code = run(
        args,
        env=env or {},
        youtube=youtube or FakeYouTube(manual=MANUAL),
        whisper=whisper or FakeWhisper(),
        stdout=stdout,
        stderr=stderr,
        cache_dir=cache_dir,
    )
    return code, stdout.getvalue(), stderr.getvalue()


def test_summarises_a_video_into_a_titled_markdown_file(tmp_path):
    out = tmp_path / "vault"
    with FakeServer([(200, GOOD_REPLY)]) as server:
        code, stdout, _ = invoke([INFO.url, "-o", str(out)], server.url, cache_dir=tmp_path / "c")

    note = out / "How Rust Works.md"
    text = note.read_text()
    assert code == 0
    assert stdout.strip() == str(note)
    assert text.startswith("---\n")
    assert 'title: "How Rust Works"' in text
    assert "video_id: abc123" in text
    assert "transcript_source: manual" in text
    assert "provider: ollama" in text
    assert "model: m" in text
    assert "tags: [youtube]" in text
    assert "# How Rust Works" in text
    assert f"[Watch on YouTube]({INFO.url})" in text
    assert "Rust is fast and safe." in text
    assert "- No garbage collector [02:05](https://youtu.be/abc123?t=125)" in text


def test_missing_out_dir_is_a_clear_usage_error(tmp_path):
    code, stdout, stderr = invoke([INFO.url, "--provider", "ollama", "--model", "m"])

    assert code == 1
    assert stdout == ""
    assert "--out-dir" in stderr


def test_missing_api_key_fails_with_one_actionable_line_and_no_file(tmp_path):
    out = tmp_path / "vault"

    code, stdout, stderr = invoke(
        [INFO.url, "-o", str(out), "--provider", "claude"], cache_dir=tmp_path / "c"
    )

    assert code == 1
    assert stderr.strip() == (
        "error: --provider claude needs ANTHROPIC_API_KEY to be set. "
        "Export it first, e.g. `export ANTHROPIC_API_KEY=...`."
    )
    assert not list(out.glob("*.md")) if out.exists() else True


def test_rerunning_the_same_combination_skips_without_calling_the_provider(tmp_path):
    out = tmp_path / "vault"
    args = [INFO.url, "-o", str(out)]
    with FakeServer([(200, GOOD_REPLY)]) as server:
        invoke(args, server.url, cache_dir=tmp_path / "c")
        note = out / "How Rust Works.md"
        before = note.read_text()

        code, stdout, stderr = invoke(args, server.url, cache_dir=tmp_path / "c")

    assert code == 0
    assert len(server.requests) == 1
    assert note.read_text() == before
    assert f"skipping" in stderr and str(note) in stderr


def test_a_different_source_is_written_alongside_the_earlier_summary(tmp_path):
    out = tmp_path / "vault"
    with FakeServer([(200, GOOD_REPLY), (200, GOOD_REPLY)]) as server:
        invoke([INFO.url, "-o", str(out)], server.url, cache_dir=tmp_path / "c")
        code, stdout, _ = invoke(
            [INFO.url, "-o", str(out), "--source", "whisper"], server.url, cache_dir=tmp_path / "c"
        )

    assert code == 0
    assert (out / "How Rust Works.md").exists()
    assert (out / "How Rust Works [whisper · ollama-m].md").exists()
    assert stdout.strip() == str(out / "How Rust Works [whisper · ollama-m].md")


def test_force_regenerates_and_overwrites_the_duplicate(tmp_path):
    out = tmp_path / "vault"
    second = {"choices": [{"message": {"content": "## TL;DR\nNew take.\n\n## Key points\n- One [01:00]\n"}}]}
    with FakeServer([(200, GOOD_REPLY), (200, second)]) as server:
        invoke([INFO.url, "-o", str(out)], server.url, cache_dir=tmp_path / "c")
        code, _, _ = invoke([INFO.url, "-o", str(out), "--force"], server.url, cache_dir=tmp_path / "c")

    assert code == 0
    assert "New take." in (out / "How Rust Works.md").read_text()
    assert len(list(out.glob("*.md"))) == 1


def test_transcript_only_writes_a_transcript_file_and_needs_no_provider(tmp_path):
    out = tmp_path / "vault"

    code, stdout, _ = invoke([INFO.url, "-o", str(out), "--transcript-only"], cache_dir=tmp_path / "c")

    note = out / "How Rust Works.transcript.md"
    assert code == 0
    assert stdout.strip() == str(note)
    text = note.read_text()
    assert "transcript_source: manual" in text
    assert "[00:00] manual text" in text
    assert not (out / "How Rust Works.md").exists()


def reply(text):
    return (200, {"choices": [{"message": {"content": text}}]})


def test_long_transcripts_are_summarised_in_chunks_then_merged(tmp_path):
    from yt_summariser.transcript.models import Segment

    long_captions = [Segment(i * 60.0, "word " * 80) for i in range(6)]  # ~100 tokens each
    out = tmp_path / "vault"
    responses = [
        reply("chunk-1-notes [00:00]"),
        reply("chunk-2-notes [02:00]"),
        reply("chunk-3-notes [04:00]"),
        (200, GOOD_REPLY),
    ]
    with FakeServer(responses) as server:
        code, _, _ = invoke(
            [INFO.url, "-o", str(out), "--max-context-tokens", "250"],
            server.url,
            youtube=FakeYouTube(manual=long_captions),
            cache_dir=tmp_path / "c",
        )

    merge_prompt = server.requests[-1]["body"]["messages"][1]["content"]
    assert code == 0
    assert len(server.requests) == 4
    assert all(n in merge_prompt for n in ("chunk-1-notes", "chunk-2-notes", "chunk-3-notes"))
    assert "Rust is fast and safe." in (out / "How Rust Works.md").read_text()


def test_malformed_output_is_retried_once(tmp_path):
    out = tmp_path / "vault"
    with FakeServer([reply("Sure! Here is a summary."), (200, GOOD_REPLY)]) as server:
        code, _, stderr = invoke([INFO.url, "-o", str(out)], server.url, cache_dir=tmp_path / "c")

    assert code == 0
    assert len(server.requests) == 2
    assert "Rust is fast and safe." in (out / "How Rust Works.md").read_text()
    assert stderr == ""


def test_still_incomplete_output_is_written_with_what_validates_and_a_warning(tmp_path):
    out = tmp_path / "vault"
    tldr_only = reply("## TL;DR\nRust is fast.\n")
    with FakeServer([tldr_only, tldr_only]) as server:
        code, _, stderr = invoke([INFO.url, "-o", str(out)], server.url, cache_dir=tmp_path / "c")

    text = (out / "How Rust Works.md").read_text()
    assert code == 0
    assert "Rust is fast." in text
    assert "## Key points" not in text
    assert "warning" in stderr and "key points" in stderr


def test_output_with_nothing_usable_is_an_error_and_writes_no_file(tmp_path):
    out = tmp_path / "vault"
    with FakeServer([reply("no idea"), reply("still no idea")]) as server:
        code, _, stderr = invoke([INFO.url, "-o", str(out)], server.url, cache_dir=tmp_path / "c")

    assert code == 1
    assert stderr.startswith("error:")
    assert not list(out.glob("*.md"))


def test_transcripts_are_cached_between_runs(tmp_path):
    out, cache = tmp_path / "vault", tmp_path / "cache"
    youtube = FakeYouTube(manual=MANUAL)
    with FakeServer([(200, GOOD_REPLY), (200, GOOD_REPLY)]) as server:
        invoke([INFO.url, "-o", str(out)], server.url, youtube=youtube, cache_dir=cache)
        invoke([INFO.url, "-o", str(out), "--force"], server.url, youtube=youtube, cache_dir=cache)

    assert youtube.info_calls == 1


def test_no_cache_flag_refetches_the_transcript(tmp_path):
    out, cache = tmp_path / "vault", tmp_path / "cache"
    youtube = FakeYouTube(manual=MANUAL)
    with FakeServer([(200, GOOD_REPLY), (200, GOOD_REPLY)]) as server:
        invoke([INFO.url, "-o", str(out)], server.url, youtube=youtube, cache_dir=cache)
        invoke([INFO.url, "-o", str(out), "--force", "--no-cache"], server.url, youtube=youtube, cache_dir=cache)

    assert youtube.info_calls == 2


def test_different_sources_are_cached_separately(tmp_path):
    out, cache = tmp_path / "vault", tmp_path / "cache"
    youtube = FakeYouTube(manual=MANUAL)
    with FakeServer([(200, GOOD_REPLY), (200, GOOD_REPLY)]) as server:
        invoke([INFO.url, "-o", str(out)], server.url, youtube=youtube, cache_dir=cache)
        invoke([INFO.url, "-o", str(out), "--source", "whisper"], server.url, youtube=youtube, cache_dir=cache)

    assert youtube.info_calls == 2


def test_summary_language_defaults_to_english_and_can_be_overridden(tmp_path):
    with FakeServer([(200, GOOD_REPLY), (200, GOOD_REPLY)]) as server:
        invoke([INFO.url, "-o", str(tmp_path / "a")], server.url, cache_dir=tmp_path / "c")
        invoke([INFO.url, "-o", str(tmp_path / "b"), "--language", "French"], server.url, cache_dir=tmp_path / "c")

    system_prompts = [r["body"]["messages"][0]["content"] for r in server.requests]
    assert "Write the summary in English." in system_prompts[0]
    assert "Write the summary in French." in system_prompts[1]


def test_provider_is_required_for_summaries(tmp_path):
    code, _, stderr = invoke([INFO.url, "-o", str(tmp_path / "v")], cache_dir=tmp_path / "c")

    assert code == 1
    assert "--provider is required" in stderr
    assert "claude, openai or ollama" in stderr
