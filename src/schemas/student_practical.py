from typing import List, Optional, Union

from pydantic import BaseModel, ConfigDict, PositiveInt, model_validator
from typing_extensions import Self

from src.enums import QuestionTypeOption


class StudentAnswerBase(BaseModel):
    q_id: PositiveInt
    q_type: QuestionTypeOption


class StudentAnswer(StudentAnswerBase):
    a_id: int


class StudentAnswers(StudentAnswerBase):
    a_ids: List[int]


class StudentMatching(BaseModel):
    left_id: int
    right_id: int


class StudentMatchingList(StudentAnswerBase):
    matching: List[StudentMatching]


class StudentPractical(BaseModel):
    lesson_id: PositiveInt
    student_answers: List[Union[StudentAnswer, StudentAnswers, StudentMatchingList]]


class SubmitStudentPractical(BaseModel):
    attempt_id: PositiveInt
    student_id: PositiveInt
    lesson_id: PositiveInt


class NewAttempt(BaseModel):
    attempt_number: PositiveInt
    attempt_score: Optional[int] = None
    student_id: PositiveInt


class ExamNewAttempt(NewAttempt):
    exam_id: PositiveInt


class TestNewAttempt(NewAttempt):
    test_id: PositiveInt


class StudentAnswerBase(BaseModel):
    score: int | float
    question_id: PositiveInt
    question_type: QuestionTypeOption
    student_attempt_id: PositiveInt


class StudentAnswerDetail(StudentAnswerBase):
    answer_id: PositiveInt


class StudentAnswersDetail(StudentAnswerBase):
    answer_ids: List[PositiveInt]


class StudentMatchingDetail(StudentAnswerBase):
    left_id: PositiveInt
    right_id: PositiveInt


class ExamAttemptResponse(ExamNewAttempt):
    id: PositiveInt

    model_config = ConfigDict(from_attributes=True)


class ExamResponse(ExamAttemptResponse):
    message: str = ""

    @model_validator(mode='after')
    def set_message(self) -> Self:
        self.message = f"Your exam score {self.attempt_score}"
        return self


class TestAttemptResponse(TestNewAttempt):
    id: PositiveInt

    model_config = ConfigDict(from_attributes=True)


class TestResponse(TestAttemptResponse):
    message: str = ""

    @model_validator(mode='after')
    def set_message(self) -> Self:
        self.message = f"Your test score {self.attempt_score}"
        return self
