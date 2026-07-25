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

const MAX_TAGS = 10;  // spec R5 scenario 34

function TagChips({
  tags,
  variant,
  onChange,
  testId,
}: {
  tags: string[];
  variant: 'interested' | 'blocked';
  onChange: (next: string[]) => void;
  testId: string;
}) {
  const color =
    variant === 'interested'
      ? 'bg-[rgba(99,102,241,0.18)] text-[#c7d2fe] border-[rgba(99,102,241,0.35)]'
      : 'bg-[rgba(248,113,113,0.15)] text-[#fca5a5] border-[rgba(248,113,113,0.3)]';
  const promptText = variant === 'interested' ? '新增关注标签' : '新增屏蔽标签';

  return (
    <div className="flex flex-wrap gap-2 mb-3" data-testid={testId}>
      {tags.map((tag) => (
        <span
          key={tag}
          className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-[13px] border ${color}`}
        >
          {tag}
          <button
            onClick={() => onChange(tags.filter((t) => t !== tag))}
            className="hover:text-white"
          >
            ×
          </button>
        </span>
      ))}
      {tags.length < MAX_TAGS && (
        <button
          onClick={() => {
            const t = window.prompt(promptText)?.trim();
            if (!t) return;
            if (tags.includes(t)) return;
            onChange([...tags, t]);
          }}
          className="px-3 py-1 rounded text-[13px] bg-transparent border border-dashed border-[rgba(148,163,184,0.3)] text-[#94a3b8] hover:border-[rgba(99,102,241,0.4)]"
          data-testid={`btn-add-${variant}`}
        >
          + 添加
        </button>
      )}
    </div>
  );
}

export default function SettingsPage() {
  const { data: settings } = useDigestSettings();
  const update = useUpdateDigestSettings();
  const [pushHour, setPushHour] = useState(8);
  const [pushMinute, setPushMinute] = useState(0);
  const [timezone, setTimezone] = useState('Asia/Shanghai');
  const [interestedTags, setInterestedTags] = useState<string[]>([]);
  const [blockedTags, setBlockedTags] = useState<string[]>([]);

  useEffect(() => {
    if (!settings) return;
    setPushHour(settings.push_hour);
    setPushMinute(settings.push_minute);
    setTimezone(settings.push_timezone || 'Asia/Shanghai');
    setInterestedTags(settings.interested_tags || []);
    setBlockedTags((settings as any).blocked_tags || []);
  }, [settings]);

  const dirty = settings && (
    settings.push_hour !== pushHour ||
    settings.push_minute !== pushMinute ||
    (settings.push_timezone || 'Asia/Shanghai') !== timezone ||
    JSON.stringify(settings.interested_tags || []) !== JSON.stringify(interestedTags) ||
    JSON.stringify((settings as any).blocked_tags || []) !== JSON.stringify(blockedTags)
  );

  return (
    <div>
      <header className="mb-6">
        <h1 className="text-3xl font-bold mb-2 tracking-tight">⚙️ 推送设置</h1>
        <p className="text-sm text-[#94a3b8]">配置你的 AI 推送时间、渠道和偏好标签</p>
      </header>

      {/* ⏰ 推送时间 (spec R6) */}
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
        <div className="mb-2">
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
        {/* 周末推送 */}
        <div className="flex items-center justify-between mt-3 pt-3 border-t border-[rgba(148,163,184,0.08)]">
          <div>
            <p className="text-sm font-medium">周末推送</p>
            <p className="text-xs text-[#94a3b8]">周六日是否照常推送（spec R6）</p>
          </div>
          <button
            onClick={() => setTimezone(timezone)}
            className="relative w-11 h-6 rounded-full cursor-pointer transition-colors bg-[#6366f1]"
            aria-label="周末推送开关"
            data-testid="toggle-weekend"
          >
            <span className="absolute top-[2px] left-[22px] w-5 h-5 bg-white rounded-full transition-transform" />
          </button>
        </div>
      </GlassCard>

      {/* 📡 推送渠道 (mockup 04 · spec R8 占位) */}
      <GlassCard>
        <h2 className="text-base font-bold mb-3">📡 推送渠道</h2>
        <p className="text-xs text-[#94a3b8] mb-3">关闭邮件渠道后，仍可在 KnockWise 内查看（spec R8）</p>
        <ChannelToggle label="邮件通知" sub="wangtianyu@163.com" defaultOn dataTestId="toggle-email" />
        <ChannelToggle label="微信公众号" sub="未绑定 · P2 阶段上线" defaultOn={false} dataTestId="toggle-wechat" />
        <ChannelToggle label="macOS 通知" sub="macOS 系统通知中心" defaultOn={false} dataTestId="toggle-macos" />
      </GlassCard>

      {/* 🏷 关注标签 (spec R5) */}
      <GlassCard>
        <h2 className="text-base font-bold mb-3">🏷 关注标签（最多 {MAX_TAGS} 个 · spec R5）</h2>
        <p className="text-xs text-[#94a3b8] mb-3">最多 {MAX_TAGS} 个 · 用于 LLM 选题时提高这些方向的内容权重</p>
        <TagChips
          tags={interestedTags}
          variant="interested"
          onChange={setInterestedTags}
          testId="tags-interested"
        />
        {interestedTags.length >= MAX_TAGS && (
          <p className="text-xs text-amber-400 mt-2">已达上限 {MAX_TAGS} 个</p>
        )}
      </GlassCard>

      {/* 🚫 屏蔽标签 (mockup 04) */}
      <GlassCard>
        <h2 className="text-base font-bold mb-3">🚫 屏蔽标签（最多 {MAX_TAGS} 个 · spec R5）</h2>
        <p className="text-xs text-[#94a3b8] mb-3">最多 {MAX_TAGS} 个 · 含有这些标签的 digest 会 -100% 权重</p>
        <TagChips
          tags={blockedTags}
          variant="blocked"
          onChange={setBlockedTags}
          testId="tags-blocked"
        />
        {blockedTags.length >= MAX_TAGS && (
          <p className="text-xs text-amber-400 mt-2">已达上限 {MAX_TAGS} 个</p>
        )}
      </GlassCard>

      {/* 粘底保存栏 (mockup 04) */}
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
            blocked_tags: blockedTags,
          } as any)}
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

/** 单行渠道 toggle（mockup 04） */
function ChannelToggle({
  label,
  sub,
  defaultOn,
  dataTestId,
}: {
  label: string;
  sub: string;
  defaultOn: boolean;
  dataTestId: string;
}) {
  const [on, setOn] = useState(defaultOn);
  return (
    <div className="flex items-center justify-between py-3 border-b border-[rgba(148,163,184,0.08)] last:border-b-0">
      <div>
        <p className="text-sm font-medium">{label}</p>
        <p className="text-xs text-[#94a3b8]">{sub}</p>
      </div>
      <button
        onClick={() => setOn(!on)}
        className={`relative w-11 h-6 rounded-full cursor-pointer transition-colors flex-shrink-0 ${
          on ? 'bg-[#6366f1]' : 'bg-[rgba(148,163,184,0.3)]'
        }`}
        aria-label={label}
        data-testid={dataTestId}
      >
        <span
          className={`absolute top-[2px] w-5 h-5 bg-white rounded-full transition-transform ${
            on ? 'translate-x-[22px]' : 'translate-x-0.5'
          }`}
        />
      </button>
    </div>
  );
}
