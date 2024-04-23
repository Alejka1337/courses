from sqlalchemy import func
from sqlalchemy.orm import Session, aliased, joinedload

from src.enums import CourseStatus, LessonType
from src.models import (CourseIconOrm, CourseOrm, StudentCourseAssociation, StudentLessonOrm, TestOrm, TestQuestionOrm,
                        ExamQuestionOrm, ExamOrm)

from src.schemas.course import CourseCreate, CourseIconCreate, CourseIconUpdate, CourseUpdate


def create_course_db(db: Session, data: CourseCreate):
    new_course = CourseOrm(
        title=data.title,
        image_path=data.image_path if data.image_path else None,
        price=data.price,
        old_price=data.old_price if data.old_price else None,
        category_id=data.category_id,
        intro_text=data.intro_text,
        skills_text=data.skills_text,
        about_text=data.about_text,
        c_type=data.c_type if data.c_type else None,
        c_duration=data.c_duration if data.c_duration else None,
        c_award=data.c_award if data.c_award else None,
        c_language=data.c_language if data.c_language else None,
        c_level=data.c_level if data.c_level else None,
        c_access=data.c_access if data.c_access else None
    )

    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    return new_course


def create_course_icon_db(db: Session, course_id: int, icon_data: CourseIconCreate):
    new_icon = CourseIconOrm(
        icon_path=icon_data.icon_path,
        icon_number=icon_data.icon_number,
        icon_title=icon_data.icon_title,
        icon_text=icon_data.icon_text,
        course_id=course_id
    )

    db.add(new_icon)
    db.commit()
    db.refresh(new_icon)


def select_course_by_id_db(db: Session, course_id: int, student_id: int = None):
    course = (db.query(CourseOrm)
              .filter(CourseOrm.id == course_id, CourseOrm.is_published)
              .options(joinedload(CourseOrm.icons))
              .options(joinedload(CourseOrm.lessons))
              .first())

    for lesson in course.lessons:
        if lesson.type == LessonType.test.value:
            test_id = db.query(TestOrm.id).filter(TestOrm.lesson_id == lesson.id).scalar()
            count_questions = db.query(TestQuestionOrm).filter(TestQuestionOrm.test_id == test_id).count()
            setattr(lesson, "count_questions", count_questions)

        elif lesson.type == LessonType.exam.value:
            exam_id = db.query(ExamOrm.id).filter(ExamOrm.lesson_id == lesson.id).scalar()
            count_questions = db.query(ExamQuestionOrm).filter(ExamQuestionOrm.exam_id == exam_id).count()
            setattr(lesson, "count_questions", count_questions)

    if student_id:
        student_course = (db.query(StudentCourseAssociation.grade.label("grade"),
                                   StudentCourseAssociation.progress.label("progress"))
                          .filter(StudentCourseAssociation.course_id == course.id,
                                  StudentCourseAssociation.student_id == student_id)
                          .first())

        if student_course is not None:
            setattr(course, "bought", True)
            setattr(course, "grade", student_course.grade)
            setattr(course, "progress", student_course.progress)

        for lesson in course.lessons:
            student_lesson = (db.query(StudentLessonOrm)
                              .filter(StudentLessonOrm.lesson_id == lesson.id,
                                      StudentLessonOrm.student_id == student_id)
                              .first())

            if student_lesson:
                setattr(lesson, "status", student_lesson.status)

        return course
    else:
        return course


def select_courses_by_category_id_db(db: Session, category_id: int, student_id: int = None):
    courses = (db.query(CourseOrm)
               .filter(CourseOrm.category_id == category_id, CourseOrm.is_published)
               .options(joinedload(CourseOrm.icons))
               .all())

    if student_id:
        for course in courses:
            student_course = (db.query(StudentCourseAssociation.grade.label("grade"),
                                       StudentCourseAssociation.progress.label("progress"))
                              .filter(StudentCourseAssociation.course_id == course.id,
                                      StudentCourseAssociation.student_id == student_id)
                              .first())

            if student_course is not None:
                setattr(course, "bought", True)
                setattr(course, "grade", student_course.grade)
                setattr(course, "progress", student_course.progress)

        return courses
    else:
        return courses


