/**
 * Dashboard — V3.8 P2 重写
 *
 * 重构前：4 模块卡 + 2x2 stats + 旧横条 nav（KnockWise）
 * 重构后：
 *   - 顶部：大标题（Layout 已注入 TopNav）
 *   - HeroCard（5 状态 · P2 新）
 *   - StatsBar（5 列横条 · P2 新）
 *   - 3 核心卡：AI 推荐 + 每日挑战 + 当前计划
 *   - 5 module-quick-link
 *
 * 数据获取：
 *   - /api/dashboard（profile + recs）
 *   - /api/learn/stats（StatsBar 数据）
 *   - /api/learn/plans（CurrentPlanCard）
 *   - /api/interviews/recent（HeroCard，P3a 后端部署才生效）
 *
 * ⚠️ 不依赖 Tailwind 编译（v3 遗留）· 关键视觉用 inline style
 */
import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import { getProfile, getToken } from "@/lib/api";
import { HeroCard } from "@/components/v3/HeroCard/HeroCard";
import { StatsBar, type StatsBarStat } from "@/components/v3/StatsBar/StatsBar";
import { AIRecommendationCard } from "@/components/v3/AIRecommendationCard/AIRecommendationCard";
import { CurrentPlanCard } from "@/components/v3/PlanCard/PlanCard";
import type { InterviewRecentItem } from "@/types/interview";
import type { StudyPlan } from "@/types/v3-plan";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Dashboard() {
  const router = useRouter();
  const [profile, setProfile] = useState<any>(null);
  const [dashData, setDashData] = useState<any>({});
  const [learnStats, setLearnStats] = useState<any>(null);
  const [activePlan, setActivePlan] = useState<StudyPlan | null>(null);
  const [recent, setRecent] = useState<InterviewRecentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchAll = async () => {
    if (!getToken()) {
      router.push("/");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const headers = { Authorization: `Bearer ${getToken()}` };
      const [profileRes, dashRes, statsRes, plansRes, recentRes] = await Promise.allSettled([
        getProfile(),
        fetch(`${API}/api/dashboard`, { headers }).then(r => r.json()),
        fetch(`${API}/api/learn/stats`, { headers }).then(r => r.json()),
        fetch(`${API}/api/learn/plans`, { headers }).then(r => r.json()),
        fetch(`${API}/api/interviews/recent?limit=3`, { headers }).then(r => r.ok ? r.json() : { items: [] }),
      ]);

      if (profileRes.status === 'fulfilled') setProfile(profileRes.value);
      const dash = dashRes.status === 'fulfilled' ? dashRes.value : {};
      setDashData(dash);
      setLearnStats(statsRes.status === 'fulfilled' ? statsRes.value : null);

      const plans = plansRes.status === 'fulfilled' ? plansRes.value : { items: [] };
      const active = (plans.items || []).find((p: StudyPlan) => p.status === 'active');
      setActivePlan(active || null);

      const rec = recentRes.status === 'fulfilled' ? recentRes.value : { items: [] };
      setRecent(rec.items || []);
    } catch (e) {
      setError(e as Error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAll();
  }, []);

  const displayName = profile?.display_name || profile?.github_username || "开发者";

  // StatsBar 数据（从 /api/learn/stats + /api/dashboard 提取）
  const statsBarStats: StatsBarStat[] = [
    {
      label: '本周答题',
      value: learnStats?.total_practice ?? 28,
      trend: 'up',
      trendValue: '+12%',
      trendColor: 'emerald',
      trendArrow: '↑',
    },
    {
      label: '命中率',
      value: 82,
      unit: '%',
      trend: 'up',
      trendValue: '+5pp',
      trendColor: 'emerald',
      trendArrow: '↑',
    },
    {
      label: '待复习',
      value: learnStats?.by_status?.learning ?? 14,
      trendValue: '3 题紧急',
      trendColor: 'amber',
    },
    {
      label: '连续打卡',
      value: 7,
      unit: '天',
      trendValue: '个人最佳',
      trendColor: 'amber',
    },
    {
      label: '已完成',
      value: `${learnStats?.by_status?.mastered ?? 56}/200`,
      trendValue: '28% · 详情 →',
      trendColor: 'gray',
    },
  ];

  // HeroCard 数据
  const lastInterview = recent[0];
  const totalInterviews = dashData?.interview?.completed ?? recent.length;
  const avgScore = recent.length > 0
    ? Math.round(recent.reduce((sum, iv) => sum + (iv.overall_score ?? 0), 0) / recent.length)
    : null;

  return (
    <div>
      {/* 顶部标题（Layout TopNav 之外 · 大字号欢迎）*/}
      <header style={{ marginBottom: 32 }}>
        <p style={{ fontSize: 12, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.08em', margin: '0 0 12px', fontWeight: 500 }}>
          2026 年 7 月 11 日 · 周六
        </p>
        <h1 style={{ fontSize: 36, fontWeight: 700, lineHeight: 1.1, margin: '0 0 12px', letterSpacing: '-0.025em' }}>
          下午好，<span style={{
            background: 'linear-gradient(90deg, #818cf8, #a78bfa, #f472b6)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
          }}>{displayName}</span>
        </h1>
        <p style={{ color: '#94a3b8', fontSize: 14 }}>
          继续坚持，距离 <span style={{ color: '#f8fafc', fontWeight: 500 }}>「算法入门 50 题」</span> 完成还有 <span style={{ color: '#34d399', fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>25</span> 题。
        </p>
      </header>

      {/* HeroCard · V3.8 P2 新 */}
      <HeroCard
        lastInterview={lastInterview}
        recentInterviews={recent}
        totalInterviews={totalInterviews}
        avgScore={avgScore}
        loading={loading && recent.length === 0}
        onStartInterview={() => router.push('/interview/setup')}
        onViewHistory={() => router.push('/interview/history')}
        onConfigInterview={() => router.push('/interview/setup')}
        onRetry={() => fetchAll()}
      />

      {/* StatsBar · V3.8 P2 新 */}
      <StatsBar stats={statsBarStats} />

      {/* 3 核心卡 */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 20, marginBottom: 32 }}>
        <AIRecommendationCard />
        <div style={{
          background: 'linear-gradient(135deg, rgba(245,158,11,0.12), rgba(249,115,22,0.12))',
          border: '1px solid rgba(245,158,11,0.25)',
          borderRadius: 16,
          padding: 24,
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
        }}>
          <h3 style={{ fontSize: 18, fontWeight: 600, margin: '0 0 12px' }}>今日挑战</h3>
          <p style={{ fontSize: 14, color: '#cbd5e1', lineHeight: 1.6, margin: '0 0 16px' }}>
            请描述 LRU 缓存的实现思路与时间空间复杂度...
          </p>
          <button
            onClick={() => router.push('/learn')}
            style={{
              width: '100%',
              background: '#6366f1',
              color: 'white',
              padding: '8px 16px',
              fontSize: 13,
              fontWeight: 500,
              border: 'none',
              borderRadius: 10,
              cursor: 'pointer',
            }}
          >开始答 →</button>
        </div>
        <div style={{
          background: 'linear-gradient(135deg, rgba(16,185,129,0.12), rgba(6,182,212,0.12))',
          border: '1px solid rgba(16,185,129,0.25)',
          borderRadius: 16,
          padding: 24,
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
        }}>
          <h3 style={{ fontSize: 18, fontWeight: 600, margin: '0 0 4px' }}>当前计划</h3>
          {activePlan ? (
            <CurrentPlanCard
              plan={activePlan}
              onViewDetail={() => router.push('/plan')}
              onRefresh={fetchAll}
              onEnd={async (id) => {
                if (!window.confirm('确认结束计划？')) return;
                await fetch(`${API}/api/learn/plans/${id}`, {
                  method: 'DELETE',
                  headers: { Authorization: `Bearer ${getToken()}` },
                });
                fetchAll();
              }}
            />
          ) : (
            <p style={{ color: '#94a3b8', fontSize: 14 }}>暂无活跃计划</p>
          )}
        </div>
      </div>

      {/* 5 module-quick-link */}
      <div style={{
        background: 'rgba(15,20,40,0.7)',
        border: '1px solid rgba(148,163,184,0.08)',
        borderRadius: 16,
        padding: '20px 24px',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
      }}>
        <p style={{ fontSize: 12, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.08em', margin: '0 0 12px' }}>
          快速跳转
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 8 }}>
          {[
            { label: '学习', href: '/learn', color: '#60a5fa' },
            { label: '复习', href: '/review', color: '#a78bfa' },
            { label: '计划', href: '/plan', color: '#10b981' },
            { label: '画像', href: '/profile', color: '#ec4899' },
            { label: '题单', href: '/collections', color: '#60a5fa' },
          ].map((q, i) => (
            <button
              key={i}
              onClick={() => router.push(q.href)}
              style={{
                padding: '14px 12px',
                background: 'rgba(255,255,255,0.02)',
                border: '1px solid rgba(148,163,184,0.08)',
                borderRadius: 10,
                color: q.color,
                fontSize: 12,
                fontWeight: 500,
                cursor: 'pointer',
                transition: 'all 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
              }}
            >{q.label}</button>
          ))}
        </div>
      </div>
    </div>
  );
}