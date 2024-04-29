from sqlalchemy.orm import Session

from src.models import ExamAnswerOrm, ExamMatchingLeftOrm, ExamMatchingRightOrm, ExamOrm, ExamQuestionOrm


class ExamRepository:
    def __init__(self, db: Session):
        self.db = db
        self.exam_model = ExamOrm
        self.question_model = ExamQuestionOrm
        self.answer_model = ExamAnswerOrm
        self.matching_left_model = ExamMatchingLeftOrm
        self.matching_right_model = ExamMatchingRightOrm

    def create_exam_question(
            self,
            q_text: str,
            q_number: int,
            q_type: str,
            q_score: int,
            hidden: bool,
            exam_id: int,
            image_path: str = None
    ) -> int:

        question = self.question_model(
            q_text=q_text,
            q_type=q_type,
            q_number=q_number,
            q_score=q_score,
            hidden=hidden,
            exam_id=exam_id,
            image_path=image_path if image_path else None,
        )
        self.db.add(question)
        self.db.commit()
        self.db.refresh(question)
        return question.id

    def create_exam_answer(
            self,
            question_id: int,
            a_text: str,
            is_correct: bool,
            image_path: str = None
    ) -> None:

        answer = self.answer_model(
            a_text=a_text,
            is_correct=is_correct,
            question_id=question_id,
            image_path=image_path if image_path else None
        )
        self.db.add(answer)
        self.db.commit()
        self.db.refresh(answer)

    def create_exam_matching(self, left_text: str, right_text: str, question_id: int) -> None:
        right_option = self.matching_right_model(text=right_text, question_id=question_id)
        self.db.add(right_option)
        self.db.commit()

        left_option = self.matching_left_model(text=left_text, question_id=question_id, right_id=right_option.id)
        self.db.add(left_option)
        self.db.commit()

        self.db.refresh(right_option)
        self.db.refresh(left_option)

    def select_exam_question(self, question_id: int):
        return self.db.query(self.question_model).filter(self.question_model.id == question_id).first()

    def select_correct_answer(self, question_id: int) -> int:
        return (self.db.query(self.answer_model.id)
                .filter(self.answer_model.question_id == question_id)
                .filter(self.answer_model.is_correct)
                .scalar())

    def select_count_correct_answers(self, question_id: int) -> int:
        return (self.db.query(self.answer_model.id.label("id"))
                .filter(self.answer_model.question_id == question_id)
                .filter(self.answer_model.is_correct)
                .count())

    def select_correct_answers(self, question_id: int) -> list:
        answers_ids = (self.db.query(self.answer_model.id.label("id"))
                       .filter(self.answer_model.question_id == question_id)
                       .filter(self.answer_model.is_correct)
                       .all())

        answers = [answer.id for answer in answers_ids]
        return answers

    def select_correct_right_option(self, left_id: int) -> int:
        return self.db.query(self.matching_left_model.right_id).filter(self.matching_left_model.id == left_id).scalar()

    def select_exam_answers(self, question_id: int):
        return self.db.query(self.answer_model).filter(self.answer_model.question_id == question_id).all()

    def select_exam_id(self, lesson_id: int):
        return self.db.query(self.exam_model.id).filter(self.exam_model.lesson_id == lesson_id).scalar()
