"""Load meeting transcripts from JSON, CSV, or plain text/Markdown.

The original transcript text is always preserved; never overwritten.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

from .models import MeetingTranscript, TranscriptSegment

_TIMESTAMP_RE = re.compile(r"^\s*(\d{1,2}:\d{2}(?::\d{2})?)\s*$")


def load_transcript(path: str | Path) -> MeetingTranscript:
    p = Path(path)
    if p.is_dir():
        return _load_dir(p)
    return _load_file(p)


def _load_dir(p: Path) -> MeetingTranscript:
    """Load a meeting directory.

    Prefers ``metadata.json`` + ``transcript.json``; otherwise falls back to the
    first transcript file (``.json`` / ``.csv`` / ``.txt`` / ``.md``) found in
    the directory, so a single dropped-in transcript file also works.
    """
    metadata = _read_json(p / "metadata.json", default={})
    transcript = _read_json(p / "transcript.json", default={})
    if transcript:
        t = _from_json(transcript, metadata)
    else:
        t = None
        for suffix in (".json", ".csv", ".txt", ".md"):
            for candidate in sorted(p.glob(f"*{suffix}")):
                if candidate.name in ("metadata.json", "transcript.json"):
                    continue
                t = _load_file(candidate)
                break
            if t is not None:
                break
        if t is None:
            return MeetingTranscript(meeting_id=p.name, segments=[])
    meeting_id = metadata.get("meeting_id") or p.name
    return t.model_copy(update={"meeting_id": meeting_id})


def _load_file(p: Path) -> MeetingTranscript:
    if p.suffix == ".json":
        return _from_json(_read_json(p, default={}), {})
    if p.suffix == ".csv":
        return _from_csv(p)
    # .txt / .md / anything else -> plain text fallback
    return _from_text(p.read_text(encoding="utf-8"), meeting_id=p.stem)


def _read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _from_json(data: dict, metadata: dict) -> MeetingTranscript:
    meeting_id = data.get("meeting_id") or metadata.get("meeting_id") or "unknown"
    title = data.get("title") or metadata.get("title") or ""
    segments = [
        TranscriptSegment(
            segment_id=s.get("segment_id", f"S{i + 1:03d}"),
            speaker_id=s.get("speaker_id", "unknown"),
            timestamp_start=s.get("timestamp_start", ""),
            timestamp_end=s.get("timestamp_end", ""),
            language=s.get("language", "unknown"),
            text=s.get("text", ""),
        )
        for i, s in enumerate(data.get("segments", []))
    ]
    return MeetingTranscript(
        meeting_id=meeting_id,
        title=title,
        language_mix=data.get("language_mix", []),
        segments=segments,
    )


def _from_csv(path: Path) -> MeetingTranscript:
    segments: list[TranscriptSegment] = []
    with path.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        for i, row in enumerate(reader):
            segments.append(
                TranscriptSegment(
                    segment_id=row.get("segment_id", f"S{i + 1:03d}"),
                    speaker_id=row.get("speaker_id", "unknown"),
                    timestamp_start=row.get("timestamp_start", ""),
                    timestamp_end=row.get("timestamp_end", ""),
                    language=row.get("language", "unknown"),
                    text=row.get("text", ""),
                )
            )
    return MeetingTranscript(meeting_id=path.stem, segments=segments)


def _from_text(raw: str, meeting_id: str) -> MeetingTranscript:
    """Parse a plain transcript in the common webinar/auto-transcript layout:

        Speaker / section header
        0:00
        one or more lines of text…
        0:05
        next chunk of text…
        0:10
        …

    A ``timestamp`` line starts a new segment; following non-timestamp lines are
    its text (until the next timestamp). A short non-timestamp line that is
    immediately followed by a timestamp is treated as a speaker/header.
    """
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    segments: list[TranscriptSegment] = []
    speaker = "unknown"
    i = 0
    while i < len(lines):
        line = lines[i]
        if _TIMESTAMP_RE.match(line):
            ts = line
            body: list[str] = []
            j = i + 1
            while j < len(lines) and not _TIMESTAMP_RE.match(lines[j]):
                if _is_speaker_header(lines, j):
                    break
                body.append(lines[j])
                j += 1
            segments.append(
                TranscriptSegment(
                    segment_id=f"S{len(segments) + 1:03d}",
                    speaker_id=speaker,
                    timestamp_start=ts,
                    text=" ".join(body),
                )
            )
            i = j
        else:
            speaker = line
            i += 1
    return MeetingTranscript(meeting_id=meeting_id, segments=segments)


def _is_speaker_header(lines: list[str], idx: int) -> bool:
    """A short non-timestamp line followed by a timestamp is a speaker/header."""
    return (
        len(lines[idx].split()) <= 5
        and idx + 1 < len(lines)
        and bool(_TIMESTAMP_RE.match(lines[idx + 1]))
    )
