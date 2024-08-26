from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.celery import celery_tasks
from src.crud.student_lesson import (
    confirm_student_practical_db,
    select_student_lesson_db,
)
from src.crud.student_test import StudentTestRepository
from src.models import UserOrm
from src.schemas.student_practical import (
    StudentPractical,
    SubmitStudentPractical,
    TestResponse,
)
from src.session import get_db
from src.utils.assessment_managers import TestManager
from src.utils.exceptions import PermissionDeniedException
from src.utils.get_user import get_current_user

router = APIRouter(prefix="/student-test")


@router.post("/send", response_model=TestResponse)
async def confirm_student_test(
        data: StudentPractical,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.is_student:
        manager = TestManager(db=db, data=data, student_id=user.student.id)
        new_attempt = manager.start_inspect()
        return new_attempt
    else:
        raise PermissionDeniedException()


@router.get("/attempts")
async def get_test_attempts(
        test_id: int,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.is_student:
        student_test_repo = StudentTestRepository(db=db)
        return student_test_repo.select_student_attempts(test_id=test_id, student_id=user.student.id)
    else:
        raise PermissionDeniedException()


@router.get("/attempt/{attempt_id}")
async def get_attempt_info(
        attempt_id: int,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.is_student:
        student_test_repo = StudentTestRepository(db=db)
        return student_test_repo.select_student_answers(attempt_id=attempt_id)
    else:
        raise PermissionDeniedException()


@router.post("/submit")
async def submit_test_attempt(
        data: SubmitStudentPractical,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.is_student:
        student_test_repo = StudentTestRepository(db=db)
        student_lesson = select_student_lesson_db(db=db, student_id=data.student_id, lesson_id=data.lesson_id)
        test_attempt = student_test_repo.select_attempt_by_id(attempt_id=data.attempt_id)
        confirm_student_practical_db(
            db=db, score=test_attempt.attempt_score, attempt=test_attempt.id, student_lesson=student_lesson
        )

        # celery logic
        celery_tasks.update_student_lesson_status.delay(student_id=data.student_id, lesson_id=data.lesson_id)
        celery_tasks.update_student_course_progress.delay(student_id=data.student_id, lesson_id=data.lesson_id)
        celery_tasks.update_student_course_grade.delay(
            student_id=data.student_id, lesson_id=data.lesson_id, score=test_attempt.attempt_score
        )

        return {"Message": f"Your test was submitted. Score - {test_attempt.attempt_score}"}
    else:
        raise PermissionDeniedException()
