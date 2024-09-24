from fastapi import Depends, APIRouter, status

from sqlalchemy.orm import Session

from src.session import get_db
from src.utils.get_user import get_current_user
from src.models import UserOrm
from src.enums import LessonTemplateType
from src.utils.exceptions import PermissionDeniedException
from src.utils.template_serialize import (
    serialize_lecture_response,
    serialize_practical_response
)
from src.crud.template import TemplateRepository
from src.schemas.template import (
    CreateLectureTemplate,
    CreatePracticalTemplate,
    TemplateMessageResponse,
    TemplateBaseResponse,
    LectureTemplateResponse,
    PracticalTemplateResponse,
    DeleteTemplateMessageResponse
)

router = APIRouter(prefix="/template")


@router.post("/create/lecture", status_code=status.HTTP_201_CREATED, response_model=TemplateMessageResponse)
async def create_lecture_template(
        data: CreateLectureTemplate,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.is_moder:
        repository = TemplateRepository(db)
        repository.init_lecture_model()
        new_template = repository.create_new_template(title=data.title, t_type=data.type)
        repository.create_lecture_template_attrs(template_data=data.template_data, template_id=new_template.id)
        return TemplateMessageResponse(template_id=new_template.id)

    raise PermissionDeniedException()


@router.post("/create/practical", status_code=status.HTTP_201_CREATED, response_model=TemplateMessageResponse)
async def create_practical_template(
        data: CreatePracticalTemplate,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.is_moder:
        repository = TemplateRepository(db)
        repository.init_practical_model()
        new_template = repository.create_new_template(title=data.title, t_type=data.type)
        repository.create_practical_template_question(template_data=data.template_data, template_id=new_template.id)
        return TemplateMessageResponse(template_id=new_template.id)

    raise PermissionDeniedException()


@router.get("/get/all", response_model=list[TemplateBaseResponse])
async def get_all_templates(
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.is_moder:
        repository = TemplateRepository(db)
        return repository.select_templates()

    raise PermissionDeniedException()


@router.get("/get/practical/{template_id}", response_model=PracticalTemplateResponse)
async def get_template_by_id(
        template_id: int,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.is_moder:
        repository = TemplateRepository(db)
        template_db_data = repository.select_template_by_id(
            template_id=template_id,
            t_type=LessonTemplateType.practical.value
        )

        return serialize_practical_response(template_db_data=template_db_data)

    raise PermissionDeniedException()


@router.get("/get/lecture/{template_id}", response_model=LectureTemplateResponse)
async def get_template_by_id(
        template_id: int,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.is_moder:
        repository = TemplateRepository(db)
        template_db_data = repository.select_template_by_id(
            template_id=template_id,
            t_type=LessonTemplateType.lecture.value
        )

        return serialize_lecture_response(template_db_data=template_db_data)

    raise PermissionDeniedException()


@router.delete("/delete/{template_id}", response_model=DeleteTemplateMessageResponse)
async def delete_template_by_id(
        template_id: int,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.is_moder:
        repository = TemplateRepository(db)
        repository.delete_template_by_id(template_id=template_id)
        return DeleteTemplateMessageResponse()

    raise PermissionDeniedException()
