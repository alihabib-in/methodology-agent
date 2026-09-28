"""Speech-to-text transcription using faster-whisper (optional dependency).

This module is intentionally lazy about importing ``faster_whisper`` so the
core API image (which does not install it) keeps working without it.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class TranscriptSegment:
    start: float
    end: float
    text: str
    language: str
    probability: float


class Transcriber:
    """Thin wrapper around faster-whisper for Arabic/English transcription."""

    def __init__(
        self,
        model_size: str = "small",
        device: str = "cpu",
        compute_type: str = "int8",
    ) -> None:
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise ImportError(
                "faster-whisper is not installed. "
                "Install it with: pip install -r requirements-asr.txt"
            ) from exc

        self.model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type,
        )
        self.model_size = model_size

    def transcribe(
        self,
        audio_path: str | Path,
        language: str | None = None,
        beam_size: int = 5,
    ) -> tuple[list[TranscriptSegment], dict]:
        segments, info = self.model.transcribe(
            str(audio_path),
            language=language,
            vad_filter=True,
            beam_size=beam_size,
        )

        result = [
            TranscriptSegment(
                start=round(seg.start, 2),
                end=round(seg.end, 2),
                text=seg.text.strip(),
                language=info.language or "unknown",
                probability=round(info.language_probability or 0.0, 4),
            )
            for seg in segments
        ]

        info_dict = {
            "language": info.language,
            "language_probability": info.language_probability,
            "duration": info.duration,
        }

        return result, info_dict

    def to_dict(self, segment: TranscriptSegment) -> dict:
        return asdict(segment)
