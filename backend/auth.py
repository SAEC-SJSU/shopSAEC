import secrets

from fastapi import Header, HTTPException

from config import settings

MANAGER_HEADER = "X-Manager-Password"


def check_manager_password(password: str | None) -> bool:
    """Constant-time check of a supplied password against MANAGER_PASSWORD.

    Returns False when no password is configured so a missing/blank env var
    locks the manager surface down instead of opening it to everyone.
    """
    if not settings.MANAGER_PASSWORD:
        return False
    if not password:
        return False
    return secrets.compare_digest(password, settings.MANAGER_PASSWORD)


async def require_manager(x_manager_password: str | None = Header(default=None)):
    """Dependency guarding endpoints that expose or mutate customer order data."""
    if not check_manager_password(x_manager_password):
        raise HTTPException(status_code=401, detail="Manager authentication required")
