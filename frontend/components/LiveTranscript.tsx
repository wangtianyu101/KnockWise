/**
 * LiveTranscript — scrolling transcript display for real-time conversation.
 * Shows AI and user speech in a chat-like interface with auto-scroll.
 */

import { useEffect, useRef, useState } from "react";

interface Line {
  id: number;
  speaker: "ai" | "user";
  text: string;
  time: string;
}

interface Props {
  lines: Line[];
  maxLines?: number;
}

export default function LiveTranscript({ lines, maxLines = 50 }: Props) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [lines]);

  const displayLines = lines.slice(-maxLines);

  return (
    <div className="w-full">
      {/* Toggle header */}
      <button
        onClick={() => setVisible(!visible)}
        className="flex items-center gap-2 text-xs text-gray-500 mb-2 hover:text-gray-300 transition-colors"
      >
        <span>{visible ? "▼" : "▶"}</span>
        实时字幕 ({lines.length})
      </button>

      {visible && (
        <div
          ref={scrollRef}
          className="max-h-64 overflow-y-auto rounded-xl bg-white/[0.03] border border-indigo-500/10 p-4 space-y-3 scroll-smooth"
        >
          {displayLines.length === 0 && (
            <div className="text-center text-gray-600 text-sm py-4">
              等待对话开始...
            </div>
          )}
          {displayLines.map(line => (
            <div key={line.id} className={`flex gap-3 ${line.speaker === "ai" ? "" : "flex-row-reverse"}`}>
              {/* Avatar bubble */}
              <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 ${
                line.speaker === "ai"
                  ? "bg-gradient-to-br from-indigo-500 to-purple-500 text-white"
                  : "bg-white/10 text-gray-300"
              }`}>
                {line.speaker === "ai" ? "A" : "我"}
              </div>
              {/* Message */}
              <div className={`text-sm leading-relaxed px-3 py-2 rounded-2xl max-w-[75%] ${
                line.speaker === "ai"
                  ? "bg-indigo-500/10 text-gray-200 rounded-tl-sm"
                  : "bg-white/5 text-gray-300 rounded-tr-sm"
              }`}>
                <div>{line.text}</div>
                <div className="text-[10px] text-gray-600 mt-1 text-right">{line.time}</div>
              </div>
            </div>
          ))}

          {/* Typing indicator */}
          {displayLines.length > 0 && displayLines[displayLines.length - 1].speaker === "user" && (
            <div className="flex gap-2 pl-9">
              {[0, 1, 2].map(i => (
                <div key={i} className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-bounce"
                  style={{ animationDelay: `${i * 150}ms` }} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
