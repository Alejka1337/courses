from datetime import datetime, timedelta

from jose.jwt import encode

from src.config import ACCESS_TOKEN_EXPIRE, ALGORITHM, REFRESH_TOKEN_EXPIRE, SECRET_KEY
from src.models import UserOrm


def create_access_token(data: dict, expire_delta: timedelta = None):
    to_encode = data.copy()
    if expire_delta:
        expire = datetime.utcnow() + expire_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE)
    to_encode.update({"exp": expire})
    access_token = encode(claims=to_encode, key=SECRET_KEY, algorithm=ALGORITHM)
    return access_token, expire


def create_refresh_token(data: dict):
    expire = datetime.utcnow() + timedelta(minutes=REFRESH_TOKEN_EXPIRE)
    data.update({"exp": expire})
    refresh_token = encode(claims=data, key=SECRET_KEY, algorithm=ALGORITHM)
    return refresh_token, expire


def check_expire_token(user: UserOrm, exp_token: int):
    expire_token = datetime.utcfromtimestamp(exp_token)
    expire_token_str = expire_token.strftime("%Y-%m-%d %H:%M:%S")
    user_expire_token_str = user.exp_token.strftime("%Y-%m-%d %H:%M:%S")
    if expire_token_str == user_expire_token_str:
        return True
    return False
