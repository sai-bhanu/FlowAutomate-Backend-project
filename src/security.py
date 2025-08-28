from fastapi import Header, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import time, jwt
from .config import settings

bearer = HTTPBearer(auto_error=False)

def require_api_key(x_api_key: str | None = Header(default=None)):
    if x_api_key and x_api_key in settings.API_KEYS:
        return True
    raise HTTPException(status_code=401, detail="Invalid or missing API key")

def require_jwt(request: Request, credentials: HTTPAuthorizationCredentials | None = None):
    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"], issuer=settings.JWT_ISSUER)
        request.state.user = payload.get("sub")
        return True
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid JWT")

def mint_jwt(sub: str, ttl_sec: int = 3600) -> str:
    now = int(time.time())
    payload = {
        "iss": settings.JWT_ISSUER,
        "sub": sub,
        "iat": now,
        "exp": now + ttl_sec
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
