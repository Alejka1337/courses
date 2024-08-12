from typing import Optional

from pydantic import BaseModel, PositiveInt, ConfigDict


class CategoryCreate(BaseModel):
    title: str
    description: str
    image_path: Optional[str] = None


class CategoryUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str]
    image_path: Optional[str]
    discount: Optional[PositiveInt]


class CategoryResponse(CategoryCreate):
    id: PositiveInt
    discount: PositiveInt

    model_config = ConfigDict(from_attributes=True)


class CategoryImagePathResponse(BaseModel):
    newPath: str


class CategoryDeleteResponse(BaseModel):
    message: str = "Category have been deleted"
