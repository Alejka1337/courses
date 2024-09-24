from typing import Optional

from pydantic import BaseModel, PositiveInt, ConfigDict


class CreateFolder(BaseModel):
    name: str
    student_id: PositiveInt
    parent_id: Optional[PositiveInt] = None


class CreateNote(BaseModel):
    title: str
    text: str
    folder_id: PositiveInt
    lecture_id: PositiveInt


class CreateFolderResponse(CreateFolder):
    id: PositiveInt

    model_config = ConfigDict(from_attributes=True)


class CreateNoteResponse(CreateNote):
    id: PositiveInt

    model_config = ConfigDict(from_attributes=True)
