import { useState, useRef, useCallback, useEffect } from "react";

interface VoiceRoomProps {
  interviewId: string | null;
  onSpeech: (text: string) => void;
  disabled: boolean;
  onTranscribing?: (text: string) => void;
}

const LOG_MAX = 20;

export default function VoiceRoom({ interviewId, onSpeech, disabled, onTranscribing }: VoiceRoomProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [status, setStatus] = useState<"idle" | "recording" | "processing" | "done" | "error">("idle");
  const [errorMsg, setErrorMsg] = useState("");
  const [debugLogs, setDebugLogs] = useState<string[]>([]);

  const animFrame = useRef<number>(0);
  const audioContext = useRef<AudioContext | null>(null);
  const analyser = useRef<AnalyserNode | null>(null);
  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const audioChunks = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const logIndexRef = useRef(0);

  const log = useCallback((tag: string, detail: string) => {
    const ts = new Date().toISOString().slice(11, 23);
    const line = `[${ts}] ${tag}: ${detail}`;
    console.log(`[VoiceRoom] ${line}`);
    logIndexRef.current += 1;
    setDebugLogs((prev) => {
      const next = [...prev, line];
      return next.length > LOG_MAX ? next.slice(-LOG_MAX) : next;
    });
  }, []);

  useEffect(() => {
    log("INIT", `ua=${navigator.userAgent.slice(0, 60)}`);
    return () => { cleanup(); };
  }, []);

  const cleanup = useCallback(() => {
    if (animFrame.current) cancelAnimationFrame(animFrame.current);
    if (audioContext.current) { audioContext.current.close(); audioContext.current = null; }
    analyser.current = null;
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    setAudioLevel(0);
  }, []);

  const sendToBackend = useCallback(async (blob: Blob): Promise<string> => {
    log("SEND", `sending audio size=${blob.size} type=${blob.type}`);
    try {
      const formData = new FormData();
      const ext = blob.type.includes("webm") ? "webm" : blob.type.includes("wav") ? "wav" : "webm";
      formData.append("file", blob, `recording.${ext}`);

      const token = localStorage.getItem("codemock_token");
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/interviews/transcribe`,
        {
          method: "POST",
          headers: token ? { Authorization: `Bearer ${token}` } : {},
          body: formData,
        }
      );
      if (!res.ok) {
        const errText = await res.text();
        log("SEND", `ERROR HTTP ${res.status}: ${errText.slice(0, 100)}`);
        return "";
      }
      const data = await res.json();
      log("SEND", `response text="${data.text?.slice(0, 50) || ""}"`);
      return data.text || "";
    } catch (e: any) {
      log("SEND", `fetch ERROR: ${e?.message || e}`);
      return "";
    }
  }, [log]);

  const startRecording = useCallback(async () => {
    if (disabled) return;
    log("START", "begin");
    cleanup();
    setStatus("idle");
    setErrorMsg("");

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      log("MIC", `got stream tracks=${stream.getAudioTracks().length}`);

      // Audio level meter
      audioContext.current = new AudioContext();
      analyser.current = audioContext.current.createAnalyser();
      const source = audioContext.current.createMediaStreamSource(stream);
      source.connect(analyser.current);
      analyser.current.fftSize = 256;
      const dataArray = new Uint8Array(analyser.current.frequencyBinCount);

      const updateLevel = () => {
        if (!analyser.current) return;
        analyser.current.getByteFrequencyData(dataArray);
        const avg = dataArray.reduce((a, b) => a + b, 0) / dataArray.length;
        setAudioLevel(Math.min(100, avg * 2));
        animFrame.current = requestAnimationFrame(updateLevel);
      };
      updateLevel();
      log("LEVEL", "meter started");

      // MediaRecorder
      let mimeType = "audio/webm";
      if (!MediaRecorder.isTypeSupported("audio/webm")) {
        mimeType = "audio/mp4";
      }
      audioChunks.current = [];
      mediaRecorder.current = new MediaRecorder(stream, { mimeType });
      log("REC", `MediaRecorder started mime=${mimeType}`);

      mediaRecorder.current.ondataavailable = (e) => {
        if (e.data.size > 0) {
          audioChunks.current.push(e.data);
        }
      };

      mediaRecorder.current.onerror = (e: any) => {
        log("REC", `MediaRecorder ERROR: ${e?.error || e}`);
      };

      mediaRecorder.current.start(100); // collect data every 100ms
      setIsRecording(true);
      setStatus("recording");
    } catch (err: any) {
      log("MIC", `ERROR name=${err?.name} msg=${err?.message}`);
      if (err?.name === "NotAllowedError") {
        setErrorMsg("麦克风权限被拒绝，请在浏览器设置中允许");
      } else if (err?.name === "NotFoundError") {
        setErrorMsg("未检测到麦克风设备");
      } else {
        setErrorMsg(`麦克风错误: ${err?.message || err}`);
      }
      setStatus("error");
    }
  }, [disabled, cleanup, log]);

  const stopRecording = useCallback(() => {
    log("STOP", "begin");
    setIsRecording(false);

    if (mediaRecorder.current && mediaRecorder.current.state !== "inactive") {
      mediaRecorder.current.onstop = async () => {
        log("STOP", "MediaRecorder onstop fired");
        setIsProcessing(true);
        setStatus("processing");

        const mimeType = mediaRecorder.current?.mimeType || "audio/webm";
        const blob = new Blob(audioChunks.current, { type: mimeType });
        log("STOP", `blob size=${blob.size} chunks=${audioChunks.current.length}`);

        cleanup();

        if (blob.size < 100) {
          log("STOP", "blob too small — probably no audio captured");
          setErrorMsg("未录制到声音，请确保麦克风正常工作");
          setStatus("error");
          setIsProcessing(false);
          return;
        }

        const text = await sendToBackend(blob);

        if (text.trim()) {
          log("DONE", `text="${text.slice(0, 60)}..."`);
          setStatus("done");
          onSpeech(text.trim());
        } else {
          log("DONE", "backend returned empty text");
          setErrorMsg("语音识别失败，请重试或使用下方文本框输入");
          setStatus("error");
        }
        setIsProcessing(false);
      };

      mediaRecorder.current.stop();
      log("REC", "stop() called");
    } else {
      log("STOP", "MediaRecorder was not active");
      cleanup();
    }
  }, [cleanup, sendToBackend, onSpeech, log]);

  const handlePointerDown = useCallback(() => {
    if (disabled || isProcessing) return;
    startRecording();
  }, [disabled, isProcessing, startRecording]);

  const handlePointerUp = useCallback(() => {
    if (!isRecording) return;
    stopRecording();
  }, [isRecording, stopRecording]);

  return (
    <div className="flex flex-col items-center gap-3">
      {/* Audio level meter */}
      {isRecording && (
        <div className="w-full max-w-xs h-1.5 bg-gray-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 transition-all duration-100 rounded-full"
            style={{ width: `${audioLevel}%` }}
          />
        </div>
      )}

      {/* Status text */}
      {isRecording && (
        <div className="text-xs text-indigo-400 animate-pulse">录音中...</div>
      )}
      {isProcessing && (
        <div className="text-xs text-amber-400 animate-pulse">
          正在识别语音...
          <span className="inline-flex gap-1 ml-1">
            <span className="w-1 h-1 bg-amber-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
            <span className="w-1 h-1 bg-amber-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
            <span className="w-1 h-1 bg-amber-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
          </span>
        </div>
      )}

      {/* Error */}
      {errorMsg && !isProcessing && (
        <div className="text-xs text-amber-400 text-center max-w-xs">{errorMsg}</div>
      )}

      {/* Mic button */}
      <button
        onPointerDown={handlePointerDown}
        onPointerUp={handlePointerUp}
        onPointerLeave={handlePointerUp}
        disabled={disabled || isProcessing}
        className={`w-20 h-20 rounded-full flex items-center justify-center transition-all ${
          isRecording
            ? "bg-gradient-to-r from-red-500 to-pink-500 scale-110 shadow-lg shadow-red-500/30"
            : isProcessing
            ? "bg-gray-800 cursor-wait"
            : disabled
            ? "bg-gray-800 cursor-not-allowed"
            : "bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 active:scale-95 shadow-lg shadow-purple-500/20"
        }`}
        aria-label={isRecording ? "松开发送" : isProcessing ? "识别中..." : "按住说话"}
      >
        {isProcessing ? (
          <svg className="w-8 h-8 animate-spin text-gray-500" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        ) : (
          <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 14a3 3 0 003-3V5a3 3 0 10-6 0v6a3 3 0 003 3zm5-3a5 5 0 01-10 0H5a7 7 0 0014 0h-2z" />
          </svg>
        )}
      </button>

      <p className="text-xs text-gray-500">
        {isProcessing ? "识别中..." : isRecording ? "松开发送" : disabled ? "等待中..." : "按住说话"}
      </p>

      {/* Debug log panel */}
      <details className="w-full max-w-md mt-2">
        <summary className="text-[10px] text-gray-600 cursor-pointer select-none hover:text-gray-400">
          调试日志 ({debugLogs.length})
        </summary>
        <div className="mt-1 max-h-40 overflow-y-auto bg-gray-950/80 rounded-lg p-2 font-mono text-[10px] leading-relaxed space-y-0.5">
          {debugLogs.length === 0 && (
            <div className="text-gray-700">暂无日志，按住麦克风按钮开始</div>
          )}
          {debugLogs.map((l, i) => (
            <div key={i} className={
              l.includes("ERROR") ? "text-red-400" :
              l.includes("backend returned empty") ? "text-red-400" :
              l.includes("DONE") ? "text-emerald-400" :
              l.includes("response text") ? "text-emerald-300" :
              l.includes("SEND") ? "text-indigo-400" :
              l.includes("STOP") ? "text-purple-300" :
              "text-gray-500"
            }>{l}</div>
          ))}
        </div>
      </details>
    </div>
  );
}
