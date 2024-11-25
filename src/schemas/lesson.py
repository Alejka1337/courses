from typing import Optional

from pydantic import BaseModel, PositiveInt

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


class LessonAuthResponse(LessonDetailResponse):
    score: Optional[int] = None
    status: Optional[LessonStatus] = None


class LessonUpdate(BaseModel):
    number: Optional[PositiveInt] = None
    title: Optional[str] = None
    description: Optional[str] = None
    scheduled_time: Optional[PositiveInt] = None
    image_path: Optional[str] = None
