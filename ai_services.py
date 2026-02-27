# ─── ai_services.py ───────────────────────────────────────────────────────────
# LLM streaming and Speech-to-Text via Groq's OpenAI-compatible API.
# ──────────────────────────────────────────────────────────────────────────────

import io
from openai import OpenAI
from config import GROQ_BASE_URL, MAX_TOKENS, TEMPERATURE, WHISPER_MODEL, CRM_SYSTEM_PROMPT


def _get_client(api_key: str) -> OpenAI:
    """Create a Groq-compatible OpenAI client."""
    return OpenAI(api_key=api_key, base_url=GROQ_BASE_URL)


# ─── Streaming LLM ──────────────────────────────────────────────────────────

def stream_ai(api_key: str, model: str, conversation: list):
    """
    Stream LLM response token-by-token.

    Yields text chunks as they arrive from the Groq streaming API.
    Use with st.write_stream() or manual accumulation for real-time display.

    Args:
        api_key: Groq API key
        model: Model identifier (e.g. "llama-3.3-70b-versatile")
        conversation: List of {"role": ..., "content": ...} dicts

    Yields:
        str: Text chunks (tokens) as they arrive
    """
    if not api_key:
        yield "Please add your Groq API key in the sidebar to continue."
        return

    try:
        client = _get_client(api_key)
        clean = [{"role": m["role"], "content": m["content"]} for m in conversation]
        payload = [{"role": "system", "content": CRM_SYSTEM_PROMPT}] + clean

        stream = client.chat.completions.create(
            model=model,
            messages=payload,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            stream=True,
        )

        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    except Exception as e:
        err = str(e)
        if "401" in err or "invalid_api_key" in err.lower():
            yield "Invalid API key — check the sidebar."
        elif "rate_limit" in err.lower():
            yield "Rate limit hit. Please wait a moment."
        elif "connection" in err.lower():
            yield "Connection error. Check your internet."
        else:
            yield f"Error: {err}"


def call_ai(api_key: str, model: str, conversation: list) -> str:
    """
    Non-streaming LLM call. Returns the full response as a string.
    Used for the initial greeting where streaming isn't needed.
    """
    if not api_key:
        return "Please add your Groq API key in the sidebar to continue."

    try:
        client = _get_client(api_key)
        clean = [{"role": m["role"], "content": m["content"]} for m in conversation]
        payload = [{"role": "system", "content": CRM_SYSTEM_PROMPT}] + clean

        resp = client.chat.completions.create(
            model=model,
            messages=payload,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
        )
        return resp.choices[0].message.content

    except Exception as e:
        err = str(e)
        if "401" in err or "invalid_api_key" in err.lower():
            return "Invalid API key — check the sidebar."
        elif "rate_limit" in err.lower():
            return "Rate limit hit. Please wait a moment."
        elif "connection" in err.lower():
            return "Connection error. Check your internet."
        return f"Error: {err}"


# ─── Speech-to-Text ─────────────────────────────────────────────────────────

def call_stt(api_key: str, audio_bytes: bytes) -> str:
    """
    Transcribe audio using Groq's Whisper API.

    Args:
        api_key: Groq API key
        audio_bytes: Raw audio bytes (WAV format)

    Returns:
        Transcribed text, or empty string on failure
    """
    if not api_key:
        return ""

    try:
        client = _get_client(api_key)
        buf = io.BytesIO(audio_bytes)
        buf.name = "recording.wav"
        result = client.audio.transcriptions.create(
            model=WHISPER_MODEL,
            file=buf,
            response_format="text",
        )
        return (result if isinstance(result, str) else result.text).strip()

    except Exception as e:
        return f"[Transcription error: {e}]"
