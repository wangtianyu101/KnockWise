/**
 * DailySummaryCard — V2.3 V2_ENABLED feature flag 控制
 *
 * 显示 /dashboard 顶部"今日学习总结"卡（component-spec.md §2 完整定义）
 * 6 状态：加载 / 正常 / LLM 降级 / 完全失败 / 首次使用 / 本周无答题
 */
import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import { Card, Tag, Button, Skeleton, message } from "antd";
import { RightOutlined, ReloadOutlined } from "@ant-design/icons";
import { getToken } from "@/lib/api";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface TopicSettlement {
  topic: string;
  error_rate: number;
  practice_count: number;
  last_practiced_at: string;
  related_question_ids: string[];
}

interface DailySummary {
  title: string;
  date: string;
  yesterday_count: number;
  mastered: TopicSettlement[];
  weak_shift: { from_topic?: string; to_topic?: string; delta?: number }[];
  body: string;
  _fallback: boolean;
}

export function V2_ENABLED(): boolean {
  // 默认 true（开发期），生产可关 NEXT_PUBLIC_V2_ENABLED=false
  return process.env.NEXT_PUBLIC_V2_ENABLED !== "false";
}

interface Props {
  clickable?: boolean;
}

export default function DailySummaryCard({ clickable = true }: Props) {
  const router = useRouter();
  const [summary, setSummary] = useState<DailySummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!V2_ENABLED()) {
      setLoading(false);
      return;
    }
    fetch(`${API}/api/v2/dashboard/summary`, {
      headers: { Authorization: `Bearer ${getToken()}` },
    })
      .then(async (r) => {
        if (!r.ok && r.status !== 200) {
          // 401/422/429: 不弹错误，骨架态
          setLoading(false);
          return;
        }
        const data = await r.json();
        setSummary(data);
        setLoading(false);
      })
      .catch(() => {
        setError("network");
        setLoading(false);
      });
  }, []);

  if (!V2_ENABLED()) return null;

  if (loading) {
    return (
      <Card className="mb-5" style={{ background: "rgba(99, 102, 241, 0.05)" }}>
        <Skeleton active paragraph={{ rows: 2 }} />
      </Card>
    );
  }

  // 错误态（v2_enabled 排除）
  if (error === "network") {
    return (
      <Card className="mb-5">
        <div className="text-gray-400 text-sm">网络错误 — 暂无法加载今日总结</div>
      </Card>
    );
  }

  // 0 数据态
  if (
    !summary ||
    (summary.yesterday_count === 0 &&
      summary.mastered.length === 0 &&
      !summary.body)
  ) {
    return (
      <Card
        className="mb-5"
        style={{
          background:
            "linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(168, 85, 247, 0.1) 100%)",
          borderColor: "rgba(99, 102, 241, 0.2)",
        }}
      >
        <div className="text-gray-300 text-sm">
          完成首日学习后，这里会显示你的成长总结 ✨
        </div>
      </Card>
    );
  }

  // 正常态（含 LLM 降级 _fallback=true）
  return (
    <Card
      className="mb-5"
      style={{
        background:
          "linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(168, 85, 247, 0.1) 100%)",
        borderColor: summary._fallback
          ? "rgba(251, 191, 36, 0.3)"
          : "rgba(99, 102, 241, 0.3)",
      }}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs text-indigo-300 font-medium">
              ✨ {summary.title} · {summary.date}
            </span>
            {summary._fallback && (
              <Tag color="warning" className="text-xs">
                降级版
              </Tag>
            )}
          </div>
          <p className="text-sm text-gray-200 leading-relaxed mb-3">
            {summary.body}
          </p>
          {summary.yesterday_count > 0 && (
            <div className="flex items-center gap-3 text-xs text-gray-400">
              <span>昨天答了 {summary.yesterday_count} 题</span>
              {summary.mastered.length > 0 && (
                <span>
                  · 掌握 {summary.mastered.length} 个新 topic
                </span>
              )}
            </div>
          )}
        </div>
        {clickable && (
          <Button
            type="link"
            icon={<RightOutlined />}
            onClick={() => router.push("/profile")}
            className="text-indigo-300 hover:text-indigo-200"
          >
            查看画像
          </Button>
        )}
      </div>
    </Card>
  );
}
