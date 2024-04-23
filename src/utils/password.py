from passlib.hash import bcrypt


def hash_password(password: str) -> str:
    hashed_password = bcrypt.hash(password)
    return hashed_password


def check_password(password: str, hashed_password: str) -> bool:
    return bcrypt.verify(password, hashed_password)
