"""T4 v5 auth endpoint 最小 pytest（不依赖 DB session · 只测纯逻辑）

覆盖：
- Schema 验证（AuthenticateRequest / CheckEmailResponse / TokenResponse）
- _authenticate_core 纯函数单元（validate 错误码）
- endpoint 注册到 router（FastAPI TestClient 检查 route 存在）
- 旧 endpoint 标 deprecated

T8 阶段会扩展 happy path + race condition + 真实 DB mock 测试。
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

import pytest


# ── Schema validation ──────────────────────────────────────


def test_authenticate_request_schema():
    """AuthenticateRequest 接受 email/password/display_name 可选"""
    from api.auth import AuthenticateRequest
    # 必须字段
    req = AuthenticateRequest(email="user@example.com", password="123456")
    assert req.email == "user@example.com"
    assert req.password == "123456"
    assert req.display_name is None
    # display_name 可选
    req_with_name = AuthenticateRequest(
        email="user@example.com", password="123456", display_name="昵称"
    )
    assert req_with_name.display_name == "昵称"


def test_check_email_response_schema():
    """CheckEmailResponse 返回 exists/email"""
    from api.auth import CheckEmailResponse
    resp = CheckEmailResponse(exists=True, email="wangtianyu@example.com")
    assert resp.exists is True
    assert resp.email == "wangtianyu@example.com"


def test_token_response_default_mode_login():
    """TokenResponse mode 字段默认 login（兼容旧调用方）"""
    from api.auth import TokenResponse
    resp = TokenResponse(access_token="eyJ...", user={"id": "1"})
    assert resp.mode == "login"  # default


def test_token_response_register_mode():
    """TokenResponse mode 字段显式 register"""
    from api.auth import TokenResponse
    resp = TokenResponse(access_token="eyJ...", user={"id": "1"}, mode="register")
    assert resp.mode == "register"


# ── _authenticate_core 纯函数（validate 错误码） ───────────────


def test_authenticate_core_invalid_email_format():
    """邮箱格式错（无 @）→ 400"""
    from api.auth import _authenticate_core
    with pytest.raises(HTTPException) as exc_info:
        # 用 asyncio.run 跑 async function
        import asyncio
        asyncio.run(_authenticate_core(email="invalid-no-at", password="123456"))
    assert exc_info.value.status_code == 400
    assert "Invalid email" in exc_info.value.detail


def test_authenticate_core_short_password():
    """密码 < 6 位 → 400"""
    from api.auth import _authenticate_core
    import asyncio
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(_authenticate_core(email="user@example.com", password="123"))
    assert exc_info.value.status_code == 400
    assert "at least 6" in exc_info.value.detail


def test_authenticate_core_display_name_too_long():
    """display_name > 50 字符 → 422"""
    from api.auth import _authenticate_core
    import asyncio
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(_authenticate_core(
            email="user@example.com", password="123456", display_name="a" * 51
        ))
    assert exc_info.value.status_code == 422


def test_authenticate_core_empty_email():
    """email 为空 → 400"""
    from api.auth import _authenticate_core
    import asyncio
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(_authenticate_core(email="", password="123456"))
    assert exc_info.value.status_code == 400


# ── Endpoint 注册验证（FastAPI TestClient 检查 route 存在） ─────


def test_endpoint_check_email_registered():
    """GET /api/auth/check-email 已注册"""
    from api.auth import router
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    # 实际调用会失败（没 DB）· 但能验证路由注册（响应不是 404）
    resp = client.get("/api/auth/check-email?email=test@example.com")
    # 不应是 404（路由没注册）
    assert resp.status_code != 404


def test_endpoint_authenticate_registered():
    """POST /api/auth/authenticate 已注册"""
    from api.auth import router
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    resp = client.post("/api/auth/authenticate", json={})
    # 422 (validation) 而不是 404 (route not found)
    assert resp.status_code in (400, 422)


def test_endpoint_login_marked_deprecated():
    """POST /api/auth/login 标 deprecated（FastAPI 自动 deprecated 标记）"""
    from api.auth import router
    routes = {r.path: r for r in router.routes}
    assert "/api/auth/login" in routes
    # deprecated=True 在 FastAPI Route 上有属性
    assert routes["/api/auth/login"].deprecated is True


def test_endpoint_register_marked_deprecated():
    """POST /api/auth/register 标 deprecated"""
    from api.auth import router
    routes = {r.path: r for r in router.routes}
    assert "/api/auth/register" in routes
    assert routes["/api/auth/register"].deprecated is True


def test_endpoint_check_email_not_deprecated():
    """GET /api/auth/check-email 是新接口 · 不应标 deprecated（默认 None 或 False）"""
    from api.auth import router
    routes = {r.path: r for r in router.routes}
    assert "/api/auth/check-email" in routes
    assert not routes["/api/auth/check-email"].deprecated  # None or False 都算 not deprecated


def test_endpoint_authenticate_not_deprecated():
    """POST /api/auth/authenticate 是新接口 · 不应标 deprecated（默认 None 或 False）"""
    from api.auth import router
    routes = {r.path: r for r in router.routes}
    assert "/api/auth/authenticate" in routes
    assert not routes["/api/auth/authenticate"].deprecated  # None or False 都算 not deprecated


# ── 路由列表完整性 ───────────────────────────────────────


def test_all_5_auth_endpoints_registered():
    """所有 5 个 auth endpoint 都注册（check-email/authenticate/login/register + github/dev-login）"""
    from api.auth import router
    paths = [r.path for r in router.routes]
    # 核心 4 个
    assert "/api/auth/check-email" in paths
    assert "/api/auth/authenticate" in paths
    assert "/api/auth/login" in paths
    assert "/api/auth/register" in paths
    # GitHub + dev-login（保留兼容）
    assert "/api/auth/github/url" in paths or "/api/auth/dev-login" in paths


# ── 旧 endpoint 内部 redirect（不依赖 DB · 通过 router 行为） ─────


def test_legacy_login_calls_authenticate_core(monkeypatch):
    """旧 /login endpoint 内部 redirect 到 _authenticate_core（mode=login 强制）

    通过 monkeypatch _authenticate_core 验证被调用 + mode_override="login"
    """
    from api import auth
    calls = []

    async def fake_authenticate(email, password, display_name, mode_override=None):
        calls.append({
            "email": email,
            "password": password,
            "display_name": display_name,
            "mode_override": mode_override,
        })
        return {
            "access_token": "fake-token",
            "token_type": "bearer",
            "user": {"id": "1", "email": email, "display_name": "user"},
            "mode": "login",
        }

    monkeypatch.setattr(auth, "_authenticate_core", fake_authenticate)

    from api.auth import router
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    resp = client.post("/api/auth/login", json={
        "email": "user@example.com",
        "password": "123456",
    })
    assert resp.status_code == 200
    assert len(calls) == 1
    assert calls[0]["email"] == "user@example.com"
    assert calls[0]["password"] == "123456"
    assert calls[0]["display_name"] is None  # login 流程忽略 display_name
    assert calls[0]["mode_override"] == "login"  # 强制 login 模式


def test_legacy_register_calls_authenticate_core(monkeypatch):
    """旧 /register endpoint 内部 redirect 到 _authenticate_core（mode=register 强制）"""
    from api import auth
    calls = []

    async def fake_authenticate(email, password, display_name, mode_override=None):
        calls.append({
            "email": email,
            "password": password,
            "display_name": display_name,
            "mode_override": mode_override,
        })
        return {
            "access_token": "fake-token",
            "token_type": "bearer",
            "user": {"id": "1", "email": email, "display_name": display_name},
            "mode": "register",
        }

    monkeypatch.setattr(auth, "_authenticate_core", fake_authenticate)

    from api.auth import router
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    resp = client.post("/api/auth/register", json={
        "email": "newuser@example.com",
        "password": "123456",
        "display_name": "新用户",
    })
    assert resp.status_code == 200
    assert len(calls) == 1
    assert calls[0]["email"] == "newuser@example.com"
    assert calls[0]["password"] == "123456"
    assert calls[0]["display_name"] == "新用户"  # register 流程保留 display_name
    assert calls[0]["mode_override"] == "register"  # 强制 register 模式


def test_new_authenticate_calls_authenticate_core_no_override(monkeypatch):
    """新 /authenticate endpoint 不传 mode_override（自动判断）"""
    from api import auth
    calls = []

    async def fake_authenticate(email, password, display_name, mode_override=None):
        calls.append({"mode_override": mode_override, "display_name": display_name})
        return {
            "access_token": "fake-token",
            "token_type": "bearer",
            "user": {"id": "1", "email": email},
            "mode": "login",
        }

    monkeypatch.setattr(auth, "_authenticate_core", fake_authenticate)

    from api.auth import router
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    client.post("/api/auth/authenticate", json={
        "email": "user@example.com",
        "password": "123456",
        "display_name": "昵称",
    })
    assert len(calls) == 1
    assert calls[0]["mode_override"] is None  # 新接口不强制 mode
    assert calls[0]["display_name"] == "昵称"  # display_name 透传


# ─── T8 后端 auth 综合测试（happy / race / 旧 endpoint 兼容） ─────────
# 使用 pytest-asyncio (asyncio_mode = "auto" · 来自 pyproject.toml)
# 用 AsyncMock 替换 async_session 上下文管理器（不依赖真实 DB）

import pytest


def make_mock_db_session(user_in_db=None, raise_integrity_error=False):
    """创建 mock async DB session 上下文管理器

    user_in_db: None (邮箱不存在 · 走注册) 或 SimpleNamespace (邮箱存在 · 走登录)
    raise_integrity_error: True 时 flush() 抛 IntegrityError（模拟 race condition）

    用 class 模拟 async context manager（避免 AsyncMock __aenter__ 不被 await 的问题）
    """
    from sqlalchemy.exc import IntegrityError

    class FakeDB:
        def __init__(self):
            self.user = user_in_db
            self._raise_integrity = raise_integrity_error

        async def execute(self, query):
            class _Result:
                def scalar_one_or_none(self_inner):
                    return self.user
            return _Result()

        async def flush(self):
            if self._raise_integrity:
                raise IntegrityError("INSERT", {}, Exception("Duplicate entry"))

        async def commit(self):
            pass

        async def refresh(self, user):
            user.id = 42  # DB INSERT 后分配 id

        async def add(self, obj):
            pass

        async def rollback(self):
            pass

    class FakeSessionCtx:
        def __init__(self):
            self.db = FakeDB()

        async def __aenter__(self):
            return self.db

        async def __aexit__(self, *args):
            return None

    return FakeSessionCtx()


# ─── happy path 测试（端到端 + mock DB） ──────────────────────


def test_authenticate_register_happy_path_new_email():
    """新邮箱 → 走注册流程 · 200 + mode=register + token + user"""
    from api.auth import router
    from fastapi import FastAPI
    mock_session = make_mock_db_session(user_in_db=None)

    with patch("core.database.async_session", return_value=mock_session):
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        resp = client.post("/api/auth/authenticate", json={
            "email": "newuser@example.com",
            "password": "123456",
            "display_name": "新用户",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["mode"] == "register"
        assert body["user"]["email"] == "newuser@example.com"
        assert body["user"]["display_name"] == "新用户"
        assert "access_token" in body
        assert body["token_type"] == "bearer"


def test_authenticate_register_default_display_name():
    """新邮箱 + display_name 缺省 → 用 email 前缀"""
    from api.auth import router
    from fastapi import FastAPI
    mock_session = make_mock_db_session(user_in_db=None)

    with patch("core.database.async_session", return_value=mock_session):
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        resp = client.post("/api/auth/authenticate", json={
            "email": "auto-name@example.com",
            "password": "123456",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["user"]["display_name"] == "auto-name"  # email 前缀


def test_authenticate_login_happy_path_existing_email():
    """已注册邮箱 + 正确密码 → 走登录流程 · 200 + mode=login"""
    from api.auth import _hash_password, router
    from fastapi import FastAPI
    user = SimpleNamespace(
        id=42, email="existing@example.com",
        display_name="existing", github_username=None, avatar_url=None,
        password_hash=_hash_password("123456"),
        last_login_at=None,
    )
    mock_session = make_mock_db_session(user_in_db=user)

    with patch("core.database.async_session", return_value=mock_session):
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        resp = client.post("/api/auth/authenticate", json={
            "email": "existing@example.com",
            "password": "123456",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["mode"] == "login"
        assert body["user"]["email"] == "existing@example.com"


def test_authenticate_login_wrong_password_returns_401():
    """已注册邮箱 + 错误密码 → 401"""
    from api.auth import _hash_password, router
    from fastapi import FastAPI
    user = SimpleNamespace(
        id=42, email="existing@example.com",
        display_name="existing", github_username=None, avatar_url=None,
        password_hash=_hash_password("correct"),
        last_login_at=None,
    )
    mock_session = make_mock_db_session(user_in_db=user)

    with patch("core.database.async_session", return_value=mock_session):
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        resp = client.post("/api/auth/authenticate", json={
            "email": "existing@example.com",
            "password": "wrongpassword",  # ≥ 6 位避免 password length 校验（400）· 测试密码错
        })
        assert resp.status_code == 401
        assert "Invalid email or password" in resp.json()["detail"]


# ─── race condition 测试 ─────────────────────────────────


def test_authenticate_race_condition_returns_409():
    """race condition · check-email 后到 submit 之间被抢先注册 → IntegrityError → 409"""
    from api.auth import router
    from fastapi import FastAPI
    # user_in_db=None 模拟 check-email 之后被其他请求抢先注册
    # flush() 抛 IntegrityError（DB 触发 unique 约束）
    mock_session = make_mock_db_session(user_in_db=None, raise_integrity_error=True)

    with patch("core.database.async_session", return_value=mock_session):
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        resp = client.post("/api/auth/authenticate", json={
            "email": "race@example.com",
            "password": "123456",
            "display_name": "race",
        })
        assert resp.status_code == 409
        assert "just registered" in resp.json()["detail"]


# ─── check-email endpoint 测试 ────────────────────────────


def test_check_email_returns_200_exists_true():
    """GET /api/auth/check-email · 邮箱存在 → 200 + exists=true"""
    from api.auth import router
    from fastapi import FastAPI
    user = SimpleNamespace(id=42, email="wangtianyu@example.com")
    mock_session = make_mock_db_session(user_in_db=user)

    with patch("core.database.async_session", return_value=mock_session):
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        resp = client.get("/api/auth/check-email?email=wangtianyu@example.com")
        assert resp.status_code == 200
        body = resp.json()
        assert body["exists"] is True
        assert body["email"] == "wangtianyu@example.com"


def test_check_email_returns_200_exists_false():
    """GET /api/auth/check-email · 邮箱不存在 → 200 + exists=false"""
    from api.auth import router
    from fastapi import FastAPI
    mock_session = make_mock_db_session(user_in_db=None)

    with patch("core.database.async_session", return_value=mock_session):
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        resp = client.get("/api/auth/check-email?email=newuser@example.com")
        assert resp.status_code == 200
        body = resp.json()
        assert body["exists"] is False


def test_check_email_invalid_format_returns_400():
    """GET /api/auth/check-email · 邮箱格式错 → 400"""
    from api.auth import router
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    resp = client.get("/api/auth/check-email?email=invalid-no-at")
    assert resp.status_code == 400
    assert "Invalid email" in resp.json()["detail"]


# ─── 旧 endpoint 兼容（end-to-end · 不 mock _authenticate_core） ─


def test_legacy_register_endpoint_compat_with_email_exists():
    """旧 /register endpoint · 邮箱已存在 → 409（mode_override=register 强制）"""
    from api.auth import _hash_password, router
    from fastapi import FastAPI
    user = SimpleNamespace(
        id=42, email="existing@example.com",
        display_name="existing", github_username=None, avatar_url=None,
        password_hash=_hash_password("123456"),
        last_login_at=None,
    )
    mock_session = make_mock_db_session(user_in_db=user)

    with patch("core.database.async_session", return_value=mock_session):
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        resp = client.post("/api/auth/register", json={
            "email": "existing@example.com",
            "password": "123456",
            "display_name": "duplicate",
        })
        assert resp.status_code == 409
        assert "already registered" in resp.json()["detail"]


def test_legacy_login_endpoint_compat_with_email_not_exists():
    """旧 /login endpoint · 邮箱不存在 → 401（mode_override=login 强制）"""
    from api.auth import router
    from fastapi import FastAPI
    mock_session = make_mock_db_session(user_in_db=None)

    with patch("core.database.async_session", return_value=mock_session):
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        resp = client.post("/api/auth/login", json={
            "email": "notfound@example.com",
            "password": "123456",
        })
        assert resp.status_code == 401
        assert "Invalid email or password" in resp.json()["detail"]


def test_legacy_login_endpoint_compat_login_success():
    """旧 /login endpoint · 邮箱存在 + 正确密码 → 200 + mode=login"""
    from api.auth import _hash_password, router
    from fastapi import FastAPI
    user = SimpleNamespace(
        id=42, email="existing@example.com",
        display_name="existing", github_username=None, avatar_url=None,
        password_hash=_hash_password("123456"),
        last_login_at=None,
    )
    mock_session = make_mock_db_session(user_in_db=user)

    with patch("core.database.async_session", return_value=mock_session):
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        resp = client.post("/api/auth/login", json={
            "email": "existing@example.com",
            "password": "123456",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["mode"] == "login"


def test_legacy_register_endpoint_compat_register_success():
    """旧 /register endpoint · 邮箱不存在 + display_name → 200 + mode=register"""
    from api.auth import router
    from fastapi import FastAPI
    mock_session = make_mock_db_session(user_in_db=None)

    with patch("core.database.async_session", return_value=mock_session):
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        resp = client.post("/api/auth/register", json={
            "email": "newuser@example.com",
            "password": "123456",
            "display_name": "新用户",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["mode"] == "register"
        assert body["user"]["display_name"] == "新用户"