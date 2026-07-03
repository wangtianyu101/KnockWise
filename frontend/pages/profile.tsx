/**
 * /profile — V2.3 我的画像（决策 6A 新建页）
 *
 * 4 区块：累计统计 / 弱项列表 / 已掌握列表 / 学习趋势图
 * 用 recharts LineChart（V1 dashboard 已用）
 */
import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import {
  Card,
  Statistic,
  Button,
  message,
  Empty,
  Row,
  Col,
  Tag,
  Spin,
} from "antd";
import {
  ReloadOutlined,
  FolderOpenOutlined,
  RightOutlined,
} from "@ant-design/icons";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { getProfile, getToken } from "@/lib/api";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface TopicSettlement {
  topic: string;
  error_rate: number;
  practice_count: number;
  last_practiced_at: string;
  related_question_ids: string[];
}

interface Profile {
  user_id: string;
  display_name: string;
  weak_topics: TopicSettlement[];
  mastered_topics: TopicSettlement[];
  learning_trajectory: Record<string, { mastered_count: number }>;
  last_active_at: string | null;
}

const NavLink = ({
  href,
  children,
  active,
}: {
  href: string;
  children: React.ReactNode;
  active?: boolean;
}) => {
  const router = useRouter();
  return (
    <button
      onClick={() => router.push(href)}
      className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
        active
          ? "bg-indigo-500/20 text-indigo-300"
          : "text-gray-400 hover:text-gray-200"
      }`}
    >
      {children}
    </button>
  );
};

export default function ProfilePage() {
  const router = useRouter();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [weekly, setWeekly] = useState<any>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const h = () => ({ Authorization: `Bearer ${getToken()}` });

  useEffect(() => {
    if (!getToken()) {
      router.push("/");
      return;
    }
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [p, w] = await Promise.all([
        getProfile(),
        fetch(`${API}/api/v2/profile/weekly?week=2026-W26`, { headers: h() })
          .then((r) => (r.ok ? r.json() : null))
          .catch(() => null),
      ]);
      setProfile(p as any);
      setWeekly(w);
    } catch (e) {
      setError("network");
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      const res = await fetch(`${API}/api/v2/profile/refresh`, {
        method: "POST",
        headers: h(),
      });
      if (res.ok) {
        message.success("画像已刷新");
        loadData();
      } else {
        message.error("刷新失败");
      }
    } catch {
      message.error("网络错误");
    } finally {
      setRefreshing(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#050914] text-[#f1f5f9] flex items-center justify-center">
        <Spin size="large" />
      </div>
    );
  }

  const weak = profile?.weak_topics || [];
  const mastered = profile?.mastered_topics || [];
  const trajectory = weekly?.trajectory || {};
  const trajectoryData = Object.entries(trajectory)
    .sort(([a], [b]) => a.localeCompare(b))
    .slice(-12)
    .map(([week, v]: [string, any]) => ({ week, count: v.mastered_count }));

  return (
    <div className="min-h-screen bg-[#050914] text-[#f1f5f9]">
      <nav className="sticky top-0 z-50 flex items-center justify-between px-6 py-3.5 bg-[#0c1024]/90 backdrop-blur-xl border-b border-indigo-500/10">
        <div className="flex items-center gap-3">
          <span className="text-lg font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
            DevBrain
          </span>
          <div className="hidden md:flex gap-1 ml-6">
            <NavLink href="/dashboard">仪表盘</NavLink>
            <NavLink href="/interview/profile">面试</NavLink>
            <NavLink href="/learn">学</NavLink>
            <NavLink href="/review">复习</NavLink>
            <NavLink href="/profile" active>画像</NavLink>
            <NavLink href="/knowledge">知识库</NavLink>
            <NavLink href="/news">信息流</NavLink>
          </div>
        </div>
      </nav>

      <main className="max-w-6xl mx-auto px-6 py-10">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold">我的画像</h1>
            <p className="text-gray-400 text-sm mt-1">
              {profile?.display_name || "用户"} 的成长轨迹
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              icon={<FolderOpenOutlined />}
              onClick={() =>
                window.open(`file://${navigator.platform}`, "_blank")
              }
            >
              打开 Obsidian
            </Button>
            <Button
              type="primary"
              icon={<ReloadOutlined />}
              loading={refreshing}
              onClick={handleRefresh}
            >
              触发刷新画像
            </Button>
          </div>
        </div>

        {/* 累计统计 4 卡 */}
        <Row gutter={16} className="mb-8">
          <Col xs={12} sm={6}>
            <Card>
              <Statistic
                title="已做题"
                value={
                  (mastered.reduce((a, b) => a + b.practice_count, 0) || 0) +
                  (weak.reduce((a, b) => a + b.practice_count, 0) || 0)
                }
                valueStyle={{ color: "#a5b4fc" }}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card>
              <Statistic
                title="已掌握"
                value={mastered.length}
                valueStyle={{ color: "#34d399" }}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card>
              <Statistic
                title="学习中"
                value={weak.length}
                valueStyle={{ color: "#60a5fa" }}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card>
              <Statistic
                title="Obsidian 沉淀"
                value={weekly?.total_questions || 0}
                valueStyle={{ color: "#fbbf24" }}
                suffix="篇"
              />
            </Card>
          </Col>
        </Row>

        {/* 弱项 + 已掌握 */}
        <Row gutter={16} className="mb-8">
          <Col xs={24} md={12}>
            <Card title="📉 弱项（Top 5）">
              {weak.length === 0 ? (
                <Empty
                  description={
                    profile
                      ? "答 3 道题后这里会出现你的成长轨迹"
                      : "加载中…"
                  }
                />
              ) : (
                weak.slice(0, 5).map((w, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between py-2 border-b border-indigo-500/10 last:border-0"
                  >
                    <div>
                      <div className="text-red-400 font-medium">
                        {w.topic}
                      </div>
                      <div className="text-xs text-gray-500">
                        错题率 {(w.error_rate * 100).toFixed(0)}% · 练习{" "}
                        {w.practice_count} 次
                      </div>
                    </div>
                    <Button
                      type="link"
                      icon={<RightOutlined />}
                      onClick={() =>
                        router.push(
                          `/learn?topic=${encodeURIComponent(w.topic)}`
                        )
                      }
                    >
                      开始刷
                    </Button>
                  </div>
                ))
              )}
            </Card>
          </Col>
          <Col xs={24} md={12}>
            <Card title="🏆 已掌握（最近 10）">
              {mastered.length === 0 ? (
                <Empty description="暂无已掌握 topic" />
              ) : (
                mastered.slice(0, 10).map((m, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between py-2 border-b border-indigo-500/10 last:border-0"
                  >
                    <div>
                      <div className="text-emerald-400 font-medium">
                        {m.topic}
                      </div>
                      <div className="text-xs text-gray-500">
                        {new Date(m.last_practiced_at).toLocaleDateString()} 已掌握
                      </div>
                    </div>
                    <Tag color="green">mastered</Tag>
                  </div>
                ))
              )}
            </Card>
          </Col>
        </Row>

        {/* 学习趋势图 */}
        <Card title="📈 学习趋势（最近 12 周）" className="mb-8">
          {trajectoryData.length < 2 ? (
            <div className="text-center py-8 text-gray-400">
              继续学习 2 周后看到趋势
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={trajectoryData}>
                <CartesianGrid stroke="#1f2937" strokeDasharray="3 3" />
                <XAxis dataKey="week" stroke="#8b8fa3" />
                <YAxis stroke="#8b8fa3" />
                <Tooltip
                  contentStyle={{
                    background: "#0c1024",
                    border: "1px solid rgba(99, 102, 241, 0.3)",
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="count"
                  stroke="#a78bfa"
                  strokeWidth={2}
                  dot={{ fill: "#a78bfa", r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </Card>

        {/* V2_ENABLED 提示（开发期调试用） */}
        {process.env.NEXT_PUBLIC_V2_ENABLED === "false" && (
          <div className="text-center text-xs text-gray-500 py-4">
            V2 已禁用（NEXT_PUBLIC_V2_ENABLED=false）
          </div>
        )}
      </main>
    </div>
  );
}
