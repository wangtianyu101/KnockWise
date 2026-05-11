import { useEffect, useState, useCallback, useRef } from "react";
import { useRouter } from "next/router";
import { startInterview, getNextQuestion, submitAnswer, getProfile } from "@/lib/api";
import VoiceRoom from "@/components/VoiceRoom";
import SubtitleBar from "@/components/SubtitleBar";

interface Message {
  role: "interviewer" | "user" | "system";
  content: string;
  type?: string;
}

interface QuestionState {
  record_id: string;
  question_id: string;
  question_text: string;
  topic: string;
  sub_topic: string;
  followup_tree: any;
  asked_count?: number;
}

export default function InterviewPage() {
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([]);
  const [question, setQuestion] = useState<QuestionState | null>(null);
  const [interviewId, setInterviewId] = useState<string | null>(null);
  const [isThinking, setIsThinking] = useState(false);
  const [phase, setPhase] = useState<"intro" | "questioning" | "done">("intro");
  const [subtitleText, setSubtitleText] = useState("");
  const [liveTranscript, setLiveTranscript] = useState("");
  const [transcriptError, setTranscriptError] = useState<string | null>(null);
  const [ttsEnabled, setTtsEnabled] = useState(true);
  const [setupInfo, setSetupInfo] = useState<any>(null);
  const [textInput, setTextInput] = useState("");
  const messagesEnd = useRef<HTMLDivElement>(null);
  const ttsVoice = useRef<SpeechSynthesisVoice | null>(null);
  const ttsReady = useRef(false);

  // Load best Chinese TTS voice on mount
  useEffect(() => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) return;

    const loadVoices = () => {
      const voices = window.speechSynthesis.getVoices();
      if (voices.length === 0) return;

      // Try to find the most natural Chinese voice
      // macOS: Ting-Ting (zh-CN) is very natural
      // Chrome: Google 普通话（中国大陆）or Microsoft Huihui
      const preferred = voices.find(
        (v) => v.lang === "zh-CN" && (v.name.includes("Ting-Ting") || v.name.includes("TingTing"))
      ) || voices.find(
        (v) => v.lang === "zh-CN" && v.name.includes("Google")
      ) || voices.find(
        (v) => v.lang === "zh-CN"
      ) || voices.find(
        (v) => v.lang.startsWith("zh-TW")
      ) || voices.find(
        (v) => v.lang.startsWith("zh")
      );

      if (preferred) {
        ttsVoice.current = preferred;
        ttsReady.current = true;
      }
    };

    loadVoices();
    window.speechSynthesis.onvoiceschanged = loadVoices;
    return () => { window.speechSynthesis.onvoiceschanged = null; };
  }, []);

  // Browser TTS — softer, more human-like
  function speakText(text: string) {
    if (!ttsEnabled || typeof window === "undefined" || !("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "zh-CN";
    utterance.rate = 0.92;    // slightly slower — more deliberate
    utterance.pitch = 1.0;    // natural pitch
    utterance.volume = 0.85;  // comfortable volume

    if (ttsVoice.current) {
      utterance.voice = ttsVoice.current;
    }

    // Speak with a tiny delay for a more natural conversational rhythm
    setTimeout(() => {
      window.speechSynthesis.speak(utterance);
    }, 150);
  }

  useEffect(() => {
    const raw = localStorage.getItem("codemock_setup");
    if (raw) {
      try { setSetupInfo(JSON.parse(raw)); } catch {}
    }
    initInterview();
  }, []);

  useEffect(() => {
    messagesEnd.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, liveTranscript, isThinking]);

  async function initInterview() {
    try {
      await getProfile();
      const raw = localStorage.getItem("codemock_setup");
      let round = "round1";
      if (raw) {
        try { const s = JSON.parse(raw); round = s.round || "round1"; } catch {}
      }
      const interview = await startInterview(round);
      setInterviewId(interview.id);

      if (setupInfo) {
        const roundLabel = { round1: "一面", round2: "二面", round3: "三面" }[round] || round;
        addMessage("system", `🎯 ${setupInfo.company} · ${setupInfo.department} · ${roundLabel} · ${setupInfo.role}`);
      }
      addMessage("interviewer", "你好，我是今天的面试官。准备好了吗？我们开始第一题。");
      await askNextQuestion(interview.id);
    } catch {
      router.push("/");
    }
  }

  async function askNextQuestion(ivId: string) {
    setIsThinking(true);
    try {
      const data = await getNextQuestion(ivId);
      setQuestion(data);
      addMessage("interviewer", data.question_text);
      setSubtitleText(data.question_text);
      setPhase("questioning");
      speakText(data.question_text);
    } finally {
      setIsThinking(false);
    }
  }

  function addMessage(role: "interviewer" | "user" | "system", content: string) {
    setMessages((prev) => [...prev, { role, content }]);
  }

  const handleLiveTranscript = useCallback((text: string) => {
    setLiveTranscript(text);
    setTranscriptError(null);
  }, []);

  const onUserSpeech = useCallback(async (text: string) => {
    if (!text.trim() || !interviewId || !question) return;

    addMessage("user", text);
    setLiveTranscript("");
    setIsThinking(true);
    setSubtitleText("");

    try {
      const result = await submitAnswer(question.record_id, text, 0);
      setPhase("questioning");

      if (result.followup_text && result.has_followup) {
        addMessage("interviewer", result.followup_text);
        setSubtitleText(result.followup_text);
        speakText(result.followup_text);
        setQuestion((prev) => prev ? { ...prev } : prev);
      } else {
        await askNextQuestion(interviewId);
      }

      if (result.score) {
        const scoreEmoji = result.score >= 4 ? "" : result.score >= 3 ? "" : "";
        addMessage("system", `评分: ${result.score}/5 ${scoreEmoji}  ${result.feedback || ""}`);
      }
    } finally {
      setIsThinking(false);
    }
  }, [interviewId, question]);

  if (phase === "done") {
    return (
      <div className="min-h-screen gradient-page text-white flex flex-col items-center justify-center gap-4">
        <div className="gradient-card rounded-2xl p-10 text-center max-w-md animate-slideUp">
          <div className="text-5xl mb-4"></div>
          <h2 className="text-2xl font-bold bg-gradient-to-r from-emerald-400 to-teal-400 bg-clip-text text-transparent">
            面试完成
          </h2>
          <p className="text-gray-400 mt-2">正在为你生成面试报告...</p>
          <button
            onClick={() => router.push(`/report?interviewId=${interviewId}`)}
            className="mt-6 px-8 py-3 rounded-xl font-medium bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 shadow-lg shadow-purple-500/20 transition-all"
          >
            查看报告
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen gradient-page text-white flex flex-col">
      {/* Header */}
      <div className="px-6 py-3 border-b border-indigo-500/20 flex items-center justify-between bg-gray-950/50 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
            CodeMock
          </h1>
          {setupInfo && (
            <span className="text-xs text-gray-500 hidden sm:inline">
              {setupInfo.company} · {setupInfo.round === "round2" ? "二面" : setupInfo.round === "round3" ? "三面" : "一面"}
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setTtsEnabled(!ttsEnabled)}
            className={`text-xs px-3 py-1.5 rounded-full transition-all duration-200 ${
              ttsEnabled
                ? "bg-gradient-to-r from-emerald-500 to-teal-500 text-white shadow-lg shadow-emerald-500/20"
                : "bg-gray-800 text-gray-400"
            }`}
          >
            {ttsEnabled ? " 声音 开" : " 声音 关"}
          </button>
          <span className={`text-xs px-2 py-1 rounded-full ${
            phase === "intro" ? "bg-yellow-500/20 text-yellow-400" : phase === "questioning" ? "bg-emerald-500/20 text-emerald-400" : "bg-gray-700 text-gray-400"
          }`}>
            {phase === "intro" ? "准备中" : "面试中"}
          </span>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4 max-w-3xl mx-auto w-full">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-3 animate-fadeIn ${
                msg.role === "interviewer"
                  ? "gradient-card text-gray-100"
                  : msg.role === "user"
                  ? "bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-lg shadow-purple-500/20"
                  : "bg-gray-900/50 text-gray-400 text-sm italic border border-gray-800"
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}

        {/* Live transcript */}
        {liveTranscript && (
          <div className="flex justify-end">
            <div className="max-w-[80%] rounded-2xl px-4 py-3 bg-indigo-500/30 text-gray-300 text-sm italic border border-indigo-500/30">
              {liveTranscript}
              <span className="inline-block w-1.5 h-4 bg-purple-400 ml-1 animate-pulse align-middle rounded-full" />
            </div>
          </div>
        )}

        {/* Thinking */}
        {isThinking && (
          <div className="flex justify-start">
            <div className="gradient-card rounded-2xl px-5 py-3 shimmer">
              <span className="inline-flex gap-1.5">
                <span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                <span className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                <span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
              </span>
            </div>
          </div>
        )}

        {transcriptError && (
          <div className="flex justify-center">
            <div className="bg-red-500/10 text-red-400 text-xs rounded-lg px-3 py-1.5 border border-red-500/20">
              {transcriptError}
            </div>
          </div>
        )}

        <div ref={messagesEnd} />
      </div>

      <SubtitleBar text={subtitleText} visible={!isThinking && !!subtitleText} />

      {/* Input area: voice + text fallback */}
      <div className="border-t border-indigo-500/20 bg-gray-950/30">
        <VoiceRoom
          interviewId={interviewId}
          onSpeech={onUserSpeech}
          disabled={isThinking || phase === "done"}
          onTranscribing={handleLiveTranscript}
        />

        {/* Text input fallback */}
        <div className="px-6 pb-4 max-w-lg mx-auto">
          <div className="flex gap-2 items-center">
            <input
              type="text"
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && textInput.trim()) {
                  onUserSpeech(textInput.trim());
                  setTextInput("");
                }
              }}
              placeholder="或直接输入文字回答..."
              disabled={isThinking || phase === "done"}
              className="flex-1 bg-gray-800/50 border border-gray-700/50 rounded-xl px-4 py-2.5 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500 transition-colors disabled:opacity-40"
            />
            <button
              onClick={() => {
                if (textInput.trim()) {
                  onUserSpeech(textInput.trim());
                  setTextInput("");
                }
              }}
              disabled={!textInput.trim() || isThinking || phase === "done"}
              className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 text-sm font-medium disabled:opacity-30 disabled:cursor-not-allowed hover:from-indigo-500 hover:to-purple-500 transition-all shadow-lg shadow-purple-500/20 flex-shrink-0"
            >
              发送
            </button>
          </div>
          <p className="text-center text-[10px] text-gray-600 mt-2">
            按住上方麦克风说话，或在此输入文字
          </p>
        </div>
      </div>
    </div>
  );
}
