from typing import List

from sqlalchemy import asc
from sqlalchemy.orm import Session

from src.crud.lesson import select_lesson_by_id_db
from src.enums import CourseStatus, LessonStatus, LessonType
from src.models import LessonOrm, StudentCourseAssociation, StudentLessonOrm


def select_student_lesson_db(db: Session, lesson_id: int, student_id: int):
    return (db.query(StudentLessonOrm)
            .filter(StudentLessonOrm.lesson_id == lesson_id, StudentLessonOrm.student_id == student_id)
            .first())


def create_student_lesson_db(db: Session, student_id: int, lesson_id: int, status: LessonStatus):
    new_student_lesson = StudentLessonOrm(student_id=student_id, lesson_id=lesson_id, status=status)
    db.add(new_student_lesson)
    db.commit()
    db.refresh(new_student_lesson)


def confirm_student_test_db(db: Session, student_lesson: StudentLessonOrm, score: int, attempt: int):
    student_lesson.score = score
    student_lesson.attempt = attempt
    student_lesson.status = LessonStatus.completed.value
    db.commit()
    db.refresh(student_lesson)


def confirm_student_lecture_db(db: Session, student_lesson: StudentLessonOrm):
    student_lesson.status = LessonStatus.completed.value
    db.commit()
    db.refresh(student_lesson)


def set_active_student_lesson_db(db: Session, student_lesson: StudentLessonOrm):
    student_lesson.status = LessonStatus.active.value
    db.commit()
    db.refresh(student_lesson)


def set_available_student_lesson_db(db: Session, student_lesson: StudentLessonOrm):
    student_lesson.status = LessonStatus.available.value
    db.commit()
    db.refresh(student_lesson)


def update_student_lesson_status_db(db: Session, student_id: int, lesson_id: int):
    current_lesson = select_lesson_by_id_db(db=db, lesson_id=lesson_id)

    next_lessons = (db.query(LessonOrm.id.label("id"), LessonOrm.type.label("type"))
                    .filter(LessonOrm.course_id == current_lesson.course_id,
                            LessonOrm.number > current_lesson.number)
                    .order_by(asc(LessonOrm.number))
                    .all())

    for index, lesson in enumerate(next_lessons):
        if index == 0:
            (db.query(StudentLessonOrm)
             .filter(StudentLessonOrm.lesson_id == lesson.id, StudentLessonOrm.student_id == student_id)
             .update({StudentLessonOrm.status: LessonStatus.active.value}, synchronize_session=False))

        elif lesson.type == LessonType.lecture.value and index > 1:
            (db.query(StudentLessonOrm)
             .filter(StudentLessonOrm.lesson_id == lesson.id, StudentLessonOrm.student_id == student_id)
             .update({StudentLessonOrm.status: LessonStatus.available.value}, synchronize_session=False))

        elif lesson.type == LessonType.test.value or lesson.type == LessonType.exam.value:
            break

    db.commit()


def select_students_for_course_db(db: Session, course_id: int):
    return (db.query(StudentCourseAssociation.student_id.label("id"))
            .filter(StudentCourseAssociation.course_id == course_id,
                    StudentCourseAssociation.status == CourseStatus.in_progress.value)
            .distinct()
            .all())


def select_student_lessons_db(db: Session, course_lessons: List[LessonOrm], student_id: int):
    return (db.query(StudentLessonOrm)
            .filter(StudentLessonOrm.lesson_id.in_([lesson.id for lesson in course_lessons]))
            .filter(StudentLessonOrm.student_id == student_id)
            .all())


def select_count_student_lessons_db(db: Session, course_lessons: List[LessonOrm], student_id: int):
    return (db.query(StudentLessonOrm)
            .filter(StudentLessonOrm.lesson_id.in_([lesson.id for lesson in course_lessons]))
            .filter(StudentLessonOrm.student_id == student_id)
            .count())


def select_count_completed_student_lessons_db(db: Session, course_lessons: List[LessonOrm], student_id: int):
    return (db.query(StudentLessonOrm)
            .filter(StudentLessonOrm.lesson_id.in_([lesson.id for lesson in course_lessons]))
            .filter(StudentLessonOrm.student_id == student_id)
            .filter(StudentLessonOrm.status == LessonStatus.completed.value)
            .count())


