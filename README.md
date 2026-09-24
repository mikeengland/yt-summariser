# yt-summariser

Downloads, transcribes and summarises key points from YouTube videos into Markdown notes
(built with an Obsidian vault in mind).

```console
$ yts "https://www.youtube.com/watch?v=jNQXAC9IVRw" -o ~/Vault/YouTube --provider claude
/Users/you/Vault/YouTube/Me at the zoo.md
```

## Install

Requires Python 3.14+ and [uv](https://docs.astral.sh/uv/).

```console
uv tool install .                    # captions only
uv tool install ".[whisper]"         # + local Whisper fallback (faster-whisper)
```

The command is available as `yts` and `yt-summariser`. Run `yts --help` for all options.

## Usage

`-o/--out-dir` is required (created if missing) and so is `--provider`. See
[docs/providers.md](docs/providers.md) for each provider's environment variables and errors.

| Flag | Meaning |
| --- | --- |
| `-o, --out-dir DIR` | Where to write the note. **Required.** |
| `--provider claude\|openai\|ollama` | Who writes the summary. **Required** (except with `--transcript-only`). |
| `--model NAME` | Model to use. Defaulted for claude/openai, required for ollama. |
| `--base-url URL` | Override the provider's API endpoint. |
| `--source auto\|captions\|whisper` | Transcript source. `auto` = manual captions, then auto captions, then Whisper. |
| `--transcript-only` | Write `<title>.transcript.md` and skip the LLM. |
| `--force` | Overwrite an identical existing note. |
| `--no-cache` | Ignore cached transcripts. |
| `--language LANG` | Language of the summary (default English). |
| `--max-context-tokens N` | Chunk transcripts longer than this before summarising. |
| `--cookies-from-browser B` | Pass browser cookies to yt-dlp for restricted videos. |

## What you get

A note named after the video title, with YAML frontmatter (`title`, `url`, `video_id`, `channel`,
`published`, `duration`, `tags`, `transcript_source`, `provider`, `model`), a link back to the video,
a TL;DR, and key points whose timestamps link to `youtu.be/ID?t=SECONDS`.

### Comparing sources or models on one video

Nothing is overwritten. If `Title.md` already exists for a different combination, the new note is
written as `Title [<source> · <provider>-<model>].md`. Re-running an identical combination is
skipped with a warning unless you pass `--force`.

```console
yts URL -o vault --provider claude --source captions
yts URL -o vault --provider claude --source whisper     # -> Title [whisper · claude-...].md
yts URL -o vault --transcript-only --source captions    # dump the raw transcripts to diff
yts URL -o vault --transcript-only --source whisper
```

Transcripts are cached per video and source in your platform cache directory
(`~/Library/Caches/yt-summariser` on macOS), so re-summarising does not refetch or re-transcribe.

## Development

```console
uv run pytest
```

Design decisions are recorded in [docs/adr/](docs/adr/) and the vocabulary in [CONTEXT.md](CONTEXT.md).
