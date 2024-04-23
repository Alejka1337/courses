from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from src.enums import NotificationType
from src.models import StudentNotification


def create_course_update_notification(db: Session, message: str, student_id: int):
    new_notification = StudentNotification(
        message=message,
        type=NotificationType.change_course.value,
        sent=False,
        student_id=student_id
    )

    db.add(new_notification)
    db.commit()
    db.refresh(new_notification)


def create_course_add_notification(db: Session, message: str, student_id: int):
    new_notification = StudentNotification(
        message=message,
        type=NotificationType.added_course.value,
        sent=False,
        expires=datetime.now() + timedelta(days=30),
        student_id=student_id
    )

    db.add(new_notification)
    db.commit()
    db.refresh(new_notification)


def select_user_notifications(db: Session, student_id: int):
    return db.query(StudentNotification).filter(StudentNotification.student_id == student_id).all()


def select_user_notification(db: Session, student_id: int, notification_id: int):
    return (db.query(StudentNotification)
            .filter(StudentNotification.student_id == student_id,
                    StudentNotification.id == notification_id)
            .first())


def update_notification_sent_status(db: Session, notification_id: int):
    (db.query(StudentNotification)
     .filter(StudentNotification.id == notification_id)
     .update({StudentNotification.sent: True}, synchronize_session=False))

    db.commit()
    return db.query(StudentNotification).filter(StudentNotification.id == notification_id).first()
