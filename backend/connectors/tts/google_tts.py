"""Google Cloud TTS connector — synthesize Marathi text to audio."""

import base64

from backend.services.tts import synthesize_marathi


def speak_marathi(text: str) -> dict:
    """Synthesize Marathi text to audio. Returns base64-encoded MP3.

    Returns:
        {"audio_base64": str, "format": "mp3"}
    """
    audio_bytes = synthesize_marathi(text)
    return {
        "audio_base64": base64.b64encode(audio_bytes).decode("ascii"),
        "format": "mp3",
    }
