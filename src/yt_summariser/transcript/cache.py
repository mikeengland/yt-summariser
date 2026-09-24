import json
import re
from pathlib import Path

from yt_summariser.transcript.models import Segment, Transcript, VideoInfo

_VIDEO_ID = re.compile(r"(?:v=|youtu\.be/|/shorts/|/embed/|/live/)([A-Za-z0-9_-]+)")


def parse_video_id(url: str) -> str | None:
    match = _VIDEO_ID.search(url)
    return match.group(1) if match else None


class TranscriptCache:
    def __init__(self, directory: Path):
        self.directory = directory

    def _path(self, video_id: str, source: str) -> Path:
        return self.directory / f"{video_id}.{source}.json"

    def get(self, video_id: str, source: str) -> Transcript | None:
        path = self._path(video_id, source)
        if not path.exists():
            return None
        data = json.loads(path.read_text())
        return Transcript(
            data["source"],
            [Segment(**s) for s in data["segments"]],
            VideoInfo(**data["info"]),
        )

    def put(self, video_id: str, source: str, transcript: Transcript) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        data = {
            "source": transcript.source,
            "segments": [vars(s) for s in transcript.segments],
            "info": vars(transcript.info),
        }
        self._path(video_id, source).write_text(json.dumps(data))
