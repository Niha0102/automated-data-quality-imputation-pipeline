"""Rate limiting middleware — Requirement 15.4.

100 requests/minute per authenticated user.
Unauthenticated requests are not rate-limited here (auth endpoints handle that).
"""
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from jose import JWTError
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.security import decode_token
from app.db.redis import get_redis, RATE_LIMIT_TTL

RATE_LIMIT = 100  # requests per window
WINDOW_SECONDS = 60


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        user_id = _extract_user_id(request)

        if user_id:
            try:
                redis = get_redis()
                key = f"rate_limit:{user_id}"
                count = await redis.incr(key)
                if count == 1:
                    await redis.expire(key, WINDOW_SECONDS)

                if count > RATE_LIMIT:
                    ttl = await redis.ttl(key)
                    return JSONResponse(
                        status_code=429,
                        content={
                            "error": {
                                "code": "RATE_LIMIT_EXCEEDED",
                                "message": f"Rate limit of {RATE_LIMIT} requests/minute exceeded.",
                                "request_id": request.headers.get("x-request-id", ""),
                            }
                        },
                        headers={"Retry-After": str(max(ttl, 1))},
                    )
            except Exception:
                # Redis unavailable — fail open (allow request through)
                pass

        return await call_next(request)


def _extract_user_id(request: Request) -> str | None:
    """Extract user_id from Bearer token without hitting the DB."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth[7:]
    try:
        payload = decode_token(token)
        return payload.get("sub")
    except (JWTError, Exception):
        return None
