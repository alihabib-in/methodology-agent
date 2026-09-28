"""Language normalization for transcripts (segment-level)."""

from __future__ import annotations

from app.agent.terminology import canonicalize, detect_language

from .models import MeetingTranscript


def normalize_transcript(transcript: MeetingTranscript) -> MeetingTranscript:
    segments = []
    for s in transcript.segments:
        language = s.language if s.language not in ("", "unknown", "auto") else detect_language(s.text)
        # The normalized text is a supplementary aid only; the original Arabic
        # text is always preserved on the segment for evidence.
        normalized = canonicalize(s.text) if language in ("ar", "mixed") else s.text
        segments.append(s.model_copy(update={"language": language, "normalized_text": normalized}))
    return transcript.model_copy(update={"segments": segments})


def language_breakdown(transcript: MeetingTranscript) -> dict[str, float]:
    total = max(1, len(transcript.segments))
    counts: dict[str, int] = {}
    for s in transcript.segments:
        lang = "ar" if s.language in ("ar", "mixed") else "en"
        counts[lang] = counts.get(lang, 0) + 1
    return {lang: round(count / total * 100, 1) for lang, count in sorted(counts.items())}
