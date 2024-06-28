from datetime import datetime

from sqlalchemy.orm import Session

from jose import ExpiredSignatureError, JWTError
from jose.jwt import decode

from src.config import ALGORITHM, GOOGLE_AUTH_SECRET, SECRET_KEY
from src.crud.user import select_user_by_username
from src.session import SessionLocal
from src.utils.exceptions import (AccessTokenExpireException, InvalidAuthenticationTokenException,
                                  InvalidRefreshTokenException, RefreshTokenExpireException, UserNotFoundException)
from src.utils.token import check_expire_token


def decode_google_token(token):
    decoded_data = decode(
        token=token,
        key=GOOGLE_AUTH_SECRET,
        algorithms=['RS256'],
        audience=GOOGLE_AUTH_SECRET,
        options={"verify_signature": False}
    )
    return decoded_data


def decode_access_token(db: Session, access_token: str):
    try:
        payload = decode(access_token, SECRET_KEY, algorithms=ALGORITHM)
    except Exception:
        raise AccessTokenExpireException()

    token_exp: int = payload.get("exp")
    username: str = payload.get("sub")

    if username is None:
        raise InvalidAuthenticationTokenException()

    user = select_user_by_username(db=db, username=username)

    if user is None:
        raise UserNotFoundException()

    if check_expire_token(user, token_exp):
        return user
    else:
        raise AccessTokenExpireException()


def decode_and_check_refresh_token(refresh_token: str):
    try:
        payload = decode(refresh_token, SECRET_KEY, algorithms=ALGORITHM)
        token_exp = payload.get("exp")
        username = payload.get("sub")

        if username is None:
            raise InvalidRefreshTokenException()

        exp_date = datetime.utcfromtimestamp(token_exp).strftime("%Y-%m-%d %H:%M:%S")

        if exp_date <= datetime.today().strftime("%Y-%m-%d %H:%M:%S"):
            raise RefreshTokenExpireException()

        return {"sub": username}

    except ExpiredSignatureError:
        raise RefreshTokenExpireException()

    except JWTError:
        raise InvalidRefreshTokenException()
