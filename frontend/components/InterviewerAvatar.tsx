/**
 * InterviewerAvatar — animated avatar for the virtual interviewer.
 * States: idle (静止) | listening (呼吸灯) | speaking (嘴部动画) | thinking (旋转)
 */

type AvatarState = "idle" | "listening" | "speaking" | "thinking" | "disconnected";

interface Props {
  state: AvatarState;
  name?: string;
}

export default function InterviewerAvatar({ state, name = "Alex" }: Props) {
  const ringColor = {
    idle: "border-gray-600",
    listening: "border-emerald-400 shadow-emerald-500/30",
    speaking: "border-indigo-400 shadow-indigo-500/50",
    thinking: "border-amber-400 shadow-amber-500/30",
    disconnected: "border-gray-700",
  }[state];

  return (
    <div className="flex flex-col items-center gap-3">
      {/* Avatar circle */}
      <div className={`relative w-24 h-24 md:w-32 md:h-32 rounded-full border-3 transition-all duration-500 ${ringColor} ${
        state === "speaking" || state === "thinking" ? "shadow-xl" : "shadow-md"
      }`}>
        {/* Face */}
        <div className="absolute inset-0 rounded-full bg-gradient-to-br from-indigo-500/20 to-purple-500/20 flex items-center justify-center overflow-hidden">
          {/* Eyes */}
          <div className="flex gap-4 md:gap-6">
            <div className={`w-2.5 h-2.5 md:w-3 md:h-3 rounded-full bg-indigo-300 transition-all duration-300 ${
              state === "speaking" ? "scale-125" : ""
            }`} />
            <div className={`w-2.5 h-2.5 md:w-3 md:h-3 rounded-full bg-indigo-300 transition-all duration-300 ${
              state === "speaking" ? "scale-125" : ""
            }`} />
          </div>

          {/* Mouth */}
          <div className="absolute bottom-5 md:bottom-7 left-1/2 -translate-x-1/2">
            {state === "speaking" ? (
              // Animated mouth when speaking
              <div className="flex gap-1">
                {[0, 1, 2].map(i => (
                  <div key={i} className="w-1 h-1 md:w-1.5 md:h-1.5 rounded-full bg-indigo-400 animate-bounce"
                    style={{ animationDelay: `${i * 100}ms`, animationDuration: "600ms" }} />
                ))}
              </div>
            ) : state === "thinking" ? (
              // Thinking dots
              <div className="flex gap-1 animate-pulse">
                <div className="w-1 h-1 rounded-full bg-amber-400" />
                <div className="w-1 h-1 rounded-full bg-amber-400" />
                <div className="w-1 h-1 rounded-full bg-amber-400" />
              </div>
            ) : (
              // Resting mouth
              <div className="w-5 h-1 rounded-full bg-indigo-400/40" />
            )}
          </div>
        </div>

        {/* Listening ring animation */}
        {state === "listening" && (
          <div className="absolute inset-0 rounded-full border-2 border-emerald-400/30 animate-ping" />
        )}

        {/* Speaking ring */}
        {state === "speaking" && (
          <div className="absolute -inset-1 rounded-full border-2 border-indigo-400/20 animate-pulse" />
        )}
      </div>

      {/* Name + Status */}
      <div className="text-center">
        <div className="text-lg font-semibold">{name}</div>
        <div className="text-xs text-gray-500 mt-0.5">
          {state === "idle" && "等待中"}
          {state === "listening" && "正在聆听..."}
          {state === "speaking" && "说话中"}
          {state === "thinking" && "思考中..."}
          {state === "disconnected" && "已断开"}
        </div>
      </div>
    </div>
  );
}
