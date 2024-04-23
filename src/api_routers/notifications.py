from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.celery import update_student_course_progress, update_student_lessons
from src.crud.lesson import select_lesson_by_type_and_title_db
from src.crud.notifications import select_user_notification, select_user_notifications, update_notification_sent_status
from src.enums import UserType
from src.models import UserOrm
from src.session import get_db
from src.utils.get_user import get_current_user
from src.utils.notifications import parse_notification_text

router = APIRouter(prefix="/notifications")


@router.get("/get")
async def get_my_notifications(
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.student.value:
        return select_user_notifications(db=db, student_id=user.student.id)
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only for students")


@router.patch("/send")
async def send_notification(
        notification_id: int,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.student.value:
        return update_notification_sent_status(db=db, notification_id=notification_id)
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only for students")


@router.patch("/agree")
async def agree_with_notification(
        notification_id: int,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.student.value:
        notification = select_user_notification(db=db, student_id=user.student.id, notification_id=notification_id)
        lesson_info = parse_notification_text(notification.message)

        new_lesson = select_lesson_by_type_and_title_db(
            db=db, lesson_title=lesson_info["lesson_title"], lesson_type=lesson_info["lesson_type"]
        )

        update_student_lessons.delay(student_id=user.student.id, lesson_info=lesson_info)
        update_student_course_progress.delay(student_id=user.student.id, lesson_id=new_lesson.id)
        return {"message": "Wait for your course update"}
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only for students")
