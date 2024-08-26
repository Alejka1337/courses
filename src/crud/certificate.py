from sqlalchemy.orm import Session

from src.models import CategoryCertificateOrm, CourseCertificateOrm


class CertificateRepository:
    def __init__(self, db: Session):
        self.db = db
        self.course_certificate = CourseCertificateOrm
        self.category_certificate = CategoryCertificateOrm

    def create_course_certificate(self, student_id: int, course_id: int) -> None:
        new_certificate = self.course_certificate(
            link="static/certificate/certificate.webp",
            student_id=student_id,
            course_id=course_id
        )
        self.db.add(new_certificate)
        self.db.commit()

    def select_student_course_certificate(self, student_id: int):
        result = (self.db.query(self.course_certificate.link, self.course_certificate.course_id)
                  .filter(self.course_certificate.student_id == student_id)
                  .all())
        return result
