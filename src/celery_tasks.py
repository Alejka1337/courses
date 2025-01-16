import os
from datetime import datetime

from src.celery_config import DatabaseTask, celery_app
from src.config import SPEECHES_DIR
from src.crud.category import CategoryRepository
from src.crud.certificate import CertificateRepository
from src.crud.course import CourseRepository
from src.crud.exam import ExamRepository
from src.crud.lecture import LectureRepository
from src.crud.lesson import LessonRepository
from src.crud.notifications import NotificationRepository
from src.crud.stripe import StripeCourseRepository
from src.crud.student_course import (
    select_student_course_db,
    select_students_whose_bought_courses,
    update_course_present,
    update_course_score,
    update_course_status, check_competed_category,
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
from src.enums import (
    LessonStatus,
    LessonType,
    CeleryQueues
)

from src.schemas.practical import ExamConfigUpdate

from src.utils.activate_code import (
    generate_activation_code,
    generate_reset_code
)
from src.utils.certificate import CertificateWriter
from src.utils.convert_to_pdf import convert_to_pdf
from src.utils.lecture_text import create_lecture_text
from src.utils.notifications import (
    create_notification_text_for_add_new_course,
    create_notification_text_for_update_course,
)
from src.utils.save_files import delete_files_in_directory
from src.utils.smtp import send_mail_with_code
from src.utils.speaches import (
    initial_boto,
    synthesize_female_speech,
    synthesize_male_speech
)
from src.utils.stripe_logic import (
    create_new_product,
    create_new_price,
    update_product,
    update_price,
    update_product_price
)


class CeleryTasks:

    @celery_app.task(bind=True, base=DatabaseTask, queue=CeleryQueues.auth)
    def send_activate_code(
            self,
            user_id: int,
            email: str
    ):
        user_repository = UserRepository(db=self.db)
        code = generate_activation_code()
        user_repository.create_activation_code(
            code=code,
            user_id=user_id
        )

        send_mail_with_code(
            to_email=email,
            mail_title="Your activation code",
            mail_body=code
        )

    @celery_app.task(bind=True, base=DatabaseTask, queue=CeleryQueues.auth)
    def activate_user(
            self,
            user_id: int,
            access_token: str,
            exp_token: datetime,
            refresh_token: str
    ):
        user_repository = UserRepository(db=self.db)
        user = user_repository.select_user_by_id(user_id=user_id)
        user_repository.activate_user(
            user=user,
            access_token=access_token,
            refresh_token=refresh_token,
            exp_token=exp_token
        )

    @celery_app.task(bind=True, base=DatabaseTask, queue=CeleryQueues.auth)
    def send_reset_pass_code(
            self,
            user_id: int,
            email: str
    ):
        code = generate_reset_code()
        user_repository = UserRepository(db=self.db)
        user_repository.create_reset_code(
            code=code,
            user_id=user_id
        )

        send_mail_with_code(
            to_email=email,
            mail_title="Your reset password code",
            mail_body=code
        )

    @celery_app.task(bind=True, base=DatabaseTask, queue=CeleryQueues.auth)
    def resend_activate_code(
            self,
            email: str,
            code: str
    ):
        send_mail_with_code(
            to_email=email,
            mail_title="Your activate code",
            mail_body=code
        )

    @celery_app.task(bind=True, base=DatabaseTask, queue=CeleryQueues.auth)
    def resend_reset_pass_code(
            self,
            email: str,
            code: str
    ):
        send_mail_with_code(
            to_email=email,
            mail_title="Your reset password code",
            mail_body=code
        )

    @celery_app.task(bind=True, base=DatabaseTask, queue=CeleryQueues.course)
    def create_student_lesson(
            self,
            student_id: int,
            course_id: int
    ):
        lesson_repo = LessonRepository(db=self.db)
        lessons = lesson_repo.select_lessons_by_course_db(course_id=course_id)

        for index, lesson in enumerate(lessons):
            if lesson.number == 1:
                create_student_lesson_db(
                    db=self.db,
                    student_id=student_id,
                    lesson_id=lesson.id,
                    status=LessonStatus.active
                )

            elif lesson.type == LessonType.test.value or lesson.type == LessonType.exam.value:
                create_student_lesson_db(
                    db=self.db,
                    student_id=student_id,
                    lesson_id=lesson.id,
                    status=LessonStatus.blocked
                )
            else:
                if any(les.type == LessonType.test.value for les in lessons[:index]):
                    create_student_lesson_db(
                        db=self.db,
                        student_id=student_id,
                        lesson_id=lesson.id,
                        status=LessonStatus.blocked
                    )
                else:
                    create_student_lesson_db(
                        db=self.db,
                        student_id=student_id,
                        lesson_id=lesson.id,
                        status=LessonStatus.available
                    )

    @celery_app.task(bind=True, base=DatabaseTask, queue=CeleryQueues.course)
    def update_student_course_progress(
            self,
            student_id: int,
            lesson_id: int
    ):
        lesson_repo = LessonRepository(db=self.db)
        lesson = lesson_repo.select_lesson_by_id_db(lesson_id=lesson_id)
        course_lessons = lesson_repo.select_lessons_by_course_db(course_id=lesson.course_id)

        total_lessons = select_count_student_lessons_db(
            db=self.db,
            course_lessons=course_lessons,
            student_id=student_id
        )

        completed_lessons = select_count_completed_student_lessons_db(
            db=self.db,
            course_lessons=course_lessons,
            student_id=student_id
        )

        student_course = select_student_course_db(
            db=self.db,
            course_id=lesson.course_id,
            student_id=student_id
        )

        progress = round((completed_lessons / total_lessons) * 100)
        update_course_present(
            db=self.db,
            student_course=student_course,
            progress=progress
        )

    @celery_app.task(bind=True, base=DatabaseTask, queue=CeleryQueues.course)
    def update_student_course_grade(
            self,
            student_id: int,
            lesson_id: int,
            score: int
    ):
        lesson_repo = LessonRepository(db=self.db)
        lesson = lesson_repo.select_lesson_by_id_db(lesson_id=lesson_id)
        student_course = select_student_course_db(
            db=self.db,
            course_id=lesson.course_id,
            student_id=student_id
        )

        update_course_score(
            db=self.db,
            student_course=student_course,
            score=score
        )

    @celery_app.task(bind=True, base=DatabaseTask, queue=CeleryQueues.course)
    def update_student_lesson_status(
            self,
            lesson_id: int,
            student_id: int
    ):
        update_student_lesson_status_db(
            db=self.db,
            lesson_id=lesson_id,
            student_id=student_id
        )

    @celery_app.task(bind=True, base=DatabaseTask, queue=CeleryQueues.course)
    def complete_student_course(
            self,
            lesson_id: int,
            student_id: int
    ):
        lesson_repo = LessonRepository(db=self.db)
        certificate_repo = CertificateRepository(db=self.db)
        lesson = lesson_repo.select_lesson_by_id_db(lesson_id=lesson_id)
        student_course = select_student_course_db(
            db=self.db,
            course_id=lesson.course_id,
            student_id=student_id
        )

        update_course_status(
            db=self.db,
            student_course=student_course
        )

        student = UserRepository(db=self.db).select_student_name_by_id(student_id=student_id)
        student_name = f"{student.name} {student.surname}"
        course = CourseRepository(db=self.db).select_base_course_by_id(course_id=lesson.course_id)
        category_name = CategoryRepository(db=self.db).select_category_name_by_id(category_id=course.category_id)

        writer = CertificateWriter(
            cert_type='course',
            student_name=student_name,
            course_name=course.title,
            category_name=category_name
        )

        dir_name, docx_path = writer.write_course_certificate_data()
        convert_to_pdf(dir_name, docx_path)
        certificate_path = docx_path.replace('docx', 'pdf')

        certificate_repo.create_course_certificate(
            path=certificate_path,
            student_id=student_id,
            course_id=lesson.course_id
        )

        # check_complete_category
        res = check_competed_category(
            db=self.db,
            student_id=student_id,
            category_id=course.category_id
        )

        if res:
            courses_list = CourseRepository(db=self.db).select_courses_name_by_category(category_id=course.category_id)
            writer = CertificateWriter(
                cert_type='category',
                student_name=student_name,
                courses_list=[
                    "Business analytics",
                    "Operations Management",
                    "Business Ethics",
                    "Human Resource Management",
                    "Business Administration"
                ],
                category_name=category_name
            )
            dir_name, docx_path = writer.write_category_certificate_data()
            convert_to_pdf(dir_name, docx_path)
            certificate_path = docx_path.replace('docx', 'pdf')

            certificate_repo.create_category_certificate(
                path=certificate_path,
                student_id=student_id,
                category_id=course.category_id
            )



    @celery_app.task(bind=True, base=DatabaseTask, queue=CeleryQueues.tts)
    def create_lecture_audio(
            self,
            lecture_id: int
    ):
        repository = LectureRepository(db=self.db)
        lecture_attrs = repository.select_lecture_attrs(lecture_id=lecture_id)
        lecture_text = create_lecture_text(attrs=lecture_attrs)

        folder = f"{SPEECHES_DIR}/lecture{lecture_id}"
        os.makedirs(folder, exist_ok=True)
        delete_files_in_directory(
            directory=folder,
            mode="all"
        )

        result = []
        polly = initial_boto()

        output_path_male = os.path.join(folder, "male.mp3")
        synthesize_male_speech(
            text=lecture_text,
            file_path=output_path_male,
            polly=polly
        )

        result.append(output_path_male)

        output_path_female = os.path.join(folder, "female.mp3")
        synthesize_female_speech(
            text=lecture_text,
            file_path=output_path_female,
            polly=polly
        )
        result.append(output_path_female)

        repository.update_lecture_audio(
            lecture_id=lecture_id,
            audios=result
        )

    @celery_app.task(bind=True, base=DatabaseTask, queue=CeleryQueues.default)
    def create_update_course_notification(
            self,
            new_lesson_id: int,
            course_id: int
    ):
        student_ids = select_students_for_course_db(
            db=self.db,
            course_id=course_id
        )

        lesson_repo = LessonRepository(db=self.db)
        lesson = lesson_repo.select_lesson_by_id_db(lesson_id=new_lesson_id)

        course_repository = CourseRepository(db=self.db)
        course_name = course_repository.select_course_title_by_id(course_id=course_id)

        notification_rep = NotificationRepository(db=self.db)

        for student in student_ids:
            notification_text = create_notification_text_for_update_course(
                course_name=course_name,
                lesson_title=lesson.title,
                lesson_type=lesson.type
            )

            notification_rep.create_notification_about_course_updates(
                message=notification_text,
                student_id=student.id
            )

    @celery_app.task(bind=True, base=DatabaseTask, queue=CeleryQueues.course)
    def update_student_lessons(
            self,
            student_id: int,
            lesson_info: dict
    ):

        lesson_repo = LessonRepository(db=self.db)
        new_lesson = lesson_repo.select_lesson_by_type_and_title_db(
            lesson_title=lesson_info["lesson_title"],
            lesson_type=lesson_info["lesson_type"]
        )

        course_lessons = lesson_repo.select_lessons_by_course_db(course_id=new_lesson.course_id)
        student_lessons = select_student_lessons_db(
            db=self.db,
            course_lessons=course_lessons,
            student_id=student_id
        )

        update_student_lesson_structure(
            db=self.db,
            new_lesson=new_lesson,
            course_lessons=course_lessons,
            student_lessons=student_lessons,
            student_id=student_id
        )

    @celery_app.task(bind=True, base=DatabaseTask, queue=CeleryQueues.default)
    def add_new_course_notification(
            self,
            course_id: int
    ):
        student_ids = select_students_whose_bought_courses(
            db=self.db,
            course_id=course_id
        )

        course_rep = CourseRepository(db=self.db)

        new_course = course_rep.select_course_info(course_id=course_id)
        notification_rep = NotificationRepository(db=self.db)

        for student in student_ids:
            message = create_notification_text_for_add_new_course(
                course_name=new_course.title,
                category_name=new_course.category.title
            )

            notification_rep.create_notification_about_adding_new_course(
                message=message,
                student_id=student.id
            )

    @celery_app.task(bind=True, base=DatabaseTask, queue=CeleryQueues.course)
    def check_correct_score(
            self,
            course_id: int
    ):
        exam_rep = ExamRepository(db=self.db)
        test_repo = TestRepository(db=self.db)

        exam = exam_rep.select_exam_score(course_id=course_id)
        tests_scores = test_repo.select_tests_scores(course_id=course_id)

        if exam is not None:
            if exam.score + tests_scores > 200:
                diff = 200 - (exam.score + tests_scores)
                new_exam_score = exam.score - abs(diff)
                exam_rep.update_exam_config(
                    exam_id=exam.id,
                    data=ExamConfigUpdate(score=new_exam_score)
                )

    @celery_app.task(bind=True, base=DatabaseTask, queue=CeleryQueues.auth)
    def update_user_token_after_login(
            self,
            user_id: int,
            access_token: str,
            refresh_token: str,
            exp_token: datetime
    ):
        user_repository = UserRepository(db=self.db)
        user = user_repository.select_user_by_id(user_id=user_id)
        user_repository.update_user_token(
            user=user,
            access_token=access_token,
            refresh_token=refresh_token,
            exp_token=exp_token
        )

    @celery_app.task(bind=True, base=DatabaseTask, queue=CeleryQueues.stripe)
    def create_stripe_price(
            self,
            course_id
    ):
        course_repository = CourseRepository(db=self.db)
        course = course_repository.select_base_course_by_id(course_id=course_id)

        image = course.image_path if course.image_path else None
        name = course.title
        price = course.price

        product_id = create_new_product(
            name=name,
            image_path=image
        )

        stripe_data = create_new_price(
            price=price,
            stripe_product_id=product_id
        )
        stripe_data["course_id"] = course_id

        stripe_course_repo = StripeCourseRepository(db=self.db)
        stripe_course_repo.create_stripe_product(stripe_data)

    @celery_app.task(bind=True, base=DatabaseTask, queue=CeleryQueues.stripe)
    def update_stripe_product(
            self,
            course_id: int,
            title: str,
            image_path: str
    ):
        stripe_course_repo = StripeCourseRepository(db=self.db)
        stripe_product_id = stripe_course_repo.select_stripe_product_id(course_id=course_id)
        update_product(
            stripe_product_id=stripe_product_id,
            new_name=title,
            new_image_path=image_path
        )

    @celery_app.task(bind=True, base=DatabaseTask, queue=CeleryQueues.stripe)
    def update_stripe_price(
            self,
            course_id: int,
            price: str
    ):
        stripe_course_repo = StripeCourseRepository(db=self.db)
        stripe_product_id = stripe_course_repo.select_stripe_product_id(course_id=course_id)
        stripe_price_id = stripe_course_repo.select_stripe_price_id(course_id=course_id)

        stripe_data = create_new_price(
            price=price,
            stripe_product_id=stripe_product_id
        )
        new_stripe_price_id = stripe_data["stripe_price_id"]

        update_product_price(
            stripe_product_id=stripe_product_id,
            stripe_price_id=new_stripe_price_id
        )

        update_price(stripe_price_id=stripe_price_id)

        stripe_course_repo.update_stripe_price_id(
            course_id=course_id,
            stripe_price_id=new_stripe_price_id
        )


tasks = CeleryTasks()