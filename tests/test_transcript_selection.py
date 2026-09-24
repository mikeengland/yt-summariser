import pytest

from yt_summariser.transcript.selection import TranscriptError, get_transcript

from fakes import AUTO, INFO, MANUAL, SPOKEN, ExplodingWhisper, FakeWhisper, FakeYouTube


def test_auto_prefers_manual_captions_and_never_runs_whisper():
    youtube = FakeYouTube(manual=MANUAL, auto=AUTO)

    transcript = get_transcript(INFO.url, "auto", youtube, ExplodingWhisper())

    assert transcript.source == "manual"
    assert transcript.segments == MANUAL
    assert transcript.info == INFO
    assert not youtube.audio_downloaded


def test_auto_falls_back_to_generated_captions():
    youtube = FakeYouTube(manual=None, auto=AUTO)

    transcript = get_transcript(INFO.url, "auto", youtube, ExplodingWhisper())

    assert transcript.source == "auto"
    assert transcript.segments == AUTO


def test_auto_transcribes_with_whisper_when_there_are_no_captions():
    youtube = FakeYouTube()

    transcript = get_transcript(INFO.url, "auto", youtube, FakeWhisper())

    assert transcript.source == "whisper"
    assert transcript.segments == SPOKEN
    assert youtube.audio_downloaded


def test_forced_whisper_ignores_existing_captions():
    youtube = FakeYouTube(manual=MANUAL, auto=AUTO)

    transcript = get_transcript(INFO.url, "whisper", youtube, FakeWhisper())

    assert transcript.source == "whisper"
    assert transcript.segments == SPOKEN


def test_forced_captions_fail_rather_than_fall_back_to_whisper():
    youtube = FakeYouTube()

    with pytest.raises(TranscriptError, match="No captions"):
        get_transcript(INFO.url, "captions", youtube, ExplodingWhisper())

    assert not youtube.audio_downloaded


def test_missing_whisper_extra_gives_an_actionable_error():
    youtube = FakeYouTube()

    with pytest.raises(TranscriptError) as error:
        get_transcript(INFO.url, "auto", youtube, whisper=None)

    assert str(error.value) == (
        "No captions found; install with uv tool install 'yt-summariser[whisper]'."
    )
    assert not youtube.audio_downloaded


def test_forced_whisper_without_the_extra_does_not_blame_missing_captions():
    youtube = FakeYouTube(manual=MANUAL)

    with pytest.raises(TranscriptError) as error:
        get_transcript(INFO.url, "whisper", youtube, whisper=None)

    assert str(error.value) == (
        "Whisper is not installed; install with uv tool install 'yt-summariser[whisper]'."
    )
