---
status: accepted
---
# Write files only, into a required output directory

The tool never prints the Summary to stdout: it writes a Markdown file into `-o/--out-dir` (required, created if missing) and prints the path. The output is meant to live in a notes vault, and file naming (see ADR-0004) is central to that. `--transcript-only` also writes a file, with a `.transcript.md` suffix, so transcripts don't clutter the summaries. Piping and stdout output were dropped deliberately; wrapping the CLI later is possible if needed.
