import logging
import os
from datetime import datetime

from kombu import Exchange, Queue
from sqlalchemy.exc import SQLAlchemyError
from TTS.api import TTS
from celery import Celery, Task
from celery.signals import worker_ready

from src.config import BROKER_URL, SPEECHES_DIR, VOICE_MODEL
from src.crud.certificate import CertificateRepository
from src.crud.course import CourseRepository
from src.crud.exam import ExamRepository
from src.crud.lecture import LectureRepository
from src.crud.lesson import LessonRepository
from src.crud.notifications import NotificationRepository
from src.crud.student_course import (
    select_student_course_db,
    select_students_whose_bought_courses,
    update_course_present,
    update_course_score,
    update_course_status,
)
from src.crud.student_lesson import (
    create_student_lesson_db,
    select_count_completed_student_lessons_db,
    select_count_student_lessons_db,
    select_student_lessons_db,
    select_students_for_course_db,
    update_student_lesson_status_db,
    update_student_lesson_structure,
)
from src.crud.test import TestRepository
from src.crud.user import UserRepository
from src.enums import LessonStatus, LessonType
from src.schemas.practical import ExamConfigUpdate
from src.session import SessionLocal
from src.utils.activate_code import generate_activation_code, generate_reset_code
from src.utils.lecture_text import create_lecture_text
from src.utils.notifications import (
    create_notification_text_for_add_new_course,
    create_notification_text_for_update_course,
)
from src.utils.save_files import delete_files_in_directory
from src.utils.smtp import send_mail_with_code

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

celery_app.conf.update(
    task_default_queue='default',
    task_default_exchange='default',
    task_default_routing_key='default',
    worker_pool='solo',
    worker_concurrency=1,
)
celery_app.conf.task_queues = (
    Queue('default', Exchange('default'), routing_key='default'),
    Queue('audio_tasks', Exchange('audio'), routing_key='audio.#'),
)

celery_app.Task = DatabaseTask

tts = None


@worker_ready.connect
def setup_tts_model(sender, **kwargs):
    if sender.hostname.startswith('worker_audio'):
        global tts
        tts = TTS(model_name=VOICE_MODEL)


