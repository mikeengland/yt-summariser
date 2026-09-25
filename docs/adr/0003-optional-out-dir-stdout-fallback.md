---
status: accepted
---
# Write files into an optional output directory; print to stdout without one

With `-o/--out-dir` the tool writes a Markdown file into that directory (created if missing) and prints the path. The output is meant to live in a notes vault, and file naming (see ADR-0004) is central to that. `--transcript-only` also writes a file, with a `.transcript.md` suffix, so transcripts don't clutter the summaries.

Without `-o`, the note is printed to stdout instead and nothing is written, so no filename planning or skip-if-exists check applies. Diagnostics still go to stderr, so stdout can be piped. (Originally the directory was required and stdout output was deliberately dropped; this reverses that.)
