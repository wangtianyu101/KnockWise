"""Text-to-Speech wrapper using piper-tts (local, MIT license).

Voice model: zh_CN-huayan-medium (Chinese female).
Downloads automatically from HuggingFace on first use.
"""

from __future__ import annotations

import io
import wave
from pathlib import Path

from huggingface_hub import hf_hub_download
from piper.config import SynthesisConfig

from core.config import settings


MODEL_DIR = Path(settings.upload_dir) / "piper_models"
VOICE_REPO = "rhasspy/piper-voices"
VOICE_PATH = "zh/zh_CN/huayan/medium/zh_CN-huayan-medium"

# Soft, natural-sounding voice config
_SOFT_CONFIG = SynthesisConfig(
    length_scale=1.15,     # slightly slower → softer, more deliberate pace
    noise_scale=0.4,       # lower → warmer, less robotic timbre
    noise_w_scale=0.55,    # lower → less harsh breathiness
    volume=0.9,            # slightly quieter to avoid clipping
)


def _download_model() -> tuple[str, str]:
    """Download voice model files, returning (model_path, config_path)."""
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    model_path = hf_hub_download(
        repo_id=VOICE_REPO,
        filename=f"{VOICE_PATH}.onnx",
        cache_dir=str(MODEL_DIR),
    )
    config_path = hf_hub_download(
        repo_id=VOICE_REPO,
        filename=f"{VOICE_PATH}.onnx.json",
        cache_dir=str(MODEL_DIR),
    )
    return model_path, config_path


class TTSEngine:
    """Local TTS using piper-tts with a soft Chinese female voice."""

    def __init__(self):
        from piper import PiperVoice

        model_path, config_path = _download_model()
        self.voice = PiperVoice.load(model_path, config_path=config_path)

    def synthesize(self, text: str) -> bytes:
        """Synthesize text to WAV audio bytes with a soft, natural tone."""
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            self.voice.synthesize_wav(text, wf, syn_config=_SOFT_CONFIG)

        buf.seek(0)
        return buf.read()


# Lazy singleton
_tts_engine: TTSEngine | None = None


def get_tts() -> TTSEngine:
    global _tts_engine
    if _tts_engine is None:
        _tts_engine = TTSEngine()
    return _tts_engine
