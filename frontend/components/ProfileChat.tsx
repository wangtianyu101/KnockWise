import { useState, useRef, useEffect } from "react";

interface ProfileData {
  tech_stack: string[];
  years_of_exp: number;
  current_level: string;
}

interface ProfileChatProps {
  onProfile: (profile: ProfileData) => void;
}

type ChatStep = "greeting" | "tech_stack" | "experience" | "confirm";

const TECH_OPTIONS = [
  "LangChain", "LangGraph", "RAG", "Python", "Java", "Go",
  "React", "Vue", "K8s", "Docker", "Agent", "LLM",
];

const LEVEL_OPTIONS = [
  { value: "junior", label: "初级 (0-2年)" },
  { value: "mid", label: "中级 (2-5年)" },
  { value: "senior", label: "高级 (5年+)" },
];

export default function ProfileChat({ onProfile }: ProfileChatProps) {
  const [step, setStep] = useState<ChatStep>("greeting");
  const [messages, setMessages] = useState<Array<{ role: "bot" | "user"; content: string | React.ReactNode }>>([]);
  const [techStack, setTechStack] = useState<string[]>([]);
  const [yearsOfExp, setYearsOfExp] = useState<number>(3);
  const [level, setLevel] = useState<string>("mid");
  const [userInput, setUserInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const chatEnd = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEnd.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    // Start greeting
    setTimeout(() => {
      addBotMessage("你好！在开始面试之前，我想简单了解下你的技术背景。你主要用哪些技术栈？比如 LangChain、LangGraph、RAG、Python、Java 等。");
      setStep("tech_stack");
    }, 500);
  }, []);

  function addBotMessage(content: string) {
    setMessages((prev) => [...prev, { role: "bot", content }]);
  }

  function addUserMessage(content: string | React.ReactNode) {
    setMessages((prev) => [...prev, { role: "user", content }]);
  }

  function handleTechSubmit() {
    if (!userInput.trim()) return;
    addUserMessage(userInput);

    // Extract tech keywords
    const found = TECH_OPTIONS.filter((t) =>
      userInput.toLowerCase().includes(t.toLowerCase())
    );
    const selected = found.length > 0 ? found : [userInput.trim()];
    setTechStack(selected);

    setIsTyping(true);
    setTimeout(() => {
      addBotMessage(`了解了，你熟悉 ${selected.join("、")}。你有几年开发经验呢？`);
      setUserInput("");
      setStep("experience");
      setIsTyping(false);
    }, 800);
  }

  function handleExpSubmit() {
    const num = parseInt(userInput) || 3;
    addUserMessage(`${num} 年`);
    setYearsOfExp(num);

    setIsTyping(true);
    setTimeout(() => {
      addBotMessage("好的。你的职位级别是？");
      setUserInput("");
      setStep("confirm");
      setIsTyping(false);
    }, 600);
  }

  function handleLevelSelect(lvl: string) {
    const opt = LEVEL_OPTIONS.find((o) => o.value === lvl);
    addUserMessage(opt?.label || lvl);
    setLevel(lvl);

    setIsTyping(true);
    setTimeout(() => {
      addBotMessage(
        `确认一下：技术栈 ${techStack.join("、")}，${yearsOfExp} 年经验，${opt?.label}。准备好了我们就开始面试？`
      );
      setIsTyping(false);
    }, 800);

    onProfile({
      tech_stack: techStack,
      years_of_exp: yearsOfExp,
      current_level: lvl,
    });
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (step === "tech_stack") handleTechSubmit();
      else if (step === "experience") handleExpSubmit();
    }
  };

  return (
    <div className="flex flex-col h-full max-w-2xl mx-auto">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[75%] rounded-2xl px-4 py-3 ${
                msg.role === "bot"
                  ? "bg-gray-800 text-gray-100"
                  : "bg-blue-600 text-white"
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}
        {isTyping && (
          <div className="flex justify-start">
            <div className="bg-gray-800 rounded-2xl px-4 py-3 text-gray-400 animate-pulse">
              ...
            </div>
          </div>
        )}
        <div ref={chatEnd} />
      </div>

      {/* Input area */}
      <div className="px-4 py-3 border-t border-gray-800">
        {step === "confirm" ? (
          <div className="flex gap-2">
            {LEVEL_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => handleLevelSelect(opt.value)}
                className={`flex-1 py-3 rounded-xl text-sm font-medium transition-all ${
                  level === opt.value
                    ? "bg-blue-600 text-white"
                    : "bg-gray-800 text-gray-300 hover:bg-gray-700"
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        ) : (
          <div className="flex gap-2">
            <input
              type={step === "experience" ? "number" : "text"}
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={
                step === "tech_stack"
                  ? "例如：LangChain、Python、RAG..."
                  : "你的工作年限"
              }
              className="flex-1 bg-gray-800 rounded-xl px-4 py-3 text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              autoFocus
            />
            <button
              onClick={
                step === "tech_stack" ? handleTechSubmit : handleExpSubmit
              }
              disabled={!userInput.trim()}
              className="px-5 py-3 bg-blue-600 rounded-xl text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:bg-blue-500 transition-colors"
            >
              发送
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
