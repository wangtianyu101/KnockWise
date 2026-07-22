/**
 * /ai/history · V3.8 P3b · AI 推送历史（EmptyState 占位 · vault 类型）
 */
import { useRouter } from "next/router";

export default function AiHistoryPage() {
  const router = useRouter();
  return (
    <div>
      <header style={{ marginBottom: 32 }}>
        <span style={{
          display: 'inline-block',
          background: 'rgba(99,102,241,0.2)',
          color: '#c7d2fe',
          border: '1px solid rgba(99,102,241,0.3)',
          padding: '4px 10px',
          borderRadius: 6,
          fontSize: 12,
          fontWeight: 600,
          marginBottom: 12,
        }}>V3 新增</span>
        <h1 style={{ fontSize: 30, fontWeight: 700, margin: '12px 0 8px', letterSpacing: '-0.025em' }}>推送历史</h1>
        <p style={{ color: '#94a3b8', fontSize: 14 }}>/ai/history · AI 日报/周报历史</p>
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
          <rect x="10" y="14" width="36" height="36" rx="4" stroke="#f59e0b" strokeWidth="1.5" opacity="0.4" />
          <circle cx="28" cy="32" r="6" stroke="#f59e0b" strokeWidth="1.5" opacity="0.4" />
        </svg>
        <h2 style={{ fontSize: 22, fontWeight: 600, margin: '0 0 12px', color: '#f8fafc' }}>
          推送历史
        </h2>
        <p style={{ color: '#94a3b8', fontSize: 14, maxWidth: 480, margin: '0 auto 24px', lineHeight: 1.6 }}>
          完成更多面试 + 答题后，AI 会自动推送日报 / 周报。届时此处可查阅历史推送内容。
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