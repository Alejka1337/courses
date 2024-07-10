from typing import Annotated

from fastapi import APIRouter, Body, Depends, File, Request, UploadFile
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from src.celery import celery_tasks
from src.crud.category import CategoryRepository
from src.crud.course import CourseRepository
from src.crud.lesson import search_lesson
from src.crud.student_course import subscribe_student_to_course_db
from src.crud.user import (create_new_student, create_new_student_google, create_new_user, create_new_user_with_google,
                           create_student_image_db, select_activate_code, select_reset_code, select_student_by_email,
                           select_student_by_user_id, select_student_courses_db, select_student_image_by_id_db,
                           select_student_image_db, select_student_images_db, select_user_by_id,
                           select_user_by_username, update_student_email_db, update_student_info_db,
                           update_student_main_image_db, update_student_studying_time, update_user_password,
                           update_user_token, update_user_username_db, user_logout_db)
from src.enums import StaticFileType, UserType
from src.models import UserOrm
from src.schemas.user import (AuthResponse, BuyCourse, LoginWithGoogle, ResetPassword, SetNewPassword, UserActivate,
                              UsernameUpdate, UserRegistration, UserUpdate)
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


@router.post("/create")
async def create_user(
        form_data: UserRegistration,
        db: Session = Depends(get_db)

):
    student = select_student_by_email(db=db, email=form_data.email)
    if student:
        raise EmailDoesExistException(form_data.email)

    user = select_user_by_username(db=db, username=form_data.username)

    if user:
        raise UsernameDoesExistException(form_data.username)

    new_user = create_new_user(db=db, data=form_data)
    create_new_student(db=db, data=form_data, user_id=new_user.id)

    celery_tasks.send_activate_code.delay(user_id=new_user.id, email=form_data.email)

    # send_activate_code.delay(user_id=new_user.id, email=form_data.email)
    return JSONResponse(
        content={"message": "Successful registration. We have sent a confirmation code to your email"},
        status_code=201
    )


@router.post("/login")
async def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_db),
):
    user = select_user_by_username(db=db, username=form_data.username)

    if not user:
        raise InvalidUsernameException()

    if user.is_active is False:
        raise NotActivateAccountException()

    if not check_password(form_data.password, user.hashed_pass):
        raise InvalidPasswordException()

    data = {"sub": user.username}
    access_token, access_token_expire = create_access_token(data=data)
    refresh_token, refresh_token_expire = create_refresh_token(data=data)

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

    update_user_token(
        db=db, user=user, access_token=access_token, refresh_token=refresh_token,
        exp_token=access_token_expire.strftime("%Y-%m-%d %H:%M:%S")
    )

    return response


