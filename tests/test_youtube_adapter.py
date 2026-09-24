import pytest
from fake_server import FakeServer
from yt_dlp.utils import DownloadError

from yt_summariser.transcript.models import Segment, VideoInfo
from yt_summariser.transcript.selection import TranscriptError
from yt_summariser.transcript.whisper import FasterWhisperTranscriber
from yt_summariser.transcript.youtube import YtDlpYouTube

URL = "https://www.youtube.com/watch?v=abc123"

JSON3 = {
    "events": [
        {"tStartMs": 1500, "segs": [{"utf8": "Hello "}, {"utf8": "world"}]},
        {"tStartMs": 3000, "segs": [{"utf8": "\n"}]},
        {"tStartMs": 65000, "segs": [{"utf8": "second\nline"}]},
        {"tStartMs": 70000},
    ]
}


def extracted(**overrides):
    data = {
        "id": "abc123",
        "title": "How Rust Works",
        "channel": "Rustacean",
        "upload_date": "20260102",
        "duration": 600,
        "webpage_url": URL,
        "language": "en",
        "subtitles": {},
        "automatic_captions": {},
    }
    data.update(overrides)
    return data


def tracks(url, *languages):
    return {lang: [{"ext": "vtt", "url": "unused"}, {"ext": "json3", "url": url}] for lang in languages}


def adapter_for(data, sleep=lambda seconds: None):
    return YtDlpYouTube(extract=lambda url: data, sleep=sleep)


def test_info_maps_extracted_metadata():
    info = adapter_for(extracted()).info(URL)

    assert info == VideoInfo("abc123", "How Rust Works", "Rustacean", "2026-01-02", 600, URL)


def test_info_falls_back_to_uploader_and_tolerates_missing_date():
    data = extracted(channel=None, uploader="Some Uploader", upload_date=None)

    info = adapter_for(data).info(URL)

    assert info.channel == "Some Uploader"
    assert info.published == ""


def test_captions_are_downloaded_and_parsed_into_timestamped_segments():
    with FakeServer([(200, JSON3)]) as server:
        data = extracted(subtitles=tracks(server.url + "/en.json3", "en"))

        segments = adapter_for(data).captions(URL, "manual")

    assert segments == [Segment(1.5, "Hello world"), Segment(65.0, "second line")]


def test_manual_and_auto_captions_come_from_their_own_tracks():
    with FakeServer([(200, JSON3)]) as server:
        data = extracted(automatic_captions=tracks(server.url + "/a.json3", "en"))
        youtube = adapter_for(data)

        assert youtube.captions(URL, "manual") is None
        assert youtube.captions(URL, "auto") == [Segment(1.5, "Hello world"), Segment(65.0, "second line")]


@pytest.mark.parametrize(
    "available, original, expected",
    [
        (["fr", "en-GB", "en"], "fr", "en"),
        (["fr", "en-GB"], "fr", "en-GB"),
        (["fr", "de"], "fr", "fr"),
        (["fr", "de"], "es", None),
    ],
)
def test_language_preference_is_english_then_the_videos_original(available, original, expected):
    with FakeServer([(200, JSON3)]) as server:
        subs = {lang: tracks(f"{server.url}/{lang}.json3", lang)[lang] for lang in available}
        youtube = adapter_for(extracted(subtitles=subs, language=original))

        segments = youtube.captions(URL, "manual")

        if expected is None:
            assert segments is None
            assert server.requests == []
        else:
            assert segments is not None
            assert server.requests[0]["path"] == f"/{expected}.json3"


def test_captions_without_a_json3_format_are_treated_as_missing():
    data = extracted(subtitles={"en": [{"ext": "vtt", "url": "unused"}]})

    assert adapter_for(data).captions(URL, "manual") is None


def test_restricted_video_error_keeps_the_reason_and_hints_at_cookies():
    def failing(url):
        raise DownloadError("ERROR: [youtube] abc123: Sign in to confirm your age")

    with pytest.raises(TranscriptError) as error:
        YtDlpYouTube(extract=failing).info(URL)

    assert str(error.value) == (
        "Sign in to confirm your age. "
        "If the video is restricted, try --cookies-from-browser <browser>."
    )


class FakeWhisperModel:
    def transcribe(self, path):
        class Piece:
            def __init__(self, start, text):
                self.start, self.text = start, text

        return iter([Piece(0.0, " Hello "), Piece(2.5, "   "), Piece(4.0, "world")]), None


def test_whisper_adapter_returns_trimmed_non_empty_segments():
    transcriber = FasterWhisperTranscriber(model=FakeWhisperModel())

    assert transcriber.transcribe("audio.m4a") == [Segment(0.0, "Hello"), Segment(4.0, "world")]


def json3_track(url):
    return [{"ext": "json3", "url": url}]


def test_original_language_track_is_preferred_over_a_machine_translation():
    with FakeServer([(200, JSON3)]) as server:
        auto = {
            "en": json3_track(f"{server.url}/translated.json3?lang=ar&tlang=en"),
            "en-orig": json3_track(f"{server.url}/original.json3?lang=en"),
        }

        segments = adapter_for(extracted(automatic_captions=auto)).captions(URL, "auto")

    assert segments is not None
    assert [r["path"] for r in server.requests] == ["/original.json3?lang=en"]


def test_a_real_track_in_the_videos_language_beats_an_english_translation():
    with FakeServer([(200, JSON3)]) as server:
        auto = {
            "en": json3_track(f"{server.url}/translated.json3?lang=ar&tlang=en"),
            "ar": json3_track(f"{server.url}/arabic.json3?lang=ar"),
        }

        adapter_for(extracted(automatic_captions=auto, language="ar")).captions(URL, "auto")

    assert [r["path"] for r in server.requests] == ["/arabic.json3?lang=ar"]


def test_translation_is_used_only_when_nothing_else_exists():
    with FakeServer([(200, JSON3)]) as server:
        auto = {"en": json3_track(f"{server.url}/translated.json3?lang=ar&tlang=en")}

        segments = adapter_for(extracted(automatic_captions=auto, language="ar")).captions(URL, "auto")

    assert segments is not None


def test_rate_limited_caption_download_is_retried_with_backoff():
    sleeps = []
    with FakeServer([(429, {}), (429, {}), (200, JSON3)]) as server:
        data = extracted(subtitles=tracks(server.url + "/en.json3", "en"))

        segments = adapter_for(data, sleep=sleeps.append).captions(URL, "manual")

    assert segments == [Segment(1.5, "Hello world"), Segment(65.0, "second line")]
    assert sleeps == [1, 2]


def test_persistent_rate_limiting_is_a_one_line_actionable_error():
    with FakeServer([(429, {})] * 4) as server:
        data = extracted(subtitles=tracks(server.url + "/en.json3", "en"))

        with pytest.raises(TranscriptError) as error:
            adapter_for(data).captions(URL, "manual")

    assert str(error.value) == (
        "YouTube is rate-limiting caption downloads (HTTP 429). "
        "Wait a few minutes and retry, or use --source whisper."
    )
