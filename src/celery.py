import logging
import os
from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError

from celery import Celery, Task
from src.config import BROKER_URL
from src.crud.course import CourseRepository
from src.crud.exam import ExamRepository
from src.crud.test import TestRepository
from src.crud.student_course import (select_student_course_db, select_students_whose_bought_courses,
                                     update_course_present, update_course_score)
from src.crud.lecture import LectureRepository
from src.crud.lesson import select_lesson_by_id_db, select_lesson_by_type_and_title_db, select_lessons_by_course_db
from src.crud.notifications import NotificationRepository
from src.crud.student_lesson import (create_student_lesson_db, select_count_completed_student_lessons_db,
                                     select_count_student_lessons_db, select_student_lessons_db,
                                     select_students_for_course_db, update_student_lesson_status_db,
                                     update_student_lesson_structure)
from src.crud.user import activate_user, create_activation_code, create_reset_code, select_user_by_id
from src.schemas.test import ExamConfigUpdate
from src.enums import LessonStatus, LessonType
from src.session import SessionLocal
from src.utils.activate_code import generate_activation_code, generate_reset_code
from src.utils.notifications import (create_notification_text_for_add_new_course, 
                                     create_notification_text_for_update_course)
from src.utils.save_files import delete_files_in_directory
from src.utils.smtp import send_mail_with_code
from src.utils.text_to_speach import create_lecture_text, text_to_speach


logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    _db = None

    @property
    def db(self):
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def on_success(self, retval, task_id, args, kwargs):
        self.close_db()

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        self.close_db()

    def close_db(self):
        if self._db:
            self._db.close()
            self._db = None


celery_app = Celery("celery", broker=BROKER_URL)
celery_app.Task = DatabaseTask


