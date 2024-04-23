from fastapi import APIRouter

# from sqlalchemy.orm import Session
#
# from src.models import UserOrm
# from src.session import get_db
# from src.utils.get_user import get_current_user
# from src.schemas.student_test import StudentTest

router = APIRouter(prefix="/student-exam")


# @router.post("/send")
# async def confirm_student_exam(
#         data: StudentTest,
#         db: Session = Depends(get_db),
#         user: UserOrm = Depends(get_current_user)
# ):
#     test_score = 0
#     student_id = user.student.id
#
#     for student_answer in data.student_answers:
#         question = select_exam_question_db(db=db, question_id=student_answer.q_id)
#
#         if student_answer.q_type == "matching":
#             q_score = check_student_exam_matching(db=db, student_matching=student_answer.matching, question=question)
#             test_score += q_score
#
#         elif student_answer.q_type == "multiple_choice":
#             q_score = check_student_multiple_choice_exam(db=db, question=question, student_answers=student_answer.a_ids)
#             test_score += q_score
#
#         else:
#             q_score = check_student_default_exam(db=db, question=question, student_answer=student_answer.a_id)
#             test_score += q_score
#
#     student_lesson = select_student_lesson_db(db=db, lesson_id=data.lesson_id, student_id=student_id)
#     update_student_lesson_score_db(db=db, student_lesson=student_lesson, score=test_score)
#     confirm_student_lesson_db(db=db, student_lesson=student_lesson)
#     lesson = select_lesson_by_id_db(db=db, lesson_id=data.lesson_id)
#     student_course = select_student_course_db(db=db, course_id=lesson.course_id, student_id=student_id)
#     update_course_status(db=db, student_course=student_course)
#     return {"message": "You are success completed course"}
