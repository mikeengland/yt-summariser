---
status: accepted
---
# Name files by video title and never overwrite or rename existing ones

The user wants to compare sources and providers on one video without losing earlier Summaries, but also wants clean filenames. So a new file is `Title.md` when that name is free, and otherwise `Title [<source> · <provider>-<model>].md` (with ` · <detail>` added when the Detail level isn't `standard`), with `(<video_id>)` appended if that too belongs to a different video. Only `Title.md` and `Title [*].md` count as collision candidates (a `Title*` glob would match unrelated videos), and each candidate's frontmatter (`video_id`, `transcript_source`, `provider`, `model`, `detail`; a missing `detail` means `standard`, as in notes written before Detail levels existed) decides whether a run is a duplicate of an existing Combination. Duplicates are skipped with a warning unless `--force` overwrites that file. Existing files are never renamed, so the first Summary keeps the plain name whatever its Combination.

## Consequences

- The filename alone doesn't identify a Combination; the frontmatter is the source of truth.
- Titles are sanitised for Obsidian (illegal characters replaced, about 120 characters max).
