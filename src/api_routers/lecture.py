from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.celery import celery_tasks
from src.crud.lecture import LectureRepository
from src.crud.lesson import select_lesson_by_id_db, select_lesson_by_number_and_course_id_db
from src.crud.student_lesson import confirm_student_lecture_db, select_student_lesson_db, set_active_student_lesson_db
from src.enums import UserType
from src.models import UserOrm
from src.schemas.lecture import (LectureAttributeBase, LectureAttributeBaseUpdate, LectureAttributeCreate,
                                 LectureAttributeUpdate, LectureFileAttributeUpdate, LectureFileBase,
                                 LectureAttributeResponse, FileResponse, LinkResponse)
from src.session import get_db
from src.utils.exceptions import PermissionDeniedException
from src.utils.get_user import get_current_user

router = APIRouter(prefix="/lecture")


@router.post("/create/text", response_model=LectureAttributeResponse)
async def create_text_attribute(
        lecture_id: int,
        data: LectureAttributeBase,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        repository = LectureRepository(db=db)
        new_attr = repository.create_attribute_base(
            lecture_id=lecture_id,
            a_type=data.a_type,
            a_title=data.a_title,
            a_number=data.a_number,
            a_text=data.a_text,
            hidden=data.hidden
        )

        response = LectureAttributeResponse(
            a_id=new_attr.id,
            a_type=new_attr.a_type,
            a_title=new_attr.a_title,
            a_number=new_attr.a_number,
            a_text=new_attr.a_text,
            hidden=new_attr.hidden,
            files=[],
            links=[]
        )

        celery_tasks.create_lecture_audio.delay(lecture_id)
        return response
    else:
        raise PermissionDeniedException()


@router.patch("/update/text")
async def update_text_attribute(
        attr_id: int,
        data: LectureAttributeBaseUpdate,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        repository = LectureRepository(db=db)
        repository.update_lecture_attr(
            attr_id=attr_id,
            a_text=data.a_text,
            a_title=data.a_title,
            a_number=data.a_number,
            hidden=data.hidden
        )
        return {"message": "Attribute successfully updated"}

    else:
        raise PermissionDeniedException()


@router.post("/create/file", response_model=LectureAttributeResponse)
async def create_file_attribute(
        lecture_id: int,
        data: LectureFileBase,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        repository = LectureRepository(db=db)
        attribute = repository.create_attribute_base(
            lecture_id=lecture_id,
            a_type=data.a_type,
            a_title=data.a_title,
            a_number=data.a_number,
            a_text=data.a_text,
            hidden=data.hidden
        )

        file_record = repository.create_attribute_file(
            attribute_id=attribute.id,
            filename=data.filename,
            file_path=str(data.file_path),
            file_size=data.file_size,
            file_description=data.file_description,
            download_allowed=data.download_allowed
        )

        files = []
        files.append(FileResponse.from_orm(file_record))

        response = LectureAttributeResponse(
            a_id=attribute.id,
            a_type=attribute.a_type,
            a_title=attribute.a_title,
            a_number=attribute.a_number,
            a_text=attribute.a_text,
            hidden=attribute.hidden,
            files=files,
            links=[]
        )

        celery_tasks.create_lecture_audio.delay(lecture_id)
        return response
    else:
        raise PermissionDeniedException()


@router.patch("/update/file")
async def update_file_attribute(
        attr_id: int,
        data: LectureFileAttributeUpdate,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        repository = LectureRepository(db=db)
        repository.update_lecture_file_attr(attr_id=attr_id, data=data)
        return {"message": "Attribute successfully updated"}
    else:
        raise PermissionDeniedException()


@router.post("/create/files", response_model=LectureAttributeResponse)
async def create_files_attribute(
        lecture_id: int,
        data: LectureAttributeCreate,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        repository = LectureRepository(db=db)
        attribute = repository.create_attribute_base(
            lecture_id=lecture_id,
            a_type=data.a_type,
            a_title=data.a_title,
            a_number=data.a_number,
            a_text=data.a_text,
            hidden=data.hidden
        )

        files = []

        for file_item in data.files:
            file_record = repository.create_attribute_file(
                attribute_id=attribute.id,
                filename=file_item.filename,
                file_path=str(file_item.file_path),
                file_size=file_item.file_size,
                file_description=file_item.file_description,
                download_allowed=file_item.download_allowed
            )

            files.append(FileResponse.from_orm(file_record))

        response = LectureAttributeResponse(
            a_id=attribute.id,
            a_type=attribute.a_type,
            a_title=attribute.a_title,
            a_number=attribute.a_number,
            a_text=attribute.a_text,
            hidden=attribute.hidden,
            files=files,
            links=[]
        )

        celery_tasks.create_lecture_audio.delay(lecture_id)
        return response

    else:
        raise PermissionDeniedException()


@router.patch("/update/files")
async def update_files_attribute(
        attr_id: int,
        data: LectureAttributeUpdate,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        repository = LectureRepository(db=db)
        repository.update_lecture_files_attr(attr_id=attr_id, data=data)

    else:
        raise PermissionDeniedException()


@router.post("/create/images", response_model=LectureAttributeResponse)
async def create_images_attribute(
        lecture_id: int,
        data: LectureAttributeCreate,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        repository = LectureRepository(db=db)
        attribute = repository.create_attribute_base(
            lecture_id=lecture_id,
            a_type=data.a_type,
            a_title=data.a_title,
            a_number=data.a_number,
            a_text=data.a_text,
            hidden=data.hidden
        )

        files = []

        for image_item in data.files:
            file_record = repository.create_attribute_file(
                attribute_id=attribute.id,
                filename=image_item.filename,
                file_path=str(image_item.file_path),
                file_size=image_item.file_size,
                file_description=image_item.file_description,
                download_allowed=image_item.download_allowed
            )

            files.append(FileResponse.from_orm(file_record))

        response = LectureAttributeResponse(
            a_id=attribute.id,
            a_type=attribute.a_type,
            a_title=attribute.a_title,
            a_number=attribute.a_number,
            a_text=attribute.a_text,
            hidden=attribute.hidden,
            files=files,
            links=[]
        )

        celery_tasks.create_lecture_audio.delay(lecture_id)
        return response

    else:
        raise PermissionDeniedException()


@router.patch("/update/images")
async def update_images_attribute(
        attr_id: int,
        data: LectureAttributeUpdate,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        repository = LectureRepository(db=db)
        repository.update_lecture_files_attr(attr_id=attr_id, data=data)

    else:
        raise PermissionDeniedException()


@router.post("/create/link", response_model=LectureAttributeResponse)
async def create_link_attribute(
        lecture_id: int,
        data: LectureAttributeCreate,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        repository = LectureRepository(db=db)
        attribute = repository.create_attribute_base(
            lecture_id=lecture_id,
            a_type=data.a_type,
            a_title=data.a_title,
            a_number=data.a_number,
            a_text=data.a_text,
            hidden=data.hidden
        )

        links = []

        for link_item in data.links:
            link_record = repository.create_attribute_link(
                attribute_id=attribute.id,
                link=link_item.link,
                anchor=link_item.anchor
            )

            links.append(LinkResponse.from_orm(link_record))

        response = LectureAttributeResponse(
            a_id=attribute.id,
            a_type=attribute.a_type,
            a_title=attribute.a_title,
            a_number=attribute.a_number,
            a_text=attribute.a_text,
            hidden=attribute.hidden,
            files=[],
            links=links
        )

        celery_tasks.create_lecture_audio.delay(lecture_id)
        return response

    else:
        raise PermissionDeniedException()


@router.patch("/update/link")
async def update_link_attribute(
        attr_id: int,
        data: LectureAttributeUpdate,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        repository = LectureRepository(db=db)
        repository.update_lecture_links_attr(attr_id=attr_id, data=data)

    else:
        raise PermissionDeniedException()


@router.delete("/delete/attr")
async def delete_attribute(
        attr_id: int,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        repository = LectureRepository(db=db)
        repository.delete_lecture_attr(attr_id=attr_id)
        return {"message": "Successfully deleted"}
    else:
        raise PermissionDeniedException()


@router.post("/confirm")
async def confirm_lecture(
        lesson_id: int,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.student.value:
        lesson = select_lesson_by_id_db(db=db, lesson_id=lesson_id)
        student_lesson = select_student_lesson_db(db=db, lesson_id=lesson_id, student_id=user.student.id)
        confirm_student_lecture_db(db=db, student_lesson=student_lesson)

        number = lesson.number + 1
        next_lesson = select_lesson_by_number_and_course_id_db(db=db, number=number, course_id=lesson.course_id)
        next_student_lesson = select_student_lesson_db(db=db, lesson_id=next_lesson.id, student_id=user.student.id)
        set_active_student_lesson_db(db=db, student_lesson=next_student_lesson)

        celery_tasks.update_student_course_progress.delay(student_id=user.student.id, lesson_id=lesson_id)
        return {"message": "Lecture successfully confirm"}
    else:
        raise PermissionDeniedException()
