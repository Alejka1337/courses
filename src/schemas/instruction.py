from typing import List, Optional

from pydantic import BaseModel, PositiveInt

from src.enums import InstructionType


class InstructionFilesBase(BaseModel):
    file_type: str
    file_name: str
    file_path: str
    file_size: PositiveInt


class InstructionCreate(BaseModel):
    name: str
    type: InstructionType
    title: str
    text: str
    category_id: Optional[int] = None
    files: Optional[List[InstructionFilesBase]] = None


class InstructionUpdate(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    text: Optional[str] = None
    category_id: Optional[PositiveInt] = None
    files: Optional[List[InstructionFilesBase]] = None
