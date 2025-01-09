from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, PositiveInt


class CategoryCreate(BaseModel):
    title: str
    description: str
    image_path: Optional[str] = None
    certificate_info: Optional[str] = None


class CategoryUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    image_path: Optional[str] = None
    discount: Optional[PositiveInt] = None
    certificate_info: Optional[str] = None


class CategoryResponse(CategoryCreate):
    id: PositiveInt
    discount: PositiveInt
    is_published: Optional[bool] = None
    timestamp_add: Optional[datetime] = None
    timestamp_change: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CategoryImagePathResponse(BaseModel):
    newPath: str


class CategoryDeleteResponse(BaseModel):
    message: str = "Category have been deleted"
