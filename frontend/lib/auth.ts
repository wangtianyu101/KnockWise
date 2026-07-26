/**
 * lib/auth.ts · JWT 解码 + userName 派生（决策 8 方案 A 最小改）
 *
 * 设计要点：
 * - decodeJwt 不验证签名（前端用 · 仅解析 payload）
 * - getUserNameFromToken 从 JWT email 字段派生 userName（email 前缀）
 * - 与 spec.md § 5.1 Schema 一致：JwtPayload / UserInfo
 */

export interface JwtPayload {
  /** user.id (JWT spec 强制 string) */
  sub: string;
  /** expiration timestamp (秒) */
  exp: number;
  /** 用户邮箱（可选 · 用于 userName 派生） */
  email?: string;
}

/**
 * 解码 JWT payload（base64url → JSON）
 * 不验证签名 — 仅前端用，安全性由后端 _create_token 签名保证
 *
 * @param token JWT 字符串（3 段：header.payload.signature）
 * @returns payload 对象或 null（无效 token / 解析失败 / 非 string）
 */
export function decodeJwt(token: string): JwtPayload | null {
  if (!token || typeof token !== "string") return null;
  const parts = token.split(".");
  if (parts.length !== 3) return null;
  try {
    // base64url → base64
    const payload = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const padded = payload + "=".repeat((4 - (payload.length % 4)) % 4);
    const decoded = atob(padded);
    return JSON.parse(decoded) as JwtPayload;
  } catch {
    return null;
  }
}

/**
 * 从 token 派生 userName（email 前缀）
 *
 * @param token JWT 字符串或 null
 * @returns userName（email 前缀）或 null（无法派生）
 *
 * 决策 8 方案 A：去 hardcode + Layout 必填 userName + _app 从 JWT 解 email 前缀注入
 */
export function getUserNameFromToken(token: string | null): string | null {
  if (!token) return null;
  const payload = decodeJwt(token);
  if (!payload?.email) return null;
  const atIdx = payload.email.indexOf("@");
  if (atIdx <= 0) return null;
  return payload.email.substring(0, atIdx);
}