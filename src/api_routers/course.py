from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from src.celery import add_new_course_notification
from src.crud.course import (create_course_db, create_course_icon_db, delete_course_db, select_all_courses_db,
                             select_course_by_id_db, select_courses_by_category_id_db, update_course_db,
                             update_course_icon_db)
from src.crud.lesson import check_validity_lesson
from src.enums import UserType
from src.models import UserOrm
from src.schemas.course import CourseCreate, CourseIconsCreate, CourseIconUpdate, CourseUpdate
from src.session import get_db
from src.utils.decode_code import decode_access_token
from src.utils.get_user import get_current_user
from src.utils.save_files import save_course_icon, save_course_image

router = APIRouter(prefix="/course")


@router.post("/create")
async def create_course(
        data: CourseCreate,
        icon_data: CourseIconsCreate = None,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        course = create_course_db(db=db, data=data)
        if icon_data:
            for item in icon_data.icons:
                create_course_icon_db(db=db, course_id=course.id, icon_data=item)
        add_new_course_notification.delay(course.id)
        return course
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")


@router.put("/update/{course_id}")
async def update_course(
        course_id: int,
        data: CourseUpdate,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        course = select_course_by_id_db(db=db, course_id=course_id)
        return update_course_db(db=db, course=course, data=data)
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")


@router.delete("/delete/{course_id}")
async def delete_course(
        course_id: int,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        course = select_course_by_id_db(db=db, course_id=course_id)
        delete_course_db(db=db, course=course)
        return {"message": "Course has been deleted"}
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")


@router.get("/all")
async def get_courses(
        request: Request,
        db: Session = Depends(get_db)
):
    authorization = request.headers.get("authorization")
    if authorization and authorization.startswith("Bearer") and len(authorization) > 10:
        user = decode_access_token(authorization[7:])
        return select_all_courses_db(db=db, student_id=user.student.id)
    else:
        return select_all_courses_db(db=db)


@router.get("/get/{course_id}")
async def get_course(
        request: Request,
        course_id: int,
        db: Session = Depends(get_db)
):
    authorization = request.headers.get("authorization")
    if authorization and authorization.startswith("Bearer") and len(authorization) > 10:
        user = decode_access_token(authorization[7:])
        return select_course_by_id_db(db=db, course_id=course_id, student_id=user.student.id)
    else:
        return select_course_by_id_db(db=db, course_id=course_id)


@router.get("/get/category/{category_id}")
async def get_courses_by_category(
        request: Request,
        category_id: int,
        db: Session = Depends(get_db)
):
    authorization = request.headers.get("authorization")
    if authorization and authorization.startswith("Bearer") and len(authorization) > 10:
        user = decode_access_token(authorization[7:])
        return select_courses_by_category_id_db(db=db, category_id=category_id, student_id=user.student.id)
    else:
        return select_courses_by_category_id_db(db=db, category_id=category_id)


@router.post("/upload/course/image")
async def upload_course_image(
        file: UploadFile = File(...),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        image_path = save_course_image(file=file)
        return {"image_path": image_path}
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")


@router.post("/upload/course/icons")
async def upload_course_icons(
        file: UploadFile = File(...),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        icon_path = save_course_icon(file=file)
        return {"icon_path": icon_path}
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")


@router.post("/attach/icon")
async def attach_icons_for_course(
        course_id: int,
        data: CourseIconsCreate,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        for icon in data.icons:
            create_course_icon_db(db=db, course_id=course_id, icon_data=icon)
        return {"message": "Successful attached"}
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")


@router.put("/update/icon/{icon_id}")
async def update_icon(
        icon_id: int,
        data: CourseIconUpdate,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        return update_course_icon_db(db=db, data=data, icon_id=icon_id)
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")


@router.put("/publish/{course_id}")
async def publish_course(
        course_id: int,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        return check_validity_lesson(db=db, course_id=course_id)
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
