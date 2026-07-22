/**
 * /admin/sync · V3.8 P3b · 手动同步（EmptyState 占位）
 */
import { useRouter } from "next/router";

export default function AdminSyncPage() {
  const router = useRouter();
  return (
    <div>
      <header style={{ marginBottom: 32 }}>
        <span style={{
          display: 'inline-block',
          background: 'rgba(245,158,11,0.2)',
          color: '#fcd34d',
          border: '1px solid rgba(245,158,11,0.3)',
          padding: '4px 10px',
          borderRadius: 6,
          fontSize: 12,
          fontWeight: 600,
          marginBottom: 12,
        }}>🆕 ADMIN</span>
        <h1 style={{ fontSize: 30, fontWeight: 700, margin: '12px 0 8px', letterSpacing: '-0.025em' }}>手动同步</h1>
        <p style={{ color: '#94a3b8', fontSize: 14 }}>/admin/sync · 数据源同步即将开放</p>
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
          <path d="M28 8a20 20 0 0 1 14 34M28 48a20 20 0 0 1-14-34M28 8v8M28 40v8" stroke="#6366f1" strokeWidth="1.5" strokeLinecap="round" opacity="0.4" />
        </svg>
        <h2 style={{ fontSize: 22, fontWeight: 600, margin: '0 0 12px', color: '#f8fafc' }}>
          手动同步 · 即将上线
        </h2>
        <p style={{ color: '#94a3b8', fontSize: 14, maxWidth: 480, margin: '0 auto 24px', lineHeight: 1.6 }}>
          数据源同步功能即将开放。可手动触发 LeetCode / GitHub 等多源拉取，配合 V3.7 定时任务使用。
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