def update_student_lesson_structure(
        db: Session,
        new_lesson: LessonOrm,
        course_lessons: List[LessonOrm],
        student_lessons: List[StudentLessonOrm],
        student_id: int
):
    if new_lesson.type == LessonType.test.value:
        prev_lesson_number = new_lesson.number - 1
        prev_lesson = [lesson for lesson in course_lessons if lesson.number == prev_lesson_number][0]
        prev_student_lesson = [sl for sl in student_lessons if sl.lesson_id == prev_lesson.id][0]

        if prev_student_lesson.status == LessonStatus.completed:
            # новый lesson делаем со статусом active все следующие lesson ставим статус blocked
            try:
                new_student_lesson = StudentLessonOrm(
                    status=LessonStatus.active.value, lesson_id=new_lesson.id, student_id=student_id)

                db.add(new_student_lesson)

                next_lesson_numbers = [lesson.number for lesson in course_lessons if lesson.number > new_lesson.number]
                next_lesson_ids = [lesson.id for lesson in course_lessons if lesson.number in next_lesson_numbers]
                next_student_lessons = (db.query(StudentLessonOrm)
                                        .filter(StudentLessonOrm.student_id == student_id,
                                                StudentLessonOrm.lesson_id.in_(next_lesson_ids))
                                        .all())

                for next_student_lesson in next_student_lessons:
                    next_student_lesson.status = LessonStatus.blocked.value

                db.commit()
            except Exception:
                db.rollback()
                raise

        elif prev_student_lesson.status == LessonStatus.available or prev_student_lesson.status == LessonStatus.active:
            # новый lesson делаем со статусом blocked все следующие lesson ставим статус blocked
            try:
                new_student_lesson = StudentLessonOrm(
                    status=LessonStatus.blocked.value, lesson_id=new_lesson.id, student_id=student_id)

                db.add(new_student_lesson)

                next_lesson_numbers = [lesson.number for lesson in course_lessons if lesson.number > new_lesson.number]
                next_lesson_ids = [lesson.id for lesson in course_lessons if lesson.number in next_lesson_numbers]
                next_student_lessons = (db.query(StudentLessonOrm)
                                        .filter(StudentLessonOrm.student_id == student_id,
                                                StudentLessonOrm.lesson_id.in_(next_lesson_ids))
                                        .all())

                for next_student_lesson in next_student_lessons:
                    next_student_lesson.status = LessonStatus.blocked.value

                db.commit()
            except Exception:
                db.rollback()
                raise

        elif prev_student_lesson.status == LessonStatus.blocked:
            # новый lesson делаем со статусом blocked другие не трогаем
            new_student_lesson = StudentLessonOrm(
                status=LessonStatus.blocked.value,
                lesson_id=new_lesson.id,
                student_id=student_id
            )

            db.add(new_student_lesson)
            db.commit()

    elif new_lesson.type == LessonType.lecture.value:
        prev_lesson_number = new_lesson.number - 1
        prev_lesson = [lesson for lesson in course_lessons if lesson.number == prev_lesson_number][0]
        prev_student_lesson = [sl for sl in student_lessons if sl.lesson_id == prev_lesson.id][0]

        if prev_student_lesson.status == LessonStatus.completed:
            # новый lesson делаем со статусом active
            # следующий урок если это тест делаем статус blocked если лекция делаем статус available
            try:
                new_student_lesson = StudentLessonOrm(
                    status=LessonStatus.active.value,
                    lesson_id=new_lesson.id,
                    student_id=student_id
                )

                db.add(new_student_lesson)
                next_lesson_num = new_lesson.number + 1
                next_lesson = [lesson for lesson in course_lessons if lesson.number == next_lesson_num][0]
                next_lesson_status = LessonStatus.blocked.value if next_lesson.type == LessonType.test.value \
                    else LessonStatus.available.value

                (db.query(StudentLessonOrm)
                 .filter(StudentLessonOrm.lesson_id == next_lesson.id)
                 .update({StudentLessonOrm.status: next_lesson_status}))

                db.commit()

            except Exception:
                db.rollback()
                raise

        elif (
                (prev_student_lesson.status == LessonStatus.active and prev_lesson.type == LessonType.test) or
                prev_student_lesson.status == LessonStatus.blocked
        ):
            # новый lesson делаем со статусом blocked
            new_student_lesson = StudentLessonOrm(
                status=LessonStatus.blocked.value,
                lesson_id=new_lesson.id,
                student_id=student_id
            )

            db.add(new_student_lesson)
            db.commit()

        elif (
                (prev_student_lesson.status == LessonStatus.active and prev_lesson.type == LessonType.lecture) or
                prev_student_lesson.status == LessonStatus.available
        ):

            new_student_lesson = StudentLessonOrm(
                status=LessonStatus.available.value,
                lesson_id=new_lesson.id,
                student_id=student_id
            )

            db.add(new_student_lesson)
            db.commit()
