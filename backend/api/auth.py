import hashlib
import os
import httpx
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Literal, Optional
from jose import jwt
from datetime import datetime, timedelta, timezone

from core.config import settings

logger = logging.getLogger("knockwise")
router = APIRouter(prefix="/api/auth", tags=["auth"])


# ── Schemas ────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: str
    password: str
    display_name: str

class LoginRequest(BaseModel):
    email: str
    password: str

class AuthenticateRequest(BaseModel):
    """v5 合并登录/注册接口（决策 13）"""
    email: str
    password: str
    display_name: Optional[str] = None  # 仅注册流程用 · 缺省 = email 前缀

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict
    mode: Literal["login", "register"] = "login"  # v5 新增

class CheckEmailResponse(BaseModel):
    """v5 check-email 接口（决策 10 · 自动判断前端用）"""
    exists: bool
    email: str


# ── Password Hashing (stdlib pbkdf2 — zero deps) ──────────────

def _hash_password(password: str) -> str:
    """Hash a password with PBKDF2-SHA256. Returns salt$hash hex."""
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 600_000)
    return salt.hex() + "$" + key.hex()

def _verify_password(password: str, stored: str) -> bool:
    """Verify a password against a stored PBKDF2 hash."""
    try:
        salt_hex, key_hex = stored.split("$")
        salt = bytes.fromhex(salt_hex)
        key = bytes.fromhex(key_hex)
        new_key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 600_000)
        return new_key == key
    except Exception:
        return False


# ── JWT Helpers ────────────────────────────────────────────────

def _create_token(user_id: str, email: str | None = None) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes),
    }
    if email:
        payload["email"] = email
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def _user_response(user) -> dict:
    return {
        "id": str(user.id),
        "email": user.email,
        "display_name": user.display_name or user.github_username or "",
        "avatar_url": user.avatar_url,
    }


# ── v5 核心：合并登录/注册（决策 13） ────────────────────────

async def _authenticate_core(
    email: str,
    password: str,
    display_name: Optional[str] = None,
    mode_override: Optional[Literal["login", "register"]] = None,
) -> dict:
    """合并 login + register 逻辑（v5 决策 13）

    - email 已存在 → 验证密码 · mode="login"
    - email 不存在 → 创建用户（display_name 缺省 = email 前缀）· mode="register"
    - race condition → IntegrityError → 返回 409

    mode_override 用于旧 endpoint 强制指定模式（如 login/register deprecated 兼容）
    """
    from models import User, Profile
    from core.database import async_session
    from sqlalchemy import select
    from sqlalchemy.exc import IntegrityError

    # Validate
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Invalid email")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    if display_name is not None and len(display_name) > 50:
        raise HTTPException(status_code=422, detail="display_name too long (max 50)")

    async with async_session() as db:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if user:
            # 邮箱存在 → 走登录流程
            if mode_override == "register":
                # 旧 register endpoint 显式要求新账号 · 但邮箱已存在 → 409
                raise HTTPException(status_code=409, detail="Email already registered")
            if not user.password_hash:
                raise HTTPException(status_code=401, detail="Invalid email or password")
            if not _verify_password(password, user.password_hash):
                raise HTTPException(status_code=401, detail="Invalid email or password")
            user.last_login_at = datetime.now(timezone.utc)
            mode = "login"
        else:
            # 邮箱不存在 → 走注册流程
            if mode_override == "login":
                # 旧 login endpoint 期望已注册用户 · 邮箱不存在 → 401
                raise HTTPException(status_code=401, detail="Invalid email or password")
            # display_name 缺省 = email 前缀
            effective_display_name = display_name if display_name else email.split("@")[0]
            try:
                user = User(
                    email=email,
                    password_hash=_hash_password(password),
                    display_name=effective_display_name,
                )
                db.add(user)
                await db.flush()
                profile = Profile(user_id=user.id)
                db.add(profile)
                await db.commit()
                await db.refresh(user)
                mode = "register"
            except IntegrityError:
                # race condition · 邮箱被其他请求抢先注册
                await db.rollback()
                raise HTTPException(status_code=409, detail="Email just registered, please login")

        token = _create_token(user.id, user.email)
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": _user_response(user),
            "mode": mode,
        }


# ── Auth Endpoints ─────────────────────────────────────────────

@router.get("/check-email", response_model=CheckEmailResponse)
async def check_email(email: str):
    """v5 新增 · 前端 onBlur 调 · 用于 UI 状态自动判断（决策 10）"""
    from models import User
    from core.database import async_session
    from sqlalchemy import select

    # Validate email format
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Invalid email")

    async with async_session() as db:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        return CheckEmailResponse(exists=user is not None, email=email)


