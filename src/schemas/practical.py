from typing import Any, List, NamedTuple, Optional, Union

from pydantic import BaseModel, PositiveInt
from typing_extensions import Self

from src.enums import QuestionTypeOption


class MatchingTuple(NamedTuple):
    left_id: PositiveInt
    left_text: str
    right_id: PositiveInt
    right_text: str


class AnswerBase(BaseModel):
    a_text: str
    is_correct: bool
    image_path: Optional[str] = None


class AnswerResponse(AnswerBase):
    a_id: PositiveInt

    @classmethod
    def from_orm(cls, obj: Any) -> Self:
        return cls(
            a_id=obj.id,
            a_text=obj.a_text,
            is_correct=obj.is_correct,
            image_path=obj.image_path
        )


class TestAnswerResponse(AnswerResponse):
    pass


class ExamAnswerResponse(AnswerResponse):
    pass


class MatchingResponseAfterAdd(BaseModel):
    left_id: PositiveInt
    left_text: str
    right_id: PositiveInt
    right_text: str

    @classmethod
    def from_orm(cls, obj: MatchingTuple):
        return cls(
            left_id=obj.left_id,
            left_text=obj.left_text,
            right_id=obj.right_id,
            right_text=obj.right_text
        )


class MatchingItem(BaseModel):
    id: PositiveInt
    value: str


class MatchingLeft(BaseModel):
    left: List[MatchingItem]


class MatchingRight(BaseModel):
    right: List[MatchingItem]


class MatchingResponse(BaseModel):
    left: List[MatchingItem]
    right: List[MatchingItem]


class MatchingBase(BaseModel):
    right_text: str
    left_text: str


class QuestionBase(BaseModel):
    q_text: str
    q_number: PositiveInt
    q_score: PositiveInt
    q_type: QuestionTypeOption
    hidden: Optional[bool] = False
    image_path: Optional[str] = None
    answers: List[Union[AnswerBase, MatchingBase]]


class TestQuestionBase(QuestionBase):
    pass


class ExamQuestionBase(QuestionBase):
    pass


class ConfigUpdate(BaseModel):
    score: Optional[PositiveInt] = None
    attempts: Optional[PositiveInt] = None


class TestConfigUpdate(ConfigUpdate):
    pass


class ExamConfigUpdate(ConfigUpdate):
    timer: Optional[int] = None
    min_score: Optional[PositiveInt] = None


class QuestionUpdate(BaseModel):
    q_text: Optional[str] = None
    q_number: Optional[PositiveInt] = None
    q_score: Optional[PositiveInt] = None
    hidden: Optional[bool] = False
    image_path: Optional[str] = None


class TestQuestionUpdate(QuestionUpdate):
    pass


class ExamQuestionUpdate(QuestionUpdate):
    pass


class AnswerUpdate(BaseModel):
    a_text: Optional[str] = None
    is_correct: Optional[bool] = False
    image_path: Optional[str] = None


class TestAnswerUpdate(AnswerUpdate):
    pass


class ExamAnswerUpdate(AnswerUpdate):
    pass


class MatchingUpdate(BaseModel):
    right_text: Optional[str] = None
    left_text: Optional[str] = None


class TestMatchingUpdate(MatchingUpdate):
    pass


class ExamMatchingUpdate(MatchingUpdate):
    pass


class AnswerAdd(AnswerBase):
    question_id: PositiveInt


class TestAnswerAdd(AnswerAdd):
    pass


class ExamAnswerAdd(AnswerAdd):
    pass


class MatchingAdd(MatchingBase):
    question_id: PositiveInt


class TestMatchingAdd(MatchingAdd):
    pass


class ExamMatchingAdd(MatchingAdd):
    pass


class QuestionResponse(BaseModel):
    q_id: PositiveInt
    q_text: str
    q_number: PositiveInt
    q_score: PositiveInt
    q_type: QuestionTypeOption
    hidden: Optional[bool] = False
    image_path: Optional[str] = None
    answers: List[Union[AnswerResponse, MatchingResponse]]


class TestQuestionResponse(QuestionResponse):
    pass


class ExamQuestionResponse(QuestionResponse):
    pass


class QuestionListResponse(BaseModel):
    questions: List[QuestionResponse]


class UpdateMessageResponse(BaseModel):
    message: str = "Successfully updated"


class DeleteMessageResponse(BaseModel):
    message: str = "Successfully deleted"
