/**
 * V3 /plan 页面（PR 1 · V3.0 · 用户已点痛点修复）
 * 入口：`/plan` · 4 子卡：当前计划 + 创建 + 历史 + 详情
 */
import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { message } from 'antd';
import {
  CurrentPlanCard,
  CreatePlanButton,
  HistoryPlansList,
  PlanDetailCard,
} from '@/components/v3/PlanCard/PlanCard';
import { PlanCreateModal } from '@/components/v3/PlanCard/PlanCreateModal';
import { getToken } from '@/lib/api';
import type { StudyPlan } from '@/types/v3-plan';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function PlanPage() {
  const router = useRouter();
  const [plans, setPlans] = useState<StudyPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedPlan, setSelectedPlan] = useState<StudyPlan | null>(null);
  const [createOpen, setCreateOpen] = useState(false);

  useEffect(() => {
    if (!getToken()) {
      router.push('/');
      return;
    }
    loadPlans();
  }, []);

  async function loadPlans() {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/learn/plans`, {
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setPlans(data.items || []);
    } catch (err) {
      message.error('加载学习计划失败');
    } finally {
      setLoading(false);
    }
  }

  const currentPlan = plans.find((p) => p.status === 'active');
  const historyPlans = plans.filter((p) => p.status !== 'active');

  if (loading) {
    return (
      <div className="min-h-screen bg-[#050914] text-[#f1f5f9] flex items-center justify-center">
        <div className="text-gray-400">加载中…</div>
      </div>
    );
  }

  // 详情视图
  if (selectedPlan) {
    return (
      <div className="min-h-screen bg-[#050914] text-[#f1f5f9]">
        <main className="max-w-5xl mx-auto px-6 py-10">
          <PlanDetailCard plan={selectedPlan} onBack={() => setSelectedPlan(null)} />
        </main>
      </div>
    );
  }

  // 列表视图
  return (
    <div className="min-h-screen bg-[#050914] text-[#f1f5f9]">
      <header className="mb-8 mt-10 px-6 max-w-5xl mx-auto">
        <div className="flex items-center gap-3 mb-2">
          <span className="text-xs px-2 py-0.5 rounded bg-red-500/15 text-red-300">🔴 用户已点痛点</span>
          <span className="text-xs px-2 py-0.5 rounded bg-indigo-500/15 text-indigo-300">V3.0</span>
        </div>
        <h1 className="text-3xl font-bold mb-2" style={{ letterSpacing: '-0.025em' }}>学习计划</h1>
        <p className="text-sm text-gray-400">按节奏刷题，让成长可视化。</p>
      </header>

      <main className="max-w-5xl mx-auto px-6 pb-16 space-y-6">
        {currentPlan ? (
          <CurrentPlanCard
            plan={currentPlan}
            onViewDetail={(id) => {
              const p = plans.find((x) => x.id === id);
              if (p) setSelectedPlan(p);
            }}
            onRefresh={async (id) => {
              message.loading('刷新中…');
              await loadPlans();
              message.success('✓ 进度已刷新');
            }}
            onEnd={async (id) => {
              const ok = window.confirm('确认结束计划？');
              if (!ok) return;
              try {
                await fetch(`${API_BASE}/api/learn/plans/${id}`, {
                  method: 'DELETE',
                  headers: { Authorization: `Bearer ${getToken()}` },
                });
                message.success('✓ 计划已结束');
                await loadPlans();
              } catch {
                message.error('结束计划失败');
              }
            }}
          />
        ) : (
          <div className="rounded-2xl p-12 bg-white/[0.04] border border-dashed border-white/10 text-center">
            <div className="text-5xl mb-4">🎯</div>
            <h2 className="text-xl font-semibold mb-2">还没有学习计划</h2>
            <p className="text-sm text-gray-400 mb-6">创建你的第一个学习计划，开始有节奏地刷题</p>
            <button
              onClick={() => setCreateOpen(true)}
              className="px-6 py-3 rounded-xl text-sm font-medium text-white"
              style={{ background: 'var(--color-primary)' }}
            >
              + 创建新计划
            </button>
          </div>
        )}

        <HistoryPlansList
          plans={historyPlans}
          onClick={(id) => {
            const p = plans.find((x) => x.id === id);
            if (p) setSelectedPlan(p);
          }}
        />
      </main>

      {currentPlan && <CreatePlanButton onClick={() => setCreateOpen(true)} />}

      <PlanCreateModal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={async () => {
          setCreateOpen(false);
          await loadPlans();
          message.success('✓ 计划创建成功');
        }}
      />
    </div>
  );
}
