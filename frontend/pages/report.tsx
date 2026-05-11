import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import { generateReport, getReport } from "@/lib/api";
import RadarChart from "@/components/RadarChart";

export default function ReportPage() {
  const router = useRouter();
  const { interviewId } = router.query;
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!interviewId) return;
    loadReport(interviewId as string);
  }, [interviewId]);

  async function loadReport(id: string) {
    try {
      let data = await getReport(id);
      if (!data || !data.radar_data) {
        data = await generateReport(id);
      }
      setReport(data);
    } catch {
      try {
        const data = await generateReport(id);
        setReport(data);
      } catch {
        setReport(null);
      }
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen gradient-page text-white flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="flex items-center justify-center gap-2">
            <div className="w-3 h-3 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
            <div className="w-3 h-3 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
            <div className="w-3 h-3 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
          </div>
          <p className="text-gray-400">正在生成面试报告...</p>
        </div>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="min-h-screen gradient-page text-white flex items-center justify-center">
        <div className="gradient-card rounded-2xl p-8 text-center">
          <p className="text-red-400">报告生成失败，请重试。</p>
          <button
            onClick={() => router.push("/")}
            className="mt-4 px-6 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 text-white"
          >
            返回首页
          </button>
        </div>
      </div>
    );
  }

  const radarData = report.radar_data || {};
  const blindSpots = report.top_blind_spots || [];
  const improvementPlan = report.improvement_plan || [];

  return (
    <div className="min-h-screen gradient-page text-white">
      <div className="max-w-3xl mx-auto px-6 py-8 space-y-8">
        {/* Header */}
        <div className="text-center space-y-3 animate-slideUp">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
            面试报告
          </h1>
          <p className="text-gray-400 text-sm">{report.summary || ""}</p>
          <div className="inline-flex items-baseline gap-1">
            <span className="text-6xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
              {report.overall_score || "?"}
            </span>
            <span className="text-lg text-gray-500">/ 5</span>
          </div>
          {/* Score bar */}
          <div className="w-48 mx-auto h-2 bg-gray-800 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 transition-all duration-1000"
              style={{ width: `${((report.overall_score || 0) / 5) * 100}%` }}
            />
          </div>
        </div>

        {/* Radar Chart */}
        <div className="gradient-card rounded-2xl p-6 animate-slideUp" style={{ animationDelay: "0.1s" }}>
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <span className="w-1.5 h-5 rounded-full bg-gradient-to-b from-indigo-400 to-purple-400" />
            能力雷达图
          </h2>
          <RadarChart data={radarData} />
        </div>

        {/* Blind Spots */}
        {blindSpots.length > 0 && (
          <div className="gradient-card rounded-2xl p-6 animate-slideUp" style={{ animationDelay: "0.2s" }}>
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <span className="w-1.5 h-5 rounded-full bg-gradient-to-b from-red-400 to-pink-400" />
              薄弱环节
            </h2>
            <div className="space-y-3">
              {blindSpots.map((spot: any, i: number) => (
                <div key={i} className="flex items-start gap-3 p-3 bg-gray-900/50 rounded-xl border border-gray-800">
                  <span
                    className={`px-2 py-0.5 rounded-full text-xs mt-0.5 font-medium ${
                      spot.severity === "high"
                        ? "bg-red-500/20 text-red-400 border border-red-500/30"
                        : spot.severity === "medium"
                        ? "bg-yellow-500/20 text-yellow-400 border border-yellow-500/30"
                        : "bg-gray-700 text-gray-400"
                    }`}
                  >
                    {spot.severity === "high" ? "高" : spot.severity === "medium" ? "中" : "低"}
                  </span>
                  <div>
                    <div className="font-medium text-gray-200">{spot.topic}</div>
                    <div className="text-sm text-gray-500 mt-0.5">{spot.suggestion}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Improvement Plan */}
        {improvementPlan.length > 0 && (
          <div className="gradient-card rounded-2xl p-6 animate-slideUp" style={{ animationDelay: "0.3s" }}>
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <span className="w-1.5 h-5 rounded-full bg-gradient-to-b from-emerald-400 to-teal-400" />
              提升计划
            </h2>
            <div className="space-y-3">
              {improvementPlan.map((item: any, i: number) => (
                <div key={i} className="p-4 bg-gray-900/50 rounded-xl border border-gray-800">
                  <div className="font-medium text-gray-200">{item.action}</div>
                  <div className="text-sm text-gray-500 mt-1">{item.resources}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-4 pt-4">
          <button
            onClick={() => { localStorage.removeItem("codemock_setup"); router.push("/setup"); }}
            className="flex-1 py-3 rounded-xl font-medium bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 shadow-lg shadow-purple-500/20 transition-all"
          >
            再来一次
          </button>
          <button
            onClick={() => router.push("/onboarding")}
            className="flex-1 py-3 rounded-xl font-medium bg-gray-800/50 hover:bg-gray-700/50 border border-gray-700/30 text-gray-300 transition-all"
          >
            调整画像
          </button>
        </div>
      </div>
    </div>
  );
}
