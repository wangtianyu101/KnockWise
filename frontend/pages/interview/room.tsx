/**
 * Interview Room — browser-native speech recognition + backend interview agent.
 * Flow: mic → SpeechRecognition → text → POST /api/interviews → TTS response
 */

import { useEffect, useState, useRef, useCallback } from "react";
import { useRouter } from "next/router";
import { getToken } from "@/lib/api";
import InterviewerAvatar from "@/components/InterviewerAvatar";
import LiveTranscript from "@/components/LiveTranscript";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type RoomState = "connecting" | "ready" | "interviewing" | "ended";
type AvatarState = "idle" | "listening" | "speaking" | "thinking" | "disconnected";

export default function InterviewRoom() {
  const router = useRouter();
  const { id } = router.query;

  const [roomState, setRoomState] = useState<RoomState>("connecting");
  const [avatarState, setAvatarState] = useState<AvatarState>("idle");
  const [transcript, setTranscript] = useState<{ id: number; speaker: "ai" | "user"; text: string; time: string }[]>([]);
  const [duration, setDuration] = useState(0);
  const [interviewId, setInterviewId] = useState<string>("");
  const counter = useRef(0);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const recognitionRef = useRef<any>(null);
  const synthRef = useRef<SpeechSynthesis | null>(null);

  // Init: create interview via REST API
  useEffect(() => {
    if (!getToken()) { router.push("/"); return; }
    const init = async () => {
      const h = { Authorization: `Bearer ${getToken()}`, "Content-Type": "application/json" };
      const res = await fetch(`${API}/api/interviews`, {
        method: "POST", headers: h, body: JSON.stringify({ round: "round1", style: "standard" }),
      });
      const data = await res.json();
      setInterviewId(data.id);
      setRoomState("ready");
      startListening(data.id);
    };
    init().catch(() => setRoomState("connecting"));
  }, []);

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

  const speak = useCallback((text: string) => {
    if (!synthRef.current) synthRef.current = window.speechSynthesis;
    const s = synthRef.current;
    s.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = "zh-CN";
    u.rate = 1.1;
    u.onstart = () => setAvatarState("speaking");
    u.onend = () => { setAvatarState("listening"); startListening(interviewId); };
    // Find Chinese voice
    const voices = s.getVoices();
    const zh = voices.find(v => v.lang.startsWith("zh"));
    if (zh) u.voice = zh;
    s.speak(u);
    addLine(text, "ai");
  }, [interviewId, addLine]);

  const sendAnswer = useCallback(async (text: string) => {
    addLine(text, "user");
    setAvatarState("thinking");

    // Just call a simple answer endpoint that returns the next AI response
    const h = { Authorization: `Bearer ${getToken()}`, "Content-Type": "application/json" };
    const res = await fetch(`${API}/api/interviews/voice/respond`, {
      method: "POST", headers: h,
      body: JSON.stringify({ interview_id: interviewId, user_answer: text }),
    });
    const data = await res.json();
    speak(data.response);
  }, [interviewId, addLine, speak]);

  const startListening = useCallback((iid: string) => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      addLine("浏览器不支持语音识别，请使用 Chrome", "ai");
      return;
    }
    const rec = new SpeechRecognition();
    rec.lang = "zh-CN";
    rec.interimResults = false;
    rec.continuous = false;
    rec.onresult = (e: any) => {
      const text = e.results[0][0].transcript;
      if (text.trim()) sendAnswer(text.trim());
    };
    rec.onerror = (e: any) => {
      if (e.error === "no-speech") startListening(iid);
      else addLine(`语音错误: ${e.error}`, "ai");
    };
    rec.onend = () => {};
    recognitionRef.current = rec;
    try { rec.start(); setAvatarState("listening"); } catch {}
  }, [sendAnswer, addLine]);

  const endInterview = () => {
    if (timerRef.current) clearInterval(timerRef.current);
    if (recognitionRef.current) recognitionRef.current.stop();
    if (synthRef.current) synthRef.current.cancel();
    setRoomState("ended");
    router.push("/interview/history");
  };

  const fmtDuration = (s: number) => {
    const m = Math.floor(s / 60), sec = s % 60;
    return `${m.toString().padStart(2, "0")}:${sec.toString().padStart(2, "0")}`;
  };

  return (
    <div className="min-h-screen bg-[#050914] text-[#f1f5f9] flex flex-col">
      <nav className="flex items-center justify-between px-6 py-3 bg-[#0c1024]/90 backdrop-blur-xl border-b border-indigo-500/10">
        <button onClick={endInterview} className="text-gray-400 hover:text-white text-sm">← 退出</button>
        <div className="text-sm font-medium">面试中</div>
        <div className="text-sm font-mono text-indigo-400">{fmtDuration(duration)}</div>
      </nav>

      <main className="flex-1 flex flex-col items-center justify-center px-6 py-8 max-w-2xl mx-auto w-full gap-8">
        <InterviewerAvatar state={avatarState} name="Alex" />

        {roomState === "connecting" && <div className="text-gray-400 text-sm animate-pulse">正在创建面试...</div>}
        {roomState === "ready" && <div className="text-gray-400 text-sm">点击下方开始</div>}
        {roomState === "interviewing" && (
          <div className="text-xs text-gray-500">
            {avatarState === "listening" && "🎤 正在聆听，请说话..."}
            {avatarState === "thinking" && "🤔 正在思考..."}
            {avatarState === "speaking" && "🔊 面试官正在说话..."}
          </div>
        )}

        <div className="w-full mt-4">
          <LiveTranscript lines={transcript} />
        </div>
      </main>

      <footer className="px-6 py-4 border-t border-indigo-500/10 flex justify-center gap-4">
        {roomState === "ready" && (
          <button onClick={() => { setRoomState("interviewing"); startListening(interviewId); }}
            className="px-8 py-3 rounded-full bg-gradient-to-r from-indigo-500 to-purple-500 text-white shadow-lg font-medium text-sm">
            🎤 开始面试
          </button>
        )}
        {roomState === "interviewing" && (
          <button onClick={endInterview}
            className="px-8 py-3 rounded-full bg-red-500/20 text-red-400 border border-red-500/30 hover:bg-red-500/30 transition-all font-medium text-sm">
            ⏹ 结束面试
          </button>
        )}
      </footer>
    </div>
  );
}
