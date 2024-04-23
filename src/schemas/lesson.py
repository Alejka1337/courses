from pydantic import BaseModel

from src.enums import LessonType


class LessonCreate(BaseModel):
    type: LessonType
    number: int
    title: str
    description: str
    scheduled_time: int
    course_id: int
    image_path: str
