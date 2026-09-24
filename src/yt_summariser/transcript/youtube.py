import re
import tempfile
from pathlib import Path

import httpx
import yt_dlp
from yt_dlp.utils import DownloadError

from yt_summariser.transcript.models import Segment, VideoInfo
from yt_summariser.transcript.selection import TranscriptError


class YtDlpYouTube:
    def __init__(self, cookies_from_browser: str | None = None):
        self.cookies_from_browser = cookies_from_browser
        self._extracted: dict[str, dict] = {}

    def _options(self, **extra) -> dict:
        options = {"quiet": True, "no_warnings": True, "noprogress": True, **extra}
        if self.cookies_from_browser:
            options["cookiesfrombrowser"] = (self.cookies_from_browser,)
        return options

    def _extract(self, url: str) -> dict:
        if url not in self._extracted:
            try:
                with yt_dlp.YoutubeDL(self._options()) as ydl:
                    self._extracted[url] = ydl.extract_info(url, download=False)
            except DownloadError as error:
                reason = re.sub(r"^ERROR:\s*(\[[^\]]*\]\s*)?", "", str(error)).strip()
                raise TranscriptError(
                    f"{reason} If the video is restricted, try --cookies-from-browser <browser>."
                ) from error
        return self._extracted[url]

    def info(self, url: str) -> VideoInfo:
        data = self._extract(url)
        upload = data.get("upload_date") or ""
        published = f"{upload[:4]}-{upload[4:6]}-{upload[6:]}" if len(upload) == 8 else ""
        return VideoInfo(
            video_id=data["id"],
            title=data["title"],
            channel=data.get("channel") or data.get("uploader") or "",
            published=published,
            duration=int(data.get("duration") or 0),
            url=data.get("webpage_url") or url,
        )

    def captions(self, url: str, kind: str) -> list[Segment] | None:
        data = self._extract(url)
        tracks = data.get("subtitles" if kind == "manual" else "automatic_captions") or {}
        language = _pick_language(tracks, data.get("language"))
        if language is None:
            return None
        fmt = next((f for f in tracks[language] if f.get("ext") == "json3"), None)
        if fmt is None:
            return None
        response = httpx.get(fmt["url"], timeout=60, follow_redirects=True)
        response.raise_for_status()
        return parse_json3(response.json())

    def audio(self, url: str) -> Path:
        directory = Path(tempfile.mkdtemp(prefix="yt-summariser-"))
        options = self._options(format="bestaudio/best", outtmpl=str(directory / "%(id)s.%(ext)s"))
        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                ydl.download([url])
        except DownloadError as error:
            raise TranscriptError(f"Could not download audio: {error}") from error
        return next(directory.iterdir())


def _pick_language(tracks: dict, original: str | None) -> str | None:
    english = sorted(lang for lang in tracks if lang == "en" or lang.startswith("en-"))
    if english:
        return "en" if "en" in english else english[0]
    if original and original in tracks:
        return original
    return None


def parse_json3(data: dict) -> list[Segment]:
    segments = []
    for event in data.get("events", []):
        text = "".join(seg.get("utf8", "") for seg in event.get("segs", [])).replace("\n", " ").strip()
        if text:
            segments.append(Segment(event.get("tStartMs", 0) / 1000, text))
    return segments
