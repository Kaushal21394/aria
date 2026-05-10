from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..auth.tokens import create_access_token
from ..db.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])

# Demo orgs exposed to the frontend login panel
DEMO_ORG_IDS = ["org_acme", "org_globex", "org_initech"]


class TokenRequest(BaseModel):
    org_id: str
    user_id: str  # free-form name, no password for demo


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    org_id: str
    org_name: str
    plan: str
    expires_in_minutes: int


@router.post("/token", response_model=TokenResponse)
def login(body: TokenRequest) -> TokenResponse:
    """
    Demo login endpoint — no password required.
    Select an org and supply any user name to receive a JWT.

    In production this would validate credentials against a users table.
    """
    if not body.org_id or not body.user_id.strip():
        raise HTTPException(status_code=422, detail="org_id and user_id are required")

    conn = get_db()
    row = conn.execute(
        "SELECT id, name, plan FROM orgs WHERE id = ?", (body.org_id,)
    ).fetchone()
    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail=f"Unknown org: {body.org_id}")

    from ..config import settings

    token = create_access_token(user_id=body.user_id.strip(), org_id=row["id"])
    return TokenResponse(
        access_token=token,
        org_id=row["id"],
        org_name=row["name"],
        plan=row["plan"],
        expires_in_minutes=settings.jwt_expire_minutes,
    )


@router.get("/orgs")
def list_orgs() -> list:
    """Return the available demo orgs for the login panel."""
    conn = get_db()
    rows = conn.execute("SELECT id, name, plan FROM orgs ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]
