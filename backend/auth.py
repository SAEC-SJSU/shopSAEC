import base64
import hashlib
import hmac
import json
import time

from fastapi import Header, HTTPException

from config import settings

_SESSION_KEY_INFO = b"saec-manager-session-v1"

# In-memory login throttling. Per-process only, which is fine for the single
# container this API runs in; a multi-worker deploy would need shared state.
_LOGIN_FAILURES: dict[str, list[float]] = {}
MAX_LOGIN_FAILURES = 10
LOGIN_WINDOW_SECONDS = 300

# Backstop for when per-IP buckets are evaded entirely -- forged forwarded
# headers, a botnet, or IPv6 rotation all give an attacker unlimited fresh keys.
# Deliberately generous so a manager mistyping their password can never trip it;
# it exists to cap total throughput, not to police individuals.
_GLOBAL_FAILURES: list[float] = []
MAX_GLOBAL_LOGIN_FAILURES = 100


def _signing_key() -> bytes | None:
    """Key used to sign manager session tokens.

    Falls back to a key derived from MANAGER_PASSWORD so no extra configuration
    is required; rotating the password then invalidates outstanding sessions.
    Returns None when nothing is configured, so auth fails closed.
    """
    if settings.MANAGER_SECRET:
        return settings.MANAGER_SECRET.encode()
    if settings.MANAGER_PASSWORD:
        return hmac.new(
            settings.MANAGER_PASSWORD.encode(), _SESSION_KEY_INFO, hashlib.sha256
        ).digest()
    return None


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _sign(body: str, key: bytes) -> str:
    return _b64encode(hmac.new(key, body.encode(), hashlib.sha256).digest())


def check_manager_password(password: str | None) -> bool:
    """Constant-time check of a supplied password against MANAGER_PASSWORD.

    Returns False when no password is configured so a missing/blank env var
    locks the manager surface down instead of opening it to everyone.
    """
    if not settings.MANAGER_PASSWORD:
        return False
    if not password:
        return False
    return hmac.compare_digest(password, settings.MANAGER_PASSWORD)


def issue_manager_token() -> str:
    """Mint a signed token that expires after MANAGER_SESSION_HOURS."""
    key = _signing_key()
    if key is None:
        raise HTTPException(status_code=503, detail="Manager auth is not configured")

    payload = json.dumps(
        {
            "sub": "manager",
            "exp": int(time.time()) + settings.MANAGER_SESSION_HOURS * 3600,
        },
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    body = _b64encode(payload)
    return f"{body}.{_sign(body, key)}"


def verify_manager_token(token: str | None) -> bool:
    key = _signing_key()
    if key is None or not token:
        return False

    body, separator, signature = token.partition(".")
    if not separator or not body or not signature:
        return False

    # Verify the signature before trusting anything inside the payload.
    if not hmac.compare_digest(signature, _sign(body, key)):
        return False

    try:
        payload = json.loads(_b64decode(body))
        expires_at = int(payload["exp"])
    except (ValueError, KeyError, TypeError):
        return False

    return payload.get("sub") == "manager" and expires_at > time.time()


async def require_manager(authorization: str | None = Header(default=None)):
    """Dependency guarding endpoints that expose or mutate customer order data."""
    scheme, separator, token = (authorization or "").partition(" ")
    if not separator or scheme.lower() != "bearer" or not verify_manager_token(token.strip()):
        raise HTTPException(
            status_code=401,
            detail="Manager authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )


def login_rate_limited(client: str) -> bool:
    """True when either the per-client or the global failure budget is spent."""
    cutoff = time.time() - LOGIN_WINDOW_SECONDS

    global _GLOBAL_FAILURES
    _GLOBAL_FAILURES = [t for t in _GLOBAL_FAILURES if t > cutoff]
    if len(_GLOBAL_FAILURES) >= MAX_GLOBAL_LOGIN_FAILURES:
        return True

    recent = [t for t in _LOGIN_FAILURES.get(client, []) if t > cutoff]
    if recent:
        _LOGIN_FAILURES[client] = recent
    else:
        _LOGIN_FAILURES.pop(client, None)
    return len(recent) >= MAX_LOGIN_FAILURES


def record_login_failure(client: str) -> None:
    _LOGIN_FAILURES.setdefault(client, []).append(time.time())
    _GLOBAL_FAILURES.append(time.time())


def clear_login_failures(client: str) -> None:
    """Called after a correct password, which also releases the global budget."""
    _LOGIN_FAILURES.pop(client, None)
    _GLOBAL_FAILURES.clear()
