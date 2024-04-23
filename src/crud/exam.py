from sqlalchemy.orm import Session

from src.models import ExamAnswerOrm, ExamMatchingLeftOrm, ExamMatchingRightOrm, ExamQuestionOrm


def create_exam_question_db(
        db: Session,
        q_text: str,
        q_number: int,
        q_type: str,
        q_score: int,
        hidden: bool,
        exam_id: int
):
    question = ExamQuestionOrm(
        q_text=q_text,
        q_type=q_type,
        q_number=q_number,
        q_score=q_score,
        hidden=hidden,
        exam_id=exam_id
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


def create_exam_question_with_photo_db(
        db: Session,
        q_text: str,
        q_number: int,
        q_type: str,
        q_score: int,
        hidden: bool,
        image_path: str,
        exam_id: int
):
    question = ExamQuestionOrm(
        q_text=q_text,
        q_type=q_type,
        q_number=q_number,
        q_score=q_score,
        hidden=hidden,
        exam_id=exam_id,
        image_path=image_path
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


def create_exam_answer_db(db: Session, question_id: int, a_text: str, is_correct: bool):
    answer = ExamAnswerOrm(a_text=a_text, is_correct=is_correct, question_id=question_id)
    db.add(answer)
    db.commit()
    db.refresh(answer)


def create_exam_answer_with_photo_db(db: Session, question_id: int, a_text: str, is_correct: bool, image_path: str):
    answer = ExamAnswerOrm(question_id=question_id, a_text=a_text, is_correct=is_correct, image_path=image_path)
    db.add(answer)
    db.commit()
    db.refresh(answer)


def create_exam_matching_db(db: Session, left_text: str, right_text: str, question_id: int):
    right_option = ExamMatchingRightOrm(text=right_text, question_id=question_id)
    db.add(right_option)
    db.commit()

    left_option = ExamMatchingLeftOrm(text=left_text, question_id=question_id, right_id=right_option.id)
    db.add(left_option)
    db.commit()
    db.refresh(right_option)
    db.refresh(left_option)


def select_exam_question_db(db: Session, question_id: int):
    return db.query(ExamQuestionOrm).filter(ExamQuestionOrm.id == question_id).first()


def select_correct_exam_answer_db(db: Session, question_id: int):
    return (db.query(ExamAnswerOrm.id)
            .filter(ExamAnswerOrm.question_id == question_id, ExamAnswerOrm.is_correct)
            .scalar())


def select_total_correct_exam_answers_db(db: Session, question_id: int):
    total = (db.query(ExamAnswerOrm.id.label("id"))
             .filter(ExamAnswerOrm.question_id == question_id, ExamAnswerOrm.is_correct)
             .count())
    return total


def select_correct_exam_answers_db(db: Session, question_id: int):
    answers_ids = (db.query(ExamAnswerOrm.id.label("id"))
                   .filter(ExamAnswerOrm.question_id == question_id, ExamAnswerOrm.is_correct)
                   .all())

    answers = [answer.id for answer in answers_ids]
    return answers


def select_correct_exam_right_db(db: Session, left_id: int):
    return db.query(ExamMatchingLeftOrm.right_id).filter(ExamMatchingLeftOrm.id == left_id).scalar()


def select_exam_answers_db(db: Session, question_id: int):
    return db.query(ExamAnswerOrm).filter(ExamAnswerOrm.question_id == question_id).all()
