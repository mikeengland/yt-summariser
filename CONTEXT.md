# YouTube Summariser

Turns a single YouTube video into a Markdown note of its key points, intended to be stored in a personal notes vault such as Obsidian.

## Language

**Video**:
A single YouTube video, identified by its video ID.
_Avoid_: Clip, link, URL

**Transcript**:
The timestamped text of what is said in a Video, from one Transcript source.
_Avoid_: Subtitles, text

**Transcript source**:
Where a Transcript came from: `manual` (uploader-provided captions), `auto` (YouTube-generated captions) or `whisper` (speech-to-text run locally).
_Avoid_: Caption type, origin

**Provider**:
The language-model service that writes a Summary: `claude`, `openai` or `ollama`.
_Avoid_: Backend, vendor, engine

**Summary**:
The Markdown note for a Video: a title, a TL;DR and key points with timestamp links.
_Avoid_: Digest, recap, output

**Key point**:
One bullet in a Summary, linked to the moment in the Video it comes from.
_Avoid_: Highlight, takeaway

**Combination**:
The (Video, Transcript source, Provider, model) tuple that identifies one Summary. Two runs with the same Combination are duplicates.
_Avoid_: Variant, run

**Vault**:
The output directory the user points the tool at, typically an Obsidian folder.
_Avoid_: Library, folder
