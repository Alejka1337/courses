from typing import Any, List, Optional, Union

from pydantic import BaseModel, PositiveInt
from typing_extensions import Self

from src.enums import QuestionTypeOption


class TestAnswerBase(BaseModel):
    a_text: str
    is_correct: bool
    image_path: Optional[str] = None


class TestAnswerResponse(TestAnswerBase):
    a_id: PositiveInt

    @classmethod
    def from_orm(cls, obj: Any) -> Self:
        return cls(
            a_id=obj.id,
            a_text=obj.a_text,
            is_correct=obj.is_correct,
            image_path=obj.image_path
        )


class MatchingItem(BaseModel):
    id: PositiveInt
    value: str


class MatchingLeft(BaseModel):
    left: List[MatchingItem]


class MatchingRight(BaseModel):
    right: List[MatchingItem]


class TestMatchingBase(BaseModel):
    right_text: str
    left_text: str


class TestQuestionBase(BaseModel):
    q_text: str
    q_number: PositiveInt
    q_score: PositiveInt
    q_type: QuestionTypeOption
    hidden: Optional[bool] = False
    image_path: Optional[str] = None
    answers: List[Union[TestAnswerBase, TestMatchingBase]]


class ExamQuestionBase(TestQuestionBase):
    pass


class TestConfigUpdate(BaseModel):
    score: Optional[PositiveInt] = None
    attempts: Optional[PositiveInt] = None


class ExamConfigUpdate(TestConfigUpdate):
    timer: Optional[int] = None
    min_score: Optional[PositiveInt] = None


class TestQuestionUpdate(BaseModel):
    q_text: Optional[str] = None
    q_number: Optional[PositiveInt] = None
    q_score: Optional[PositiveInt] = None
    hidden: Optional[bool] = False
    image_path: Optional[str] = None


class ExamQuestionUpdate(TestQuestionUpdate):
    pass


class TestAnswerUpdate(BaseModel):
    a_text: Optional[str] = None
    is_correct: Optional[bool] = False
    image_path: Optional[str] = None


class ExamAnswerUpdate(TestAnswerUpdate):
    pass


class TestMatchingUpdate(BaseModel):
    right_text: Optional[str] = None
    left_text: Optional[str] = None


class ExamMatchingUpdate(TestMatchingUpdate):
    pass


class TestAnswerAdd(TestAnswerBase):
    question_id: PositiveInt


class ExamAnswerAdd(TestAnswerAdd):
    pass


class TestMatchingAdd(TestMatchingBase):
    question_id: PositiveInt


class ExamMatchingAdd(TestMatchingAdd):
    pass


class TestQuestionResponse(BaseModel):
    q_id: PositiveInt
    q_text: str
    q_number: PositiveInt
    q_score: PositiveInt
    q_type: QuestionTypeOption
    hidden: Optional[bool] = False
    image_path: Optional[str] = None
    answers: List[Union[TestAnswerResponse, Union[MatchingLeft, MatchingRight]]]


class QuestionListResponse(BaseModel):
    questions: List[TestQuestionResponse]
