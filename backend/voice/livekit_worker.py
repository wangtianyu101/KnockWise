"""LiveKit Agent Worker — bridges real-time voice with the LangGraph interview engine.

Audio flow:
  User mic → LiveKit Server → Agent Worker (this) → WhisperLive STT
  → LangGraph Agent → piper-tts → LiveKit Server → User speaker

Uses local WhisperLive + Piper TTS (zero external dependencies).
Falls back to SimpleSTT (batch whisper) when WhisperLive is unavailable.
"""

import asyncio
import logging
from typing import AsyncIterable, Optional

from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli
from livekit.agents.llm import ChatContext, ChatMessage
from livekit.agents.voice import VoicePipelineAgent
from livekit.plugins import silero

from core.config import settings
from agents.states import create_initial_state
from agents.question_agent import question_engine
from agents.followup_agent import followup_engine

logger = logging.getLogger("codemock-voice")


class LocalSTT:
    """LiveKit-compatible STT adapter using our local WhisperLive / SimpleSTT."""

    def __init__(self):
        self._whisper_client = None
        self._simple_stt = None
        self._connected = False

    async def _ensure_whisper(self):
        if self._whisper_client is not None:
            return
        try:
            from voice.stt import WhisperLiveClient
            self._whisper_client = WhisperLiveClient()
            await self._whisper_client.connect()
            self._connected = True
            logger.info("WhisperLive STT connected")
        except Exception as e:
            logger.warning(f"WhisperLive unavailable ({e}), using SimpleSTT fallback")
            self._whisper_client = None

    def _get_simple_stt(self):
        if self._simple_stt is None:
            from voice.stt import SimpleSTT
            self._simple_stt = SimpleSTT()
        return self._simple_stt

    async def recognize(self, *, audio: bytes) -> str:
        """Recognize speech from raw audio bytes."""
        if not audio or len(audio) < 160:  # at least 10ms at 16kHz
            return ""

        if self._whisper_client is not None:
            try:
                await self._whisper_client.send_audio(audio)
                # In streaming mode, we'd need to handle VAD-based sentence boundaries.
                # For now, return accumulated text from WhisperLive.
                text = await self._whisper_client.receive_transcript()
                return text
            except Exception:
                pass

        # Fallback: batch transcribe with SimpleSTT
        try:
            return self._get_simple_stt().transcribe_bytes(audio)
        except Exception as e:
            logger.warning(f"STT failure: {e}")
            return ""

    async def aclose(self):
        if self._whisper_client:
            try:
                await self._whisper_client.close()
            except Exception:
                pass
            self._whisper_client = None


class LocalTTS:
    """LiveKit-compatible TTS adapter using piper-tts."""

    def __init__(self):
        self._engine = None
        self._sample_rate = 22050

    def _ensure_engine(self):
        if self._engine is not None:
            return
        try:
            from voice.tts import get_tts
            self._engine = get_tts()
            self._sample_rate = self._engine.voice.config.sample_rate
            logger.info(f"Piper TTS loaded (sample_rate={self._sample_rate})")
        except Exception as e:
            logger.warning(f"Piper TTS unavailable ({e})")
            self._engine = None

    def synthesize(self, *, text: str) -> bytes:
        """Synthesize text to WAV audio bytes."""
        self._ensure_engine()
        if self._engine is None:
            return b""
        try:
            return self._engine.synthesize(text)
        except Exception as e:
            logger.warning(f"TTS failure: {e}")
            return b""


