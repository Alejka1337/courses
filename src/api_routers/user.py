from typing import Annotated

from fastapi import APIRouter, Body, Depends, File, Request, UploadFile, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from src.celery import celery_tasks
from src.crud.category import CategoryRepository
from src.crud.chat import select_chats_for_moderator
from src.crud.course import CourseRepository
from src.crud.lesson import LessonRepository
from src.crud.student_course import subscribe_student_to_course_db
from src.crud.user import UserRepository
from src.enums import StaticFileType
from src.models import UserOrm
from src.schemas.user import (AuthResponse, BuyCourse, LoginWithGoogle, ResetPassword, SetNewPassword, StudentCreate,
                              StudentCreateViaGoogle, UserActivate, UsernameUpdate, UserRegistration, UserUpdate,
                              UserRegistrationResponse, UserAdmin)
from src.session import get_db
from src.utils.decode_code import decode_and_check_refresh_token, decode_google_token
from src.utils.exceptions import (CookieNotFoundException, EmailDoesExistException, EmailNotFoundException,
                                  InvalidActivateCodeException, InvalidPasswordException, InvalidResetCodeException,
                                  InvalidUsernameException, NotActivateAccountException, PermissionDeniedException,
                                  UpdateEmailException, UpdateUsernameException, UsernameDoesExistException)
from src.utils.get_user import get_current_user
from src.utils.info_me import set_info_me
from src.utils.password import check_password
from src.utils.responses import after_auth_response
from src.utils.save_files import save_file
from src.utils.token import create_access_token, create_refresh_token

router = APIRouter(prefix="/user")


@router.post("/create-admin")
async def create_admin(
        form_data: UserAdmin,
        db: Session = Depends(get_db)
):
    user_repository = UserRepository(db=db)
    user = user_repository.create_admin(password=form_data.password, username=form_data.username)

    token_data = {"sub": user.username}
    access_token, access_token_expire = create_access_token(data=token_data)
    refresh_token, refresh_token_expire = create_refresh_token(data=token_data)

    response_data = AuthResponse(
        access_token=access_token,
        access_token_expire=access_token_expire,
        user_id=user.id,
        username=user.username,
        user_type=user.usertype,
        refresh_token=refresh_token,
        refresh_token_expire=refresh_token_expire,
        message="Success login"
    )

    response = after_auth_response(response_data=response_data)

    celery_tasks.update_user_token_after_login.delay(
        user_id=user.id,
        access_token=access_token,
        refresh_token=refresh_token,
        exp_token=access_token_expire
    )

    return response


@router.post("/create", status_code=status.HTTP_201_CREATED, response_model=UserRegistrationResponse)
async def create_user(
        form_data: UserRegistration,
        db: Session = Depends(get_db)
):
    user_repository = UserRepository(db=db)

    student = user_repository.select_student_by_email(email=form_data.email)
    if student:
        raise EmailDoesExistException(form_data.email)

    user = user_repository.select_user_by_username(username=form_data.username)
    if user:
        raise UsernameDoesExistException(form_data.username)

    new_user = user_repository.create_new_user(username=form_data.username, password=form_data.password)
    student_data = StudentCreate(
        user_id=new_user.id,
        name=form_data.name,
        surname=form_data.surname,
        phone=form_data.phone,
        country=form_data.country,
        email=form_data.email
    )
    user_repository.create_new_student(data=student_data)

    celery_tasks.send_activate_code.delay(user_id=new_user.id, email=form_data.email)

    return UserRegistrationResponse()


@router.post("/login")
async def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_db),
):
    user_repository = UserRepository(db=db)
    user = user_repository.select_user_by_username(username=form_data.username)

    if not user:
        raise InvalidUsernameException()

    if user.is_active is False:
        raise NotActivateAccountException()

    if not check_password(form_data.password, user.hashed_pass):
        raise InvalidPasswordException()

    token_data = {"sub": user.username}
    access_token, access_token_expire = create_access_token(data=token_data)
    refresh_token, refresh_token_expire = create_refresh_token(data=token_data)

    response_data = AuthResponse(
        access_token=access_token,
        access_token_expire=access_token_expire,
        user_id=user.id,
        username=user.username,
        user_type=user.usertype,
        refresh_token=refresh_token,
        refresh_token_expire=refresh_token_expire,
        message="Success login"
    )

    response = after_auth_response(response_data=response_data)

    celery_tasks.update_user_token_after_login.delay(
        user_id=user.id,
        access_token=access_token,
        refresh_token=refresh_token,
        exp_token=access_token_expire
    )

    return response


