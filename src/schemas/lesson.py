from pydantic import BaseModel, PositiveInt

from src.enums import LessonType


class LessonCreate(BaseModel):
    type: LessonType
    number: PositiveInt
    title: str
    description: str
    scheduled_time: PositiveInt
    course_id: PositiveInt
    image_path: str