class InterviewAgent(VoicePipelineAgent):
    """Voice-enabled interview agent that wraps the LangGraph interview engine."""

    def __init__(self, ctx: JobContext):
        # Use local STT/TTS adapters instead of cloud services
        local_stt = LocalSTT()
        local_tts = LocalTTS()

        super().__init__(
            vad=silero.VAD.load(),
            stt=local_stt,
            tts=local_tts,
            chat_ctx=ChatContext(),
        )
        self.ctx = ctx
        self.interview_state = None
        self.profile = {
            "tech_stack": ["LangChain", "LangGraph", "RAG"],
            "years_of_exp": 3,
            "current_level": "mid",
            "target_companies": [],
        }

    async def on_enter(self):
        """Called when a user joins the voice room."""
        await self.ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
        logger.info(f"User joined room: {self.ctx.room.name}")

        # Greet and start interview flow
        self.interview_state = create_initial_state(
            user_id="voice_user",
            profile=self.profile,
            round="round1",
        )

        greeting = (
            "你好，我是今天的面试官。"
            "开始之前，简单介绍一下你自己吧？你主要用哪些技术栈、几年经验、在看什么机会？"
        )
        await self.say(greeting)

    async def on_user_message(self, text: str):
        """Handle transcribed user speech."""
        if not text.strip():
            return

        phase = (
            self.interview_state.get("interview_phase", "intro")
            if self.interview_state
            else "intro"
        )

        if phase == "intro":
            await self._handle_intro(text)
        elif phase in ("questioning", "following_up"):
            await self._handle_answer(text)

    async def _handle_intro(self, text: str):
        """Extract profile from intro conversation."""
        tech_keywords = [
            "langchain", "langgraph", "rag", "python", "go", "java",
            "react", "vue", "k8s", "docker", "agent", "llm"
        ]
        found_tech = [t for t in tech_keywords if t.lower() in text.lower()]

        if found_tech:
            self.profile["tech_stack"] = list(set(found_tech))
            self.interview_state["profile"] = self.profile

        next_q = question_engine.select_next_question(
            round="round1",
            profile=self.profile,
            questions_asked=[],
            blind_spots=[],
        )
        if next_q:
            self.interview_state["current_question"] = next_q
            self.interview_state["current_question_id"] = next_q["id"]
            self.interview_state["interview_phase"] = "questioning"
            await self.say(next_q["question_text"])
        else:
            await self.say("好的，我们直接开始吧。请简单说一下你对 Agent 架构的理解？")

    async def _handle_answer(self, text: str):
        """Process an interview answer through the followup engine."""
        self.interview_state["user_answer"] = text

        question = self.interview_state.get("current_question", {})
        result = await followup_engine.determine_action(
            question=question,
            user_answer=text,
            current_depth=self.interview_state.get("current_depth", 0),
            followup_count=self.interview_state.get("followup_count", 0),
            max_depth=4,
        )

        action = result.get("action", "next_question")

        if action == "skip_and_record":
            self.interview_state["blind_spots"] = self.interview_state.get(
                "blind_spots", []
            ) + [result.get("blind_spot", "")]
            await self.say("好的，我们换个方向。")

            next_q = question_engine.select_next_question(
                round=self.interview_state.get("round", "round1"),
                profile=self.profile,
                questions_asked=self.interview_state.get("questions_asked", []),
                blind_spots=self.interview_state.get("blind_spots", []),
            )
            if next_q:
                self.interview_state["current_question"] = next_q
                self.interview_state["current_question_id"] = next_q["id"]
                self.interview_state["current_depth"] = 0
                self.interview_state["followup_count"] = 0
                await self.say(next_q["question_text"])
            else:
                await self.say("面试就到这里，感谢你的时间。稍后给你一份面试报告。")
                self.interview_state["interview_phase"] = "done"

        elif action in ("followup", "probe", "give_hint", "degrade"):
            self.interview_state["current_depth"] = (
                self.interview_state.get("current_depth", 0) + 1
            )
            self.interview_state["followup_count"] = (
                self.interview_state.get("followup_count", 0) + 1
            )
            followup_text = result.get("followup_text", "能再详细说说吗？")
            await self.say(followup_text)

        else:  # next_question
            next_q = question_engine.select_next_question(
                round=self.interview_state.get("round", "round1"),
                profile=self.profile,
                questions_asked=self.interview_state.get("questions_asked", []),
                blind_spots=self.interview_state.get("blind_spots", []),
            )
            if next_q:
                self.interview_state["current_question"] = next_q
                self.interview_state["current_question_id"] = next_q["id"]
                self.interview_state["current_depth"] = 0
                self.interview_state["followup_count"] = 0
                await self.say(next_q["question_text"])
            else:
                await self.say("面试就到这里，感谢你的时间！")
                self.interview_state["interview_phase"] = "done"


def entrypoint(ctx: JobContext):
    """LiveKit agent entry point."""
    agent = InterviewAgent(ctx)
    agent.start(ctx.room)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
