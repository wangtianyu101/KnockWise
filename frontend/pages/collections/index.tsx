/**
 * V3 /collections 页面（PR 2 · V3.1 · LeetCode 风格题单列表）
 * 入口：`/collections` · 5-8 题单卡片 + 订阅/进度可视化
 */
import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { message } from 'antd';
import { CollectionCard, type QuestionCollection } from '@/components/v3/CollectionCard/CollectionCard';
import { getToken } from '@/lib/api';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function CollectionsPage() {
  const router = useRouter();
  const [collections, setCollections] = useState<QuestionCollection[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'subscribed'>('all');

  useEffect(() => {
    if (!getToken()) {
      router.push('/');
      return;
    }
    loadCollections();
  }, []);

  async function loadCollections() {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/learn/collections`, {
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setCollections(data.items || []);
    } catch (err) {
      message.error('加载题单失败');
    } finally {
      setLoading(false);
    }
  }

  async function handleSubscribe(id: string) {
    try {
      const res = await fetch(`${API_BASE}/api/learn/collections/${id}/subscribe`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (res.status === 409) {
        message.warning('已经订阅过了');
        return;
      }
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      message.success('✓ 订阅成功');
      await loadCollections();
    } catch {
      message.error('订阅失败');
    }
  }

  async function handleUnsubscribe(id: string) {
    try {
      const res = await fetch(`${API_BASE}/api/learn/collections/${id}/subscribe`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      message.success('✓ 已取消订阅');
      await loadCollections();
    } catch {
      message.error('取消订阅失败');
    }
  }

  function handleStart(id: string) {
    router.push(`/collections/${id}`);
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-[#050914] text-[#f1f5f9] flex items-center justify-center">
        <div className="text-gray-400">加载题单中…</div>
      </div>
    );
  }

  const filtered = filter === 'subscribed'
    ? collections.filter((c) => c.subscribed)
    : collections;

  return (
    <div className="min-h-screen bg-[#050914] text-[#f1f5f9]">
      <header className="mb-8 mt-10 px-6 max-w-6xl mx-auto">
        <div className="flex items-center gap-3 mb-2">
          <span className="text-xs px-2 py-0.5 rounded bg-blue-500/15 text-blue-300">⭐ LeetCode 风格</span>
          <span className="text-xs px-2 py-0.5 rounded bg-indigo-500/15 text-indigo-300">V3.1</span>
        </div>
        <h1 className="text-3xl font-bold mb-2" style={{ letterSpacing: '-0.025em' }}>精选题单</h1>
        <p className="text-sm text-gray-400">官方精选题单，跟着系统化刷题。</p>
      </header>

      <main className="max-w-6xl mx-auto px-6 pb-16">
        {/* 筛选 */}
        <div className="flex items-center gap-2 mb-6 flex-wrap">
          <span className="text-xs text-gray-500 mr-2">筛选</span>
          <button
            className={`text-xs px-3 py-1.5 rounded-md transition-all ${
              filter === 'all' ? 'bg-indigo-500/20 text-white' : 'bg-white/5 text-gray-400 hover:text-white'
            }`}
            onClick={() => setFilter('all')}
          >
            全部 ({collections.length})
          </button>
          <button
            className={`text-xs px-3 py-1.5 rounded-md transition-all ${
              filter === 'subscribed' ? 'bg-amber-500/20 text-white' : 'bg-white/5 text-gray-400 hover:text-white'
            }`}
            onClick={() => setFilter('subscribed')}
          >
            ⭐ 已订阅 ({collections.filter((c) => c.subscribed).length})
          </button>
        </div>

        {/* 题单网格 */}
        {filtered.length === 0 ? (
          <div className="rounded-2xl p-12 bg-white/[0.04] border border-dashed border-white/10 text-center">
            <div className="text-4xl mb-3">📭</div>
            <p className="text-gray-400">{filter === 'subscribed' ? '还没有订阅的题单' : '题单建设中'}</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {filtered.map((c) => (
              <CollectionCard
                key={c.id}
                collection={c}
                onStart={handleStart}
                onSubscribe={handleSubscribe}
                onUnsubscribe={handleUnsubscribe}
                onClick={(id) => router.push(`/collections/${id}`)}
              />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
