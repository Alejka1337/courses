from typing import List, Literal

from sqlalchemy.orm import Session

from src.crud.exam import ExamRepository
from src.crud.test import TestRepository
from src.enums import QuestionTypeOption
from src.schemas.practical import (
    AnswerBase,
    AnswerResponse,
    MatchingBase,
    MatchingItem,
    MatchingResponse,
    QuestionBase,
    QuestionListResponse,
    QuestionResponse,
)

MODE = Literal["test", "exam"]


class CreatePracticalLesson:
    _repository = None

    def __init__(self, mode: MODE, db: Session, questions_data: List[QuestionBase], practical_id: int):
        self._mode = mode
        self._db = db
        self._question_data = questions_data
        self._practical_id = practical_id
        self.result = []

    def init_repository(self):
        if self._repository is not None:
            return self._repository
        else:

            if self._mode == "test":
                self._repository = TestRepository(db=self._db)

            elif self._mode == "exam":
                self._repository = ExamRepository(db=self._db)

            else:
                raise ValueError("Invalid Mode")

    def create_question(self, question_data: QuestionBase):
        if self._mode == "test":
            question_orm = self._repository.create_test_question(
                q_text=question_data.q_text,
                q_number=question_data.q_number,
                q_type=question_data.q_type,
                q_score=question_data.q_score,
                hidden=question_data.hidden,
                image_path=question_data.image_path if question_data.image_path else None,
                test_id=self._practical_id
            )

        else:
            question_orm = self._repository.create_exam_question(
                q_text=question_data.q_text,
                q_number=question_data.q_number,
                q_type=question_data.q_type,
                q_score=question_data.q_score,
                hidden=question_data.hidden,
                image_path=question_data.image_path if question_data.image_path else None,
                exam_id=self._practical_id
            )

        return question_orm

    def create_answers(self, question_id: int, answers_data: List[AnswerBase]):
        answers = []

        if self._mode == "test":
            for answer in answers_data:
                answer_orm = self._repository.create_test_answer(
                    question_id=question_id,
                    a_text=answer.a_text,
                    is_correct=answer.is_correct,
                    image_path=answer.image_path if answer.image_path else None
                )

                answers.append(AnswerResponse.from_orm(answer_orm))

        else:
            for answer in answers_data:
                answer_orm = self._repository.create_exam_answer(
                    question_id=question_id,
                    a_text=answer.a_text,
                    is_correct=answer.is_correct,
                    image_path=answer.image_path if answer.image_path else None
                )

                answers.append(AnswerResponse.from_orm(answer_orm))

        return answers

    def create_matching(self, question_id: int, answers_data: List[MatchingBase]):
        left = []
        right = []
        answers = []

        if self._mode == "test":
            for answer in answers_data:
                left_orm, right_orm = self._repository.create_test_matching(
                    left_text=answer.left_text,
                    right_text=answer.right_text,
                    question_id=question_id
                )

                left_item = MatchingItem(id=left_orm.id, value=left_orm.text)
                left.append(left_item)

                right_item = MatchingItem(id=right_orm.id, value=right_orm.text)
                right.append(right_item)

        else:
            for answer in answers_data:
                left_orm, right_orm = self._repository.create_exam_matching(
                    left_text=answer.left_text,
                    right_text=answer.right_text,
                    question_id=question_id
                )

                left_item = MatchingItem(id=left_orm.id, value=left_orm.text)
                left.append(left_item)

                right_item = MatchingItem(id=right_orm.id, value=right_orm.text)
                right.append(right_item)

        answers.append(MatchingResponse(left=left, right=right))
        return answers

    def create_response_for_question(self, question, answers):
        question_response = QuestionResponse(
            q_id=question.id,
            q_text=question.q_text,
            q_number=question.q_number,
            q_score=question.q_score,
            q_type=question.q_type,
            hidden=question.hidden,
            image_path=question.image_path,
            answers=answers
        )

        self.result.append(question_response)

    def start_creating(self):
        self.init_repository()

        for question_data in self._question_data:
            question_orm = self.create_question(question_data=question_data)

            if question_data.q_type != QuestionTypeOption.matching.value:
                answers = self.create_answers(question_id=question_orm.id, answers_data=question_data.answers)
            else:
                answers = self.create_matching(question_id=question_orm.id, answers_data=question_data.answers)

            self.create_response_for_question(question=question_orm, answers=answers)

        return QuestionListResponse(questions=self.result)
