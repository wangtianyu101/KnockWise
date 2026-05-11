import logging
import logging
from uuid import uuid4

from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db
from models import User

logger = logging.getLogger("codemock.auth")
bearer_scheme = HTTPBearer()


def _make_virtual_user(user_id_str: str, username: str) -> User:
    """Create an in-memory User object without DB — uses string IDs for MySQL."""
    uid = user_id_str if len(user_id_str) == 36 else str(uuid4())
    return User(id=uid, github_id=f"dev_{username}", github_username=username)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id_str = payload["sub"]
        username = payload.get("username", "unknown")
    except (JWTError, ValueError, KeyError):
        raise HTTPException(status_code=401, detail="Invalid token")

    # Try DB lookup first
    try:
        result = await db.execute(select(User).where(User.id == user_id_str))
        user = result.scalar_one_or_none()
        if user:
            return user
    except Exception:
        logger.debug("DB unavailable, using virtual user from token")

    # Dev mode fallback: create virtual user from token claims
    return _make_virtual_user(user_id_str, username)
