from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, Body, Request
from sqlalchemy.orm import Session

from src.celery import celery_tasks
from src.crud.course import CourseRepository
from src.crud.student_course import select_count_student_course_db
from src.crud.lesson import (check_lesson_number_db, create_exam_db, create_lecture_db, create_lesson_db,
                             create_test_db, select_lesson_db, update_lesson_number_db)
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
        if check_lesson_number_db(db=db, course_id=data.course_id, number=data.number) >= 1:
            update_lesson_number_db(db=db, course_id=data.course_id, number=data.number)

        lesson = create_lesson_db(db=db, data=data)
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

        course_repository = CourseRepository(db=db)

        if data.type.value == LessonType.lecture.value:
            course_repository.update_quantity_lecture(course_id=data.course_id)
            lecture = create_lecture_db(db=db, lesson_id=lesson.id)
            response["lecture_id"] = lecture.id

        elif data.type.value == LessonType.test.value:
            course_repository.update_quantity_test(course_id=data.course_id)
            test = create_test_db(db=db, lesson_id=lesson.id)
            response["test_id"] = test.id
            celery_tasks.check_correct_score.delay(course_id=data.course_id)

        else:
            exam = create_exam_db(db=db, lesson_id=lesson.id, course_id=data.course_id)
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
    if user.usertype == UserType.student.value:
        return select_lesson_db(db=db, lesson_id=lesson_id, student_id=user.student.id)
    else:
        return select_lesson_db(db=db, lesson_id=lesson_id)
