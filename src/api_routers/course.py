from fastapi import APIRouter, Depends, File, Request, UploadFile
from sqlalchemy.orm import Session

from src.celery import celery_tasks
from src.crud.course import CourseRepository
from src.crud.lesson import LessonRepository
from src.crud.student_course import (
    select_student_course_info,
    select_student_lesson_info,
)
from src.enums import StaticFileType
from src.models import UserOrm
from src.schemas.course import (
    AttachedIconResponse,
    CourseCreate,
    CourseDetailResponse,
    CourseIconsCreate,
    CourseIconUpdate,
    CourseResponse,
    CourseUpdate,
    DeleteCourseResponse,
    IconResponse,
    IconUploadedResponse,
    ImageUploadedResponse,
    PublishCourseResponse,
)
from src.session import get_db
from src.utils.decode_code import decode_access_token
from src.utils.exceptions import (
    CourseNotFoundException,
    PermissionDeniedException
)
from src.utils.get_user import get_current_user
from src.utils.save_files import save_file

router = APIRouter(prefix="/course")


@router.post("/create", response_model=CourseResponse)
async def create_course(
        data: CourseCreate,
        icon_data: CourseIconsCreate = None,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.is_moder:
        repository = CourseRepository(db=db)
        course = repository.create_course(data)
        if icon_data:
            for item in icon_data.icons:
                repository.create_course_icon(course_id=course.id, icon_data=item)

        return course
    else:
        raise PermissionDeniedException()


@router.put("/update/{course_id}", response_model=CourseResponse)
async def update_course(
        course_id: int,
        data: CourseUpdate,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.is_moder:
        repository = CourseRepository(db=db)
        course = repository.select_base_course_by_id(course_id=course_id)

        if course.title != data.title or course.image_path != data.image_path:
            celery_tasks.update_stripe_product.delay(course.id, data.title, data.image_path)

        if course.price != data.price:
            celery_tasks.update_stripe_price.delay(course.id, data.price)

        result = repository.update_course(course=course, data=data)
        return result
    else:
        raise PermissionDeniedException()


@router.delete("/delete/{course_id}", response_model=DeleteCourseResponse)
async def delete_course(
        course_id: int,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.is_moder:
        repository = CourseRepository(db=db)
        course = repository.select_base_course_by_id(course_id=course_id)
        repository.delete_course(course=course)
        return DeleteCourseResponse()
    else:
        raise PermissionDeniedException()


@router.get("/all", response_model=list[CourseDetailResponse])
async def get_courses(
        request: Request,
        db: Session = Depends(get_db)
):
    repository = CourseRepository(db=db)
    authorization = request.headers.get("authorization")
    if authorization and authorization.startswith("Bearer") and len(authorization) > 10:
        user = decode_access_token(db=db, access_token=authorization[7:])

        if user.is_student:
            courses = repository.select_all_courses()
            for course in courses:
                select_student_course_info(db=db, course=course, student_id=user.student.id)
                select_student_lesson_info(db=db, course=course, student_id=user.student.id)
            return courses

        else:
            return repository.select_all_courses_for_moder()

    else:
        return repository.select_all_courses()


@router.get("/popular", response_model=list[CourseResponse])
async def get_popular_course(db: Session = Depends(get_db)):
    repository = CourseRepository(db=db)
    return repository.select_popular_course()


@router.get("/get/{course_id}", response_model=CourseDetailResponse)
async def get_course(
        request: Request,
        course_id: int,
        db: Session = Depends(get_db)
):
    repository = CourseRepository(db=db)
    authorization = request.headers.get("authorization")
    if authorization and authorization.startswith("Bearer") and len(authorization) > 10:
        user = decode_access_token(db=db, access_token=authorization[7:])

        if user.is_student:
            course = repository.select_course_by_id(course_id=course_id)
            if course is None:
                CourseNotFoundException()

            select_student_course_info(db=db, course=course, student_id=user.student.id)
            select_student_lesson_info(db=db, course=course, student_id=user.student.id)
            return course
        else:
            return repository.select_course_by_id(course_id=course_id)

    else:
        return repository.select_course_by_id(course_id=course_id)


@router.get("/get/category/{category_id}", response_model=list[CourseDetailResponse])
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


@router.post("/upload/course/image", response_model=ImageUploadedResponse)
async def upload_course_image(
        file: UploadFile = File(...),
        user: UserOrm = Depends(get_current_user)
):
    if user.is_moder:
        image_path = save_file(file=file, file_type=StaticFileType.course_image.value)
        return ImageUploadedResponse(image_path=image_path)
    else:
        raise PermissionDeniedException()


@router.post("/upload/course/icons", response_model=IconUploadedResponse)
async def upload_course_icons(
        file: UploadFile = File(...),
        user: UserOrm = Depends(get_current_user)
):
    if user.is_moder:
        icon_path = save_file(file=file, file_type=StaticFileType.course_icon.value)
        return IconUploadedResponse(icon_path=icon_path)
    else:
        raise PermissionDeniedException()


@router.post("/attach/icon", response_model=AttachedIconResponse)
async def attach_icons_for_course(
        course_id: int,
        data: CourseIconsCreate,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.is_moder:
        repository = CourseRepository(db=db)
        for icon_data in data.icons:
            repository.create_course_icon(course_id=course_id, icon_data=icon_data)
        return AttachedIconResponse()
    else:
        raise PermissionDeniedException()


@router.put("/update/icon/{icon_id}", response_model=IconResponse)
async def update_icon(
        icon_id: int,
        data: CourseIconUpdate,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.is_moder:
        repository = CourseRepository(db=db)
        return repository.update_course_icon(data=data, icon_id=icon_id)
    else:
        raise PermissionDeniedException()


@router.put("/publish/{course_id}", response_model=PublishCourseResponse)
async def publish_course(
        course_id: int,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.is_moder:
        lesson_repo = LessonRepository(db=db)
        repository = CourseRepository(db=db)
        response = lesson_repo.check_validity_lessons(course_id=course_id)
        if response["result"]:
            repository.published_course(course_id=course_id)

        celery_tasks.add_new_course_notification.delay(course_id)
        celery_tasks.create_stripe_price.delay(course_id)

        return response
    else:
        raise PermissionDeniedException()
