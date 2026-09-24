from dataclasses import dataclass


@dataclass(frozen=True)
class Segment:
    start: float
    text: str


@dataclass(frozen=True)
class VideoInfo:
    video_id: str
    title: str
    channel: str
    published: str
    duration: int
    url: str


@dataclass(frozen=True)
class Transcript:
    source: str
    segments: list[Segment]
    info: VideoInfo
