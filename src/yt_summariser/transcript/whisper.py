from pathlib import Path

from yt_summariser.transcript.models import Segment

WHISPER_MODEL = "small"


class FasterWhisperTranscriber:
    def __init__(self, model_size: str = WHISPER_MODEL):
        self.model_size = model_size
        self._model = None

    def transcribe(self, audio_path: Path) -> list[Segment]:
        if self._model is None:
            from faster_whisper import WhisperModel

            self._model = WhisperModel(self.model_size, compute_type="int8")
        segments, _ = self._model.transcribe(str(audio_path))
        return [Segment(s.start, s.text.strip()) for s in segments if s.text.strip()]


def load_whisper() -> FasterWhisperTranscriber | None:
    try:
        import faster_whisper  # noqa: F401
    except ImportError:
        return None
    return FasterWhisperTranscriber()
