import { useRouter } from "next/router";
import { useState } from "react";

const COMPANIES = ["字节跳动", "阿里巴巴", "腾讯", "美团", "小红书", "拼多多", "百度", "京东", "蚂蚁集团", "其他"];
const DEPARTMENTS = ["AI Agent 团队", "大模型平台", "RAG/搜索", "基础架构", "业务中台", "数据平台", "其他"];
const ROUNDS = [
  { value: "round1", label: "一面", desc: "技术广度 · 基础考察" },
  { value: "round2", label: "二面", desc: "技术深度 · 项目深挖" },
  { value: "round3", label: "三面", desc: "架构设计 · 综合能力" },
];
const ROLES = ["AI Agent 工程师", "大模型应用开发", "RAG 工程师", "后端开发", "全栈开发", "其他"];

export default function SetupInterview() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [config, setConfig] = useState({
    company: "",
    custom_company: "",
    department: "",
    round: "round1",
    role: "AI Agent 工程师",
  });

  const startInterview = () => {
    const finalConfig = {
      ...config,
      company: config.company === "其他" ? config.custom_company : config.company,
    };
    localStorage.setItem("codemock_setup", JSON.stringify(finalConfig));
    router.push("/interview");
  };

  return (
    <div className="min-h-screen gradient-page text-white flex items-center justify-center">
      <div className="w-full max-w-xl px-6 py-8">
        {/* Progress dots */}
        <div className="flex justify-center gap-2 mb-8">
          {[0, 1, 2].map((i) => (
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
                  面试信息
                </h2>
                <p className="text-gray-400 text-sm mt-1">先告诉我一些背景，让我更有针对性地提问</p>
              </div>

              {/* Company */}
              <div>
                <label className="text-sm text-gray-300 mb-3 block">目标公司</label>
                <div className="grid grid-cols-3 gap-2">
                  {COMPANIES.map((c) => (
                    <button
                      key={c}
                      onClick={() => setConfig((p) => ({ ...p, company: c }))}
                      className={`py-2.5 px-3 rounded-xl text-sm transition-all duration-200 ${
                        config.company === c
                          ? "bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-lg shadow-purple-500/20"
                          : "bg-gray-800/50 text-gray-400 hover:bg-gray-700/50 hover:text-gray-200"
                      }`}
                    >
                      {c}
                    </button>
                  ))}
                </div>
                {config.company === "其他" && (
                  <input
                    value={config.custom_company}
                    onChange={(e) => setConfig((p) => ({ ...p, custom_company: e.target.value }))}
                    placeholder="输入公司名称"
                    className="w-full mt-2 px-4 py-2.5 bg-gray-800/50 border border-gray-700 rounded-xl text-sm focus:outline-none focus:border-indigo-500 transition-colors"
                  />
                )}
              </div>

              {/* Department */}
              <div>
                <label className="text-sm text-gray-300 mb-3 block">目标部门</label>
                <div className="grid grid-cols-2 gap-2">
                  {DEPARTMENTS.map((d) => (
                    <button
                      key={d}
                      onClick={() => setConfig((p) => ({ ...p, department: d }))}
                      className={`py-2.5 px-3 rounded-xl text-sm transition-all duration-200 ${
                        config.department === d
                          ? "bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-lg shadow-purple-500/20"
                          : "bg-gray-800/50 text-gray-400 hover:bg-gray-700/50 hover:text-gray-200"
                      }`}
                    >
                      {d}
                    </button>
                  ))}
                </div>
              </div>

              <button
                onClick={() => setStep(1)}
                disabled={!config.company}
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
                  面试轮次
                </h2>
                <p className="text-gray-400 text-sm mt-1">这会影响题目的深度和追问策略</p>
              </div>

              <div className="space-y-3">
                {ROUNDS.map((r) => (
                  <button
                    key={r.value}
                    onClick={() => setConfig((p) => ({ ...p, round: r.value }))}
                    className={`w-full p-4 rounded-xl text-left transition-all duration-200 ${
                      config.round === r.value
                        ? "bg-gradient-to-r from-indigo-600/30 to-purple-600/30 border border-purple-500/50 shadow-lg shadow-purple-500/10"
                        : "bg-gray-800/50 border border-gray-700/50 hover:border-gray-600"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className={`font-semibold ${config.round === r.value ? "text-purple-300" : "text-gray-200"}`}>
                        {r.label}
                      </span>
                      {config.round === r.value && (
                        <span className="w-5 h-5 rounded-full bg-purple-500 flex items-center justify-center">
                          <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                          </svg>
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-500 mt-1">{r.desc}</p>
                  </button>
                ))}
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => setStep(0)}
                  className="px-6 py-3 rounded-xl bg-gray-800/50 text-gray-400 hover:text-gray-200 transition-colors"
                >
                  上一步
                </button>
                <button
                  onClick={() => setStep(2)}
                  className="flex-1 py-3 rounded-xl font-medium transition-all duration-200 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 shadow-lg shadow-purple-500/20"
                >
                  下一步
                </button>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-2xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
                  面试岗位
                </h2>
                <p className="text-gray-400 text-sm mt-1">选择最匹配的目标岗位</p>
              </div>

              <div className="space-y-2">
                {ROLES.map((r) => (
                  <button
                    key={r}
                    onClick={() => setConfig((p) => ({ ...p, role: r }))}
                    className={`w-full py-3 px-4 rounded-xl text-sm transition-all duration-200 ${
                      config.role === r
                        ? "bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-lg shadow-purple-500/20"
                        : "bg-gray-800/50 text-gray-400 hover:bg-gray-700/50 hover:text-gray-200"
                    }`}
                  >
                    {r}
                  </button>
                ))}
              </div>

              {/* Summary */}
              <div className="bg-gray-900/50 rounded-xl p-4 border border-gray-800">
                <p className="text-xs text-gray-500 mb-2">面试配置摘要</p>
                <div className="space-y-1.5 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-400">公司</span>
                    <span className="text-indigo-300">
                      {config.company === "其他" ? config.custom_company : config.company}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">部门</span>
                    <span className="text-indigo-300">{config.department}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">轮次</span>
                    <span className="text-purple-300">
                      {ROUNDS.find((r) => r.value === config.round)?.label} · {ROUNDS.find((r) => r.value === config.round)?.desc}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">岗位</span>
                    <span className="text-indigo-300">{config.role}</span>
                  </div>
                </div>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => setStep(1)}
                  className="px-6 py-3 rounded-xl bg-gray-800/50 text-gray-400 hover:text-gray-200 transition-colors"
                >
                  上一步
                </button>
                <button
                  onClick={startInterview}
                  className="flex-1 py-3 rounded-xl font-medium transition-all duration-200 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 shadow-lg shadow-emerald-500/20 animate-pulse-glow"
                >
                  开始面试
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
