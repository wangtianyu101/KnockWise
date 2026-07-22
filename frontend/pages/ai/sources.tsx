// pages/ai/sources.tsx · T13 part
import { useState } from 'react';
import { useDigestSources, useAddDigestSource } from '@/hooks/useDigest';
import { SourceToggleRow } from '@/components/digest/SourceToggleRow';

export default function SourcesPage() {
  const { sources, system_count, user_count } = useDigestSources();
  const addSource = useAddDigestSource();
  const [showAdd, setShowAdd] = useState(false);
  // TODO: 接 useToggleDigestSource hook 后替换 noop
  const handleToggle = (_sourceId: string, _enabled: boolean) => {
    // 当前未实现 toggle API · 留作 follow-up
  };
  return (
    <div>
      <h1 className="text-2xl font-bold mb-4 text-text-primary">📡 信源管理</h1>
      <div className="grid grid-cols-4 gap-3 mb-4">
        <div className="stat-card"><div className="stat-value">{sources.length}</div><div className="stat-label">信源总数</div></div>
        <div className="stat-card"><div className="stat-value">{system_count}</div><div className="stat-label">系统默认</div></div>
        <div className="stat-card"><div className="stat-value">{user_count}</div><div className="stat-label">我的自定义</div></div>
        <div className="stat-card"><div className="stat-value">{sources.filter(s => s.enabled).length}</div><div className="stat-label">启用中</div></div>
      </div>
      <button onClick={() => setShowAdd(true)} className="btn btn-primary mb-4">+ 添加自定义源</button>
      <div className="space-y-2">
        {sources.map((s) => (
          <SourceToggleRow
            key={s.id}
            source={s}
            isDefault={s.is_default}
            enabled={s.enabled}
            onToggle={handleToggle}
          />
        ))}
      </div>
      {showAdd && <AddSourceDialog onClose={() => setShowAdd(false)} onAdd={addSource} />}
    </div>
  );
}

function AddSourceDialog({ onClose, onAdd }: { onClose: () => void; onAdd: (s: any) => void }) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <h2 className="text-xl font-bold mb-4">+ 添加自定义 RSS 源</h2>
        <input type="text" placeholder="源名称" className="form-input w-full mb-3" id="src-name" />
        <input type="text" placeholder="RSS URL" className="form-input w-full mb-3" id="src-url" />
        <div className="flex justify-end gap-2 mt-4 pt-3 border-t border-border">
          <button onClick={onClose} className="btn btn-secondary">取消</button>
          <button onClick={() => {
            const name = (document.getElementById('src-name') as HTMLInputElement)?.value;
            const url = (document.getElementById('src-url') as HTMLInputElement)?.value;
            if (name && url) onAdd({ name, url, type: 'model', region: 'domestic' });
            onClose();
          }} className="btn btn-primary">添加并启用</button>
        </div>
      </div>
    </div>
  );
}