@router.post("/authenticate", response_model=TokenResponse)
async def authenticate(data: AuthenticateRequest):
    """v5 新增 · 合并登录/注册接口（决策 13）

    后端内部根据 email 是否存在自动判断：
    - 邮箱存在 → 验证密码 → mode="login"
    - 邮箱不存在 → 创建用户 → mode="register"

    返回 access_token + user + mode · 前端用 mode 决定 toast 文案
    """
    return await _authenticate_core(
        email=data.email,
        password=data.password,
        display_name=data.display_name,
    )


@router.post("/register", response_model=TokenResponse, deprecated=True)
async def register(data: RegisterRequest):
    """⚠️ DEPRECATED · 内部 redirect 到 /api/auth/authenticate（决策 13）

    旧调用方（onboarding / dev-login / 集成测试）继续可用 · 但新代码应调 /api/auth/authenticate
    """
    return await _authenticate_core(
        email=data.email,
        password=data.password,
        display_name=data.display_name,
        mode_override="register",
    )


@router.post("/login", response_model=TokenResponse, deprecated=True)
async def login(data: LoginRequest):
    """⚠️ DEPRECATED · 内部 redirect 到 /api/auth/authenticate（决策 13）

    旧调用方（onboarding / dev-login / 集成测试）继续可用 · 但新代码应调 /api/auth/authenticate
    """
    return await _authenticate_core(
        email=data.email,
        password=data.password,
        display_name=None,  # login 流程忽略 display_name
        mode_override="login",
    )


# ── GitHub OAuth (existing, unchanged) ─────────────────────────

@router.get("/github/url")
async def github_login_url():
    url = (
        "https://github.com/login/oauth/authorize"
        f"?client_id={settings.github_client_id}"
        f"&redirect_uri={settings.github_redirect_uri}"
        "&scope=read:user,user:email"
    )
    return {"url": url}


@router.get("/github/callback")
async def github_callback(code: str):
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            json={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
                "redirect_uri": settings.github_redirect_uri,
            },
            headers={"Accept": "application/json"},
        )
        if token_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="GitHub token exchange failed")

        token_data = token_resp.json()
        if "error" in token_data:
            raise HTTPException(status_code=400, detail=token_data["error_description"])

        access_token = token_data["access_token"]

        user_resp = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if user_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch GitHub user")

        return await _process_github_user(user_resp.json())


async def _process_github_user(github_user: dict) -> dict:
    from models import User, Profile
    from core.database import async_session
    from sqlalchemy import select

    async with async_session() as db:
        result = await db.execute(
            select(User).where(User.github_id == str(github_user["id"]))
        )
        user = result.scalar_one_or_none()

        if user:
            user.last_login_at = datetime.now(timezone.utc)
            user.avatar_url = github_user.get("avatar_url")
            user.email = user.email or github_user.get("email")
        else:
            user = User(
                github_id=str(github_user["id"]),
                github_username=github_user["login"],
                avatar_url=github_user.get("avatar_url"),
                email=github_user.get("email"),
            )
            db.add(user)
            await db.flush()

            profile = Profile(user_id=user.id)
            db.add(profile)

        await db.commit()
        await db.refresh(user)

        token = _create_token(user.id, user.email)
        return {"access_token": token, "token_type": "bearer", "user": _user_response(user)}


# ── Dev Login (unchanged logic, updated for new fields) ───────

@router.get("/dev-login")
async def dev_login(username: str = "dev_user"):
    from models import User, Profile
    from core.database import async_session, engine
    from sqlalchemy import select

    try:
        async with async_session() as db:
            result = await db.execute(
                select(User).where(User.github_id == f"dev_{username}")
            )
            user = result.scalar_one_or_none()

            if user:
                user.last_login_at = datetime.now(timezone.utc)
            else:
                from core.database import Base
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                user = User(
                    github_id=f"dev_{username}",
                    github_username=username,
                )
                db.add(user)
                await db.flush()
                profile = Profile(user_id=user.id)
                db.add(profile)

            await db.commit()
            await db.refresh(user)

            token = _create_token(user.id, user.email)
            return {"access_token": token, "token_type": "bearer", "user": _user_response(user)}
    except Exception as e:
        logger.warning(f"Dev login DB error: {e}")
        return {
            "access_token": jwt.encode(
                {"sub": "dev-test-user", "exp": datetime.now(timezone.utc) + timedelta(days=7)},
                settings.jwt_secret_key, algorithm=settings.jwt_algorithm,
            ),
            "token_type": "bearer",
            "user": {"id": "dev-test-user", "display_name": username},
        }