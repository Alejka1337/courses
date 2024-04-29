from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from src.celery import create_lecture_audio, update_student_course_progress
from src.crud.lecture import create_attribute_base_db, create_attribute_file_db, create_attribute_link_db
from src.crud.lesson import select_lesson_by_id_db, select_lesson_by_number_and_course_id_db
from src.crud.student_lesson import confirm_student_lecture_db, select_student_lesson_db, set_active_student_lesson_db
from src.enums import UserType
from src.models import UserOrm
from src.schemas.lecture import LectureAttributeBase, LectureAttributeCreate, LectureFileBase
from src.session import get_db
from src.utils.get_user import get_current_user
from src.utils.save_files import save_lesson_image

router = APIRouter(prefix="/lecture")


@router.post("/upload/file")
async def upload_lecture_file(
        file: UploadFile = File(...),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        file_path = save_lesson_image(file)
        return {"filename": file.filename, "file_path": file_path, "file_size": file.size}
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")


@router.post("/create/text")
async def create_text_attribute(
        lecture_id: int,
        data: LectureAttributeBase,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        create_attribute_base_db(
            db=db,
            lecture_id=lecture_id,
            a_type=data.a_type,
            a_title=data.a_title,
            a_number=data.a_number,
            a_text=data.a_text,
            hidden=data.hidden
        )

        create_lecture_audio.delay(lecture_id)
        return {"message": "Attribute have been saved"}
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")


@router.post("/create/file")
async def create_file_attribute(
        lecture_id: int,
        data: LectureFileBase,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        attribute = create_attribute_base_db(
            db=db,
            lecture_id=lecture_id,
            a_type=data.a_type,
            a_title=data.a_title,
            a_number=data.a_number,
            a_text=data.a_text,
            hidden=data.hidden
        )

        create_attribute_file_db(
            db=db,
            attribute_id=attribute.id,
            filename=data.filename,
            file_path=data.file_path,
            file_size=data.file_size,
            file_description=data.file_description,
            download_allowed=data.download_allowed
        )
        create_lecture_audio.delay(lecture_id)
        return {"message": "Attribute have been saved"}
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")


@router.post("/create/files")
async def create_files_attribute(
        lecture_id: int,
        data: LectureAttributeCreate,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        attribute = create_attribute_base_db(
            db=db,
            lecture_id=lecture_id,
            a_type=data.a_type,
            a_title=data.a_title,
            a_number=data.a_number,
            a_text=data.a_text,
            hidden=data.hidden
        )

        for file_item in data.files:
            create_attribute_file_db(
                db=db,
                attribute_id=attribute.id,
                filename=file_item.filename,
                file_path=file_item.file_path,
                file_size=file_item.file_size,
                file_description=file_item.file_description,
                download_allowed=file_item.download_allowed
            )

        create_lecture_audio.delay(lecture_id)
        return {"message": "Attribute have been saved"}

    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")


@router.post("/create/images")
async def create_images_attribute(
        lecture_id: int,
        data: LectureAttributeCreate,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        attribute = create_attribute_base_db(
            db=db,
            lecture_id=lecture_id,
            a_type=data.a_type,
            a_title=data.a_title,
            a_number=data.a_number,
            a_text=data.a_text,
            hidden=data.hidden
        )

        for image_item in data.files:
            create_attribute_file_db(
                db=db,
                attribute_id=attribute.id,
                filename=image_item.filename,
                file_path=image_item.file_path,
                file_size=image_item.file_size,
                file_description=image_item.file_description,
                download_allowed=image_item.download_allowed
            )

        create_lecture_audio.delay(lecture_id)
        return {"message": "Attribute have been saved"}

    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")


@router.post("/create/link")
async def create_link_attribute(
        lecture_id: int,
        data: LectureAttributeCreate,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        attribute = create_attribute_base_db(
            db=db,
            lecture_id=lecture_id,
            a_type=data.a_type,
            a_title=data.a_title,
            a_number=data.a_number,
            a_text=data.a_text,
            hidden=data.hidden
        )

        for link_item in data.links:
            create_attribute_link_db(
                db=db,
                attribute_id=attribute.id,
                link=link_item.link,
                anchor=link_item.anchor
            )

        create_lecture_audio.delay(lecture_id)
        return {"message": "Attribute have been saved"}

    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")


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

        update_student_course_progress.delay(student_id=user.student.id, lesson_id=lesson_id)
        return {"message": "Lecture successfully confirm"}
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
