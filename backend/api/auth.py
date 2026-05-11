import httpx
from fastapi import APIRouter, HTTPException
from jose import jwt
from datetime import datetime, timedelta

from core.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


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
        # 1. Exchange code for access token
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

        # 2. Get user info
        user_resp = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if user_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch GitHub user")

        github_user = user_resp.json()
        return await _process_github_user(github_user)


async def _process_github_user(github_user: dict) -> dict:
    from models import User
    from models import Profile
    from core.database import async_session

    async with async_session() as db:
        # Find or create user
        from sqlalchemy import select
        result = await db.execute(
            select(User).where(User.github_id == str(github_user["id"]))
        )
        user = result.scalar_one_or_none()

        if user:
            user.last_login_at = datetime.utcnow()
            user.avatar_url = github_user.get("avatar_url")
            user.email = github_user.get("email")
        else:
            user = User(
                github_id=str(github_user["id"]),
                github_username=github_user["login"],
                avatar_url=github_user.get("avatar_url"),
                email=github_user.get("email"),
            )
            db.add(user)
            await db.flush()

            # Create default profile
            profile = Profile(user_id=user.id)
            db.add(profile)

        await db.commit()
        await db.refresh(user)

        # Generate JWT
        jwt_payload = {
            "sub": str(user.id),
            "github_id": user.github_id,
            "exp": datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes),
        }
        jwt_token = jwt.encode(jwt_payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

        return {
            "access_token": jwt_token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "github_username": user.github_username,
                "avatar_url": user.avatar_url,
                "email": user.email,
            },
        }


@router.get("/dev-login")
async def dev_login(username: str = "dev_user"):
    """Dev-only: bypass GitHub OAuth for local testing."""
    from models import User
    from models import Profile
    from core.database import async_session, engine
    from sqlalchemy import select

    try:
        async with async_session() as db:
            result = await db.execute(select(User).where(User.github_id == f"dev_{username}"))
            user = result.scalar_one_or_none()

            if user:
                user.last_login_at = datetime.utcnow()
            else:
                # Create tables if needed
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

            jwt_payload = {
                "sub": str(user.id),
                "github_id": user.github_id,
                "exp": datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes),
            }
            jwt_token = jwt.encode(jwt_payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

            return {
                "access_token": jwt_token,
                "token_type": "bearer",
                "user": {
                    "id": str(user.id),
                    "github_username": user.github_username,
                },
            }
    except Exception:
        # DB not available — generate a fake token
        return {
            "access_token": jwt.encode(
                {"sub": "dev-test-user", "exp": datetime.utcnow() + timedelta(days=7)},
                settings.jwt_secret_key, algorithm=settings.jwt_algorithm,
            ),
            "token_type": "bearer",
            "user": {"id": "dev-test-user", "github_username": username},
        }
