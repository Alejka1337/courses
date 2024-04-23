import logging
import os
from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError

from celery import Celery
from src.config import BROKER_URL
from src.crud.course import (select_course_info_db, select_course_name_by_id_db, select_student_course_db,
                             select_students_whose_bought_courses, update_course_present, update_course_score)
from src.crud.lecture import select_lecture_attrs_db, update_lecture_audio
from src.crud.lesson import select_lesson_by_id_db, select_lesson_by_type_and_title_db, select_lessons_by_course_db
from src.crud.notifications import create_course_add_notification, create_course_update_notification
from src.crud.student_lesson import (create_student_lesson_db, select_count_completed_student_lessons_db,
                                     select_count_student_lessons_db, select_student_lessons_db,
                                     select_students_for_course_db, update_student_lesson_status_db,
                                     update_student_lesson_structure)
from src.crud.user import activate_user, create_activation_code, create_reset_code, select_user_by_id
from src.enums import LessonStatus, LessonType
from src.session import SessionLocal
from src.utils.activate_code import generate_activation_code, generate_reset_code
from src.utils.notifications import (create_notification_text_for_add_new_course,
                                     create_notification_text_for_update_course)
from src.utils.save_files import delete_files_in_directory
from src.utils.smtp import send_mail_with_code
from src.utils.text_to_speach import create_lecture_text, text_to_speach

celery_app = Celery("celery", broker=BROKER_URL)
logger = logging.getLogger(__name__)


@celery_app.task
def send_activate_code(user_id: int, email: str):
    db = SessionLocal()
    code = generate_activation_code()
    create_activation_code(db=db, code=code, user_id=user_id)
    send_mail_with_code(to_email=email, mail_title="Your activate code", mail_body=code)
    db.close()


@celery_app.task
def activate_user_task(user_id: int, access_token: str, exp_token: datetime, refresh_token: str):
    db = SessionLocal()
    user = select_user_by_id(db=db, user_id=user_id)
    activate_user(db=db, user=user, access_token=access_token, refresh_token=refresh_token, exp_token=exp_token)
    db.close()


@celery_app.task
def send_reset_pass_code(user_id: int, email: str):
    db = SessionLocal()
    code = generate_reset_code()
    create_reset_code(db=db, code=code, user_id=user_id)
    send_mail_with_code(to_email=email, mail_title="Your reset password code", mail_body=code)
    db.close()


@celery_app.task
def resend_activate_code(email: str, code: str):
    send_mail_with_code(to_email=email, mail_title="Your activate code", mail_body=code)


@celery_app.task
def resend_reset_pass_code(email: str, code: str):
    send_mail_with_code(to_email=email, mail_title="Your reset password code", mail_body=code)


@celery_app.task
def create_student_lesson(student_id: int, course_id: int):
    db = SessionLocal()
    lessons = select_lessons_by_course_db(db=db, course_id=course_id)

    for index, lesson in enumerate(lessons):
        if lesson.number == 1:
            create_student_lesson_db(db=db, student_id=student_id,
                                     lesson_id=lesson.id, status=LessonStatus.active)

        elif lesson.type == LessonType.test.value or lesson.type == LessonType.exam.value:
            create_student_lesson_db(
                db=db, student_id=student_id, lesson_id=lesson.id, status=LessonStatus.blocked
            )
        else:
            if any(les.type == LessonType.test.value for les in lessons[:index]):
                create_student_lesson_db(
                    db=db, student_id=student_id, lesson_id=lesson.id, status=LessonStatus.blocked
                )
            else:
                create_student_lesson_db(
                    db=db, student_id=student_id, lesson_id=lesson.id, status=LessonStatus.available
                )
    db.close()


@celery_app.task
def update_student_course_progress(student_id: int, lesson_id: int):
    db = SessionLocal()
    try:
        lesson = select_lesson_by_id_db(db=db, lesson_id=lesson_id)
        course_lessons = select_lessons_by_course_db(db=db, course_id=lesson.course_id)

        total_lessons = select_count_student_lessons_db(
            db=db, course_lessons=course_lessons, student_id=student_id
        )

        completed_lessons = select_count_completed_student_lessons_db(
            db=db, course_lessons=course_lessons, student_id=student_id
        )

        student_course = select_student_course_db(
            db=db, course_id=lesson.course_id, student_id=student_id
        )

        progress = round((completed_lessons / total_lessons) * 100)
        update_course_present(db=db, student_course=student_course, progress=progress)

    except SQLAlchemyError as e:
        logger.error(f"Error updating student course progress: {e}")

    finally:
        db.close()


@celery_app.task
def update_student_course_grade(student_id: int, lesson_id: int, score: int):
    db = SessionLocal()
    lesson = select_lesson_by_id_db(db=db, lesson_id=lesson_id)
    student_course = select_student_course_db(db=db, course_id=lesson.course_id, student_id=student_id)
    update_course_score(db=db, student_course=student_course, score=score)
    db.close()


@celery_app.task
def update_student_lesson_status(lesson_id: int, student_id: int):
    db = SessionLocal()
    update_student_lesson_status_db(db=db, lesson_id=lesson_id, student_id=student_id)
    db.close()


@celery_app.task
def create_lecture_audio(lecture_id: int):
    db = SessionLocal()
    lecture_attrs = select_lecture_attrs_db(db=db, lecture_id=lecture_id)
    lecture_text = create_lecture_text(lecture_attrs)

    folder = "static/speeches" + "/lecture" + str(lecture_id)
    os.makedirs(folder, exist_ok=True)
    delete_files_in_directory(folder)

    result = text_to_speach(text=lecture_text, lecture_id=lecture_id)
    audio_list = [value for value in result.values()]
    update_lecture_audio(db=db, lecture_id=lecture_id, audios=audio_list)

    db.close()


@celery_app.task
def create_update_course_notification(new_lesson_id: int, course_id: int):
    db = SessionLocal()

    student_ids = select_students_for_course_db(db=db, course_id=course_id)
    lesson = select_lesson_by_id_db(db=db, lesson_id=new_lesson_id)
    course_name = select_course_name_by_id_db(db=db, course_id=course_id)

    for student in student_ids:
        notification_text = create_notification_text_for_update_course(
            course_name=course_name, lesson_title=lesson.title, lesson_type=lesson.type
        )

        create_course_update_notification(db=db, message=notification_text, student_id=student.id)

    db.close()


@celery_app.task
def update_student_lessons(student_id: int, lesson_info: dict):
    db = SessionLocal()

    new_lesson = select_lesson_by_type_and_title_db(
        db=db, lesson_title=lesson_info["lesson_title"], lesson_type=lesson_info["lesson_type"]
    )

    course_lessons = select_lessons_by_course_db(db=db, course_id=new_lesson.course_id)
    student_lessons = select_student_lessons_db(db=db, course_lessons=course_lessons, student_id=student_id)

    update_student_lesson_structure(
        db=db, new_lesson=new_lesson, course_lessons=course_lessons,
        student_lessons=student_lessons, student_id=student_id
    )

    db.close()


@celery_app.task
def add_new_course_notification(course_id: int):
    db = SessionLocal()

    student_ids = select_students_whose_bought_courses(db=db, course_id=course_id)
    new_course = select_course_info_db(db=db, course_id=course_id)

    for student in student_ids:
        message = create_notification_text_for_add_new_course(
            course_name=new_course.title, category_name=new_course.category.title
        )
        create_course_add_notification(db=db, message=message, student_id=student.id)

    db.close()
