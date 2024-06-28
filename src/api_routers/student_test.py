from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.celery import celery_tasks
from src.crud.student_lesson import confirm_student_test_db, select_student_lesson_db
from src.crud.student_test import (create_student_attempts_db, create_student_test_answer_db,
                                   create_student_test_matching_db, select_student_answers_db,
                                   select_student_attempt_by_id, select_student_attempt_db, select_student_attempts_db)
from src.crud.test import TestRepository
from src.enums import QuestionTypeOption, UserType
from src.models import UserOrm
from src.schemas.student_test import StudentTest, SubmitStudentTest
from src.session import get_db
from src.utils.exceptions import PermissionDeniedException
from src.utils.get_user import get_current_user
from src.utils.student_test import (check_student_default_test, check_student_multiple_choice_test,
                                    check_student_test_matching)

router = APIRouter(prefix="/student-test")


@router.post("/send")
async def confirm_student_test(
        data: StudentTest,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    test_repository = TestRepository(db=db)
    test_id = test_repository.select_test_id_by_lesson_id(lesson_id=data.lesson_id)
    student_id = user.student.id

    final_score = 0
    data_to_db = []

    student_attempt = select_student_attempt_db(db=db, student_id=student_id, test_id=test_id)
    attempt_number = student_attempt.attempt_number + 1 if student_attempt else 1

    for student_answer in data.student_answers:
        question = test_repository.select_test_question(question_id=student_answer.q_id)

        if student_answer.q_type == QuestionTypeOption.matching.value:
            q_score = check_student_test_matching(db=db, student_matching=student_answer.matching, question=question)
            final_score += q_score
            q_data = {
                "q_score": q_score, "q_id": question.id, "q_type": question.q_type, "matching": student_answer.matching
            }
            data_to_db.append(q_data)

        elif student_answer.q_type == QuestionTypeOption.multiple_choice.value:
            q_score = check_student_multiple_choice_test(db=db, question=question, student_answers=student_answer.a_ids)
            final_score += q_score
            q_data = {
                "q_score": q_score, "q_id": question.id, "q_type": question.q_type, "answers": student_answer.a_ids
            }
            data_to_db.append(q_data)

        else:
            q_score = check_student_default_test(db=db, question=question, student_answer=student_answer.a_id)
            final_score += q_score
            q_data = {
                "q_score": q_score, "q_id": question.id, "q_type": question.q_type, "answer": student_answer.a_id
            }
            data_to_db.append(q_data)

    new_attempt = create_student_attempts_db(
        db=db, number=attempt_number, score=final_score, test_id=test_id, student_id=student_id
    )

    for item in data_to_db:
        if item["q_type"] == QuestionTypeOption.matching.value:
            for match in item["matching"]:
                create_student_test_matching_db(
                    db=db, score=(item["q_score"]/4), question_id=item["q_id"], question_type=item["q_type"],
                    attempt_id=new_attempt.id, left_id=match.left_id, right_id=match.right_id
                )

        elif item["q_type"] == QuestionTypeOption.multiple_choice.value:
            create_student_test_answer_db(
                db=db, score=item["q_score"], question_id=item["q_id"], question_type=item["q_type"],
                attempt_id=new_attempt.id, answers=item["answers"]
            )

        else:
            create_student_test_answer_db(
                db=db, score=item["q_score"], question_id=item["q_id"], question_type=item["q_type"],
                attempt_id=new_attempt.id, answer=item["answer"]
            )

    return {"message": f"Your test score {final_score}"}


@router.get("/attempts")
async def get_test_attempts(
        test_id: int,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.student.value:
        student_id = user.student.id
        return select_student_attempts_db(db=db, test_id=test_id, student_id=student_id)
    else:
        raise PermissionDeniedException()


@router.get("/attempt/{attempt_id}")
async def get_attempt_info(
        attempt_id: int,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.student.value:
        return select_student_answers_db(db=db, attempt_id=attempt_id)
    else:
        raise PermissionDeniedException()


@router.post("/submit")
async def submit_test_attempt(
        data: SubmitStudentTest,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.student.value:
        student_lesson = select_student_lesson_db(db=db, student_id=data.student_id, lesson_id=data.lesson_id)
        test_attempt = select_student_attempt_by_id(db=db, attempt_id=data.attempt_id)
        confirm_student_test_db(
            db=db, score=test_attempt.attempt_score, attempt=test_attempt.attempt_number, student_lesson=student_lesson
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
