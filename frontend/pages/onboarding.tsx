import { useRouter } from "next/router";
import { useState } from "react";
import { updateProfile, getProfile } from "@/lib/api";

export default function Onboarding() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [profile, setProfile] = useState({
    tech_stack: [] as string[],
    years_of_exp: 3,
    current_level: "mid",
    target_companies: [] as string[],
  });

  const levels = [
    { value: "junior", label: "初级", desc: "0-2 年" },
    { value: "mid", label: "中级", desc: "2-5 年" },
    { value: "senior", label: "高级", desc: "5 年+" },
  ];
  const allTech = ["LangChain", "LangGraph", "RAG", "Python", "Java", "Go", "React", "K8s", "Docker", "Agent"];

  const toggleTech = (t: string) => {
    setProfile((p) => ({
      ...p,
      tech_stack: p.tech_stack.includes(t) ? p.tech_stack.filter((x) => x !== t) : [...p.tech_stack, t],
    }));
  };

  const saveAndGo = async () => {
    await updateProfile(profile);
    router.push("/setup");
  };

  return (
    <div className="min-h-screen gradient-page text-white flex items-center justify-center">
      <div className="w-full max-w-xl px-6 py-8">
        {/* Progress dots */}
        <div className="flex justify-center gap-2 mb-8">
          {[0, 1].map((i) => (
            <div
              key={i}
              className={`h-1.5 rounded-full transition-all duration-300 ${
                i <= step ? "gradient-accent w-8" : "bg-gray-700 w-4"
              }`}
            />
          ))}
        </div>

        <div className="gradient-card rounded-2xl p-8 backdrop-blur-sm animate-slideUp">
          {step === 0 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-2xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
                  技术画像
                </h2>
                <p className="text-gray-400 text-sm mt-1">选好技术栈，题目会更精准</p>
              </div>

              <div>
                <label className="text-sm text-gray-300 mb-3 block">技术栈（可多选）</label>
                <div className="flex flex-wrap gap-2">
                  {allTech.map((t) => (
                    <button
                      key={t}
                      onClick={() => toggleTech(t)}
                      className={`px-3.5 py-2 rounded-xl text-sm font-medium transition-all duration-200 ${
                        profile.tech_stack.includes(t)
                          ? "bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-lg shadow-purple-500/20"
                          : "bg-gray-800/50 text-gray-400 hover:bg-gray-700/50 hover:text-gray-200 border border-gray-700/30"
                      }`}
                    >
                      {t}
                    </button>
                  ))}
                </div>
              </div>

              {profile.tech_stack.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {profile.tech_stack.map((t) => (
                    <span key={t} className="px-2 py-0.5 rounded-full text-xs bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                      {t}
                    </span>
                  ))}
                </div>
              )}

              <button
                onClick={() => setStep(1)}
                disabled={profile.tech_stack.length === 0}
                className="w-full py-3 rounded-xl font-medium transition-all duration-200 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 disabled:opacity-30 disabled:cursor-not-allowed shadow-lg shadow-purple-500/20"
              >
                下一步
              </button>
            </div>
          )}

          {step === 1 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-2xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
                  经验与级别
                </h2>
                <p className="text-gray-400 text-sm mt-1">影响题目难度和追问深度</p>
              </div>

              <div>
                <label className="text-sm text-gray-300 mb-3 block">工作年限</label>
                <div className="flex items-center gap-3">
                  <input
                    type="range"
                    min="0"
                    max="15"
                    value={profile.years_of_exp}
                    onChange={(e) => setProfile((p) => ({ ...p, years_of_exp: parseInt(e.target.value) }))}
                    className="flex-1 accent-indigo-500"
                  />
                  <span className="w-12 text-center text-xl font-bold text-indigo-400">
                    {profile.years_of_exp}
                  </span>
                  <span className="text-gray-500 text-sm">年</span>
                </div>
              </div>

              <div>
                <label className="text-sm text-gray-300 mb-3 block">当前级别</label>
                <div className="grid grid-cols-3 gap-2">
                  {levels.map((l) => (
                    <button
                      key={l.value}
                      onClick={() => setProfile((p) => ({ ...p, current_level: l.value }))}
                      className={`py-3 rounded-xl transition-all duration-200 ${
                        profile.current_level === l.value
                          ? "bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-lg shadow-purple-500/20"
                          : "bg-gray-800/50 text-gray-400 hover:bg-gray-700/50 border border-gray-700/30"
                      }`}
                    >
                      <div className="font-semibold">{l.label}</div>
                      <div className="text-xs opacity-60 mt-0.5">{l.desc}</div>
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => setStep(0)}
                  className="px-6 py-3 rounded-xl bg-gray-800/50 text-gray-400 hover:text-gray-200 transition-colors border border-gray-700/30"
                >
                  上一步
                </button>
                <button
                  onClick={saveAndGo}
                  className="flex-1 py-3 rounded-xl font-medium transition-all duration-200 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 shadow-lg shadow-purple-500/20"
                >
                  保存，下一步
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
