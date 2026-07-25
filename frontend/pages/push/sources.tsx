// pages/push/sources.tsx · T13 part + 2026-07-25 P0 修
import { useState } from 'react';
import {
  useDigestSources,
  useAddDigestSource,
  usePatchDigestSource,
} from '@/hooks/useDigest';
import { SourceToggleRow } from '@/components/digest/SourceToggleRow';

type Tab = 'all' | 'system' | 'user' | 'model' | 'application';

const TABS: { value: Tab; label: string }[] = [
  { value: 'all', label: '全部' },
  { value: 'system', label: '系统默认' },
  { value: 'user', label: '我的' },
  { value: 'model', label: '模型' },
  { value: 'application', label: '应用' },
];

export default function SourcesPage() {
  const { data: sourcesData, isLoading } = useDigestSources();
  const addSource = useAddDigestSource();
  const patchSource = usePatchDigestSource();
  const [showAdd, setShowAdd] = useState(false);
  const [tab, setTab] = useState<Tab>('all');
  const sources = sourcesData?.items ?? [];
  const system_count = sourcesData?.system_count ?? 0;
  const user_count = sourcesData?.user_count ?? 0;
  const enabled_count = sources.filter((s) => s.enabled).length;

  // 客户端 tab 过滤
  const filtered = sources.filter((s) => {
    if (tab === 'all') return true;
    if (tab === 'system') return s.is_default;
    if (tab === 'user') return !s.is_default;
    if (tab === 'model') return s.type === 'model';
    if (tab === 'application') return s.type === 'application';
    return true;
  });

  return (
    <div>
      <header className="mb-6">
        <h1 className="text-3xl font-bold mb-2 tracking-tight">📡 信源管理</h1>
        <p className="text-sm text-[#94a3b8]">
          系统默认 {system_count} 源 · 自定义 {user_count} 源 · 全部启用中
        </p>
      </header>
      <div className="grid grid-cols-4 gap-3 mb-6">
        <div className="stat-card">
          <div className="stat-value">{sources.length + (sourcesData ? system_count - sources.filter((s) => s.is_default).length : 0)}</div>
          <div className="stat-label">信源总数</div>
        </div>
        <div className="stat-card">
          <div className="stat-value" style={{ background: 'linear-gradient(135deg, #10b981, #06b6d4)', WebkitBackgroundClip: 'text', backgroundClip: 'text', color: 'transparent' }}>
            {system_count}
          </div>
          <div className="stat-label">系统默认</div>
        </div>
        <div className="stat-card">
          <div className="stat-value" style={{ background: 'linear-gradient(135deg, #f59e0b, #ec4899)', WebkitBackgroundClip: 'text', backgroundClip: 'text', color: 'transparent' }}>
            {user_count}
          </div>
          <div className="stat-label">我的自定义</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{enabled_count}</div>
          <div className="stat-label">启用中</div>
        </div>
      </div>

      {/* Tabs 工具栏 + 添加按钮 */}
      <div className="flex items-center justify-between bg-[rgba(15,20,40,0.7)] backdrop-blur-xl border border-[rgba(148,163,184,0.08)] rounded-xl px-4 py-3 mb-4">
        <div className="flex items-center gap-1">
          {TABS.map((t) => (
            <button
              key={t.value}
              onClick={() => setTab(t.value)}
              className={`px-3 py-1 rounded-full text-sm transition-colors ${
                tab === t.value
                  ? 'bg-[rgba(99,102,241,0.18)] text-[#c7d2fe] border border-[rgba(99,102,241,0.35)]'
                  : 'text-[#94a3b8] hover:text-[#f8fafc] border border-transparent'
              }`}
              data-testid={`tab-${t.value}`}
            >
              {t.label}
            </button>
          ))}
        </div>
        <button
          onClick={() => setShowAdd(true)}
          className="btn btn-primary text-sm"
          data-testid="btn-add-source"
        >
          + 添加自定义源
        </button>
      </div>

      {isLoading ? (
        <p className="text-[#94a3b8]">加载中…</p>
      ) : filtered.length === 0 ? (
        <p className="text-center py-12 text-[#94a3b8]">该分类下无信源</p>
      ) : (
        <div className="space-y-2" data-testid="source-list">
          {filtered.map((s) => (
            <SourceToggleRow
              key={s.id}
              source={s}
              isDefault={s.is_default}
              enabled={s.enabled}
              onToggle={(sourceId, enabled) => patchSource.mutate({ id: sourceId, enabled })}
            />
          ))}
        </div>
      )}
      {showAdd && (
        <AddSourceDialog
          onClose={() => setShowAdd(false)}
          onAdd={(payload) => addSource.mutate(payload)}
        />
      )}
    </div>
  );
}

function AddSourceDialog({
  onClose,
  onAdd,
}: {
  onClose: () => void;
  onAdd: (s: { name: string; url: string; category: 'model' | 'application'; type: 'model' | 'application'; region: 'domestic' | 'overseas' }) => void;
}) {
  const [name, setName] = useState('');
  const [url, setUrl] = useState('');
  const [type, setType] = useState<'model' | 'application'>('model');
  const [region, setRegion] = useState<'domestic' | 'overseas'>('domestic');
  const valid = name.trim() && url.trim();
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <h2 className="text-xl font-bold mb-4">+ 添加自定义 RSS 源</h2>
        <label className="block text-xs text-[#94a3b8] mb-1">源名称</label>
        <input
          type="text"
          placeholder="例如：稀土掘金 LLM tag"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="form-input w-full mb-3"
        />
        <label className="block text-xs text-[#94a3b8] mb-1">RSS URL</label>
        <input
          type="text"
          placeholder="https://rsshub.app/juejin/tag/LLM"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          className="form-input w-full mb-3"
        />
        <div className="grid grid-cols-2 gap-3 mb-3">
          <div>
            <label className="block text-xs text-[#94a3b8] mb-1">分类</label>
            <select
              value={type}
              onChange={(e) => setType(e.target.value as 'model' | 'application')}
              className="form-input w-full"
              data-testid="select-type"
            >
              <option value="model">模型 (model)</option>
              <option value="application">应用 (application)</option>
            </select>
          </div>
          <div>
            <label className="block text-xs text-[#94a3b8] mb-1">地域</label>
            <select
              value={region}
              onChange={(e) => setRegion(e.target.value as 'domestic' | 'overseas')}
              className="form-input w-full"
              data-testid="select-region"
            >
              <option value="domestic">国内 (domestic)</option>
              <option value="overseas">国外 (overseas)</option>
            </select>
          </div>
        </div>
        <div className="flex justify-end gap-2 mt-4 pt-3 border-t border-border">
          <button onClick={onClose} className="btn btn-secondary">取消</button>
          <button
            disabled={!valid}
            onClick={() => {
              if (!valid) return;
              onAdd({ name: name.trim(), url: url.trim(), category: type, type, region });
              onClose();
            }}
            className="btn btn-primary disabled:opacity-50"
            data-testid="btn-confirm-add"
          >
            添加并启用
          </button>
        </div>
      </div>
    </div>
  );
}
