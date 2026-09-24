from yt_summariser.transcript.models import Segment, VideoInfo

MANUAL = [Segment(0.0, "manual text")]
AUTO = [Segment(0.0, "auto text")]
SPOKEN = [Segment(0.0, "whisper text")]
INFO = VideoInfo(
    video_id="abc123",
    title="How Rust Works",
    channel="Rustacean",
    published="2026-01-02",
    duration=600,
    url="https://www.youtube.com/watch?v=abc123",
)


class FakeYouTube:
    def __init__(self, manual=None, auto=None):
        self._captions = {"manual": manual, "auto": auto}
        self.audio_downloaded = False
        self.info_calls = 0

    def info(self, url):
        self.info_calls += 1
        return INFO

    def captions(self, url, kind):
        return self._captions[kind]

    def audio(self, url):
        self.audio_downloaded = True
        return "audio.m4a"


class FakeWhisper:
    def transcribe(self, audio_path):
        return SPOKEN


class ExplodingWhisper:
    def transcribe(self, audio_path):
        raise AssertionError("Whisper must not run when captions exist")
