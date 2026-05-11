import { useEffect, useState } from "react";

interface SubtitleBarProps {
  text: string;
  visible: boolean;
}

export default function SubtitleBar({ text, visible }: SubtitleBarProps) {
  const [displayText, setDisplayText] = useState("");
  const [isAnimating, setIsAnimating] = useState(false);

  useEffect(() => {
    if (text && text !== displayText) {
      setIsAnimating(true);
      if (text.length > 30) {
        let i = 0;
        const speed = Math.max(20, Math.min(50, text.length * 2));
        const timer = setInterval(() => {
          i++;
          setDisplayText(text.slice(0, i));
          if (i >= text.length) {
            clearInterval(timer);
            setIsAnimating(false);
          }
        }, speed);
        return () => clearInterval(timer);
      } else {
        setDisplayText(text);
        setIsAnimating(false);
      }
    } else if (!text) {
      setDisplayText("");
      setIsAnimating(false);
    }
  }, [text]);

  if (!visible || !displayText) return null;

  return (
    <div className="px-6 py-3 border-t border-indigo-500/20 bg-gray-950/80 backdrop-blur-sm">
      <div className="max-w-3xl mx-auto flex items-center gap-3">
        <div className={`flex-shrink-0 w-5 h-5 ${isAnimating ? "text-purple-400" : "text-gray-600"}`}>
          <svg viewBox="0 0 24 24" fill="currentColor" className={isAnimating ? "animate-pulse" : ""}>
            <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3A4.5 4.5 0 0014 8.5v7a4.47 4.47 0 002.5-3.5zM14 3v2.06A7.009 7.009 0 0121 12a7.009 7.009 0 01-7 6.94V21a9.003 9.003 0 009-9 9.003 9.003 0 00-9-9z" />
          </svg>
        </div>
        <p className="text-sm text-gray-300 leading-relaxed">
          <span className="text-xs text-indigo-400 mr-2 font-medium">面试官</span>
          {displayText}
          {isAnimating && (
            <span className="inline-block w-0.5 h-4 bg-purple-400 ml-0.5 animate-pulse rounded-full" />
          )}
        </p>
      </div>
    </div>
  );
}
