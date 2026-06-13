/**
 * Interview Room — full-duplex voice interview page.
 * Replaces old PTT-based interview.tsx with real-time phone-call experience.
 */

import { useEffect, useState, useRef, useCallback } from "react";
import { useRouter } from "next/router";
import { getToken } from "@/lib/api";
import LiveKitVoice from "@/components/LiveKitVoice";
import InterviewerAvatar from "@/components/InterviewerAvatar";
import LiveTranscript from "@/components/LiveTranscript";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const LK_URL = process.env.NEXT_PUBLIC_LIVEKIT_URL || "ws://localhost:7880";

type VoiceState = "connecting" | "connected" | "listening" | "speaking" | "disconnected" | "error";
type RoomState = "connecting" | "ready" | "interviewing" | "ended";

export default function InterviewRoom() {
  const router = useRouter();
  const { id } = router.query;

  const [roomState, setRoomState] = useState<RoomState>("connecting");
  const [voiceState, setVoiceState] = useState<VoiceState>("connecting");
  const [lkToken, setLkToken] = useState("");
  const [transcript, setTranscript] = useState<{ id: number; speaker: "ai" | "user"; text: string; time: string }[]>([]);
  const [duration, setDuration] = useState(0);
  const counter = useRef(0);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Map voice state to avatar state
  const avatarState = (
    voiceState === "speaking" ? "speaking" :
    voiceState === "listening" ? "listening" :
    voiceState === "connected" ? "listening" :
    voiceState === "connecting" ? "thinking" :
    "idle"
  ) as "idle" | "listening" | "speaking" | "thinking" | "disconnected";

  // Get LiveKit token
  useEffect(() => {
    if (!id) return;
    const h = { Authorization: `Bearer ${getToken()}` };
    fetch(`${API}/api/interviews/livekit-token`, {
      method: "POST",
      headers: { ...h, "Content-Type": "application/json" },
      body: JSON.stringify({ room_name: `interview-${id}`, participant_name: "user" }),
    })
      .then(r => r.json())
      .then(d => {
        setLkToken(d.token);
        setRoomState("ready");
      })
      .catch(() => setRoomState("connecting"));
  }, [id]);

  // Timer
  useEffect(() => {
    if (roomState === "interviewing") {
      timerRef.current = setInterval(() => setDuration(d => d + 1), 1000);
    }
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [roomState]);

  const addLine = useCallback((text: string, speaker: "ai" | "user") => {
    counter.current += 1;
    const now = new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    setTranscript(prev => [...prev, { id: counter.current, speaker, text, time: now }]);
  }, []);

  const handleTranscript = (text: string, speaker: "ai" | "user") => {
    addLine(text, speaker);
  };

  const handleVoiceState = (s: VoiceState) => {
    setVoiceState(s);
    if (s === "connected" || s === "listening" || s === "speaking") {
      setRoomState("interviewing");
    }
  };

  const endInterview = () => {
    if (timerRef.current) clearInterval(timerRef.current);
    setRoomState("ended");
    router.push("/interview/history");
  };

  const fmtDuration = (s: number) => {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return `${m.toString().padStart(2, "0")}:${sec.toString().padStart(2, "0")}`;
  };

  return (
    <div className="min-h-screen bg-[#050914] text-[#f1f5f9] flex flex-col">
      {/* Top bar */}
      <nav className="flex items-center justify-between px-6 py-3 bg-[#0c1024]/90 backdrop-blur-xl border-b border-indigo-500/10">
        <button onClick={endInterview} className="text-gray-400 hover:text-white text-sm transition-colors">← 退出</button>
        <div className="text-sm font-medium">面试中</div>
        <div className="text-sm font-mono text-indigo-400">{fmtDuration(duration)}</div>
      </nav>

      {/* Main area */}
      <main className="flex-1 flex flex-col items-center justify-center px-6 py-8 max-w-2xl mx-auto w-full gap-8">
        {/* Interviewer avatar */}
        <InterviewerAvatar state={avatarState} name="Alex" />

        {/* Voice connection — hidden UI, just the state */}
        {lkToken && (
          <LiveKitVoice
            roomName={`interview-${id}`}
            token={lkToken}
            onTranscript={handleTranscript}
            onStateChange={handleVoiceState}
          />
        )}

        {/* Connection status for no token yet */}
        {!lkToken && (
          <div className="text-gray-400 text-sm animate-pulse">正在连接语音服务...</div>
        )}

        {/* Transcript */}
        <div className="w-full mt-4">
          <LiveTranscript lines={transcript} />
        </div>
      </main>

      {/* Bottom controls */}
      <footer className="px-6 py-4 border-t border-indigo-500/10 flex justify-center">
        <button
          onClick={endInterview}
          className="px-8 py-3 rounded-full bg-red-500/20 text-red-400 border border-red-500/30 hover:bg-red-500/30 transition-all font-medium text-sm"
        >
          ⏹ 结束面试
        </button>
      </footer>
    </div>
  );
}
