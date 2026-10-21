import secrets
from fastapi import Header, HTTPException, status
from app.core.config import settings

async def require_api_key(authorization: str | None = Header(default=None)):
    """MVP bearer-key auth. Replace with OAuth/OIDC and tenant policies for production."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    if not secrets.compare_digest(token, settings.api_key):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API key")
