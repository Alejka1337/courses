from fastapi import HTTPException, status


class InvalidAuthenticationTokenException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"}
        )


class InvalidRefreshTokenException(HTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")


class UserNotFoundException(HTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


class CategoryNotFoundException(HTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")


class CourseNotFoundException(HTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")


class InstructionNotFoundException(HTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail="Instruction not found")


class AccessTokenExpireException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token expired",
            headers={"WWW-Authenticate": "Bearer"}
        )


class RefreshTokenExpireException(HTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")


class PermissionDeniedException(HTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")


class EmailDoesExistException(HTTPException):
    def __init__(self, email):
        self.email = email
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"User with email {self.email} does exist"
        )


class UsernameDoesExistException(HTTPException):
    def __init__(self, username):
        self.username = username
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"User with username {self.username} does exist"
        )


class InvalidUsernameException(HTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username")


class InvalidPasswordException(HTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")


class InvalidActivateCodeException(HTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_424_FAILED_DEPENDENCY, detail="Invalid activate code")


class InvalidResetCodeException(HTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_424_FAILED_DEPENDENCY, detail="Invalid reset code")


class NotActivateAccountException(HTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail="Activate your account")


class CookieNotFoundException(HTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail="Cookies not found")


class EmailNotFoundException(HTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found")


class UpdateUsernameException(HTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="This username is already in use")


class UpdateEmailException(HTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="This email is already in use")
