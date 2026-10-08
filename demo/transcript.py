"""Transcript loading and parsing for the demo.

Reads Markdown meeting transcripts from the ``transcript/`` folder and splits
them into timed speaker turns. Two formats are supported:

1. **Simple inline** — one turn per line::

       [00:01:02] Khalid (Data): The data comes from the commercial register.

2. **Bilingual card** — a speaker header followed by EN/AR blocks::

       **[09:00] Dr. Mariam Al Mansouri — Director of Statistical Research, SCAD**

       **EN:** Good morning everyone.
       **AR:** صباح الخير جميعًا.

For the bilingual format only the English ``**EN:**`` line is used as the turn
text (the Arabic translation is skipped for demo purposes).
"""

from __future__ import annotations

import re
from pathlib import Path

# Simple format: [hh:mm(:ss)] Speaker: text
_SIMPLE_RE = re.compile(r"^\[(\d{1,2}:\d{2}(?::\d{2})?)\]\s*(.+?):\s*(.*)$")
# Bilingual format speaker header: **[hh:mm] Name — Title, Org**
_HEADER_RE = re.compile(r"^\*{0,2}\[(\d{1,2}:\d{2}(?::\d{2})?)\]\s*(.+)$")
# Bilingual format text blocks: **EN:** ... and **AR:** ...
_EN_RE = re.compile(r"^\*{0,2}EN:\*{0,2}\s*(.*)$", re.IGNORECASE)
_AR_RE = re.compile(r"^\*{0,2}AR:\*{0,2}\s*(.*)$", re.IGNORECASE)

_TITLE_RE = re.compile(r"^#\s+(.+)$")


def list_transcripts(folder: str = "transcript") -> list[str]:
    """Return the relative paths of every ``.md`` transcript in ``folder``."""
    root = Path(folder)
    if not root.exists():
        return []
    return sorted(str(p) for p in root.glob("*.md"))


def load_transcript(path: str) -> str:
    """Read a transcript file as text."""
    return Path(path).read_text(encoding="utf-8")


def extract_title(text: str) -> str:
    """Return the meeting title (first ``#`` heading), cleaned of prefixes."""
    for line in text.splitlines():
        match = _TITLE_RE.match(line.strip())
        if match:
            title = match.group(1).strip()
            title = re.sub(r"^Methodology Meeting\s*[—–-]\s*", "", title, flags=re.IGNORECASE)
            return title
    return ""


def _speaker_name(header_text: str) -> str:
    """Pull the speaker name out of a header like ``Name — Title, Org``."""
    header_text = header_text.strip().strip("*").strip()
    name = re.split(r"\s*[—–-]\s*", header_text, maxsplit=1)[0].strip()
    return name


def parse_transcript(text: str) -> list[dict]:
    """Parse a Markdown transcript into a list of speaker turns.

    Each turn is ``{"time": "09:00", "speaker": "Dr. Mariam Al Mansouri",
    "text": "..."}``. Non-dialogue lines (headings, tables, separators) are
    ignored.
    """
    turns: list[dict] = []
    current_time: str | None = None
    current_speaker: str | None = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        # 1) Simple inline turn.
        match = _SIMPLE_RE.match(line)
        if match:
            turns.append(
                {
                    "time": match.group(1),
                    "speaker": match.group(2).strip(),
                    "text": match.group(3).strip(),
                }
            )
            current_speaker = None
            continue

        # 2) Bilingual speaker header — remember who is speaking.
        match = _HEADER_RE.match(line)
        if match:
            current_time = match.group(1)
            current_speaker = _speaker_name(match.group(2))
            continue

        # 3) English text block — attach to the current speaker.
        match = _EN_RE.match(line)
        if match and current_speaker is not None:
            turns.append(
                {
                    "time": current_time,
                    "speaker": current_speaker,
                    "text": match.group(1).strip(),
                }
            )
            continue

        # 4) Arabic text block — skipped for demo purposes.
        if _AR_RE.match(line):
            continue

    return turns


def transcript_stats(turns: list[dict]) -> dict:
    """Small helper the mock elicitation agent uses to describe the meeting."""
    speakers = list(dict.fromkeys(t["speaker"] for t in turns))
    return {
        "speaker_count": len(speakers),
        "turn_count": len(turns),
        "speakers": speakers,
        "duration": turns[-1]["time"] if turns else "00:00",
    }
