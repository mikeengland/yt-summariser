from yt_summariser.transcript.models import Transcript


class TranscriptError(Exception):
    pass


def get_transcript(url, source, youtube, whisper) -> Transcript:
    info = youtube.info(url)
    if source in ("auto", "captions"):
        for kind in ("manual", "auto"):
            segments = youtube.captions(url, kind)
            if segments:
                return Transcript(kind, segments, info)
        if source == "captions":
            raise TranscriptError("No captions found for this video")
    if whisper is None:
        raise TranscriptError(
            "No captions found; install with uv tool install 'yt-summariser[whisper]'."
        )
    audio = youtube.audio(url)
    return Transcript("whisper", whisper.transcribe(audio), info)
