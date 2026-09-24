import re

_CITATION = re.compile(r" ?\[(?:(\d+):)?(\d+):(\d{2})\]")


def link_timestamps(markdown: str, video_id: str, duration: int) -> str:
    def replace(match: re.Match[str]) -> str:
        hours, minutes, seconds = match.groups()
        total = int(hours or 0) * 3600 + int(minutes) * 60 + int(seconds)
        if total > duration:
            return ""
        return f"{match.group(0)}(https://youtu.be/{video_id}?t={total})"

    return _CITATION.sub(replace, markdown)
