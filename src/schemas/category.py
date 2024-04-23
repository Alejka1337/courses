from typing import Optional, Union

from pydantic import BaseModel


class CategoryCreate(BaseModel):
    title: str
    description: str
    image_path: Optional[str]


class CategoryUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str]
    image_path: Optional[str]
    discount: Optional[int]


class CategoryOut(BaseModel):
    id: int
    title: str
    description: str
    image_path: str = None
    discount: int
