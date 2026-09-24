import re
import tempfile
import time
from pathlib import Path

import httpx
import yt_dlp
from yt_dlp.utils import DownloadError

from yt_summariser.transcript.models import Segment, VideoInfo
from yt_summariser.transcript.selection import TranscriptError


CAPTION_RETRIES = 3


class YtDlpYouTube:
    def __init__(self, cookies_from_browser: str | None = None, extract=None, sleep=time.sleep):
        self.cookies_from_browser = cookies_from_browser
        self._sleep = sleep
        self._extract_url = extract or self._extract_with_yt_dlp
        self._extracted: dict[str, dict] = {}

    def _options(self, **extra) -> dict:
        options = {"quiet": True, "no_warnings": True, "noprogress": True, **extra}
        if self.cookies_from_browser:
            options["cookiesfrombrowser"] = (self.cookies_from_browser,)
        return options

    def _extract_with_yt_dlp(self, url: str) -> dict:
        with yt_dlp.YoutubeDL(self._options()) as ydl:
            return ydl.extract_info(url, download=False)

    def _extract(self, url: str) -> dict:
        if url not in self._extracted:
            try:
                self._extracted[url] = self._extract_url(url)
            except DownloadError as error:
                reason = re.sub(r"^ERROR:\s*(?:\[[^\]]*\][^:]*:\s*)?", "", str(error)).strip()
                raise TranscriptError(
                    f"{reason.rstrip('.')}. If the video is restricted, try --cookies-from-browser <browser>."
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
        fmt = _json3_format(tracks[language])
        if fmt is None:
            return None
        return parse_json3(self._download_json(fmt["url"]))

    def _download_json(self, url: str) -> dict:
        for attempt in range(CAPTION_RETRIES + 1):
            try:
                response = httpx.get(url, timeout=60, follow_redirects=True)
            except httpx.HTTPError as error:
                raise TranscriptError(f"Could not download captions: {error}") from error
            if response.status_code == 429:
                if attempt < CAPTION_RETRIES:
                    self._sleep(2**attempt)
                    continue
                raise TranscriptError(
                    "YouTube is rate-limiting caption downloads (HTTP 429). "
                    "Wait a few minutes and retry, or use --source whisper."
                )
            if response.status_code >= 400:
                raise TranscriptError(f"Could not download captions: HTTP {response.status_code}")
            return response.json()

    def audio(self, url: str) -> Path:
        directory = Path(tempfile.mkdtemp(prefix="yt-summariser-"))
        options = self._options(format="bestaudio/best", outtmpl=str(directory / "%(id)s.%(ext)s"))
        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                ydl.download([url])
        except DownloadError as error:
            raise TranscriptError(f"Could not download audio: {error}") from error
        return next(directory.iterdir())


def _json3_format(formats: list[dict]) -> dict | None:
    return next((f for f in formats if f.get("ext") == "json3"), None)


def _is_translation(formats: list[dict]) -> bool:
    fmt = _json3_format(formats)
    return bool(fmt and "tlang=" in fmt["url"])


def _pick_language(tracks: dict, original: str | None) -> str | None:
    """Prefer real English, then the video's own language; machine translations come last.

    YouTube serves auto-translated tracks (``tlang=``) with aggressive rate limiting, and they
    are worse than the original speech recognition anyway.
    """
    real = {lang for lang, formats in tracks.items() if not _is_translation(formats)}
    english = sorted(lang for lang in real if lang == "en" or lang.startswith("en-"))
    if english:
        return "en" if "en" in english else english[0]
    if original and original in real:
        return original
    translated = sorted(lang for lang in tracks if lang == "en" or lang.startswith("en-"))
    if translated:
        return "en" if "en" in translated else translated[0]
    return None


def parse_json3(data: dict) -> list[Segment]:
    segments = []
    for event in data.get("events", []):
        text = "".join(seg.get("utf8", "") for seg in event.get("segs", [])).replace("\n", " ").strip()
        if text:
            segments.append(Segment(event.get("tStartMs", 0) / 1000, text))
    return segments