class CeleryTasks:

    @celery_app.task(bind=True, base=DatabaseTask, queue='default')
    def send_activate_code(self, user_id: int, email: str):
        try:
            user_repository = UserRepository(db=self.db)
            code = generate_activation_code()
            user_repository.create_activation_code(code=code, user_id=user_id)
            send_mail_with_code(to_email=email, mail_title="Your activation code", mail_body=code)
        except Exception as e:
            logger.error(f"Failed to send activation code: {e}")
            raise

    @celery_app.task(bind=True, base=DatabaseTask, queue='default')
    def activate_user(self, user_id: int, access_token: str, exp_token: datetime, refresh_token: str):
        try:
            user_repository = UserRepository(db=self.db)
            user = user_repository.select_user_by_id(user_id=user_id)
            user_repository.activate_user(
                user=user,
                access_token=access_token,
                refresh_token=refresh_token,
                exp_token=exp_token
            )

        except Exception as e:
            logger.error(f"Failed to activate user: {e}")
            raise

    @celery_app.task(bind=True, base=DatabaseTask, queue='default')
    def send_reset_pass_code(self, user_id: int, email: str):
        try:
            code = generate_reset_code()
            user_repository = UserRepository(db=self.db)
            user_repository.create_reset_code(code=code, user_id=user_id)
            send_mail_with_code(to_email=email, mail_title="Your reset password code", mail_body=code)

        except Exception as e:
            logger.error(f"Failed to send reset password code: {e}")
            raise

    @celery_app.task(bind=True, base=DatabaseTask, queue='default')
    def resend_activate_code(self, email: str, code: str):
        send_mail_with_code(to_email=email, mail_title="Your activate code", mail_body=code)

    @celery_app.task(bind=True, base=DatabaseTask, queue='default')
    def resend_reset_pass_code(self, email: str, code: str):
        send_mail_with_code(to_email=email, mail_title="Your reset password code", mail_body=code)

    @celery_app.task(bind=True, base=DatabaseTask, queue='default')
    def create_student_lesson(self, student_id: int, course_id: int):
        try:
            lesson_repo = LessonRepository(db=self.db)
            lessons = lesson_repo.select_lessons_by_course_db(course_id=course_id)

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

    @celery_app.task(bind=True, base=DatabaseTask, queue='default')
    def update_student_course_progress(self, student_id: int, lesson_id: int):
        try:
            lesson_repo = LessonRepository(db=self.db)
            lesson = lesson_repo.select_lesson_by_id_db(lesson_id=lesson_id)
            course_lessons = lesson_repo.select_lessons_by_course_db(course_id=lesson.course_id)

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

    @celery_app.task(bind=True, base=DatabaseTask, queue='default')
    def update_student_course_grade(self, student_id: int, lesson_id: int, score: int):
        lesson_repo = LessonRepository(db=self.db)
        lesson = lesson_repo.select_lesson_by_id_db(lesson_id=lesson_id)
        student_course = select_student_course_db(db=self.db, course_id=lesson.course_id, student_id=student_id)
        update_course_score(db=self.db, student_course=student_course, score=score)

    @celery_app.task(bind=True, base=DatabaseTask)
    def update_student_lesson_status(self, lesson_id: int, student_id: int):
        update_student_lesson_status_db(db=self.db, lesson_id=lesson_id, student_id=student_id)

    @celery_app.task(bind=True, base=DatabaseTask,  queue='default', max_retries=3, default_retry_delay=300)
    def complete_student_course(self, lesson_id: int, student_id: int):
        lesson_repo = LessonRepository(db=self.db)
        certificate_repo = CertificateRepository(db=self.db)

        logger.info("Starting create course certificate")

        try:
            lesson = lesson_repo.select_lesson_by_id_db(lesson_id=lesson_id)
            student_course = select_student_course_db(db=self.db, course_id=lesson.course_id, student_id=student_id)
            update_course_status(db=self.db, student_course=student_course)
            certificate_repo.create_course_certificate(student_id=student_id, course_id=lesson.course_id)
        except Exception as exc:
            logger.error(f"Error while creating certificate for sudent {student_id}: {exc}", exc_info=True)
            raise self.retry(exc=exc)

    @celery_app.task(bind=True, base=DatabaseTask, queue='audio_tasks', max_retries=3, default_retry_delay=600)
    def create_lecture_audio(self, lecture_id: int):
        repository = LectureRepository(db=self.db)
        lecture_attrs = repository.select_lecture_attrs(lecture_id=lecture_id)
        lecture_text = create_lecture_text(lecture_attrs)

        folder = SPEECHES_DIR + "/lecture" + str(lecture_id)
        os.makedirs(folder, exist_ok=True)
        delete_files_in_directory(folder, "all")

        logger.info("Starting create tts")
        try:
            result = []

            output_path = os.path.join(folder, "male1.wav")
            tts.tts_to_file(text=lecture_text, speaker="p226", file_path=output_path)
            result.append(output_path)

            output_path = os.path.join(folder, "female1.wav")
            tts.tts_to_file(text=lecture_text, speaker="p225", file_path=output_path)
            result.append(output_path)
            logger.info("Created tts")
            repository.update_lecture_audio(lecture_id=lecture_id, audios=result)

        except Exception as exc:
            logger.error(f"Error while creating TTS for lecture_id {lecture_id}: {exc}", exc_info=True)
            raise self.retry(exc=exc)

    @celery_app.task(bind=True, base=DatabaseTask, queue='default')
    def create_update_course_notification(self, new_lesson_id: int, course_id: int):
        student_ids = select_students_for_course_db(db=self.db, course_id=course_id)
        lesson_repo = LessonRepository(db=self.db)
        lesson = lesson_repo.select_lesson_by_id_db(lesson_id=new_lesson_id)

        course_repository = CourseRepository(db=self.db)
        course_name = course_repository.select_course_title_by_id(course_id=course_id)

        notification_rep = NotificationRepository(db=self.db)

        for student in student_ids:
            notification_text = create_notification_text_for_update_course(
                course_name=course_name, lesson_title=lesson.title, lesson_type=lesson.type
            )

            notification_rep.create_notification_about_course_updates(message=notification_text, student_id=student.id)

    @celery_app.task(bind=True, base=DatabaseTask, queue='default')
    def update_student_lessons(self, student_id: int, lesson_info: dict):

        lesson_repo = LessonRepository(db=self.db)
        new_lesson = lesson_repo.select_lesson_by_type_and_title_db(
            lesson_title=lesson_info["lesson_title"], lesson_type=lesson_info["lesson_type"]
        )

        course_lessons = lesson_repo.select_lessons_by_course_db(course_id=new_lesson.course_id)
        student_lessons = select_student_lessons_db(db=self.db, course_lessons=course_lessons, student_id=student_id)

        update_student_lesson_structure(
            db=self.db, new_lesson=new_lesson, course_lessons=course_lessons,
            student_lessons=student_lessons, student_id=student_id
        )

    @celery_app.task(bind=True, base=DatabaseTask, queue='default')
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

    @celery_app.task(bind=True, base=DatabaseTask, queue='default')
    def check_correct_score(self, course_id: int):
        exam_rep = ExamRepository(db=self.db)
        test_repo = TestRepository(db=self.db)

        exam = exam_rep.select_exam_score(course_id=course_id)
        tests_scores = test_repo.select_tests_scores(course_id=course_id)

        if exam is not None:
            if exam.score + tests_scores > 200:
                diff = 200 - (exam.score + tests_scores)
                new_exam_score = exam.score - abs(diff)
                exam_rep.update_exam_config(exam_id=exam.id, data=ExamConfigUpdate(score=new_exam_score))

    @celery_app.task(bind=True, base=DatabaseTask, queue='default')
    def update_user_token_after_login(self, user_id: int, access_token: str, refresh_token: str, exp_token: datetime):
        user_repository = UserRepository(db=self.db)
        user = user_repository.select_user_by_id(user_id=user_id)
        user_repository.update_user_token(
            user=user,
            access_token=access_token,
            refresh_token=refresh_token,
            exp_token=exp_token
        )


celery_tasks = CeleryTasks()
