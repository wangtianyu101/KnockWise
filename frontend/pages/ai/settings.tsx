// pages/ai/settings.tsx · T14 part
import { useDigestSettings, useUpdateDigestSettings } from '@/hooks/useDigest';
import { GlassCard } from '@/components/digest/DigestCard';

export default function SettingsPage() {
  // 2026-07-22 audit 修复：hooks 返回 { data, isLoading, error, refetch }
  const { data: settings } = useDigestSettings();
  const update = useUpdateDigestSettings();
  return (
    <div>
      <h1 className="text-2xl font-bold mb-4 text-text-primary">⚙️ 推送设置</h1>
      <GlassCard>
        <h2 className="text-base font-bold mb-3">⏰ 推送时间</h2>
        <div className="flex items-center gap-2">
          <input type="number" value={settings?.push_hour ?? 8}
            onChange={(e) => update({ push_hour: parseInt(e.target.value) })}
            className="input w-16 text-center bg-bg-card border border-border rounded" />
          <span>:</span>
          <input type="number" value={settings?.push_minute ?? 0}
            onChange={(e) => update({ push_minute: parseInt(e.target.value) })}
            className="input w-16 text-center bg-bg-card border border-border rounded" />
        </div>
        <h2 className="text-base font-bold mt-6 mb-3">🏷 关注标签</h2>
        <div className="flex flex-wrap gap-2">
          {(settings?.interested_tags ?? []).map((tag) => (
            <span key={tag} className="tag">{tag} ×</span>
          ))}
          <button className="text-text-secondary text-sm">+ 添加</button>
        </div>
      </GlassCard>
    </div>
  );
}
