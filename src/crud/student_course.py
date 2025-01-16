from sqlalchemy import func
from sqlalchemy.orm import Session, aliased

from src.crud.student_lesson import select_student_lesson_db, create_student_lesson_db
from src.enums import CourseStatus, LessonStatus, LessonType
from src.models import CourseOrm, StudentCourseAssociation, CategoryOrm
from src.crud.lesson import LessonRepository


def select_student_course_info(db: Session, student_id: int, course: CourseOrm):
    student_course = (db.query(StudentCourseAssociation.grade.label("grade"),
                               StudentCourseAssociation.progress.label("progress"))
                      .filter(StudentCourseAssociation.course_id == course.id,
                              StudentCourseAssociation.student_id == student_id)
                      .first())

    if student_course is not None:
        setattr(course, "bought", True)
        setattr(course, "grade", student_course.grade)
        setattr(course, "progress", student_course.progress)

    return course


def select_student_lesson_info(db: Session, course: CourseOrm, student_id: int):
    for lesson in course.lessons:
        student_lesson = select_student_lesson_db(db=db, student_id=student_id, lesson_id=lesson.id)

        if student_lesson:
            setattr(lesson, "status", student_lesson.status)
            setattr(lesson, "score", student_lesson.score)


def subscribe_student_to_course_db(db: Session, student_id: int, course_id: int):
    new_subscribe = StudentCourseAssociation(
        student_id=student_id,
        course_id=course_id,
        status=CourseStatus.in_progress
    )

    db.add(new_subscribe)
    db.commit()
    db.refresh(new_subscribe)
    return new_subscribe


def select_student_course_db(db: Session, course_id: int, student_id: int):
    return (db.query(StudentCourseAssociation)
            .filter(StudentCourseAssociation.course_id == course_id,
                    StudentCourseAssociation.student_id == student_id)
            .first())


def select_count_student_course_db(db: Session, course_id: int):
    return db.query(StudentCourseAssociation).filter(StudentCourseAssociation.course_id == course_id).count()


def update_course_present(db: Session, student_course: StudentCourseAssociation, progress: int):
    student_course.progress = progress
    db.commit()


def update_course_score(db: Session, student_course: StudentCourseAssociation, score: int):
    student_course.grade += score
    db.commit()


def update_course_status(db: Session, student_course: StudentCourseAssociation):
    student_course.status = CourseStatus.completed.value
    db.commit()


def select_students_whose_bought_courses(db: Session, course_id: int):
    course_alias = aliased(CourseOrm)

    courses_ids = (
        db.query(CourseOrm.id)
        .filter(CourseOrm.category_id == db.query(course_alias.category_id)
                .filter(course_alias.id == course_id)
                .subquery(),
                CourseOrm.id != course_id)
        .all()
    )
    courses_ids_list = [course[0] for course in courses_ids]

    return (db.query(StudentCourseAssociation.student_id.label("id"))
            .filter(StudentCourseAssociation.course_id.in_(courses_ids_list))
            .group_by(StudentCourseAssociation.student_id)
            .having(func.count(StudentCourseAssociation.course_id) == len(courses_ids_list))
            .all())


def check_bought_course(db: Session, student_id: int, courses_ids: list[int]):
    for course_id in courses_ids:
        res = (db.query(StudentCourseAssociation)
               .filter(StudentCourseAssociation.student_id == student_id)
               .filter(StudentCourseAssociation.course_id == course_id)
               .first())

        if res is None:
            return False

    return True


def create_student_lesson(
        db: Session,
        student_id: int,
        course_id: int
):
    lesson_repo = LessonRepository(db=db)
    lessons = lesson_repo.select_lessons_by_course_db(course_id=course_id)

    for index, lesson in enumerate(lessons):
        if lesson.number == 1:
            create_student_lesson_db(
                db=db,
                student_id=student_id,
                lesson_id=lesson.id,
                status=LessonStatus.active
            )

        elif lesson.type == LessonType.test.value or lesson.type == LessonType.exam.value:
            create_student_lesson_db(
                db=db,
                student_id=student_id,
                lesson_id=lesson.id,
                status=LessonStatus.blocked
            )
        else:
            if any(les.type == LessonType.test.value for les in lessons[:index]):
                create_student_lesson_db(
                    db=db,
                    student_id=student_id,
                    lesson_id=lesson.id,
                    status=LessonStatus.blocked
                )
            else:
                create_student_lesson_db(
                    db=db,
                    student_id=student_id,
                    lesson_id=lesson.id,
                    status=LessonStatus.available
                )

def check_competed_category(db: Session, student_id: int, category_id: int) -> bool:
    category_courses = (db.query(CourseOrm.id)
                        .filter(CourseOrm.category_id == category_id)
                        .filter(CourseOrm.is_published)
                        .all())

    category_course_ids = {course_id for course_id, in category_courses}
    completed_courses = (db.query(StudentCourseAssociation.course_id)
                         .filter(StudentCourseAssociation.student_id == student_id)
                         .filter(StudentCourseAssociation.status == CourseStatus.completed.value)
                         .all())

    completed_course_ids = {course_id for course_id, in completed_courses}
    return category_course_ids.issubset(completed_course_ids)