@router.get("/logout")
async def logout(
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    response = JSONResponse(content={"message": "User have been logout"})
    response.set_cookie(key="refresh_token", value="", secure=True, httponly=True, samesite="none", path="/")
    user_repository = UserRepository(db=db)
    user_repository.user_logout_db(user=user)
    return response


@router.get("/refresh")
async def refresh(
        request: Request,
        db: Session = Depends(get_db),
):
    if "refresh_token" in request.cookies.keys():
        user_repository = UserRepository(db=db)

        client_refresh_token = request.cookies.get("refresh_token")
        data = decode_and_check_refresh_token(client_refresh_token)
        user = user_repository.select_user_by_username(username=data["sub"])

        access_token, access_token_expire = create_access_token(data=data)
        refresh_token, refresh_token_expire = create_refresh_token(data=data)

        user_repository.update_user_token(
            user=user,
            access_token=access_token,
            refresh_token=refresh_token,
            exp_token=access_token_expire.strftime("%Y-%m-%d %H:%M:%S")
        )

        response_data = AuthResponse(
            access_token=access_token,
            access_token_expire=access_token_expire,
            user_id=user.id,
            user_type=user.usertype,
            username=user.username,
            refresh_token=refresh_token,
            refresh_token_expire=refresh_token_expire,
            message="Access and refresh tokens have been updated"
        )

        response = after_auth_response(response_data=response_data)
        return response

    else:
        raise CookieNotFoundException()


@router.post("/activate")
async def activate_user(
        activate_data: UserActivate,
        db: Session = Depends(get_db)
):
    user_repository = UserRepository(db=db)
    user = user_repository.select_user_by_username(username=activate_data.username)
    if user is None:
        raise InvalidUsernameException()

    db_code = user_repository.select_activate_code(user_id=user.id)

    if activate_data.code == db_code:

        data = {"sub": user.username}
        access_token, access_token_expire = create_access_token(data=data)
        refresh_token, refresh_token_expire = create_refresh_token(data=data)

        response_data = AuthResponse(
            access_token=access_token,
            access_token_expire=access_token_expire,
            user_id=user.id,
            user_type=user.usertype,
            username=user.username,
            refresh_token=refresh_token,
            refresh_token_expire=refresh_token_expire,
            message="Success login"
        )

        response = after_auth_response(response_data=response_data)

        celery_tasks.activate_user.delay(
            user_id=user.id,
            access_token=access_token,
            refresh_token=refresh_token,
            exp_token=access_token_expire.strftime("%Y-%m-%d %H:%M:%S")
        )

        return response

    else:
        raise InvalidActivateCodeException()


@router.get("/resend-activation-code")
async def resend_activation_code(
        username: str,
        db: Session = Depends(get_db)
):
    user_repository = UserRepository(db=db)
    user = user_repository.select_user_by_username(username=username)
    db_code = user_repository.select_activate_code(user_id=user.id)
    student = user_repository.select_student_by_user_id(user_id=user.id)
    celery_tasks.resend_activate_code.delay(email=student.email, code=db_code)
    return {"message": "We have sent a confirmation code to your email"}


@router.post("/reset-pass")
async def reset_password(data: ResetPassword, db: Session = Depends(get_db)):
    user_repository = UserRepository(db=db)
    student = user_repository.select_student_by_email(email=data.email)

    if student is None:
        raise EmailNotFoundException()

    celery_tasks.send_reset_pass_code.delay(user_id=student.user_id, email=data.email)
    return {"message": "We have sent a password reset code to your email."}


@router.post("/set-new-pass")
async def set_new_password(
        data: SetNewPassword,
        db: Session = Depends(get_db)
):
    user_repository = UserRepository(db=db)
    student = user_repository.select_student_by_email(email=data.email)

    db_code = user_repository.select_reset_code(user_id=student.user_id)
    if db_code[0] == data.code:
        user = user_repository.select_user_by_id(user_id=student.user_id)

        access_token, access_token_expire = create_access_token(data={"sub": user.username})
        refresh_token, refresh_token_expire = create_refresh_token(data={"sub": user.username})

        user_repository.update_user_password(user=user, password=data.new_pass)
        user_repository.update_user_token(
            user=user, access_token=access_token, refresh_token=refresh_token,
            exp_token=access_token_expire.strftime("%Y-%m-%d %H:%M:%S")
        )

        response_data = AuthResponse(
            access_token=access_token,
            access_token_expire=access_token_expire,
            user_id=user.id,
            user_type=user.usertype,
            username=user.username,
            refresh_token=refresh_token,
            refresh_token_expire=refresh_token_expire,
            message="Success updated password"
        )

        response = after_auth_response(response_data=response_data)
        return response

    else:
        raise InvalidResetCodeException()


@router.get("/resend-password-reset-code")
async def resend_password_reset_code(
        email: str,
        db: Session = Depends(get_db)
):
    user_repository = UserRepository(db=db)
    student = user_repository.select_student_by_email(email=email)
    code = user_repository.select_reset_code(user_id=student.user_id)
    celery_tasks.resend_reset_pass_code.delay(email=email, code=code[0])
    return {"message": "We have sent a reset password code to your email"}


@router.post("/login-with-google")
async def login_with_google(
        data: LoginWithGoogle,
        db: Session = Depends(get_db)
):
    decoded_data = decode_google_token(data.google_token)
    user_repository = UserRepository(db=db)
    student = user_repository.select_student_by_email(email=decoded_data["email"])

    if student:
        user = user_repository.select_user_by_id(user_id=student.user_id)
        access_token, access_token_expire = create_access_token(data={"sub": user.username})
        refresh_token, refresh_token_expire = create_refresh_token(data={"sub": user.username})
        user_repository.update_user_token(
            user=user, access_token=access_token, refresh_token=refresh_token,
            exp_token=access_token_expire.strftime("%Y-%m-%d %H:%M:%S")
        )

        response_data = AuthResponse(
            access_token=access_token,
            access_token_expire=access_token_expire,
            user_id=user.id,
            username=user.username,
            user_type=user.usertype,
            refresh_token=refresh_token,
            refresh_token_expire=refresh_token_expire,
            message="Success login"
        )

        response = after_auth_response(response_data=response_data)
        return response

    else:
        end_index = decoded_data["email"].index("@")
        username = decoded_data["email"][:end_index]
        access_token, access_token_expire = create_access_token(data={"sub": username})
        refresh_token, refresh_token_expire = create_refresh_token(data={"sub": username})

        user = user_repository.create_new_user_with_google(
            username=username,
            access_token=access_token,
            refresh_token=refresh_token,
            exp_token=access_token_expire
        )

        student_data = StudentCreateViaGoogle(
            user_id=user.id,
            name=decoded_data["given_name"],
            surname=decoded_data["family_name"],
            email=decoded_data["email"],
        )

        user_repository.create_new_student_google(student_data)
        user_repository.create_student_image_db(user_id=user.id, image_path=decoded_data["picture"])

        response_data = AuthResponse(
            access_token=access_token,
            access_token_expire=access_token_expire,
            user_id=user.id,
            user_type=user.usertype,
            username=user.username,
            refresh_token=refresh_token,
            refresh_token_expire=refresh_token_expire,
            message="Success login"
        )

        response = after_auth_response(response_data=response_data)
        return response


@router.put("/update/image")
async def update_user_image(
        image: UploadFile = File(...),
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    user_repository = UserRepository(db=db)
    image_path = save_file(file=image, file_type=StaticFileType.student_avatar.value)
    main_image = user_repository.select_student_image_db(user_id=user.id)
    if main_image:
        user_repository.update_student_main_image_db(image=main_image, flag=False)

    return user_repository.create_student_image_db(user_id=user.id, image_path=image_path)


@router.get("/my-images")
async def get_last_user_images(
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    user_repository = UserRepository(db=db)
    return user_repository.select_student_images_db(user_id=user.id)


@router.put("/set-main-image")
async def set_new_main_image(
        image_id: int,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    user_repository = UserRepository(db=db)
    main_image = user_repository.select_student_image_db(user_id=user.id)
    user_repository.update_student_main_image_db(image=main_image, flag=False)
    new_main_image = user_repository.select_student_image_by_id_db(image_id=image_id, user_id=user.id)
    user_repository.update_student_main_image_db(image=new_main_image, flag=True)
    return {"message": "User main image have been successfully updated"}


@router.put("/update/username")
async def update_user_username(
        data: Annotated[UsernameUpdate, Body],
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    user_repository = UserRepository(db=db)
    user_db = user_repository.select_user_by_username(username=data.username)
    if user_db is None:
        user_repository.update_user_username_db(user=user, username=data.username)

        access_token, access_token_expire = create_access_token(data={"sub": user.username})
        refresh_token, refresh_token_expire = create_refresh_token(data={"sub": user.username})
        user_repository.update_user_token(
            user=user, access_token=access_token, refresh_token=refresh_token,
            exp_token=access_token_expire.strftime("%Y-%m-%d %H:%M:%S")
        )

        response_data = AuthResponse(
            access_token=access_token,
            access_token_expire=access_token_expire,
            user_id=user.id,
            user_type=user.usertype,
            username=user.username,
            refresh_token=refresh_token,
            refresh_token_expire=refresh_token_expire,
            message="Success updated username"
        )

        response = after_auth_response(response_data=response_data)
        return response
    else:
        raise UpdateUsernameException()


@router.put("/update/info")
async def update_user_info(
        data: Annotated[UserUpdate, Body],
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    user_repository = UserRepository(db=db)
    student = user_repository.select_student_by_user_id(user_id=user.id)

    if data.password:
        user_repository.update_user_password(user=user, password=data.password)

    if data.email:
        res = user_repository.select_student_by_email(email=data.email)
        if res is None:
            user_repository.update_student_email_db(student=student, email=data.email)
        else:
            raise UpdateEmailException()

    user_repository.update_student_info_db(student=student, data=data)
    return student


@router.put("/update/time")
async def update_studying_time(
        time: int,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.is_student:
        user_repository = UserRepository(db=db)
        user_repository.update_student_studying_time(time=time, user_id=user.id)
        return {"message": "Success"}
    else:
        raise PermissionDeniedException()


@router.post("/buy-course")
async def buy_course(
        data: BuyCourse,
        user: UserOrm = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    if user.is_student:
        student_course = subscribe_student_to_course_db(db=db, student_id=user.student.id, course_id=data.course_id)
        celery_tasks.create_student_lesson.delay(student_id=user.student.id, course_id=data.course_id)
        return student_course
    else:
        raise PermissionDeniedException()


@router.get("/info/me")
async def info_me(
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.is_student:
        user_repository = UserRepository(db=db)
        student, image, courses = user_repository.select_user_dashboard_info(user_id=user.id)
        response = set_info_me(user=user, student=student, image=image, courses=courses)
        return response

    else:
        return {
            "user_id": user.id,
            "user_type": user.usertype,
            "username": user.username,
            "chats": select_chats_for_moderator(db=db, user_id=user.id)
        }


@router.get("/search")
async def search(query: str, db: Session = Depends(get_db),):
    results = dict()
    category_repository = CategoryRepository(db=db)
    results["categories"] = category_repository.search_category(query=query)

    course_repository = CourseRepository(db=db)
    results["courses"] = course_repository.search_course(query=query)

    lesson_repository = LessonRepository(db=db)
    results["lessons"] = lesson_repository.search_lesson(query=query)
    return results
