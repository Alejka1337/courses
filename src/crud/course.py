from typing import cast, List
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from src.models import CourseIconOrm, CourseOrm, StudentCourseAssociation, LessonOrm
from src.schemas.course import CourseCreate, CourseIconCreate, CourseIconUpdate, CourseUpdate
from src.crud.lesson import get_lesson_info


class CourseRepository:
    def __init__(self, db: Session):
        self.db = db
        self.course_model = CourseOrm
        self.icon_model = CourseIconOrm

    def create_course(self, data: CourseCreate) -> CourseOrm:
        new_course = CourseOrm(**data.dict())
        self.db.add(new_course)
        self.db.commit()
        self.db.refresh(new_course)
        return new_course

    def create_course_icon(self, course_id: int, icon_data: CourseIconCreate) -> None:
        icon_dict = icon_data.dict()
        icon_dict.update({"course_id": course_id})
        new_icon = CourseIconOrm(**icon_dict)

        self.db.add(new_icon)
        self.db.commit()
        self.db.refresh(new_icon)

    def select_course_by_id(self, course_id: int):
        course = (self.db.query(self.course_model)
                  .filter(self.course_model.id == course_id, self.course_model.is_published)
                  .options(joinedload(self.course_model.icons))
                  .options(joinedload(self.course_model.lessons))
                  .first())

        if course and course.lessons:
            lessons: List[LessonOrm] = cast(List[LessonOrm], course.lessons)
            get_lesson_info(db=self.db, lessons=lessons)
        return course

    def select_courses_by_category_id(self, category_id: int):
        courses = (self.db.query(self.course_model)
                   .filter(self.course_model.category_id == category_id, self.course_model.is_published)
                   .options(joinedload(self.course_model.icons))
                   .all())

        for course in courses:
            if course and course.lessons:
                lessons: List[LessonOrm] = cast(List[LessonOrm], course.lessons)
                get_lesson_info(db=self.db, lessons=lessons)

        return courses

    def select_all_courses(self):
        courses = (self.db.query(self.course_model)
                   .filter(self.course_model.is_published)
                   .options(joinedload(self.course_model.icons))
                   .options(joinedload(self.course_model.lessons))
                   .all())

        for course in courses:
            if course and course.lessons:
                lessons: List[LessonOrm] = cast(List[LessonOrm], course.lessons)
                get_lesson_info(db=self.db, lessons=lessons)

        return courses

    def select_course_title_by_id(self, course_id: int):
        return self.db.query(self.course_model.title).filter(self.course_model.id == course_id).scalar()

    def select_course_info(self, course_id: int):
        return (self.db.query(self.course_model)
                .filter(self.course_model.id == course_id)
                .options(joinedload(self.course_model.category))
                .first())

    def update_course(self, data: CourseUpdate, course: CourseOrm):
        for key, value in data.dict().items():
            if value:
                setattr(course, key, value)

        self.db.commit()
        self.db.refresh(course)
        return course

    def update_quantity_lecture(self, course_id: int):
        (self.db.query(self.course_model)
         .filter(self.course_model.id == course_id)
         .update({
            self.course_model.quantity_lecture: (self.course_model.quantity_lecture + 1)
            if self.course_model.quantity_lecture else 1
         }, synchronize_session=False))

        self.db.commit()

    def update_quantity_test(self, course_id: int):
        (self.db.query(self.course_model)
         .filter(self.course_model.id == course_id)
         .update({
            self.course_model.quantity_test: (self.course_model.quantity_test + 1)
            if self.course_model.quantity_test else 1
         }, synchronize_session=False))

        self.db.commit()

    def update_course_icon(self, data: CourseIconUpdate, icon_id: int):
        icon = self.db.query(self.icon_model).filter(self.icon_model.id == icon_id).first()

        for key, value in data.dict().items():
            if value:
                setattr(icon, key, value)

        self.db.commit()
        self.db.refresh(icon)
        return icon

    def delete_course(self, course: CourseOrm) -> None:
        self.db.delete(course)
        self.db.commit()

    def search_course(self, query: str):
        regex_query = fr"\y{query}.*"
        return self.db.query(self.course_model).filter(self.course_model.title.op('~*')(regex_query)).all()

    def select_popular_course(self):
        popular_course_ids = (self.db.query(StudentCourseAssociation.course_id,
                                            func.count(StudentCourseAssociation.course_id).label('course_count'))
                              .group_by(StudentCourseAssociation.course_id)
                              .order_by(func.count(StudentCourseAssociation.course_id).desc())
                              .limit(10)
                              .all())

        course_ids = [course_id for course_id, count in popular_course_ids]
        popular_courses = self.db.query(self.course_model).filter(self.course_model.id.in_(course_ids)).all()
        return popular_courses