def select_all_courses_db(db: Session, student_id: int = None):
    courses = (db.query(CourseOrm).filter(CourseOrm.is_published)
               .options(joinedload(CourseOrm.icons)).options(joinedload(CourseOrm.lessons))
               .all())

    if student_id:
        for course in courses:
            student_course = (db.query(StudentCourseAssociation.grade.label("grade"),
                                       StudentCourseAssociation.progress.label("progress"))
                              .filter(StudentCourseAssociation.course_id == course.id,
                                      StudentCourseAssociation.student_id == student_id)
                              .first())

            if student_course is not None:
                setattr(course, "bought", True)
                setattr(course, "grade", student_course.grade)
                setattr(course, "progress", student_course.progress)

            for lesson in course.lessons:
                student_lesson = (db.query(StudentLessonOrm)
                                  .filter(StudentLessonOrm.lesson_id == lesson.id,
                                          StudentLessonOrm.student_id == student_id)
                                  .first())

                if student_lesson:
                    setattr(lesson, "status", student_lesson.status)
                    setattr(lesson, "score", student_lesson.score)

                if lesson.type == LessonType.test:
                    test_id = db.query(TestOrm.id).filter(TestOrm.lesson_id == lesson.id).scalar()
                    quantity_question = db.query(TestQuestionOrm).filter(TestQuestionOrm.test_id == test_id).count()
                    setattr(lesson, "q_count", quantity_question)

        return courses
    else:
        return courses


def select_course_name_by_id_db(db: Session, course_id: int):
    return db.query(CourseOrm.title).filter(CourseOrm.id == course_id).scalar()


def update_course_db(db: Session, data: CourseUpdate, course: CourseOrm):
    for key, value in data.dict().items():
        if value:
            setattr(course, key, value)

    db.commit()
    db.refresh(course)
    return course


def update_quantity_lecture_db(db: Session, course_id: int):
    course = select_course_by_id_db(db=db, course_id=course_id)

    if course.quantity_lecture is None:
        course.quantity_lecture = 1
        db.commit()
        db.refresh(course)

    else:
        course.quantity_lecture += 1
        db.commit()
        db.refresh(course)


def update_quantity_test_db(db: Session, course_id: int):
    course = select_course_by_id_db(db=db, course_id=course_id)

    if course.quantity_test is None:
        course.quantity_test = 1
        db.commit()
        db.refresh(course)

    else:
        course.quantity_test += 1
        db.commit()
        db.refresh(course)


def update_course_icon_db(db: Session, data: CourseIconUpdate, icon_id: int):
    icon = db.query(CourseIconOrm).filter(CourseIconOrm.id == icon_id).first()

    for key, value in data.dict().items():
        if value:
            setattr(icon, key, value)

    db.commit()
    db.refresh(icon)
    return icon


def delete_course_db(db: Session, course: CourseOrm):
    db.delete(course)
    db.commit()


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
    db.refresh(student_course)


def update_course_score(db: Session, student_course: StudentCourseAssociation, score: int):
    student_course.grade += score
    db.commit()
    db.refresh(student_course)


def update_course_status(db: Session, student_course: StudentCourseAssociation):
    student_course.status = CourseStatus.completed.value
    db.commit()
    db.refresh(student_course)


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

    # subquery = db.query(course_alias.category_id).filter(course_alias.id == course_id).limit(1).scalar_subquery()
    # courses_subquery = (db.query(CourseOrm.id)
    #                     .filter(CourseOrm.category_id == subquery, CourseOrm.id != course_id)
    #                     .subquery())

    return (db.query(StudentCourseAssociation.student_id.label("id"))
            .filter(StudentCourseAssociation.course_id.in_(courses_ids_list))
            .group_by(StudentCourseAssociation.student_id)
            .having(func.count(StudentCourseAssociation.course_id) == len(courses_ids_list))
            .all())


def select_course_info_db(db: Session, course_id: int):
    return db.query(CourseOrm).filter(CourseOrm.id == course_id).options(joinedload(CourseOrm.category)).first()
