"""Lightweight WhisperLive-compatible WebSocket server using faster-whisper.

Replaces the Docker-based ghcr.io/collabora/whisperlive:latest.
Protocol: accepts binary audio chunks via WebSocket, returns JSON transcripts.

Start: python voice/whisper_live_server.py
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import tempfile
from pathlib import Path

import websockets
from websockets.asyncio.server import serve

from core.config import settings

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

logger = logging.getLogger("knockwise.whisper-live")
MODEL_DIR = Path(settings.upload_dir) / "whisper_models"
MODEL_SIZE = os.environ.get("WHISPER_MODEL", "tiny")  # tiny=75MB, base=145MB

_model = None


def _load_model():
    global _model
    if _model is not None:
        return
    from faster_whisper import WhisperModel
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Loading faster-whisper '{MODEL_SIZE}' (first use downloads ~75MB)...")
    _model = WhisperModel(
        MODEL_SIZE, device="cpu", compute_type="int8", download_root=str(MODEL_DIR),
    )
    logger.info("Whisper model ready")


def _transcribe_file(path: str) -> str:
    _load_model()
    try:
        segments, _ = _model.transcribe(path, language="zh", beam_size=5, vad_filter=True)
        return "".join(s.text for s in segments).strip()
    except Exception:
        return ""


async def handle(websocket):
    """Per-connection handler. Accumulates audio into a temp file, transcribes on close."""
    fd, tmp_path = tempfile.mkstemp(suffix=".webm")
    os.close(fd)
    try:
        async for message in websocket:
            if isinstance(message, bytes):
                with open(tmp_path, "ab") as f:
                    f.write(message)
            elif isinstance(message, str):
                try:
                    data = json.loads(message)
                except json.JSONDecodeError:
                    data = {}
                if data.get("eof"):
                    text = _transcribe_file(tmp_path)
                    await websocket.send(json.dumps({"text": text}))
                    # Clear for next utterance
                    with open(tmp_path, "wb"):
                        pass
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


async def main():
    host, port = "0.0.0.0", 9090
    logger.info(f"WhisperLive (faster-whisper) listening on ws://{host}:{port}")
    async with serve(handle, host, port):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
    asyncio.run(main())
