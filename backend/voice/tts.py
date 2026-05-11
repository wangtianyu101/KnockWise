"""Text-to-Speech wrapper using piper-tts (local, MIT license).

Voice models download automatically on first use.
Chinese voices available: zh_CN-huayan-medium (female), zh_CN-huayan-low
"""

import io
import wave
from pathlib import Path

from core.config import settings


MODEL_DIR = Path(settings.upload_dir) / "piper_models"


class TTSEngine:
    """Local TTS using piper-tts with Chinese female voice (huayan-medium)."""

    def __init__(self, voice_name: str = "zh_CN-huayan-medium"):
        from piper import PiperVoice

        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        self.voice = PiperVoice.load(voice_name, download_dir=str(MODEL_DIR))

    def synthesize(self, text: str) -> bytes:
        """Synthesize text to WAV audio bytes."""
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.voice.config.sample_rate)
            self.voice.synthesize(text, wf)

        buf.seek(0)
        return buf.read()


# Lazy singleton
_tts_engine: TTSEngine | None = None


def get_tts() -> TTSEngine:
    global _tts_engine
    if _tts_engine is None:
        _tts_engine = TTSEngine()
    return _tts_engine
