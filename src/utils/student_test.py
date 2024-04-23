from sqlalchemy.orm import Session

from src.crud.exam import (select_correct_exam_answer_db, select_correct_exam_answers_db, select_correct_exam_right_db,
                           select_total_correct_exam_answers_db)
from src.crud.test import (select_correct_answer_db, select_correct_answers_db, select_correct_right_db,
                           select_total_correct_answers_db)
from src.models import ExamQuestionOrm, TestQuestionOrm


def check_student_test_matching(db: Session, student_matching: list, question: TestQuestionOrm):
    total_score = 0
    score_for_match = int(question.q_score / 4)

    for match in student_matching:
        correct_right = select_correct_right_db(db=db, left_id=match.left_id)
        if match.right_id == correct_right:
            total_score += score_for_match

    return total_score


def check_student_multiple_choice_test(db: Session, question: TestQuestionOrm, student_answers: list):
    count_correct = select_total_correct_answers_db(db=db, question_id=question.id)
    score_for_correct = int(question.q_score / count_correct)
    correct_answers = select_correct_answers_db(db=db, question_id=question.id)
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
    answer_id = select_correct_answer_db(db=db, question_id=question.id)
    if answer_id != student_answer:
        return 0
    else:
        return question.q_score

        # if question.q_type in ["answer_with_photo", "question_with_photo"]:
        #     return 6
        # else:
        #     return 4


def check_student_exam_matching(db: Session, student_matching: list, question: ExamQuestionOrm):
    total_score = 0
    score_for_match = int(question.q_score / 4)

    for match in student_matching:
        correct_right = select_correct_exam_right_db(db=db, left_id=match.left_id)
        if match.right_id == correct_right:
            total_score += score_for_match

    return total_score


def check_student_multiple_choice_exam(db: Session, question: ExamQuestionOrm, student_answers: list):
    total_correct = select_total_correct_exam_answers_db(db=db, question_id=question.id)
    score_for_correct = int(question.q_score / total_correct)
    correct_answers = select_correct_exam_answers_db(db=db, question_id=question.id)
    total_score = 0

    for student_answer in student_answers:
        if student_answer in correct_answers:
            total_score += score_for_correct

    return total_score


def check_student_default_exam(db: Session, question: ExamQuestionOrm, student_answer: int):
    answer_id = select_correct_exam_answer_db(db=db, question_id=question.id)
    if answer_id != student_answer:
        return 0
    else:
        return question.q_score
