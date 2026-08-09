import jwt
from fastapi import Header, HTTPException, status

from app.config import settings


def require_auth(authorization: str | None = Header(default=None)) -> dict:
    """Validates a Bearer JWT and returns its claims.

    Dev mode: if no Authorization header is sent, requests are allowed through
    as an anonymous dev user so the stack is easy to run locally. Remove this
    fallback before exposing the gateway beyond localhost.
    """
    if authorization is None:
        return {"sub": "dev-user", "scopes": ["*"]}

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Authorization header")

    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc
