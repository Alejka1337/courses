from datetime import date

from typing import List, Optional, Any

from pydantic import BaseModel, PositiveInt, ConfigDict

from src.enums import InstructionType


class InstructionFileBase(BaseModel):
    file_type: str
    file_name: str
    file_path: str
    file_size: PositiveInt


class InstructionCreate(BaseModel):
    name: str
    type: InstructionType
    title: str
    text: str
    category_id: Optional[PositiveInt] = None
    files: Optional[List[InstructionFileBase]] = None


class InstructionUpdate(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    text: Optional[str] = None
    category_id: Optional[PositiveInt] = None
    files: Optional[List[InstructionFileBase]] = None


class InstructionResponse(InstructionCreate):
    id: PositiveInt
    last_update: date

    model_config = ConfigDict(from_attributes=True)

    def model_dump(self, **kwargs) -> dict[str, Any]:
        return super().model_dump(**kwargs, exclude={"files"}, exclude_none=True)


class InstructionFileDetail(InstructionFileBase):
    id: PositiveInt
    instruction_id: PositiveInt


class InstructionDetailResponse(InstructionCreate):
    id: PositiveInt
    last_update: date
    files: List[InstructionFileDetail]

    model_config = ConfigDict(from_attributes=True)


class InstructionDeleteResponse(BaseModel):
    message: str = "Instruction successfully deleted"
