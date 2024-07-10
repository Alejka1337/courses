from fastapi.responses import JSONResponse

from src.schemas.user import AuthResponse


def after_auth_response(response_data: AuthResponse):
    response = JSONResponse(
        content={
            "access_token": response_data.access_token,
            "token_type": "bearer",
            "access_token_expire": response_data.access_token_expire.strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": response_data.user_id,
            "username": response_data.username,
            "user_type": response_data.user_type,
            "message": response_data.message
        },
        headers={
            "Authorization": f"Bearer {response_data.access_token}",
            "Content-Type": "application/json"
        }
    )

    response.set_cookie(
        key="refresh_token",
        value=response_data.refresh_token,
        secure=True,
        httponly=True,
        expires=response_data.refresh_token_expire.strftime("%Y-%m-%d %H:%M:%S"),
        samesite="none",
        path="/",
    )

    return response
