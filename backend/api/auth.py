import hashlib
import os
import httpx
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
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

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


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


# ── Auth Endpoints ─────────────────────────────────────────────

@router.post("/register")
async def register(data: RegisterRequest):
    """Register with email + password."""
    from models import User, Profile
    from core.database import async_session
    from sqlalchemy import select

    # Validate
    if len(data.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    if not data.email or "@" not in data.email:
        raise HTTPException(status_code=400, detail="Invalid email")

    async with async_session() as db:
        # Check duplicate email
        result = await db.execute(select(User).where(User.email == data.email))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Email already registered")

        user = User(
            email=data.email,
            password_hash=_hash_password(data.password),
            display_name=data.display_name,
        )
        db.add(user)
        await db.flush()

        # Create default profile
        profile = Profile(user_id=user.id)
        db.add(profile)
        await db.commit()
        await db.refresh(user)

        token = _create_token(user.id, user.email)
        return {"access_token": token, "token_type": "bearer", "user": _user_response(user)}


@router.post("/login")
async def login(data: LoginRequest):
    """Login with email + password."""
    from models import User
    from core.database import async_session
    from sqlalchemy import select

    async with async_session() as db:
        result = await db.execute(select(User).where(User.email == data.email))
        user = result.scalar_one_or_none()

        if not user or not user.password_hash:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        if not _verify_password(data.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        user.last_login_at = datetime.now(timezone.utc)
        await db.commit()

        token = _create_token(user.id, user.email)
        return {"access_token": token, "token_type": "bearer", "user": _user_response(user)}


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
