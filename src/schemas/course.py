from typing import List, Optional

from pydantic import BaseModel, PositiveFloat, PositiveInt


class CourseIconCreate(BaseModel):
    icon_path: str
    icon_number: PositiveInt
    icon_text: str
    icon_title: str


class CourseIconUpdate(BaseModel):
    icon_path: Optional[str]
    icon_number: Optional[PositiveInt]
    icon_text: Optional[str]
    icon_title: Optional[str]


class CourseIconsCreate(BaseModel):
    icons: Optional[List[CourseIconCreate]]


class CourseCreate(BaseModel):
    title: str
    image_path: Optional[str]
    price: PositiveFloat
    old_price: Optional[PositiveFloat]
    category_id: PositiveInt
    intro_text: str
    skills_text: str
    about_text: str
    c_type: Optional[str]
    c_duration: Optional[str]
    c_award: Optional[str]
    c_language: Optional[str]
    c_level: Optional[str]
    c_access: Optional[str]


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


class CourseUpdateResponse(BaseModel):
    title: str
    image_path: str
    price: float
    old_price: Optional[float] = None
    category_id: int
    intro_text: str
    skills_text: str
    about_text: str
    c_type: str
    c_duration: str
    c_award: str
    c_language: str
    c_level: str
    c_access: str
    quantity_lecture: Optional[int] = None
    quantity_test: Optional[int] = None
    is_published: bool

    class Config:
        orm_mode = True