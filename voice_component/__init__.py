# ─── voice_component/__init__.py ──────────────────────────────────────────────
# Custom Streamlit bidirectional component for the automatic voice loop.
#
# This component:
#   - Sends TTS audio (base64 MP3) to the browser for playback
#   - Receives recorded user audio (base64 WebM) after silence detection
#   - Manages the IDLE → SPEAKING → LISTENING → PROCESSING state loop
# ──────────────────────────────────────────────────────────────────────────────

import os
import streamlit.components.v1 as components
from config import SILENCE_THRESHOLD, SILENCE_DURATION, MIC_DELAY_MS, MIN_SPEECH_DURATION

# Path to the frontend HTML
_COMPONENT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")

# Declare the component (development mode uses local files)
_voice_component = components.declare_component("voice_loop", path=_COMPONENT_DIR)


def voice_loop_component(
    tts_audio_b64: str = "",
    key: str = "voice_loop",
) -> dict | None:
    """
    Render the voice loop component.

    Args:
        tts_audio_b64: Base64-encoded MP3 audio for TTS playback.
                       Pass empty string when no audio to play.
        key: Streamlit component key for state management.

    Returns:
        dict with 'audio_b64' (base64 WebM) when user audio is captured,
        or None if nothing captured yet.
    """
    result = _voice_component(
        tts_audio_b64=tts_audio_b64,
        silence_threshold=SILENCE_THRESHOLD,
        silence_duration=SILENCE_DURATION,
        mic_delay_ms=MIC_DELAY_MS,
        min_speech_duration=MIN_SPEECH_DURATION,
        key=key,
        default=None,
    )
    return result
