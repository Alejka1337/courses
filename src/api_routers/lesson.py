from typing import Annotated

from fastapi import APIRouter, Body, Depends, File, UploadFile
from sqlalchemy.orm import Session

from src.celery import celery_tasks
from src.crud.lesson import LessonRepository
from src.crud.course import CourseRepository
from src.crud.student_course import select_count_student_course_db
from src.enums import LessonType, StaticFileType, UserType
from src.models import UserOrm
from src.schemas.lesson import LessonCreate
from src.session import get_db
from src.utils.exceptions import PermissionDeniedException
from src.utils.get_user import get_current_user
from src.utils.save_files import save_file

router = APIRouter(prefix="/lesson")


@router.post("/create")
async def create_lesson(
        data: Annotated[LessonCreate, Body],
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        repository = LessonRepository(db=db)
        if repository.check_lesson_number_db(course_id=data.course_id, number=data.number) >= 1:
            repository.update_lesson_number_db(course_id=data.course_id, number=data.number)

        lesson = repository.create_lesson_db(data=data)
        response = {
            "id": lesson.id,
            "type": lesson.type,
            "number": lesson.number,
            "title": lesson.title,
            "description": lesson.description,
            "scheduled_time": lesson.scheduled_time,
            "course_id": lesson.course_id,
            "image_path": lesson.image_path,
            "is_published": lesson.is_published
        }

        if data.type.value == LessonType.lecture.value:
            course_repository = CourseRepository(db=db)
            course_repository.update_quantity_lecture(course_id=data.course_id)

            new_lecture = repository.lecture_repo.create_lecture(lesson_id=lesson.id)
            response["lecture_id"] = new_lecture.id

        elif data.type.value == LessonType.test.value:
            course_repository = CourseRepository(db=db)
            course_repository.update_quantity_test(course_id=data.course_id)

            new_test = repository.test_repo.create_test(lesson_id=lesson.id)
            response["test_id"] = new_test.id

            celery_tasks.check_correct_score.delay(course_id=data.course_id)
        else:
            exam = repository.exam_repo.create_exam(lesson_id=lesson.id, course_id=data.course_id)
            response["exam_id"] = exam.id

        if select_count_student_course_db(db=db, course_id=lesson.course_id) > 0:
            celery_tasks.create_update_course_notification.delay(lesson.id, lesson.course_id)

        return response

    else:
        raise PermissionDeniedException()


@router.post("/upload/file")
async def upload_lesson_image(
        file: UploadFile = File(...),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        file_path = save_file(file=file, file_type=StaticFileType.lesson_image.value)
        return {"filename": file.filename, "file_path": file_path, "file_size": file.size}
    else:
        raise PermissionDeniedException()


@router.get("/get/{lesson_id}")
async def get_lesson(
        lesson_id: int,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    repository = LessonRepository(db=db)
    if user.usertype == UserType.student.value:
        return repository.select_lesson_db(lesson_id=lesson_id, student_id=user.student.id)
    else:
        return repository.select_lesson_db(lesson_id=lesson_id)
