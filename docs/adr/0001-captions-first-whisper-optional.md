---
status: accepted
---
# Use YouTube captions first, with local Whisper as an optional fallback

Captions are free and near-instant, but missing on some videos and of uneven quality; Whisper is accurate but needs ffmpeg, a model download and minutes of compute. In `--source auto` we try manual captions, then auto captions, then Whisper, and record which was used as `transcript_source`. Whisper (`faster-whisper`) is an optional `[whisper]` extra so the base install stays light; yt-dlp is a core dependency because it fetches captions and metadata too. `--source` and `--transcript-only` exist so the user can compare sources on the same video.

## Considered Options

- Always transcribe with Whisper: consistent quality, but slow and heavy for the common case.
- Captions only: simplest, but fails on videos without captions.
