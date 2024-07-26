from typing import Optional

from pydantic import BaseModel, PositiveInt


class CategoryCreate(BaseModel):
    title: str
    description: str
    image_path: Optional[str] = None


class CategoryUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str]
    image_path: Optional[str]
    discount: Optional[PositiveInt]


class CategoryOut(BaseModel):
    id: int
    title: str
    description: str
    image_path: str = None
    discount: PositiveInt
