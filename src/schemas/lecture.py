from typing import List, Optional, Any
from typing_extensions import Self

from pydantic import BaseModel, PositiveInt, FilePath

from src.enums import LectureAttributeType


class LectureAttributeBase(BaseModel):
    a_type: LectureAttributeType
    a_title: str
    a_number: PositiveInt
    a_text: Optional[str] = None
    hidden: Optional[bool] = False


class LectureFileBase(LectureAttributeBase):
    filename: str
    file_path: FilePath
    file_size: PositiveInt
    file_description: Optional[str] = None
    download_allowed: Optional[bool] = False


class FileBase(BaseModel):
    filename: str
    file_path: FilePath
    file_size: PositiveInt
    file_description: Optional[str] = None
    download_allowed: Optional[bool] = False


class FileResponse(FileBase):
    file_id: PositiveInt

    @classmethod
    def from_orm(cls, obj: Any) -> Self:
        return cls(
            file_id=obj.id,
            filename=obj.filename,
            file_path=obj.file_path,
            file_size=obj.file_size,
            file_description=obj.file_description,
            download_allowed=obj.download_allowed
        )


class LinkBase(BaseModel):
    link: str
    anchor: Optional[str] = None


class LinkResponse(LinkBase):
    link_id: PositiveInt

    @classmethod
    def from_orm(cls, obj: Any) -> Self:
        return cls(
            link_id=obj.id,
            link=obj.link,
            anchor=obj.anchor
        )


class LectureAttributeCreate(LectureAttributeBase):
    files: Optional[List[FileBase]] = None
    links: Optional[List[LinkBase]] = None


class LectureFileUpdate(BaseModel):
    filename: Optional[str] = None
    file_path: Optional[FilePath] = None
    file_size: Optional[int] = None
    file_description: Optional[str] = None
    download_allowed: Optional[bool] = None


class LectureLinkUpdate(BaseModel):
    link: Optional[str] = None
    anchor: Optional[str] = None


class LectureAttributeBaseUpdate(BaseModel):
    a_title: Optional[str] = None
    a_number: Optional[PositiveInt] = None
    a_text: Optional[str] = None
    hidden: Optional[bool] = None


class LectureAttributeUpdate(LectureAttributeBaseUpdate):
    files: Optional[List[LectureFileUpdate]] = None
    links: Optional[List[LectureLinkUpdate]] = None


class LectureFileAttributeUpdate(LectureAttributeBaseUpdate):
    filename: Optional[str] = None
    file_path: Optional[FilePath] = None
    file_size: Optional[PositiveInt] = None
    file_description: Optional[str] = None
    download_allowed: Optional[bool] = None


class LectureAttributeResponse(LectureAttributeBase):
    a_id: PositiveInt
    files: List[FileResponse] = None
    links: List[LinkResponse] = None
