from typing import Optional

from pydantic import BaseModel, ConfigDict, PositiveInt, model_validator

from src.enums import LessonStatus, LessonType


class LessonCreate(BaseModel):
    type: LessonType
    number: PositiveInt
    title: str
    description: str
    scheduled_time: PositiveInt
    course_id: PositiveInt
    image_path: str


class LessonResponse(LessonCreate):
    id: PositiveInt


class LessonDetailResponse(LessonResponse):
    count_questions: Optional[int] = None

    # @model_validator(mode="after")
    # def remove_count_questions_if_not_test_or_exam(cls, instance):
    #     if instance.type not in {LessonType.test, LessonType.exam}:
    #         del instance.count_questions
    #     return instance


class LessonAuthResponse(LessonDetailResponse):
    score: Optional[int] = None
    status: Optional[LessonStatus] = None
