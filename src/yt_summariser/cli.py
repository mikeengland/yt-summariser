import argparse
import os
import sys
from pathlib import Path

from platformdirs import user_cache_dir

from yt_summariser.output.filenames import Combination, plan_output_path
from yt_summariser.output.render import render_note
from yt_summariser.providers.factory import make_provider
from yt_summariser.providers.http import ProviderError
from yt_summariser.summarise.pipeline import summarise
from yt_summariser.summarise.prompts import format_transcript
from yt_summariser.summarise.timestamps import link_timestamps
from yt_summariser.transcript.cache import TranscriptCache, parse_video_id
from yt_summariser.transcript.whisper import load_whisper
from yt_summariser.transcript.youtube import YtDlpYouTube
from yt_summariser.transcript.selection import TranscriptError, get_transcript


DEFAULT_CONTEXT_BUDGET = {"claude": 150_000, "openai": 100_000, "ollama": 2_500}


class ToolError(Exception):
    pass


class UsageError(Exception):
    pass


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise UsageError(message)


EPILOG = """\
providers (choose one with --provider; there is no default):
  claude   needs ANTHROPIC_API_KEY. Default model: claude-sonnet-5.
  openai   needs OPENAI_API_KEY. Default model: gpt-6-luna. Set OPENAI_BASE_URL (or --base-url)
           to use any OpenAI-compatible server.
  ollama   needs no key, but --model is required (e.g. --model llama3). Endpoint is
           http://localhost:11434/v1; override with OLLAMA_HOST or --base-url.

examples:
  yts URL -o ~/Vault/YouTube --provider claude
  yts URL -o ~/Vault/YouTube --provider ollama --model llama3
  yts URL -o ~/Vault/YouTube --transcript-only --source captions
"""


def build_parser() -> argparse.ArgumentParser:
    parser = _Parser(
        prog="yts",
        description="Summarise a YouTube video into a Markdown note.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument(
        "-o", "--out-dir", required=True, type=Path,
        help="directory to write the note into (created if missing)",
    )
    parser.add_argument(
        "--provider", choices=["claude", "openai", "ollama"],
        help="model provider; required unless --transcript-only",
    )
    parser.add_argument("--model", help="model name; required for ollama, defaulted for the others")
    parser.add_argument("--base-url", help="override the provider's API endpoint")
    parser.add_argument(
        "--source", choices=["auto", "captions", "whisper"], default="auto",
        help="transcript source: auto = manual captions, then auto captions, then Whisper",
    )
    parser.add_argument(
        "--transcript-only", action="store_true",
        help="write the transcript to <title>.transcript.md and skip the summary",
    )
    parser.add_argument("--force", action="store_true", help="overwrite an existing identical note")
    parser.add_argument("--no-cache", action="store_true", help="ignore cached transcripts")
    parser.add_argument("--language", default="English", help="language of the summary (default: English)")
    parser.add_argument(
        "--max-context-tokens", type=int,
        help="split transcripts longer than this into chunks (default depends on provider)",
    )
    parser.add_argument(
        "--cookies-from-browser", metavar="BROWSER",
        help="pass browser cookies to yt-dlp for restricted videos, e.g. chrome",
    )
    return parser


def run(argv, env, youtube, whisper, stdout, stderr, cache_dir=None) -> int:
    try:
        args = build_parser().parse_args(argv)
    except UsageError as error:
        print(f"error: {error}", file=stderr)
        return 1
    if not args.transcript_only and not args.provider:
        print("error: --provider is required (claude, openai or ollama).", file=stderr)
        return 1
    try:
        return _run(args, env, youtube, whisper, stdout, stderr, cache_dir)
    except (ProviderError, TranscriptError, ToolError) as error:
        print(f"error: {error}", file=stderr)
        return 1


def _run(args, env, youtube, whisper, stdout, stderr, cache_dir) -> int:
    if isinstance(youtube, type):
        youtube = youtube(args.cookies_from_browser)
    transcript = _load_transcript(args, youtube, whisper, cache_dir)
    info = transcript.info
    if args.transcript_only:
        return _write_transcript(args, transcript, stdout, stderr)
    provider = make_provider(args.provider, args.model, env, args.base_url)
    combo = Combination(info.video_id, transcript.source, args.provider, provider.model)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    plan = plan_output_path(args.out_dir, info.title, combo, force=args.force)
    if plan.skipped:
        print(f"skipping: already summarised in {plan.path} (use --force to overwrite)", file=stderr)
        return 0
    budget = args.max_context_tokens or DEFAULT_CONTEXT_BUDGET[args.provider]
    summary = summarise(transcript.segments, provider, budget, args.language)
    if not summary.usable:
        raise ToolError("The model returned no usable summary. Try again or use a different --model.")
    if not summary.complete:
        print(f"warning: the model's summary is missing its {' and '.join(summary.missing())}", file=stderr)
    body = link_timestamps(summary.to_markdown(), info.video_id, info.duration)
    plan.path.write_text(render_note(info, transcript.source, args.provider, provider.model, body))
    print(plan.path, file=stdout)
    return 0


def _load_transcript(args, youtube, whisper, cache_dir):
    video_id = parse_video_id(args.url)
    cache = TranscriptCache(cache_dir) if cache_dir and video_id and not args.no_cache else None
    if cache and (cached := cache.get(video_id, args.source)):
        return cached
    transcript = get_transcript(args.url, args.source, youtube, whisper)
    if cache:
        cache.put(video_id, args.source, transcript)
    return transcript


def _write_transcript(args, transcript, stdout, stderr) -> int:
    info = transcript.info
    combo = Combination(info.video_id, transcript.source, "none", "none")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    plan = plan_output_path(args.out_dir, info.title, combo, force=args.force, kind="transcript")
    if plan.skipped:
        print(f"skipping: already saved in {plan.path} (use --force to overwrite)", file=stderr)
        return 0
    body = format_transcript(transcript.segments)
    plan.path.write_text(render_note(info, transcript.source, "none", "none", body))
    print(plan.path, file=stdout)
    return 0


def main() -> None:
    raise SystemExit(
        run(
            sys.argv[1:],
            env=os.environ,
            youtube=YtDlpYouTube,
            whisper=load_whisper(),
            stdout=sys.stdout,
            stderr=sys.stderr,
            cache_dir=Path(user_cache_dir("yt-summariser")),
        )
    )
