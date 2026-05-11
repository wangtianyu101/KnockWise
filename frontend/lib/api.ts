const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

let token: string | null = null;

export function setToken(t: string) {
  token = t;
  if (typeof window !== "undefined") {
    localStorage.setItem("codemock_token", t);
  }
}

export function getToken(): string | null {
  if (token) return token;
  if (typeof window !== "undefined") {
    token = localStorage.getItem("codemock_token");
  }
  return token;
}

async function request(path: string, options: RequestInit = {}): Promise<any> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> || {}),
  };
  const t = getToken();
  if (t) headers["Authorization"] = `Bearer ${t}`;

  const controller = new AbortController();
  // Use longer timeout: STT can take 10-20s on first model load, LLM 5-15s
  const isTranscribe = path.endsWith("/transcribe");
  const timeoutMs = isTranscribe ? 60000 : 30000;
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(`${BASE_URL}${path}`, {
      ...options,
      headers,
      signal: controller.signal,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
  } finally {
    clearTimeout(timer);
  }
}

export function clearToken() {
  token = null;
  if (typeof window !== "undefined") {
    localStorage.removeItem("codemock_token");
  }
}

// Auth
export async function getGitHubLoginUrl() {
  return request("/api/auth/github/url");
}

export async function handleGitHubCallback(code: string) {
  const data = await request(`/api/auth/github/callback?code=${code}`);
  if (data.access_token) {
    setToken(data.access_token);
  }
  return data;
}

export async function devLogin(username: string = "dev_user") {
  const data = await request(`/api/auth/dev-login?username=${encodeURIComponent(username)}`);
  if (data.access_token) {
    setToken(data.access_token);
  }
  return data;
}

// Profile
export async function getProfile() {
  return request("/api/profile/me");
}

export async function updateProfile(profile: Record<string, any>) {
  return request("/api/profile/me", { method: "PUT", body: JSON.stringify(profile) });
}

// Interview
export async function startInterview(round: string = "round1") {
  return request("/api/interviews", {
    method: "POST",
    body: JSON.stringify({ round, style: "standard" }),
  });
}

export async function getNextQuestion(interviewId: string) {
  return request(`/api/interviews/${interviewId}/next-question`, { method: "POST" });
}

export async function submitAnswer(recordId: string, userAnswer: string, timeSpent: number = 0) {
  return request(`/api/interviews/records/${recordId}/answer`, {
    method: "POST",
    body: JSON.stringify({ user_answer: userAnswer, time_spent: timeSpent }),
  });
}

// Report
export async function getReport(interviewId: string) {
  return request(`/api/reports/interview/${interviewId}`);
}

export async function generateReport(interviewId: string) {
  return request(`/api/reports/interview/${interviewId}`, { method: "POST" });
}
