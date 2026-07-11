/**
 * /settings · V3.8 P3b · 设置（EmptyState 占位 · data 类型）
 */
import { useRouter } from "next/router";

export default function SettingsPage() {
  const router = useRouter();
  return (
    <div>
      <header style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: 30, fontWeight: 700, margin: '0 0 8px', letterSpacing: '-0.025em' }}>设置</h1>
        <p style={{ color: '#94a3b8', fontSize: 14 }}>/settings · 用户偏好设置</p>
      </header>
      <div style={{
        background: 'rgba(15, 20, 40, 0.7)',
        border: '1px solid rgba(148, 163, 184, 0.08)',
        borderRadius: 16,
        padding: 48,
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        textAlign: 'center',
        minHeight: 400,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
      }}>
        <svg width="80" height="80" viewBox="0 0 56 56" fill="none" style={{ marginBottom: 24 }}>
          <circle cx="28" cy="28" r="10" stroke="#6366f1" strokeWidth="1.5" opacity="0.4" />
          <path d="M28 8v6M28 42v6M8 28h6M42 28h6" stroke="#6366f1" strokeWidth="1.5" strokeLinecap="round" opacity="0.4" />
        </svg>
        <h2 style={{ fontSize: 22, fontWeight: 600, margin: '0 0 12px', color: '#f8fafc' }}>
          设置
        </h2>
        <p style={{ color: '#94a3b8', fontSize: 14, maxWidth: 480, margin: '0 auto 24px', lineHeight: 1.6 }}>
          用户偏好设置（昵称、邮件订阅、主题）正在开发中。
        </p>
        <button
          onClick={() => router.push('/dashboard')}
          style={{
            background: '#6366f1',
            color: 'white',
            padding: '10px 24px',
            fontSize: 14,
            fontWeight: 500,
            border: 'none',
            borderRadius: 10,
            cursor: 'pointer',
            boxShadow: '0 4px 12px rgba(99,102,241,0.3)',
          }}
        >返回 Dashboard</button>
      </div>
    </div>
  );
}