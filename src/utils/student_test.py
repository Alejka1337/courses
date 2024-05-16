from sqlalchemy.orm import Session

from src.crud.test import TestRepository
from src.models import TestQuestionOrm


def check_student_test_matching(db: Session, student_matching: list, question: TestQuestionOrm):
    repository = TestRepository(db=db)
    total_score = 0
    score_for_match = int(question.q_score / 4)

    for match in student_matching:
        correct_right = repository.select_correct_right(left_id=match.left_id)
        if match.right_id == correct_right:
            total_score += score_for_match

    return total_score


def check_student_multiple_choice_test(db: Session, question: TestQuestionOrm, student_answers: list):
    repository = TestRepository(db=db)
    count_correct = repository.select_total_correct_answers(question_id=question.id)
    correct_answers = repository.select_correct_answers(question_id=question.id)

    score_for_correct = int(question.q_score / count_correct)
    count_student_answer = len(student_answers)
    total_score = 0

    if count_student_answer == count_correct:
        for student_answer in student_answers:
            if student_answer in correct_answers:
                total_score += score_for_correct

        return total_score
    else:
        for student_answer in student_answers:
            if student_answer in correct_answers:
                total_score += score_for_correct

        if count_student_answer > count_correct:
            diff = count_student_answer - count_correct
            total_score - (diff * score_for_correct)
            return total_score if total_score >= 0 else 0


def check_student_default_test(db: Session, question: TestQuestionOrm, student_answer: int):
    repository = TestRepository(db=db)
    answer_id = repository.select_correct_answer(question_id=question.id)
    if answer_id != student_answer:
        return 0
    else:
        return question.q_score
