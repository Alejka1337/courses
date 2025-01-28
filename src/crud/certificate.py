from sqlalchemy import func
from sqlalchemy.orm import Session


from src.models import CategoryCertificateOrm, CourseCertificateOrm, CourseOrm, CategoryOrm


class CertificateRepository:
    def __init__(self, db: Session):
        self.db = db
        self.course_certificate = CourseCertificateOrm
        self.category_certificate = CategoryCertificateOrm
        self.course = CourseOrm
        self.category = CategoryOrm

    def create_course_certificate(self, path: str, student_id: int, course_id: int) -> None:
        new_certificate = self.course_certificate(
            link=path,
            student_id=student_id,
            course_id=course_id
        )
        self.db.add(new_certificate)
        self.db.commit()

    def create_category_certificate(self, path: str, student_id: int, category_id: int) -> None:
        new_certificate = self.category_certificate(
            link=path,
            addition_link="",
            student_id=student_id,
            category_id=category_id
        )
        self.db.add(new_certificate)
        self.db.commit()

    def select_student_certificate(self, student_id: int):
        result = (
            self.db.query(
                self.category.id.label("category_id"),
                self.category.title.label("category_name"),
                self.category_certificate.id.label("category_certificate_id"),
                self.category_certificate.link.label("category_certificate_link"),
                self.course.id.label("course_id"),
                self.course.title.label("course_name"),
                self.course_certificate.id.label("course_certificate_id"),
                self.course_certificate.link.label("course_certificate_link"),
            )
            .filter(self.course.is_published)
            .join(self.category_certificate, self.category.id == self.category_certificate.category_id, isouter=True)
            .join(self.course, self.category.id == self.course.category_id)
            .join(self.course_certificate,
                  (self.course.id == self.course_certificate.course_id) &
                  (self.course_certificate.student_id == student_id), isouter=True)
            .all()
        )
        # Запрос для проверки количества завершенных курсов
        category_completion = (
            self.db.query(
                self.category.id.label("category_id"),
                func.count(self.course.id).label("total_courses"),
                func.count(self.course_certificate.id).label("completed_courses"),
            )
            .filter(self.course.is_published)
            .join(self.course, self.category.id == self.course.category_id)
            .join(self.course_certificate,
                  (self.course.id == self.course_certificate.course_id) &
                  (self.course_certificate.student_id == student_id), isouter=True)
            .group_by(self.category.id)
            .all()
        )

        # Преобразование количества завершенных курсов в словарь
        completion_map = {
            row.category_id: {
                "total_courses": row.total_courses,
                "completed_courses": row.completed_courses,
            }
            for row in category_completion
        }

        # Формирование структуры результата
        certificates = {}
        for row in result:
            if row.category_id not in certificates:
                # Проверка завершенности всех курсов
                category_info = completion_map.get(row.category_id, {})
                total_courses = category_info.get("total_courses", 0)
                completed_courses = category_info.get("completed_courses", 0)

                category_certificate_link = row.category_certificate_link if total_courses == completed_courses else None

                certificates[row.category_id] = {
                    "category_name": row.category_name,
                    "category_certificate_id": row.category_certificate_id,
                    "category_certificate_link": category_certificate_link,
                    "course_certificate_data": [],
                }

            # Добавляем информацию о курсах
            if row.course_name and row.course_certificate_link:
                certificates[row.category_id]["course_certificate_data"].append({
                    "course_name": row.course_name,
                    "course_certificate_id": row.course_certificate_id,
                    "course_certificate_link": row.course_certificate_link,
                })

        return list(certificates.values())
