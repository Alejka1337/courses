from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from src.enums import NotificationType
from src.models import StudentNotification


class NotificationRepository:
    def __init__(self, db: Session):
        self.db = db
        self.model = StudentNotification

    def create_notification_about_course_updates(self, message: str, student_id: int):
        new_notification = self.model(
            message=message,
            type=NotificationType.change_course.value,
            sent=False,
            student_id=student_id
        )

        self.db.add(new_notification)
        self.db.commit()
        self.db.refresh(new_notification)

    def create_notification_about_adding_new_course(self, message: str, student_id: int):
        new_notification = StudentNotification(
            message=message,
            type=NotificationType.added_course.value,
            sent=False,
            expires=datetime.now() + timedelta(days=30),
            student_id=student_id
        )

        self.db.add(new_notification)
        self.db.commit()
        self.db.refresh(new_notification)

    def select_student_notifications(self, student_id: int):
        return self.db.query(self.model).filter(self.model.student_id == student_id).all()

    def select_one_student_notification(self, student_id: int, notification_id: int):
        return (self.db.query(self.model)
                .filter(self.model.student_id == student_id, self.model.id == notification_id)
                .first())

    def update_notification_sent_status(self, notification_id: int):
        (self.db.query(self.model)
         .filter(self.model.id == notification_id)
         .update({self.model.sent: True}, synchronize_session=False))

        self.db.commit()
        result = self.db.query(StudentNotification).filter(StudentNotification.id == notification_id).first()
        return result
