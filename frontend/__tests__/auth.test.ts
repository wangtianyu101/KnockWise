/**
 * auth.test.ts · JWT 解码 + userName 派生（决策 8 方案 A）
 *
 * 测试真实 JWT token payload（手写 base64 编码 · 用于 vitest 单元测试）
 * 决策 8 方案 A：去 hardcode + Layout 必填 userName + _app 从 JWT 解 email 前缀注入
 */
import { describe, it, expect } from "vitest";
import { decodeJwt, getUserNameFromToken } from "../lib/auth";

// 真实 JWT payload（base64url 编码）
// payload: {"sub":"12","exp":9999999999,"email":"wangtianyu@example.com"}
const VALID_JWT =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMiIsImV4cCI6OTk5OTk5OTk5OSwiZW1haWwiOiJ3YW5ndGlhbnl1QGV4YW1wbGUuY29tIn0.signature";

// payload: {"sub":"12","exp":9999999999} (无 email)
const NO_EMAIL_JWT =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMiIsImV4cCI6OTk5OTk5OTk5OX0.signature";

// payload: {"sub":"12","exp":9999999999,"email":"novalid"} (邮箱格式错)
const BAD_EMAIL_JWT =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMiIsImV4cCI6OTk5OTk5OTk5OSwiZW1haWwiOiJub3ZhbGlkIn0.signature";

describe("decodeJwt (lib/auth.ts)", () => {
  it("decodes valid JWT payload with sub/exp/email", () => {
    const result = decodeJwt(VALID_JWT);
    expect(result).toEqual({
      sub: "12",
      exp: 9999999999,
      email: "wangtianyu@example.com",
    });
  });

  it("decodes JWT without email field", () => {
    const result = decodeJwt(NO_EMAIL_JWT);
    expect(result).toEqual({
      sub: "12",
      exp: 9999999999,
    });
    expect(result?.email).toBeUndefined();
  });

  it("returns null for invalid token (not 3 parts)", () => {
    expect(decodeJwt("invalid")).toBeNull();
    expect(decodeJwt("only.two")).toBeNull();
    expect(decodeJwt("a.b.c.d")).toBeNull();
  });

  it("returns null for empty string", () => {
    expect(decodeJwt("")).toBeNull();
  });

  it("returns null for non-string input (type guard)", () => {
    expect(decodeJwt(null as unknown as string)).toBeNull();
    expect(decodeJwt(undefined as unknown as string)).toBeNull();
    expect(decodeJwt(123 as unknown as string)).toBeNull();
  });

  it("returns null for malformed base64 payload", () => {
    expect(decodeJwt("aaa.!!!invalid!!!.bbb")).toBeNull();
  });
});

describe("getUserNameFromToken (lib/auth.ts · 决策 8 方案 A)", () => {
  it("derives userName from email prefix (happy path)", () => {
    expect(getUserNameFromToken(VALID_JWT)).toBe("wangtianyu");
  });

  it("returns null for token without email", () => {
    expect(getUserNameFromToken(NO_EMAIL_JWT)).toBeNull();
  });

  it("returns null for null token", () => {
    expect(getUserNameFromToken(null)).toBeNull();
  });

  it("returns null for invalid email format (no @)", () => {
    expect(getUserNameFromToken(BAD_EMAIL_JWT)).toBeNull();
  });

  it("returns null for empty string token", () => {
    expect(getUserNameFromToken("")).toBeNull();
  });

  it("handles email with subdomain correctly", () => {
    // payload: {"sub":"1","exp":1,"email":"admin@mail.knockwise.dev"}
    const jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxLCJlbWFpbCI6ImFkbWluQG1haWwua25vY2t3aXNlLmRldiJ9.sig";
    expect(getUserNameFromToken(jwt)).toBe("admin");
  });
});