@router.get("/logout")
async def logout(
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    response = JSONResponse(content={"message": "User have been logout"})
    response.set_cookie(key="refresh_token", value="", secure=True, httponly=True, samesite="none", path="/")
    user_logout_db(db=db, user=user)
    return response


@router.get("/refresh")
async def refresh(
        request: Request,
        db: Session = Depends(get_db),
):
    if "refresh_token" in request.cookies.keys():

        client_refresh_token = request.cookies.get("refresh_token")
        data = decode_and_check_refresh_token(client_refresh_token)
        user = select_user_by_username(db=db, username=data["sub"])

        access_token, access_token_expire = create_access_token(data=data)
        refresh_token, refresh_token_expire = create_refresh_token(data=data)

        update_user_token(
            db=db, user=user, access_token=access_token, refresh_token=refresh_token,
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
    user = select_user_by_username(db=db, username=activate_data.username)
    if user is None:
        raise InvalidUsernameException()

    db_code = select_activate_code(db=db, user_id=user.id)

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
    user = select_user_by_username(db=db, username=username)
    db_code = select_activate_code(db=db, user_id=user.id)
    student = select_student_by_user_id(db=db, user_id=user.id)
    celery_tasks.resend_activate_code.delay(email=student.email, code=db_code)
    return {"message": "We have sent a confirmation code to your email"}


@router.post("/reset-pass")
async def reset_password(data: ResetPassword, db: Session = Depends(get_db)):
    student = select_student_by_email(db=db, email=data.email)

    if student is None:
        raise EmailNotFoundException()

    celery_tasks.send_reset_pass_code.delay(user_id=student.user_id, email=data.email)
    return {"message": "We have sent a password reset code to your email."}


@router.post("/set-new-pass")
async def set_new_password(
        data: SetNewPassword,
        db: Session = Depends(get_db)
):
    student = select_student_by_email(db=db, email=data.email)

    db_code = select_reset_code(db=db,  user_id=student.user_id)
    if db_code[0] == data.code:
        user = select_user_by_id(db=db, user_id=student.user_id)

        access_token, access_token_expire = create_access_token(data={"sub": user.username})
        refresh_token, refresh_token_expire = create_refresh_token(data={"sub": user.username})

        update_user_password(db=db, user=user, password=data.new_pass)
        update_user_token(
            db=db, user=user, access_token=access_token, refresh_token=refresh_token,
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
    student = select_student_by_email(db=db, email=email)
    code = select_reset_code(db=db, user_id=student.user_id)
    celery_tasks.resend_reset_pass_code.delay(email=email, code=code[0])
    return {"message": "We have sent a reset password code to your email"}


@router.post("/login-with-google")
async def login_with_google(
        data: LoginWithGoogle,
        db: Session = Depends(get_db)
):
    decoded_data = decode_google_token(data.google_token)
    student = select_student_by_email(db=db, email=decoded_data["email"])

    if student:
        user = select_user_by_id(db=db, user_id=student.user_id)
        access_token, access_token_expire = create_access_token(data={"sub": user.username})
        refresh_token, refresh_token_expire = create_refresh_token(data={"sub": user.username})
        update_user_token(
            db=db, user=user, access_token=access_token, refresh_token=refresh_token,
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
        user = create_new_user_with_google(
            db=db,
            username=username,
            access_token=access_token,
            refresh_token=refresh_token,
            exp_token=access_token_expire
        )

        create_new_student_google(
            db=db,
            user_id=user.id,
            name=decoded_data["given_name"],
            surname=decoded_data["family_name"],
            email=decoded_data["email"],
            picture=decoded_data["picture"]
        )

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
    image_path = save_file(file=image, file_type=StaticFileType.student_avatar.value)
    main_image = select_student_image_db(db=db, user_id=user.id)
    if main_image:
        update_student_main_image_db(db=db, image=main_image, flag=False)

    return create_student_image_db(db=db, user_id=user.id, image_path=image_path)


@router.get("/my-images")
async def get_last_user_images(
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    return select_student_images_db(db=db, user_id=user.id)


@router.put("/set-main-image")
async def set_new_main_image(
        image_id: int,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    main_image = select_student_image_db(db=db, user_id=user.id)
    update_student_main_image_db(db=db, image=main_image, flag=False)
    new_main_image = select_student_image_by_id_db(db=db, image_id=image_id, user_id=user.id)
    update_student_main_image_db(db=db, image=new_main_image, flag=True)
    return {"message": "User main image have been successfully updated"}


@router.put("/update/username")
async def update_user_username(
        data: Annotated[UsernameUpdate, Body],
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    user_db = select_user_by_username(db=db, username=data.username)
    if user_db is None:
        update_user_username_db(db=db, user=user, username=data.username)

        access_token, access_token_expire = create_access_token(data={"sub": user.username})
        refresh_token, refresh_token_expire = create_refresh_token(data={"sub": user.username})
        update_user_token(
            db=db, user=user, access_token=access_token, refresh_token=refresh_token,
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
    student = select_student_by_user_id(db=db, user_id=user.id)

    if data.password:
        update_user_password(db=db, user=user, password=data.password)

    if data.email:
        res = select_student_by_email(db=db, email=data.email)
        if res is None:
            update_student_email_db(db=db, student=student, email=data.email)
        else:
            raise UpdateEmailException()

    update_student_info_db(db=db, student=student, data=data)
    return student


@router.put("/update/time")
async def update_studying_time(
        time: int,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.student.value:
        update_student_studying_time(db=db, time=time, user_id=user.id)
        return {"message": "Success"}
    else:
        raise PermissionDeniedException()


@router.post("/buy-course")
async def buy_course(
        data: BuyCourse,
        user: UserOrm = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    if user.usertype == UserType.student.value:
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
    if user.usertype == UserType.student.value:
        student = select_student_by_user_id(db=db, user_id=user.id)
        image = select_student_image_db(db=db, user_id=user.id)
        student_courses = select_student_courses_db(db=db, student_id=student.id)
        return set_info_me(user=user, student=student, image=image, courses=student_courses)
    else:
        return {
            "id": user.id,
            "user_type": user.usertype,
            "username": user.username,
            "chats": []
        }


@router.get("/search")
async def search(query: str, db: Session = Depends(get_db),):
    results = dict()
    category_repository = CategoryRepository(db=db)
    results["categories"] = category_repository.search_category(query=query)

    course_repository = CourseRepository(db=db)
    results["courses"] = course_repository.search_course(query=query)

    results["lessons"] = search_lesson(db=db, query=query)
    return results
