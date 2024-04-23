from typing import List, Union

from pydantic import BaseModel

from src.enums import QuestionTypeOption


class StudentAnswerBase(BaseModel):
    q_id: int
    q_type: QuestionTypeOption


class StudentTestAnswer(StudentAnswerBase):
    a_id: int


class StudentTestAnswers(StudentAnswerBase):
    a_ids: List[int]


class StudentMatchingBase(BaseModel):
    left_id: int
    right_id: int


class StudentTestMatching(StudentAnswerBase):
    matching: List[StudentMatchingBase]


class StudentTest(BaseModel):
    lesson_id: int
    student_answers: List[Union[StudentTestAnswer, StudentTestAnswers, StudentTestMatching]]


class SubmitStudentTest(BaseModel):
    attempt_id: int
    student_id: int
    lesson_id: int
