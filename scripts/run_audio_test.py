"""Transcribe an audio file and run it through the Methodology Agent API.

Usage:
    python scripts/run_audio_test.py path/to/audio.wav [--model-size small]
       [--device cpu] [--compute-type int8] [--language ar|en|...]
       [--api-url http://127.0.0.1:8000] [--max-chars 900]
"""

import argparse
import json
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def fmt_ts(seconds: float) -> str:
    total = int(seconds)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def build_chunks(segments, max_chars: int):
    chunks = []
    current = []
    length = 0
    for seg in segments:
        current.append(seg)
        length += len(seg.text) + 1
        if length >= max_chars:
            chunks.append(current)
            current = []
            length = 0
    if current:
        chunks.append(current)
    return chunks


def parse_args():
    parser = argparse.ArgumentParser(
        description="Transcribe audio and analyze it with the Methodology Agent."
    )
    parser.add_argument("audio", help="Path to a .wav/.mp3 audio file.")
    parser.add_argument("--model-size", default="small",
                        help="Whisper model size (tiny/base/small/medium/large-v3).")
    parser.add_argument("--device", default="cpu", choices=["cpu", "cuda"],
                        help="Compute device for transcription.")
    parser.add_argument("--compute-type", default="int8",
                        help="CTranslate2 compute type (int8/float16).")
    parser.add_argument("--language", default=None,
                        help="Force a language code (e.g. ar, en) or auto-detect.")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000",
                        help="Methodology Agent API base URL.")
    parser.add_argument("--max-chars", type=int, default=500,
                        help="Max characters per transcript chunk sent to the agent.")
    return parser.parse_args()


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    args = parse_args()

    from app.speech.transcriber import Transcriber

    print(f"Transcribing {args.audio} with model '{args.model_size}' ...")
    transcriber = Transcriber(
        model_size=args.model_size,
        device=args.device,
        compute_type=args.compute_type,
    )
    segments, info = transcriber.transcribe(args.audio, language=args.language)

    print(f"Detected language : {info['language']} "
          f"(probability={info.get('language_probability', 0.0):.3f})")
    print(f"Audio duration    : {info.get('duration', 0.0):.1f}s")
    print(f"Segments          : {len(segments)}")
    print()
    print("=" * 78)
    print("FULL TRANSCRIPT")
    print("=" * 78)
    for seg in segments:
        print(f"[{fmt_ts(seg.start)} - {fmt_ts(seg.end)}] {seg.text}")
    print()

    transcript_path = Path(args.audio).with_suffix(".transcript.txt")
    transcript_path.write_text(
        "\n".join(
            f"[{fmt_ts(seg.start)} - {fmt_ts(seg.end)}] {seg.text}"
            for seg in segments
        ),
        encoding="utf-8",
    )
    print(f"Transcript saved to: {transcript_path}")
    print()

    chunks = build_chunks(segments, max_chars=args.max_chars)
    print(f"Feeding {len(chunks)} chunk(s) into the Methodology Agent "
          f"({args.api_url}) ...")
    print()

    api = args.api_url.rstrip("/")
    final = None
    questions = []

    with httpx.Client(timeout=300.0) as client:
        for i, chunk in enumerate(chunks, 1):
            text = "\n".join(seg.text for seg in chunk)
            payload = {"text": text, "language": info.get("language")}
            resp = client.post(f"{api}/analyze", json=payload)
            resp.raise_for_status()
            result = resp.json()

            gaps = result.get("gaps") or []
            top_gap = gaps[0]["domain"] if gaps else "n/a"
            q = result.get("recommended_question") or {}
            questions.append(
                {
                    "chunk": i,
                    "question": q.get("question"),
                    "domain": q.get("domain"),
                    "priority": q.get("priority"),
                }
            )
            print(f"[chunk {i}/{len(chunks)}] top-gap={top_gap:<18} "
                  f"question='{q.get('question')}'")
            final = result

    print()
    print("=" * 78)
    print("RECOMMENDED QUESTIONS PER CHUNK")
    print("=" * 78)
    for q in questions:
        print(f"  chunk {q['chunk']}: [{q['domain']}] {q['question']} "
              f"(priority={q['priority']})")

    if final:
        print()
        print("=" * 78)
        print("FINAL METHODOLOGY STATE (accumulated across all chunks)")
        print("=" * 78)
        state = final.get("methodology_state") or {}
        scalar_fields = (
            "objective", "target_population", "statistical_unit",
            "reference_period", "frequency", "geographic_scope",
        )
        for field in scalar_fields:
            f = state.get(field) or {}
            if f.get("status") not in (None, "unknown"):
                print(f"  {field:<20} {f.get('value')} "
                      f"[{f.get('status')} @ {f.get('confidence')}]")

        for key in ("indicators", "data_sources", "definitions",
                    "decisions", "constraints"):
            items = state.get(key) or []
            if items:
                print(f"  {key}: {len(items)} item(s)")
                for item in items:
                    print("    - " + json.dumps(item, ensure_ascii=False)[:220])

        print()
        print("GAPS (priority order):")
        for g in (final.get("gaps") or [])[:8]:
            print(f"  {g['domain']:<20} {g['priority']:<8} {g['status']}")


if __name__ == "__main__":
    main()
