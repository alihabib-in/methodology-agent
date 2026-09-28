"""Text-to-speech using Microsoft Edge's free neural voices.

These voices are natural and consistent, require no API key, and are served as
MP3 audio so the browser just plays them. Falls back gracefully with a 501 if
the `edge-tts` package is not installed and a 502 if synthesis fails.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

router = APIRouter()

DEFAULT_VOICE = "en-US-JennyNeural"


@router.get("/tts")
async def synthesize(text: str, voice: str = DEFAULT_VOICE) -> Response:
    text = (text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    try:
        import edge_tts
    except ImportError:
        raise HTTPException(status_code=501, detail="TTS engine not installed")

    try:
        communicate = edge_tts.Communicate(text, voice)
        chunks = []
        async for chunk in communicate.stream():
            if chunk.get("type") == "audio":
                chunks.append(chunk["data"])
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"TTS synthesis failed: {exc}")

    if not chunks:
        raise HTTPException(status_code=502, detail="TTS returned no audio")

    return Response(content=b"".join(chunks), media_type="audio/mpeg")
