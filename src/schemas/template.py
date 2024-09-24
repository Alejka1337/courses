from pydantic import BaseModel, ConfigDict, PositiveInt

from src.enums import LessonTemplateType
from src.schemas.practical import QuestionBase, QuestionResponse
from src.schemas.lecture import LectureAttributeCreate, LectureAttributeResponse


class CreateLectureTemplate(BaseModel):
    title: str
    type: LessonTemplateType = LessonTemplateType.lecture
    template_data: list[LectureAttributeCreate]

    model_config = ConfigDict(from_attributes=True)


class CreatePracticalTemplate(BaseModel):
    title: str
    type: LessonTemplateType = LessonTemplateType.practical
    template_data: list[QuestionBase]

    model_config = ConfigDict(from_attributes=True)


class TemplateMessageResponse(BaseModel):
    template_id: PositiveInt
    message: str = "Template have been saved"


class DeleteTemplateMessageResponse(BaseModel):
    message: str = "Template have been deleted"


class TemplateBaseResponse(BaseModel):
    id: PositiveInt
    title: str
    type: LessonTemplateType

    model_config = ConfigDict(from_attributes=True)


class LectureTemplateResponse(TemplateBaseResponse):
    lecture_template: list[LectureAttributeResponse]


class PracticalTemplateResponse(TemplateBaseResponse):
    practical_template: list[QuestionResponse]
