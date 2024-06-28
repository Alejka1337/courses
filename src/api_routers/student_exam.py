from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.celery import celery_tasks
from src.crud.exam import ExamRepository
from src.crud.student_exam import StudentExamRepository
from src.crud.student_lesson import confirm_student_test_db, select_student_lesson_db
from src.enums import QuestionTypeOption, UserType
from src.models import UserOrm
from src.schemas.student_exam import (ExamNewAttempt, StudentAnswerDetail, StudentAnswersDetail, StudentExam,
                                      StudentMatchingDetail, SubmitStudentExam)
from src.session import get_db
from src.utils.exceptions import PermissionDeniedException
from src.utils.get_user import get_current_user
from src.utils.student_exam import StudentExamService

router = APIRouter(prefix="/student-exam")


@router.post("/send")
async def confirm_student_exam(
        data: StudentExam,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.student.value:
        exam_repository = ExamRepository(db=db)
        student_exam_repository = StudentExamRepository(db=db)
        exam_service = StudentExamService(repository=exam_repository)

        exam_id = exam_repository.select_exam_id(lesson_id=data.lesson_id)
        final_score = 0
        data_to_db = []

        student_attempt = student_exam_repository.select_last_attempt_number(
            student_id=user.student.id, exam_id=exam_id
        )
        attempt_number = student_attempt.attempt_number + 1 if student_attempt else 1

        for student_answer in data.student_answers:
            question = exam_repository.select_exam_question(question_id=student_answer.q_id)

            if student_answer.q_type == QuestionTypeOption.matching.value:
                q_score = exam_service.check_student_exam_matching(
                    student_matching=student_answer.matching, question=question
                )
                final_score += q_score
                q_data = {
                    "q_score": q_score,
                    "q_id": question.id,
                    "q_type": question.q_type,
                    "matching": student_answer.matching
                }
                data_to_db.append(q_data)

            elif student_answer.q_type == QuestionTypeOption.multiple_choice.value:
                q_score = exam_service.check_student_multiple_choice_exam(
                    question=question, student_answers=student_answer.a_ids
                )
                final_score += q_score
                q_data = {
                    "q_score": q_score,
                    "q_id": question.id,
                    "q_type": question.q_type,
                    "answers": student_answer.a_ids
                }
                data_to_db.append(q_data)

            else:
                q_score = exam_service.check_student_default_exam(
                    question=question, student_answer=student_answer.a_id
                )
                final_score += q_score
                q_data = {
                    "q_score": q_score,
                    "q_id": question.id,
                    "q_type": question.q_type,
                    "answer": student_answer.a_id
                }
                data_to_db.append(q_data)

        new_attempt_detail = ExamNewAttempt(
            number=attempt_number, score=final_score, exam_id=exam_id, student_id=user.student.id
        )
        new_attempt = student_exam_repository.create_attempt(attempt_detail=new_attempt_detail)

        for item in data_to_db:
            if item["q_type"] == QuestionTypeOption.matching.value:
                for match in item["matching"]:
                    match_detail = StudentMatchingDetail(
                        score=(item["q_score"] / 4),
                        question_id=item["q_id"],
                        question_type=item["q_type"],
                        attempt_id=new_attempt.id,
                        left_id=match.left_id,
                        right_id=match.right_id

                    )
                    student_exam_repository.create_student_exam_matching(matching_data=match_detail)

            elif item["q_type"] == QuestionTypeOption.multiple_choice.value:
                answers_detail = StudentAnswersDetail(
                    score=item["q_score"],
                    question_id=item["q_id"],
                    question_type=item["q_type"],
                    attempt_id=new_attempt.id,
                    answers=item["answers"]
                )
                student_exam_repository.create_student_exam_answers(answers_data=answers_detail)

            else:
                answer_detail = StudentAnswerDetail(
                    score=item["q_score"],
                    question_id=item["q_id"],
                    question_type=item["q_type"],
                    attempt_id=new_attempt.id,
                    answer=item["answer"]
                )
                student_exam_repository.create_student_exam_answer(answer_data=answer_detail)

        return {"message": f"Your exam score {final_score}"}

    else:
        raise PermissionDeniedException()


@router.get("/attempts")
async def get_exam_attempts(
        exam_id: int,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.student.value:
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
    if user.usertype == UserType.student.value:
        student_exam_repository = StudentExamRepository(db=db)
        return student_exam_repository.select_attempt_by_id(attempt_id=attempt_id)
    else:
        raise PermissionDeniedException()


@router.post("/submit")
async def submit_exam_attempt(
        data: SubmitStudentExam,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.student.value:
        student_exam_repository = StudentExamRepository(db=db)
        student_lesson = select_student_lesson_db(db=db, student_id=data.student_id, lesson_id=data.lesson_id)
        exam_attempt = student_exam_repository.select_attempt_by_id(attempt_id=data.attempt_id)
        confirm_student_test_db(
            db=db, score=exam_attempt.attempt_score, attempt=exam_attempt.attempt_number, student_lesson=student_lesson
        )

        # celery logic
        celery_tasks.update_student_lesson_status.delay(student_id=data.student_id, lesson_id=data.lesson_id)
        celery_tasks.update_student_course_progress.delay(student_id=data.student_id, lesson_id=data.lesson_id)
        celery_tasks.update_student_course_grade.delay(
            student_id=data.student_id, lesson_id=data.lesson_id, score=exam_attempt.attempt_score
        )

        return {"Message": f"Your test was submitted. Score - {exam_attempt.attempt_score}"}

    else:
        raise PermissionDeniedException()
