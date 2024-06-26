from fastapi import APIRouter, Depends, File, Request, UploadFile
from sqlalchemy.orm import Session

from src.celery import celery_tasks
from src.crud.course import CourseRepository
from src.crud.student_course import select_student_course_info, select_student_lesson_info
from src.crud.lesson import check_validity_lesson
from src.enums import StaticFileType, UserType
from src.models import UserOrm
from src.schemas.course import CourseCreate, CourseIconsCreate, CourseIconUpdate, CourseUpdate
from src.session import get_db
from src.utils.decode_code import decode_access_token
from src.utils.exceptions import PermissionDeniedException
from src.utils.get_user import get_current_user
from src.utils.save_files import save_file

router = APIRouter(prefix="/course")


@router.post("/create")
async def create_course(
        data: CourseCreate,
        icon_data: CourseIconsCreate = None,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        repository = CourseRepository(db=db)
        course = repository.create_course(data)
        if icon_data:
            for item in icon_data.icons:
                repository.create_course_icon(course_id=course.id, icon_data=item)
        celery_tasks.add_new_course_notification.delay(course.id)
        return course
    else:
        raise PermissionDeniedException()


@router.put("/update/{course_id}")
async def update_course(
        course_id: int,
        data: CourseUpdate,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        repository = CourseRepository(db=db)
        course = repository.select_course_by_id(course_id=course_id)
        result = repository.update_course(course=course, data=data)
        return result
    else:
        raise PermissionDeniedException()


@router.delete("/delete/{course_id}")
async def delete_course(
        course_id: int,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        repository = CourseRepository(db=db)
        course = repository.select_course_by_id(course_id=course_id)
        repository.delete_course(course=course)
        return {"message": "Course has been deleted"}
    else:
        raise PermissionDeniedException()


@router.get("/all")
async def get_courses(
        request: Request,
        db: Session = Depends(get_db)
):
    repository = CourseRepository(db=db)
    authorization = request.headers.get("authorization")
    if authorization and authorization.startswith("Bearer") and len(authorization) > 10:
        user = decode_access_token(db=db, access_token=authorization[7:])

        courses = repository.select_all_courses()
        for course in courses:
            select_student_course_info(db=db, course=course, student_id=user.student.id)
            select_student_lesson_info(db=db, course=course, student_id=user.student.id)

        return courses
    else:
        return repository.select_all_courses()


@router.get("/popular")
async def get_popular_course(db: Session = Depends(get_db)):
    repository = CourseRepository(db=db)
    return repository.select_popular_course()


@router.get("/get/{course_id}")
async def get_course(
        request: Request,
        course_id: int,
        db: Session = Depends(get_db)
):
    repository = CourseRepository(db=db)
    authorization = request.headers.get("authorization")
    if authorization and authorization.startswith("Bearer") and len(authorization) > 10:
        user = decode_access_token(db=db, access_token=authorization[7:])

        course = repository.select_course_by_id(course_id=course_id)
        select_student_course_info(db=db, course=course, student_id=user.student.id)
        select_student_lesson_info(db=db, course=course, student_id=user.student.id)
        return course

    else:
        return repository.select_course_by_id(course_id=course_id)


@router.get("/get/category/{category_id}")
async def get_courses_by_category(
        request: Request,
        category_id: int,
        db: Session = Depends(get_db)
):
    repository = CourseRepository(db=db)
    authorization = request.headers.get("authorization")
    if authorization and authorization.startswith("Bearer") and len(authorization) > 10:
        user = decode_access_token(db=db, access_token=authorization[7:])

        courses = repository.select_courses_by_category_id(category_id=category_id)
        for course in courses:
            select_student_course_info(db=db, course=course, student_id=user.student.id)
            select_student_lesson_info(db=db, course=course, student_id=user.student.id)

        return courses
    else:
        return repository.select_courses_by_category_id(category_id=category_id)


@router.post("/upload/course/image")
async def upload_course_image(
        file: UploadFile = File(...),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        image_path = save_file(file=file, file_type=StaticFileType.course_image.value)
        return {"image_path": image_path}
    else:
        raise PermissionDeniedException()


@router.post("/upload/course/icons")
async def upload_course_icons(
        file: UploadFile = File(...),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        icon_path = save_file(file=file, file_type=StaticFileType.course_icon.value)
        return {"icon_path": icon_path}
    else:
        raise PermissionDeniedException()


@router.post("/attach/icon")
async def attach_icons_for_course(
        course_id: int,
        data: CourseIconsCreate,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        repository = CourseRepository(db=db)
        for icon_data in data.icons:
            repository.create_course_icon(course_id=course_id, icon_data=icon_data)
        return {"message": "Successful attached"}
    else:
        raise PermissionDeniedException()


@router.put("/update/icon/{icon_id}")
async def update_icon(
        icon_id: int,
        data: CourseIconUpdate,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        repository = CourseRepository(db=db)
        return repository.update_course_icon(data=data, icon_id=icon_id)
    else:
        raise PermissionDeniedException()


@router.put("/publish/{course_id}")
async def publish_course(
        course_id: int,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        return check_validity_lesson(db=db, course_id=course_id)
    else:
        raise PermissionDeniedException()
