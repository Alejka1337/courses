from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.celery import celery_tasks
from src.crud.student_exam import StudentExamRepository
from src.crud.student_lesson import (
    confirm_student_practical_db,
    select_student_lesson_db,
)
from src.models import UserOrm
from src.schemas.student_practical import (
    ExamResponse,
    StudentPractical,
    SubmitStudentPractical,
)
from src.session import get_db
from src.utils.assessment_managers import ExamManager
from src.utils.exceptions import PermissionDeniedException
from src.utils.get_user import get_current_user

router = APIRouter(prefix="/student-exam")


@router.post("/send", response_model=ExamResponse)
async def confirm_student_exam(
        data: StudentPractical,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.is_student:
        manager = ExamManager(student_id=user.student.id, data=data, db=db)
        new_attempt = manager.start_inspect()
        return new_attempt

    else:
        raise PermissionDeniedException()


@router.get("/attempts")
async def get_exam_attempts(
        exam_id: int,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.is_student:
        student_exam_repository = StudentExamRepository(db=db)
        return student_exam_repository.select_student_attempts(exam_id=exam_id, student_id=user.student.id)
    else:
        raise PermissionDeniedException()


@router.get("/attempt/{attempt_id}")
async def get_attempt_detail(
        attempt_id: int,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.is_student:
        student_exam_repository = StudentExamRepository(db=db)
        return student_exam_repository.select_student_exam_answers(attempt_id=attempt_id)
    else:
        raise PermissionDeniedException()


@router.post("/submit")
async def submit_exam_attempt(
        data: SubmitStudentPractical,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.is_student:
        student_exam_repository = StudentExamRepository(db=db)
        student_lesson = select_student_lesson_db(db=db, student_id=data.student_id, lesson_id=data.lesson_id)
        exam_attempt = student_exam_repository.select_attempt_by_id(attempt_id=data.attempt_id)
        confirm_student_practical_db(
            db=db, score=exam_attempt.attempt_score, attempt=exam_attempt.id, student_lesson=student_lesson
        )

        # celery logic
        celery_tasks.update_student_lesson_status.delay(student_id=data.student_id, lesson_id=data.lesson_id)
        celery_tasks.update_student_course_progress.delay(student_id=data.student_id, lesson_id=data.lesson_id)
        celery_tasks.update_student_course_grade.delay(
            student_id=data.student_id, lesson_id=data.lesson_id, score=exam_attempt.attempt_score
        )
        celery_tasks.complete_student_course(lesson_id=data.lesson_id, student_id=data.student_id)

        return {"Message": f"Your exam was submitted. Score - {exam_attempt.attempt_score}"}

    else:
        raise PermissionDeniedException()
