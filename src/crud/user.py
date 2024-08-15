from datetime import date, datetime

from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from src.enums import UserType
from src.models import (ActivateCodeOrm, ImageOrm, ModeratorOrm, ResetPasswordLinkOrm, StudentCourseAssociation,
                        StudentOrm, UserOrm)
from src.schemas.user import StudentCreate, StudentCreateViaGoogle, UserUpdate
from src.utils.password import hash_password


class UserRepository:
    def __init__(self, db: Session):
        self.db = db
        self.model = UserOrm
        self.image_model = ImageOrm
        self.student_model = StudentOrm
        self.moder_model = ModeratorOrm
        self.activate_code_model = ActivateCodeOrm
        self.reset_code_model = ResetPasswordLinkOrm
        self.course_model = StudentCourseAssociation

    def create_admin(self, password: str, username: str):
        hashed_pass = hash_password(password)
        new_user = self.model(
            usertype=UserType.moder,
            username=username,
            hashed_pass=hashed_pass,
            is_active=True
        )
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        return new_user

    def create_new_user(self, password: str, username: str):
        hashed_pass = hash_password(password)
        new_user = self.model(
            usertype=UserType.student,
            username=username,
            hashed_pass=hashed_pass,
            is_active=False
        )

        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        return new_user

    def create_new_user_with_google(
            self,
            username: str,
            access_token: str,
            refresh_token: str,
            exp_token: datetime
    ):
        hashed_pass = hash_password(username)
        new_user = self.model(
            usertype=UserType.student,
            username=username,
            hashed_pass=hashed_pass,
            is_active=True,
            access_token=access_token,
            refresh_token=refresh_token,
            exp_token=exp_token,
            last_active=date.today()
        )

        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        return new_user

    def create_new_student(self, data: StudentCreate):
        new_student = self.student_model(**data.dict())
        self.db.add(new_student)
        self.db.commit()
        self.db.refresh(new_student)

    def create_new_student_google(self, data: StudentCreateViaGoogle):
        new_student = self.student_model(**data.dict())
        self.db.add(new_student)
        self.db.commit()
        self.db.refresh(new_student)

    def create_activation_code(self, code: str, user_id: int):
        new_code = self.activate_code_model(code=code, user_id=user_id)
        self.db.add(new_code)
        self.db.commit()
        self.db.refresh(new_code)

    def create_reset_code(self, code: str, user_id: int):
        new_code = self.reset_code_model(link=code, user_id=user_id)
        self.db.add(new_code)
        self.db.commit()
        self.db.refresh(new_code)

    def select_user_by_id(self, user_id: int):
        return self.db.query(self.model).filter(self.model.id == user_id).first()

    def select_user_by_username(self, username: str):
        return self.db.query(self.model).filter(self.model.username == username).first()

    def select_activate_code(self, user_id: int):
        return self.db.query(self.activate_code_model.code).filter(self.activate_code_model.user_id == user_id).scalar()

    def activate_user(self, user: UserOrm, access_token: str, refresh_token: str, exp_token: datetime):
        user.is_active = True
        user.access_token = access_token
        user.refresh_token = refresh_token
        user.exp_token = exp_token
        user.last_active = date.today()

        self.db.commit()
        self.db.refresh(user)

    def update_user_token(self, user: UserOrm, access_token: str, refresh_token: str, exp_token: datetime):
        user.access_token = access_token
        user.refresh_token = refresh_token
        user.exp_token = exp_token
        user.last_active = date.today()

        self.db.commit()
        self.db.refresh(user)

    def user_logout_db(self, user: UserOrm):
        user.access_token = None
        user.refresh_token = None
        user.exp_token = None
        user.last_active = date.today()

        self.db.commit()
        self.db.refresh(user)

    def update_user_username_db(self, user: UserOrm, username: str):
        user.username = username
        self.db.commit()
        self.db.refresh(user)

    def select_student_by_email(self, email: str):
        return self.db.query(self.student_model).filter(self.student_model.email == email).first()

    def select_student_by_user_id(self, user_id: int):
        return (self.db.query(self.student_model)
                .options(joinedload(self.student_model.chats))
                .filter(self.student_model.user_id == user_id)
                .first())

    def select_reset_code(self, user_id: int):
        res = self.db.query(self.reset_code_model.link).filter(self.reset_code_model.user_id == user_id).all()
        return res[-1]

    def select_student_image_db(self, user_id: int):
        return (self.db.query(self.image_model)
                .filter(self.image_model.user_id == user_id,
                        self.image_model.is_main)
                .first())

    def select_student_fullname_db(self, user_id: int):
        fullname = self.db.query(self.student_model.fullname).filter(self.student_model.user_id == user_id).scalar()
        if fullname:
            return fullname
        else:
            return self.db.query(self.model.username).filter(self.model.id == user_id).scalar()

    def select_moder_fullname_db(self, user_id: int):
        fullname = self.db.query(self.moder_model.fullname).filter(self.moder_model.user_id == user_id).scalar()
        if fullname:
            return fullname
        else:
            return self.db.query(self.model.username).filter(self.model.id == user_id).scalar()

    def select_student_images_db(self, user_id: int):
        return (self.db.query(self.image_model)
                .filter(self.image_model.user_id == user_id)
                .order_by(desc(self.image_model.id))
                .limit(6)
                .all())

    def select_student_image_by_id_db(self, image_id: int, user_id: int):
        return (self.db.query(self.image_model)
                .filter(self.image_model.user_id == user_id,
                        self.image_model.id == image_id)
                .first())

    def update_student_main_image_db(self, image: ImageOrm, flag: bool = True):
        if flag:
            image.is_main = True
            self.db.commit()
            self.db.refresh(image)
        else:
            image.is_main = False
            self.db.commit()
            self.db.refresh(image)

    def update_user_password(self, user: UserOrm, password: str):
        hashed_pass = hash_password(password)
        user.hashed_pass = hashed_pass
        user.last_active = date.today()

        self.db.commit()
        self.db.refresh(user)

    def create_student_image_db(self, user_id: int, image_path: str):
        new_image = self.image_model(
            user_id=user_id,
            path=image_path,
            is_main=True
        )

        self.db.add(new_image)
        self.db.commit()
        self.db.refresh(new_image)
        return new_image

    def update_student_email_db(self, student: StudentOrm, email: str):
        student.email = email
        self.db.commit()
        self.db.refresh(student)

    def update_student_studying_time(self, user_id: int, time: int):
        (self.db.query(self.student_model)
         .filter(self.student_model.user_id == user_id)
         .update(
            {self.student_model.studying_time: (self.student_model.studying_time + time)},
            synchronize_session=False))

        self.db.commit()

    def update_student_info_db(self, student: StudentOrm, data: UserUpdate):
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

        self.db.commit()
        self.db.refresh(student)

    def select_user_dashboard_info(self, user_id: int):

        student = (self.db.query(self.student_model)
                   .options(joinedload(self.student_model.chats))
                   .filter(self.student_model.user_id == user_id)
                   .first())

        image = self.select_student_image_db(user_id=user_id)

        courses = (self.db.query(self.course_model).filter(self.course_model.student_id == student.id).all())

        return student, image, courses
