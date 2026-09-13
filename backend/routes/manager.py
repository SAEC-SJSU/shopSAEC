from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from auth import (
    check_manager_password,
    clear_login_failures,
    issue_manager_token,
    login_rate_limited,
    record_login_failure,
)
from config import settings

router = APIRouter()


class LoginRequest(BaseModel):
    password: str


@router.post("/login")
async def manager_login(body: LoginRequest, request: Request):
    # Note: behind a reverse proxy this is the proxy's address unless the app is
    # run with --proxy-headers and the proxy sets X-Forwarded-For.
    client = request.client.host if request.client else "unknown"

    if login_rate_limited(client):
        raise HTTPException(
            status_code=429, detail="Too many login attempts, try again later"
        )

    if not check_manager_password(body.password):
        record_login_failure(client)
        raise HTTPException(status_code=401, detail="Invalid password")

    clear_login_failures(client)
    return {
        "token": issue_manager_token(),
        "expires_in": settings.MANAGER_SESSION_HOURS * 3600,
    }
