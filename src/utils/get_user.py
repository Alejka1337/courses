from datetime import datetime

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWTError
from jose.jwt import decode
from sqlalchemy.orm import Session

from src.config import ALGORITHM, SECRET_KEY
from src.crud.user import select_user_by_username
from src.session import get_db
from src.utils.token import check_expire_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/user/login")


def get_current_user(db: Session = Depends(get_db), access_token: str = Depends(oauth2_scheme)):
    try:
        payload = decode(access_token, SECRET_KEY, algorithms=ALGORITHM)
        token_exp: int = payload.get("exp")
        username: str = payload.get("sub")

        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"}
            )

        user = select_user_by_username(db=db, username=username)

        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        if check_expire_token(user, token_exp):
            return user

        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Access token expired",
                headers={"WWW-Authenticate": "Bearer"}
            )

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token expired",
            headers={"WWW-Authenticate": "Bearer"}
        )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"}
        )


def decode_and_check_refresh_token(refresh_token: str):
    try:
        payload = decode(refresh_token, SECRET_KEY, algorithms=ALGORITHM)
        token_exp = payload.get("exp")
        username = payload.get("sub")

        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        exp_date = datetime.utcfromtimestamp(token_exp).strftime("%Y-%m-%d %H:%M:%S")

        if exp_date <= datetime.today().strftime("%Y-%m-%d %H:%M:%S"):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

        return {"sub": username}

    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
