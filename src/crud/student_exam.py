from typing import List, Optional, Union

from sqlalchemy import desc
from sqlalchemy.orm import Session

from src.enums import QuestionTypeOption
from src.models import StudentExamAnswerOrm, StudentExamAttemptsOrm, StudentExamMatchingOrm
from src.schemas.student_exam import ExamNewAttempt, StudentAnswerDetail, StudentAnswersDetail, StudentMatchingDetail


class StudentExamRepository:
    def __init__(self, db: Session):
        self.db = db
        self.attempt_model = StudentExamAttemptsOrm
        self.answer_model = StudentExamAnswerOrm
        self.matching_model = StudentExamMatchingOrm

    def create_attempt(self, attempt_detail: ExamNewAttempt) -> StudentExamAttemptsOrm:
        new_attempt = self.attempt_model(**attempt_detail.dict())
        self.db.add(new_attempt)
        self.db.commit()
        self.db.refresh(new_attempt)
        return new_attempt

    def update_attempt_score(self, attempt_id: int, score: int) -> None:
        self.db.query(self.attempt_model).filter(self.attempt_model.id == attempt_id).update(
            {self.attempt_model.attempt_score: score}, synchronize_session=False)

        self.db.commit()

    def select_student_attempts(self, exam_id: int, student_id: int) -> Union[List[StudentExamAttemptsOrm], None]:
        res = (self.db.query(self.attempt_model)
               .filter(self.attempt_model.student_id == student_id)
               .filter(self.attempt_model.exam_id == exam_id)
               .all())
        return res if res else None

    def select_attempt_by_id(self, attempt_id: int) -> Optional[StudentExamAttemptsOrm]:
        res = self.db.query(self.attempt_model).filter(self.attempt_model.id == attempt_id).first()
        return res

    def select_last_attempt_number(self, exam_id: int, student_id: int) -> Optional[int]:
        res = (self.db.query(self.attempt_model.attempt_number)
               .filter(self.attempt_model.student_id == student_id)
               .filter(self.attempt_model.exam_id == exam_id)
               .order_by(desc(self.attempt_model.attempt_number))
               .scalar())
        return res

    def create_student_exam_answer(self, answer_data: StudentAnswerDetail) -> None:
        new_answer = self.answer_model(**answer_data.dict())
        self.db.add(new_answer)
        self.db.commit()
        self.db.refresh(new_answer)

    def create_student_exam_answers(self, answers_data: StudentAnswersDetail) -> None:
        new_answers = self.answer_model(**answers_data.dict())
        self.db.add(new_answers)
        self.db.commit()
        self.db.refresh(new_answers)

    def create_student_exam_matching(self, matching_data: StudentMatchingDetail) -> None:
        new_matching = self.matching_model(**matching_data.dict())
        self.db.add(new_matching)
        self.db.commit()
        self.db.refresh(new_matching)

    def select_student_exam_answers(self, attempt_id: int) -> list:
        answers = self.db.query(self.answer_model).filter(self.answer_model.student_attempt_id == attempt_id).all()
        matching = self.db.query(self.matching_model).filter(self.matching_model.student_attempt_id == attempt_id).all()

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
