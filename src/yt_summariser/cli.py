import argparse
import os
import sys
from pathlib import Path

from yt_summariser.output.filenames import Combination, plan_output_path
from yt_summariser.output.render import render_note
from yt_summariser.providers.factory import make_provider
from yt_summariser.providers.http import ProviderError
from yt_summariser.summarise.pipeline import summarise
from yt_summariser.summarise.prompts import format_transcript
from yt_summariser.summarise.timestamps import link_timestamps
from yt_summariser.transcript.cache import TranscriptCache, parse_video_id
from yt_summariser.transcript.selection import TranscriptError, get_transcript


DEFAULT_CONTEXT_BUDGET = {"claude": 150_000, "openai": 100_000, "ollama": 6_000}


class ToolError(Exception):
    pass


class UsageError(Exception):
    pass


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise UsageError(message)


def build_parser() -> argparse.ArgumentParser:
    parser = _Parser(prog="yt-summariser")
    parser.add_argument("url")
    parser.add_argument("-o", "--out-dir", required=True, type=Path)
    parser.add_argument("--provider", choices=["claude", "openai", "ollama"])
    parser.add_argument("--model")
    parser.add_argument("--base-url")
    parser.add_argument("--max-context-tokens", type=int)
    parser.add_argument("--transcript-only", action="store_true")
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--source", choices=["auto", "captions", "whisper"], default="auto")
    return parser


def run(argv, env, youtube, whisper, stdout, stderr, cache_dir=None) -> int:
    try:
        args = build_parser().parse_args(argv)
    except UsageError as error:
        print(f"usage error: {error}", file=stderr)
        return 2
    try:
        return _run(args, env, youtube, whisper, stdout, stderr, cache_dir)
    except (ProviderError, TranscriptError, ToolError) as error:
        print(f"error: {error}", file=stderr)
        return 1


def _run(args, env, youtube, whisper, stdout, stderr, cache_dir) -> int:
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
    summary = summarise(transcript.segments, provider, budget)
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
    raise SystemExit("not wired yet")
