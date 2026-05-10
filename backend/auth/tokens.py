from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..config import settings
from ..db.database import get_db

_bearer = HTTPBearer(auto_error=False)


def create_access_token(user_id: str, org_id: str) -> str:
    """Issue a signed JWT containing user_id and org_id."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub":    user_id,
        "org_id": org_id,
        "iat":    now,
        "exp":    now + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def _decode_jwt(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired — please log in again")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> dict:
    """
    FastAPI dependency.  Accepts two credential formats:
      - Bearer <JWT>   — issued by POST /auth/token
      - Bearer sk_*    — static API key stored in the orgs table
    Returns {"user_id": str, "org_id": str, "plan": str}.
    """
    if creds is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    token = creds.credentials

    # API key path (starts with "sk_")
    if token.startswith("sk_"):
        conn = get_db()
        row = conn.execute(
            "SELECT id, plan FROM orgs WHERE api_key = ?", (token,)
        ).fetchone()
        conn.close()
        if row is None:
            raise HTTPException(status_code=401, detail="Invalid API key")
        return {"user_id": "api", "org_id": row["id"], "plan": row["plan"]}

    # JWT path
    claims = _decode_jwt(token)
    return {
        "user_id": claims["sub"],
        "org_id":  claims.get("org_id", "org_acme"),
        "plan":    claims.get("plan", "pro"),
    }
