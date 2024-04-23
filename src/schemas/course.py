from typing import List, Optional

from pydantic import BaseModel


class CourseIconCreate(BaseModel):
    icon_path: str
    icon_number: int
    icon_text: str
    icon_title: str


class CourseIconUpdate(BaseModel):
    icon_path: Optional[str]
    icon_number: Optional[int]
    icon_text: Optional[str]
    icon_title: Optional[str]


class CourseIconsCreate(BaseModel):
    icons: Optional[List[CourseIconCreate]]


class CourseCreate(BaseModel):
    title: str
    image_path: Optional[str]
    price: float
    old_price: Optional[float]
    category_id: int
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
    title: Optional[str]
    image_path: Optional[str]
    price: Optional[float]
    old_price: Optional[float]
    category_id: Optional[int]
    intro_text: Optional[str]
    skills_text: Optional[str]
    about_text: Optional[str]
    c_type: Optional[str]
    c_duration: Optional[str]
    c_award: Optional[str]
    c_language: Optional[str]
    c_level: Optional[str]
    c_access: Optional[str]
