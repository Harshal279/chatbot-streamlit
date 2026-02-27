# ─── tts_service.py ───────────────────────────────────────────────────────────
# Text-to-Speech using Edge-TTS (Microsoft neural voices).
# Free, no API key, high quality, works on Streamlit Cloud.
# ──────────────────────────────────────────────────────────────────────────────

import io
import asyncio
import edge_tts
from config import EDGE_TTS_VOICE, EDGE_TTS_RATE


def _clean_text(text: str) -> str:
    """Strip markdown formatting that sounds awkward when spoken."""
    return (
        text.replace("**", "")
            .replace("*", "")
            .replace("`", "")
            .replace("#", "")
            .replace("→", " to ")
            .replace("—", ", ")
            .replace("&amp;", "and")
            .replace("&", "and")
    )


async def _synthesize_async(text: str, voice: str = EDGE_TTS_VOICE) -> bytes:
    """
    Async Edge-TTS synthesis. Returns MP3 bytes in memory.
    No files are saved to disk.
    """
    clean = _clean_text(text)
    if not clean.strip():
        return b""

    # Limit to ~3000 chars to avoid timeouts
    clean = clean[:3000]

    communicate = edge_tts.Communicate(clean, voice, rate=EDGE_TTS_RATE)
    buffer = io.BytesIO()

    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buffer.write(chunk["data"])

    buffer.seek(0)
    return buffer.read()


def synthesize(text: str, voice: str = EDGE_TTS_VOICE) -> bytes:
    """
    Synchronous wrapper for Edge-TTS synthesis.

    Converts text to natural-sounding speech using Microsoft's neural voices.
    Returns MP3 bytes — pass directly to st.audio().

    Args:
        text: The text to speak (markdown will be cleaned)
        voice: Edge-TTS voice name (default from config)

    Returns:
        MP3 audio bytes, or empty bytes on failure
    """
    if not text or not text.strip():
        return b""

    try:
        # Handle event loop — Streamlit may or may not have one running
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # We're inside an existing event loop (e.g. Streamlit)
            # Create a new loop in a thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                result = pool.submit(
                    asyncio.run, _synthesize_async(text, voice)
                ).result(timeout=30)
            return result
        else:
            return asyncio.run(_synthesize_async(text, voice))

    except Exception as e:
        print(f"[TTS Error] {e}")
        return b""


async def list_voices(language: str = "en") -> list[dict]:
    """
    List available Edge-TTS voices for a language.
    Useful for letting users pick their preferred voice.

    Args:
        language: Language code prefix (e.g. "en", "en-US")

    Returns:
        List of voice dicts with 'Name', 'ShortName', 'Gender', etc.
    """
    voices = await edge_tts.list_voices()
    return [v for v in voices if v["Locale"].startswith(language)]
