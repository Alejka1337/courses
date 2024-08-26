from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWTError
from jose.jwt import decode
from sqlalchemy.orm import Session

from src.config import ALGORITHM, SECRET_KEY
from src.crud.user import UserRepository
from src.session import get_db
from src.utils.exceptions import (
    AccessTokenExpireException,
    InvalidAuthenticationTokenException,
    UserNotFoundException,
)
from src.utils.token import check_expire_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/user/login")


def get_current_user(db: Session = Depends(get_db), access_token: str = Depends(oauth2_scheme)):
    try:
        payload = decode(access_token, SECRET_KEY, algorithms=ALGORITHM)
        token_exp: int = payload.get("exp")
        username: str = payload.get("sub")

        if username is None:
            raise InvalidAuthenticationTokenException()

        user_repository = UserRepository(db=db)
        user = user_repository.select_user_by_username(username=username)

        if user is None:
            raise UserNotFoundException()

        if check_expire_token(user, token_exp):
            return user

        else:
            raise AccessTokenExpireException()

    except ExpiredSignatureError:
        raise AccessTokenExpireException()

    except JWTError:
        raise InvalidAuthenticationTokenException()
