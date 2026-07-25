// pages/push/settings.tsx · T14 + 2026-07-25 spec R5+R6 完整化
import { useEffect, useState } from 'react';
import { useDigestSettings, useUpdateDigestSettings } from '@/hooks/useDigest';
import { GlassCard } from '@/components/digest/DigestCard';

const TIMEZONES = [
  { value: 'Asia/Shanghai', label: 'Asia/Shanghai (UTC+8)' },
  { value: 'Asia/Tokyo', label: 'Asia/Tokyo (UTC+9)' },
  { value: 'America/New_York', label: 'America/New_York (UTC-5)' },
  { value: 'America/Los_Angeles', label: 'America/Los_Angeles (UTC-8)' },
  { value: 'Europe/London', label: 'Europe/London (UTC+0)' },
];

export default function SettingsPage() {
  const { data: settings } = useDigestSettings();
  const update = useUpdateDigestSettings();
  const [pushHour, setPushHour] = useState(8);
  const [pushMinute, setPushMinute] = useState(0);
  const [timezone, setTimezone] = useState('Asia/Shanghai');
  const [interestedTags, setInterestedTags] = useState<string[]>([]);

  useEffect(() => {
    if (!settings) return;
    setPushHour(settings.push_hour);
    setPushMinute(settings.push_minute);
    setTimezone(settings.push_timezone || 'Asia/Shanghai');
    setInterestedTags(settings.interested_tags || []);
  }, [settings]);

  const removeTag = (tag: string) =>
    setInterestedTags((cur) => cur.filter((t) => t !== tag));
  const addTag = () => {
    const t = window.prompt('新增关注标签')?.trim();
    if (!t) return;
    if (interestedTags.includes(t)) return;
    if (interestedTags.length >= 10) {
      window.alert('关注标签上限 10 · spec R5');
      return;
    }
    setInterestedTags([...interestedTags, t]);
  };

  const dirty = settings && (
    settings.push_hour !== pushHour ||
    settings.push_minute !== pushMinute ||
    (settings.push_timezone || 'Asia/Shanghai') !== timezone ||
    JSON.stringify(settings.interested_tags || []) !== JSON.stringify(interestedTags)
  );

  return (
    <div>
      <header className="mb-6">
        <h1 className="text-3xl font-bold mb-2 tracking-tight">⚙️ 推送设置</h1>
        <p className="text-sm text-[#94a3b8]">配置你的 AI 推送时间、渠道和偏好标签</p>
      </header>

      <GlassCard>
        <h2 className="text-base font-bold mb-3">⏰ 推送时间</h2>
        <p className="text-xs text-[#94a3b8] mb-3">按你本地时区计算 · 默认 08:00 Asia/Shanghai</p>
        <div className="flex items-center gap-2 mb-4">
          <input
            type="number"
            min={0}
            max={23}
            value={pushHour}
            onChange={(e) => setPushHour(Number(e.target.value))}
            className="input w-16 text-center bg-bg-card border border-border rounded"
            data-testid="input-push-hour"
          />
          <span>:</span>
          <input
            type="number"
            min={0}
            max={59}
            value={pushMinute}
            onChange={(e) => setPushMinute(Number(e.target.value))}
            className="input w-16 text-center bg-bg-card border border-border rounded"
            data-testid="input-push-minute"
          />
        </div>
        <div className="mb-4">
          <label className="text-xs text-[#94a3b8] block mb-1">时区（spec R6 · 影响 cron 触发）</label>
          <select
            value={timezone}
            onChange={(e) => setTimezone(e.target.value)}
            className="form-input w-full"
            data-testid="select-timezone"
          >
            {TIMEZONES.map((tz) => (
              <option key={tz.value} value={tz.value}>{tz.label}</option>
            ))}
          </select>
        </div>
      </GlassCard>

      <GlassCard>
        <h2 className="text-base font-bold mb-3">🏷 关注标签（最多 10 个 · spec R5）</h2>
        <div className="flex flex-wrap gap-2 mb-3" data-testid="tags-list">
          {interestedTags.map((tag) => (
            <span key={tag} className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-[13px] bg-[rgba(99,102,241,0.18)] text-[#c7d2fe] border border-[rgba(99,102,241,0.35)]">
              {tag}
              <button onClick={() => removeTag(tag)} className="hover:text-white">×</button>
            </span>
          ))}
          {interestedTags.length < 10 && (
            <button
              onClick={addTag}
              className="px-3 py-1 rounded text-[13px] bg-transparent border border-dashed border-[rgba(148,163,184,0.3)] text-[#94a3b8] hover:border-[rgba(99,102,241,0.4)]"
              data-testid="btn-add-tag"
            >
              + 添加
            </button>
          )}
        </div>
      </GlassCard>

      {/* spec R5 TAGS_LIMIT_EXCEEDED 提示 */}
      {interestedTags.length >= 10 && (
        <p className="text-xs text-amber-400 mt-2">已达上限 10 个</p>
      )}

      {/* spec R5 有未保存的修改提示（粘底保存栏） */}
      <div className="sticky bottom-0 mt-6 p-4 bg-[rgba(15,20,40,0.95)] backdrop-blur-xl border border-[rgba(148,163,184,0.08)] rounded-xl flex justify-between items-center" data-testid="save-bar">
        <span className="text-[13px] text-amber-400">
          {dirty ? '● 有未保存的修改' : '所有修改已保存'}
        </span>
        <button
          onClick={() => update.mutate({
            push_hour: pushHour,
            push_minute: pushMinute,
            push_timezone: timezone,
            interested_tags: interestedTags,
          })}
          disabled={update.isPending}
          className="px-4 py-2 rounded-lg text-sm font-medium bg-[#6366f1] text-white hover:bg-[#4f46e5] disabled:opacity-50"
          data-testid="btn-save"
        >
          保存设置
        </button>
      </div>
    </div>
  );
}
