from datetime import date, datetime

from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from src.enums import UserType
from src.models import (ActivateCodeOrm, ImageOrm, ModeratorOrm, ResetPasswordLinkOrm, StudentCourseAssociation,
                        StudentOrm, UserOrm)
from src.schemas.user import UserRegistration, UserUpdate
from src.utils.password import hash_password


def create_new_user(db: Session, data: UserRegistration):
    hashed_pass = hash_password(data.password)

    new_user = UserOrm(
        usertype=UserType.student,
        username=data.username,
        hashed_pass=hashed_pass,
        is_active=False
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def create_new_user_with_google(
        db: Session,
        username: str,
        access_token: str,
        refresh_token: str,
        exp_token: datetime
):
    hashed_pass = hash_password(username)

    new_user = UserOrm(
        usertype=UserType.student,
        username=username,
        hashed_pass=hashed_pass,
        is_active=True,
        access_token=access_token,
        refresh_token=refresh_token,
        exp_token=exp_token,
        last_active=date.today()
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def create_new_student(db: Session, data: UserRegistration, user_id: int):
    new_student = StudentOrm(
        user_id=user_id,
        name=data.name if data.name else "",
        surname=data.surname if data.surname else "",
        email=data.email,
        phone=data.phone if data.phone else None,
        country=data.country if data.country else None
    )

    db.add(new_student)
    db.commit()
    db.refresh(new_student)


def create_new_student_google(db: Session, user_id: int, name: str, surname: str, email: str, picture: str):
    new_student = StudentOrm(
        user_id=user_id,
        name=name,
        surname=surname,
        email=email,
        image_path=picture
    )

    db.add(new_student)
    db.commit()
    db.refresh(new_student)


def create_activation_code(db: Session, code: str, user_id: int):
    new_code = ActivateCodeOrm(code=code, user_id=user_id)
    db.add(new_code)
    db.commit()
    db.refresh(new_code)


def create_reset_code(db: Session, code: str, user_id: int):
    new_code = ResetPasswordLinkOrm(link=code, user_id=user_id)
    db.add(new_code)
    db.commit()
    db.refresh(new_code)


def select_user_by_id(db: Session, user_id: int):
    return db.query(UserOrm).filter(UserOrm.id == user_id).first()


def select_user_by_username(db: Session, username: str):
    return db.query(UserOrm).filter(UserOrm.username == username).first()


def select_activate_code(db: Session, user_id: int):
    return db.query(ActivateCodeOrm.code).filter(ActivateCodeOrm.user_id == user_id).scalar()


def activate_user(db: Session, user: UserOrm, access_token: str, refresh_token: str, exp_token: datetime):
    user.is_active = True
    user.access_token = access_token
    user.refresh_token = refresh_token
    user.exp_token = exp_token
    user.last_active = date.today()

    db.commit()
    db.refresh(user)


def update_user_token(db: Session, user: UserOrm, access_token: str, refresh_token: str, exp_token: datetime):
    user.access_token = access_token
    user.refresh_token = refresh_token
    user.exp_token = exp_token
    user.last_active = date.today()

    db.commit()
    db.refresh(user)


def user_logout_db(db: Session, user: UserOrm):
    user.access_token = None
    user.refresh_token = None
    user.exp_token = None
    user.last_active = date.today()

    db.commit()
    db.refresh(user)


def update_user_username_db(db: Session, user: UserOrm, username: str):
    user.username = username
    db.commit()
    db.refresh(user)


def select_student_by_email(db: Session, email: str):
    return db.query(StudentOrm).filter(StudentOrm.email == email).first()


def select_student_by_user_id(db: Session, user_id: int):
    return db.query(StudentOrm).options(joinedload(StudentOrm.chats)).filter(StudentOrm.user_id == user_id).first()


def select_reset_code(db: Session, user_id: int):
    res = db.query(ResetPasswordLinkOrm.link).filter(ResetPasswordLinkOrm.user_id == user_id).all()
    return res[-1]


def select_student_image_db(db: Session, user_id: int):
    return db.query(ImageOrm).filter(ImageOrm.user_id == user_id, ImageOrm.is_main).first()


def select_student_fullname_db(db: Session, user_id: int):
    fullname = db.query(StudentOrm.fullname).filter(StudentOrm.user_id == user_id).scalar()
    if fullname:
        return fullname
    else:
        return db.query(UserOrm.username).filter(UserOrm.id == user_id).scalar()


def select_moder_fullname_db(db: Session, user_id: int):
    fullname = db.query(ModeratorOrm.fullname).filter(ModeratorOrm.user_id == user_id).scalar()
    if fullname:
        return fullname
    else:
        return db.query(UserOrm.username).filter(UserOrm.id == user_id).scalar()


def select_student_images_db(db: Session, user_id: int):
    return db.query(ImageOrm).filter(ImageOrm.user_id == user_id).order_by(desc(ImageOrm.id)).limit(6).all()


def select_student_image_by_id_db(db: Session, image_id: int, user_id: int):
    return db.query(ImageOrm).filter(ImageOrm.user_id == user_id, ImageOrm.id == image_id).first()


def update_student_main_image_db(db: Session, image: ImageOrm, flag: bool = True):
    if flag:
        image.is_main = True
        db.commit()
        db.refresh(image)
    else:
        image.is_main = False
        db.commit()
        db.refresh(image)


def update_user_password(db: Session, user: UserOrm, password: str):
    hashed_pass = hash_password(password)
    user.hashed_pass = hashed_pass
    user.last_active = date.today()

    db.commit()
    db.refresh(user)


def create_student_image_db(db: Session, user_id: int, image_path: str):
    new_image = ImageOrm(
        user_id=user_id,
        path=image_path,
        is_main=True
    )

    db.add(new_image)
    db.commit()
    db.refresh(new_image)
    return new_image


def update_student_email_db(db: Session, student: StudentOrm, email: str):
    student.email = email
    db.commit()
    db.refresh(student)


def update_student_studying_time(db: Session, user_id: int, time: int):
    student = db.query(StudentOrm).filter(StudentOrm.user_id == user_id).first()
    student.studying_time += time
    db.commit()
    db.refresh(student)


def update_student_info_db(db: Session, student: StudentOrm, data: UserUpdate):
    if data.country:
        student.country = data.country

    if data.phone:
        student.phone = data.phone

    if data.name and student.changed_name is not True:
        student.name = data.name
        student.changed_name = True

    if data.surname and student.changed_surname is not True:
        student.surname = data.surname
        student.changed_surname = True

    db.commit()
    db.refresh(student)


def select_student_courses_db(db: Session, student_id: int):
    return db.query(StudentCourseAssociation).filter(StudentCourseAssociation.student_id == student_id).all()
