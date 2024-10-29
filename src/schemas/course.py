from typing import List, Optional, Union

from pydantic import BaseModel, ConfigDict, PositiveFloat, PositiveInt

from src.schemas.lesson import LessonAuthResponse, LessonDetailResponse, LessonResponse


class CourseIconCreate(BaseModel):
    icon_path: str
    icon_number: PositiveInt
    icon_text: str
    icon_title: str


class IconResponse(CourseIconCreate):
    id: PositiveInt
    course_id: PositiveInt


class CourseIconUpdate(BaseModel):
    icon_path: Optional[str] = None
    icon_number: Optional[PositiveInt] = None
    icon_text: Optional[str] = None
    icon_title: Optional[str] = None


class CourseIconsCreate(BaseModel):
    icons: Optional[List[CourseIconCreate]]


class CourseCreate(BaseModel):
    title: str
    image_path: Optional[str] = None
    price: PositiveFloat
    old_price: Optional[PositiveFloat] = None
    category_id: PositiveInt
    intro_text: str
    skills_text: str
    about_text: str
    c_type: Optional[str] = None
    c_duration: Optional[str] = None
    c_award: Optional[str] = None
    c_language: Optional[str] = None
    c_level: Optional[str] = None
    c_access: Optional[str] = None


class CourseUpdate(BaseModel):
    title: Optional[str] = None
    image_path: Optional[str] = None
    price: Optional[PositiveFloat] = None
    old_price: Optional[PositiveFloat] = None
    category_id: Optional[PositiveInt] = None
    intro_text: Optional[str] = None
    skills_text: Optional[str] = None
    about_text: Optional[str] = None
    c_type: Optional[str] = None
    c_duration: Optional[str] = None
    c_award: Optional[str] = None
    c_language: Optional[str] = None
    c_level: Optional[str] = None
    c_access: Optional[str] = None


class CourseResponse(BaseModel):
    id: PositiveInt
    title: str
    image_path: Optional[str] = None
    price: float
    old_price: Optional[float] = None
    category_id: PositiveInt
    intro_text: str
    skills_text: str
    about_text: str
    c_type: str
    c_duration: str
    c_award: str
    c_language: str
    c_level: str
    c_access: str
    quantity_lecture: Optional[PositiveInt] = None
    quantity_test: Optional[PositiveInt] = None
    is_published: bool

    model_config = ConfigDict(from_attributes=True)


class DeleteCourseResponse(BaseModel):
    message: str = "Course has been deleted"


class ImageUploadedResponse(BaseModel):
    image_path: str


class IconUploadedResponse(BaseModel):
    icon_path: str


class AttachedIconResponse(BaseModel):
    message: str = "Successful attached"


class PublishCourseResponse(BaseModel):
    message: str
    result: bool


class CourseDetailResponse(CourseResponse):
    icons: List[IconResponse]
    lessons: List[Union[LessonResponse, LessonDetailResponse, LessonAuthResponse]]

    bought: Optional[bool] = None
    grade: Optional[int] = None
    progress: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

    def model_dump(self, *args, **kwargs):
        return super().model_dump(exclude_none=True)


class CourseCart(BaseModel):
    student_id: int
    payment_items: list[int]