class CeleryTasks:

    @celery_app.task(bind=True, base=DatabaseTask)
    def send_activate_code(self, user_id: int, email: str):
        try:
            code = generate_activation_code()
            create_activation_code(db=self.db, code=code, user_id=user_id)
            send_mail_with_code(to_email=email, mail_title="Your activation code", mail_body=code)
        except Exception as e:
            logger.error(f"Failed to send activation code: {e}")
            raise

    @celery_app.task(bind=True, base=DatabaseTask)
    def activate_user(self, user_id: int, access_token: str, exp_token: datetime, refresh_token: str):
        try:
            user = select_user_by_id(db=self.db, user_id=user_id)
            activate_user(
                db=self.db, user=user, access_token=access_token, refresh_token=refresh_token, exp_token=exp_token
            )
        except Exception as e:
            logger.error(f"Failed to activate user: {e}")
            raise

    @celery_app.task(bind=True, base=DatabaseTask)
    def send_reset_pass_code(self, user_id: int, email: str):
        try:
            code = generate_reset_code()
            create_reset_code(db=self.db, code=code, user_id=user_id)
            send_mail_with_code(to_email=email, mail_title="Your reset password code", mail_body=code)
        except Exception as e:
            logger.error(f"Failed to send reset password code: {e}")
            raise

    @celery_app.task(bind=True, base=DatabaseTask)
    def resend_activate_code(self, email: str, code: str):
        send_mail_with_code(to_email=email, mail_title="Your activate code", mail_body=code)

    @celery_app.task(bind=True, base=DatabaseTask)
    def resend_reset_pass_code(self, email: str, code: str):
        send_mail_with_code(to_email=email, mail_title="Your reset password code", mail_body=code)

    @celery_app.task(bind=True, base=DatabaseTask)
    def create_student_lesson(self, student_id: int, course_id: int):
        try:
            lessons = select_lessons_by_course_db(db=self.db, course_id=course_id)

            for index, lesson in enumerate(lessons):
                if lesson.number == 1:
                    create_student_lesson_db(
                        db=self.db, student_id=student_id, lesson_id=lesson.id, status=LessonStatus.active
                    )

                elif lesson.type == LessonType.test.value or lesson.type == LessonType.exam.value:
                    create_student_lesson_db(
                        db=self.db, student_id=student_id, lesson_id=lesson.id, status=LessonStatus.blocked
                    )
                else:
                    if any(les.type == LessonType.test.value for les in lessons[:index]):
                        create_student_lesson_db(
                            db=self.db, student_id=student_id, lesson_id=lesson.id, status=LessonStatus.blocked
                        )
                    else:
                        create_student_lesson_db(
                            db=self.db, student_id=student_id, lesson_id=lesson.id, status=LessonStatus.available
                        )
        except SQLAlchemyError as e:
            logger.error(f"Error creating student lessons: {e}")

    @celery_app.task(bind=True, base=DatabaseTask)
    def update_student_course_progress(self, student_id: int, lesson_id: int):
        try:
            lesson = select_lesson_by_id_db(db=self.db, lesson_id=lesson_id)
            course_lessons = select_lessons_by_course_db(db=self.db, course_id=lesson.course_id)

            total_lessons = select_count_student_lessons_db(
                db=self.db, course_lessons=course_lessons, student_id=student_id
            )

            completed_lessons = select_count_completed_student_lessons_db(
                db=self.db, course_lessons=course_lessons, student_id=student_id
            )

            student_course = select_student_course_db(
                db=self.db, course_id=lesson.course_id, student_id=student_id
            )

            progress = round((completed_lessons / total_lessons) * 100)
            update_course_present(db=self.db, student_course=student_course, progress=progress)

        except SQLAlchemyError as e:
            logger.error(f"Error updating student course progress: {e}")

    @celery_app.task(bind=True, base=DatabaseTask)
    def update_student_course_grade(self, student_id: int, lesson_id: int, score: int):
        lesson = select_lesson_by_id_db(db=self.db, lesson_id=lesson_id)
        student_course = select_student_course_db(db=self.db, course_id=lesson.course_id, student_id=student_id)
        update_course_score(db=self.db, student_course=student_course, score=score)

    @celery_app.task(bind=True, base=DatabaseTask)
    def update_student_lesson_status(self, lesson_id: int, student_id: int):
        update_student_lesson_status_db(db=self.db, lesson_id=lesson_id, student_id=student_id)

    @celery_app.task(bind=True, base=DatabaseTask)
    def create_lecture_audio(self, lecture_id: int):
        repository = LectureRepository(db=self.db)
        lecture_attrs = repository.select_lecture_attrs(lecture_id=lecture_id)
        lecture_text = create_lecture_text(lecture_attrs)

        folder = "static/speeches" + "/lecture" + str(lecture_id)
        os.makedirs(folder, exist_ok=True)
        delete_files_in_directory(folder)

        result = text_to_speach(text=lecture_text, lecture_id=lecture_id)
        audio_list = [value for value in result.values()]
        repository.update_lecture_audio(lecture_id=lecture_id, audios=audio_list)

    @celery_app.task(bind=True, base=DatabaseTask)
    def create_update_course_notification(self, new_lesson_id: int, course_id: int):
        student_ids = select_students_for_course_db(db=self.db, course_id=course_id)
        lesson = select_lesson_by_id_db(db=self.db, lesson_id=new_lesson_id)

        course_repository = CourseRepository(db=self.db)
        course_name = course_repository.select_course_title_by_id(course_id=course_id)

        notification_rep = NotificationRepository(db=self.db)

        for student in student_ids:
            notification_text = create_notification_text_for_update_course(
                course_name=course_name, lesson_title=lesson.title, lesson_type=lesson.type
            )

            notification_rep.create_notification_about_course_updates(message=notification_text, student_id=student.id)

    @celery_app.task(bind=True, base=DatabaseTask)
    def update_student_lessons(self, student_id: int, lesson_info: dict):

        new_lesson = select_lesson_by_type_and_title_db(
            db=self.db, lesson_title=lesson_info["lesson_title"], lesson_type=lesson_info["lesson_type"]
        )

        course_lessons = select_lessons_by_course_db(db=self.db, course_id=new_lesson.course_id)
        student_lessons = select_student_lessons_db(db=self.db, course_lessons=course_lessons, student_id=student_id)

        update_student_lesson_structure(
            db=self.db, new_lesson=new_lesson, course_lessons=course_lessons,
            student_lessons=student_lessons, student_id=student_id
        )

    @celery_app.task(bind=True, base=DatabaseTask)
    def add_new_course_notification(self, course_id: int):
        student_ids = select_students_whose_bought_courses(db=self.db, course_id=course_id)
        course_rep = CourseRepository(db=self.db)

        new_course = course_rep.select_course_info(course_id=course_id)
        notification_rep = NotificationRepository(db=self.db)

        for student in student_ids:
            message = create_notification_text_for_add_new_course(
                course_name=new_course.title, category_name=new_course.category.title
            )
            notification_rep.create_notification_about_adding_new_course(message=message, student_id=student.id)

    @celery_app.task(bind=True, base=DatabaseTask)
    def check_correct_score(self, course_id: int):
        exam_rep = ExamRepository(db=self.db)
        exam = exam_rep.select_exam_score(course_id=course_id)

        test_repo = TestRepository(db=self.db)
        tests_scores = test_repo.select_tests_scores(course_id=course_id)

        if exam.score + tests_scores > 200:
            diff = 200 - (exam.score + tests_scores)
            new_exam_score = exam.score - abs(diff)
            exam_rep.update_exam_config(exam_id=exam.id, data=ExamConfigUpdate(score=new_exam_score))


celery_tasks = CeleryTasks()
