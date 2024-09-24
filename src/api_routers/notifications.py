from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.celery import celery_tasks
from src.crud.lesson import LessonRepository
from src.crud.notifications import NotificationRepository
from src.models import UserOrm
from src.session import get_db
from src.utils.exceptions import PermissionDeniedException
from src.utils.get_user import get_current_user
from src.utils.notifications import parse_notification_text

router = APIRouter(prefix="/notifications")


@router.get("/get")
async def get_my_notifications(
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.is_student:
        repository = NotificationRepository(db=db)
        notifications = repository.select_student_notifications(student_id=user.student.id)
        return notifications
    else:
        raise PermissionDeniedException()


@router.patch("/send")
async def send_notification(
        notification_id: int,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.is_student:
        repository = NotificationRepository(db=db)
        notification = repository.update_notification_sent_status(notification_id=notification_id)
        return notification
    else:
        raise PermissionDeniedException()


@router.patch("/agree")
async def agree_with_notification(
        notification_id: int,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.is_student:
        repository = NotificationRepository(db=db)
        notification = repository.select_one_student_notification(
            student_id=user.student.id,
            notification_id=notification_id
        )

        lesson_info = parse_notification_text(notification.message)
        lesson_repo = LessonRepository(db=db)
        new_lesson = lesson_repo.select_lesson_by_type_and_title_db(
            lesson_title=lesson_info["lesson_title"], lesson_type=lesson_info["lesson_type"]
        )

        celery_tasks.update_student_lessons.delay(student_id=user.student.id, lesson_info=lesson_info)
        celery_tasks.update_student_course_progress.delay(student_id=user.student.id, lesson_id=new_lesson.id)
        return {"message": "Wait for your course update"}
    else:
        raise PermissionDeniedException()
