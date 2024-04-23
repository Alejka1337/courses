from sqlalchemy.orm import Session

from src.models import TestAnswerOrm, TestMatchingLeftOrm, TestMatchingRightOrm, TestOrm, TestQuestionOrm


def create_test_question_db(
        db: Session,
        q_text: str,
        q_number: int,
        q_type: str,
        q_score: int,
        hidden: bool,
        test_id: int
):
    question = TestQuestionOrm(
        q_text=q_text,
        q_type=q_type,
        q_number=q_number,
        q_score=q_score,
        hidden=hidden,
        test_id=test_id
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


def create_test_question_with_photo_db(
        db: Session,
        q_text: str,
        q_number: int,
        q_type: str,
        q_score: int,
        hidden: bool,
        image_path: str,
        test_id: int
):
    question = TestQuestionOrm(
        q_text=q_text,
        q_type=q_type,
        q_number=q_number,
        q_score=q_score,
        hidden=hidden,
        test_id=test_id,
        image_path=image_path
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


def create_test_answer_db(db: Session, question_id: int, a_text: str, is_correct: bool):
    answer = TestAnswerOrm(a_text=a_text, is_correct=is_correct, question_id=question_id)
    db.add(answer)
    db.commit()
    db.refresh(answer)


def create_test_answer_with_photo_db(db: Session, question_id: int, a_text: str, is_correct: bool, image_path: str):
    answer = TestAnswerOrm(question_id=question_id, a_text=a_text, is_correct=is_correct, image_path=image_path)
    db.add(answer)
    db.commit()
    db.refresh(answer)


def create_test_matching_db(db: Session, left_text: str, right_text: str, question_id: int):
    right_option = TestMatchingRightOrm(text=right_text, question_id=question_id)
    db.add(right_option)
    db.commit()

    left_option = TestMatchingLeftOrm(text=left_text, question_id=question_id, right_id=right_option.id)
    db.add(left_option)
    db.commit()
    db.refresh(right_option)
    db.refresh(left_option)


def select_test_question_db(db: Session, question_id: int):
    return db.query(TestQuestionOrm).filter(TestQuestionOrm.id == question_id).first()


def select_test_answers_db(db: Session, question_id: int):
    return db.query(TestAnswerOrm).filter(TestAnswerOrm.question_id == question_id).all()


def select_correct_answer_db(db: Session, question_id: int):
    return (db.query(TestAnswerOrm.id)
            .filter(TestAnswerOrm.question_id == question_id, TestAnswerOrm.is_correct)
            .scalar())


def select_correct_answers_db(db: Session, question_id: int):
    answers_ids = (db.query(TestAnswerOrm.id.label("id"))
                   .filter(TestAnswerOrm.question_id == question_id, TestAnswerOrm.is_correct)
                   .all())

    answers = [answer.id for answer in answers_ids]
    return answers


def select_total_correct_answers_db(db: Session, question_id: int):
    total = (db.query(TestAnswerOrm.id.label("id"))
             .filter(TestAnswerOrm.question_id == question_id, TestAnswerOrm.is_correct)
             .count())
    return total


def select_correct_right_db(db: Session, left_id: int):
    return db.query(TestMatchingLeftOrm.right_id).filter(TestMatchingLeftOrm.id == left_id).scalar()


def select_test_id_by_lesson_id(db: Session, lesson_id: int):
    return db.query(TestOrm.id).filter(TestOrm.lesson_id == lesson_id).scalar()
