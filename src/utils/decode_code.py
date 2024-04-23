from fastapi import HTTPException, status
from jose.jwt import decode

from src.config import ALGORITHM, GOOGLE_AUTH_SECRET, SECRET_KEY
from src.crud.user import select_user_by_username
from src.session import SessionLocal
from src.utils.token import check_expire_token


def decode_google_token(token):
    decoded_data = decode(token, GOOGLE_AUTH_SECRET, algorithms=['RS256'],
                          audience=GOOGLE_AUTH_SECRET, options={"verify_signature": False})
    return decoded_data


def decode_access_token(access_token: str):
    try:
        payload = decode(access_token, SECRET_KEY, algorithms=ALGORITHM)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication token expired",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token_exp: int = payload.get("exp")
    username: str = payload.get("sub")

    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    db = SessionLocal()
    user = select_user_by_username(db=db, username=username)

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if check_expire_token(user, token_exp):
        return user
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication token expired",
            headers={"WWW-Authenticate": "Bearer"}
        )
