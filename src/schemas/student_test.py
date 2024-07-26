from typing import List, Union

from pydantic import BaseModel, PositiveInt

from src.enums import QuestionTypeOption


class StudentAnswerBase(BaseModel):
    q_id: PositiveInt
    q_type: QuestionTypeOption


class StudentTestAnswer(StudentAnswerBase):
    a_id: PositiveInt


class StudentTestAnswers(StudentAnswerBase):
    a_ids: List[PositiveInt]


class StudentMatchingBase(BaseModel):
    left_id: PositiveInt
    right_id: PositiveInt


class StudentTestMatching(StudentAnswerBase):
    matching: List[StudentMatchingBase]


class StudentTest(BaseModel):
    lesson_id: PositiveInt
    student_answers: List[Union[StudentTestAnswer, StudentTestAnswers, StudentTestMatching]]


class SubmitStudentTest(BaseModel):
    attempt_id: PositiveInt
    student_id: PositiveInt
    lesson_id: PositiveInt
