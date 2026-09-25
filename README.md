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

`--provider` is required. Without `-o/--out-dir` the note is printed to stdout; with it, the note is written there (created if missing) and its path is printed. See
[docs/providers.md](docs/providers.md) for each provider's environment variables and errors.

| Flag | Meaning |
| --- | --- |
| `-o, --out-dir DIR` | Where to write the note. Omit to print it to stdout. |
| `--provider claude\|openai\|ollama` | Who writes the summary. **Required** (except with `--transcript-only`). |
| `--model NAME` | Model to use. Defaulted for claude/openai, required for ollama. |
| `--base-url URL` | Override the provider's API endpoint. |
| `--source auto\|captions\|whisper` | Transcript source. `auto` = manual captions, then auto captions, then Whisper. |
| `--transcript-only` | Write `<title>.transcript.md` and skip the LLM. |
| `--force` | Overwrite an identical existing note. |
| `--no-cache` | Ignore cached transcripts. |
| `--detail brief\|standard\|detailed` | How thorough the summary is: 3-5, 5-10 or 10-20 key points. Defaults from length: brief under 10 min, standard under an hour, detailed beyond. |
| `--language LANG` | Language of the summary (default English). |
| `--max-context-tokens N` | Chunk transcripts longer than this before summarising. |
| `--cookies-from-browser B` | Pass browser cookies to yt-dlp for restricted videos. |

## Ollama: set its context window

The tool assumes a **16k-token context window** for Ollama and sends transcripts of up to
12,000 estimated tokens in one request (longer ones are split, summarised in chunks and merged).
Ollama itself defaults to a **4096-token** window and the tool cannot change that for you, so raise it
when you start Ollama:

```console
# Terminal: quit the Ollama menu-bar app first, then
OLLAMA_CONTEXT_LENGTH=16384 ollama serve

# macOS menu-bar app: set it for the app, then restart the app
launchctl setenv OLLAMA_CONTEXT_LENGTH 16384
```

Check it took effect with `ollama ps` (the `CONTEXT` column should say `16384`). A 12B model such as
`gemma4:12b` used about 8.4 GB at 16k on a 16 GB Mac.

If you would rather keep Ollama's defaults or use a different window, tell the tool with
`--max-context-tokens`, keeping it at roughly 75% of the window:

```console
yts URL -o vault --provider ollama --model llama3.2 --max-context-tokens 2500   # default 4096 window
yts URL -o vault --provider ollama --model gemma4:12b --max-context-tokens 24000 # 32k window
```

If the window is too small you get `The model's response was cut off ...`: lower
`--max-context-tokens` or raise Ollama's window. More detail in [docs/providers.md](docs/providers.md).

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
