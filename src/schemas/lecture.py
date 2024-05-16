from typing import List, Optional

from pydantic import BaseModel

from src.enums import LectureAttributeType


class LectureAttributeBase(BaseModel):
    a_type: LectureAttributeType
    a_title: str
    a_number: int
    a_text: Optional[str] = None
    hidden: Optional[bool] = False


class LectureFileBase(LectureAttributeBase):
    filename: str
    file_path: str
    file_size: int
    file_description: Optional[str] = None
    download_allowed: Optional[bool] = False


class FileBase(BaseModel):
    filename: str
    file_path: str
    file_size: int
    file_description: Optional[str] = None
    download_allowed: Optional[bool] = False


class LinkBase(BaseModel):
    link: str
    anchor: Optional[str] = None


class LectureAttributeCreate(LectureAttributeBase):
    files: Optional[List[FileBase]] = None
    links: Optional[List[LinkBase]] = None


class LectureFileUpdate(BaseModel):
    filename: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    file_description: Optional[str] = None
    download_allowed: Optional[bool] = None


class LectureLinkUpdate(BaseModel):
    link: Optional[str] = None
    anchor: Optional[str] = None


class LectureAttributeBaseUpdate(BaseModel):
    a_title: Optional[str] = None
    a_number: Optional[int] = None
    a_text: Optional[str] = None
    hidden: Optional[bool] = None


class LectureAttributeUpdate(LectureAttributeBaseUpdate):
    files: Optional[List[LectureFileUpdate]] = None
    links: Optional[List[LectureLinkUpdate]] = None


class LectureFileAttributeUpdate(LectureAttributeBaseUpdate):
    filename: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    file_description: Optional[str] = None
    download_allowed: Optional[bool] = None
