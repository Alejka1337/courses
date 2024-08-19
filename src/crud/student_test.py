from typing import List, Optional, Union

from sqlalchemy import desc
from sqlalchemy.orm import Session

from src.models import StudentTestAnswerOrm, StudentTestAttemptsOrm, StudentTestMatchingOrm
from src.schemas.practical import StudentAnswerDetail, StudentAnswersDetail, StudentMatchingDetail, TestNewAttempt
from src.utils.serialize_attempt import serialize_attempt_data


class StudentTestRepository:
    def __init__(self, db: Session):
        self.db = db
        self.attempt_model = StudentTestAttemptsOrm
        self.answer_model = StudentTestAnswerOrm
        self.matching_model = StudentTestMatchingOrm

    def create_attempt(self, attempt_data: TestNewAttempt) -> StudentTestAttemptsOrm:
        new_attempt = self.attempt_model(**attempt_data.dict())
        self.db.add(new_attempt)
        self.db.commit()
        self.db.refresh(new_attempt)
        return new_attempt

    def update_attempt_score(self, attempt_id: int, score: int) -> StudentTestAttemptsOrm:
        # self.db.query(self.attempt_model).filter(self.attempt_model.id == attempt_id).update(
        #     {self.attempt_model.attempt_score: score}, synchronize_session=False)

        attempt = self.select_attempt_by_id(attempt_id=attempt_id)
        attempt.attempt_score = score
        self.db.commit()
        self.db.refresh(attempt)
        return attempt

    def select_student_attempts(self, test_id: int, student_id: int) -> Union[List[StudentTestAttemptsOrm], None]:
        res = (self.db.query(self.attempt_model)
               .filter(self.attempt_model.student_id == student_id)
               .filter(self.attempt_model.test_id == test_id)
               .all())
        return res if res else None

    def select_attempt_by_id(self, attempt_id: int) -> Optional[StudentTestAttemptsOrm]:
        return self.db.query(self.attempt_model).filter(self.attempt_model.id == attempt_id).first()

    def select_last_attempt_number(self, test_id: int, student_id: int) -> Optional[int]:
        res = (self.db.query(self.attempt_model)
               .filter(self.attempt_model.student_id == student_id)
               .filter(self.attempt_model.test_id == test_id)
               .order_by(desc(self.attempt_model.attempt_number))
               .first())
        return res.attempt_number if res else None

    def create_student_answer(self, answer_data: StudentAnswerDetail) -> None:
        student_answer = self.answer_model(**answer_data.dict())
        self.db.add(student_answer)
        self.db.commit()

    def create_student_answers(self, answers_data: StudentAnswersDetail) -> None:
        student_answers = self.answer_model(**answers_data.dict())
        self.db.add(student_answers)
        self.db.commit()

    def create_student_matching(self, matching_data: StudentMatchingDetail) -> None:
        student_match = self.matching_model(**matching_data.dict())
        self.db.add(student_match)
        self.db.commit()

    def select_student_answers(self, attempt_id: int):
        answers = self.db.query(self.answer_model).filter(self.answer_model.student_attempt_id == attempt_id).all()
        matching = self.db.query(self.matching_model).filter(self.matching_model.student_attempt_id == attempt_id).all()

        return serialize_attempt_data(answers=answers, matching=matching)
