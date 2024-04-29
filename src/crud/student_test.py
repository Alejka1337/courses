from sqlalchemy import desc
from sqlalchemy.orm import Session

from src.enums import QuestionTypeOption
from src.models import StudentTestAnswerOrm, StudentTestAttemptsOrm, StudentTestMatchingOrm


def create_student_attempts_db(db: Session, number: int, score: int, test_id: int, student_id: int):
    new_attempt = StudentTestAttemptsOrm(
        attempt_number=number, attempt_score=score, test_id=test_id, student_id=student_id
    )

    db.add(new_attempt)
    db.commit()
    db.refresh(new_attempt)
    return new_attempt


def create_student_test_answer_db(
        db: Session,
        score: int,
        question_id: int,
        question_type: QuestionTypeOption,
        attempt_id: int,
        answer: int = None,
        answers: list = None
):
    student_answer = StudentTestAnswerOrm(
        score=score,
        question_id=question_id,
        question_type=question_type,
        answer_id=answer if answer else None,
        answer_ids=answers if answers else None,
        student_attempt_id=attempt_id
    )
    db.add(student_answer)
    db.commit()
    db.refresh(student_answer)


def create_student_test_matching_db(
        db: Session,
        score: int,
        question_id: int,
        question_type: QuestionTypeOption,
        attempt_id: int,
        left_id: int,
        right_id: int
):
    student_match = StudentTestMatchingOrm(
        score=score,
        question_id=question_id,
        question_type=question_type,
        student_attempt_id=attempt_id,
        left_id=left_id,
        right_id=right_id
    )
    db.add(student_match)
    db.commit()
    db.refresh(student_match)


def select_student_attempt_db(db: Session, test_id: int, student_id: int):
    return (db.query(StudentTestAttemptsOrm)
            .filter(StudentTestAttemptsOrm.student_id == student_id,
                    StudentTestAttemptsOrm.test_id == test_id)
            .order_by(desc(StudentTestAttemptsOrm.attempt_number))
            .first())


def select_student_attempts_db(db: Session, test_id: int, student_id: int):
    return (db.query(StudentTestAttemptsOrm)
            .filter(StudentTestAttemptsOrm.student_id == student_id,
                    StudentTestAttemptsOrm.test_id == test_id)
            .all())


def select_student_attempt_by_id(db: Session, attempt_id: int):
    return db.query(StudentTestAttemptsOrm).filter(StudentTestAttemptsOrm.id == attempt_id).first()


def select_student_answers_db(db: Session, attempt_id: int):
    answers = db.query(StudentTestAnswerOrm).filter(StudentTestAnswerOrm.student_attempt_id == attempt_id).all()
    matching = db.query(StudentTestMatchingOrm).filter(StudentTestMatchingOrm.student_attempt_id == attempt_id).all()
    result = []

    for answer in answers:
        if answer.question_type == QuestionTypeOption.multiple_choice:
            data = {
                "q_id": answer.question_id,
                "q_type": answer.question_type,
                "answers": answer.answer_ids
            }
            result.append(data)
        else:
            data = {
                "q_id": answer.question_id,
                "q_type": answer.question_type,
                "answer": answer.answer_id
            }
            result.append(data)

    for match in matching:
        data = {
            "q_id": match.question_id,
            "q_type": match.question_type,
            "left_id": match.left_id,
            "right_id": match.right_id
        }
        result.append(data)

    return result
