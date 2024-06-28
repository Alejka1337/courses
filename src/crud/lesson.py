from typing import List
from sqlalchemy import asc, func
from sqlalchemy.orm import Session

from src.crud.exam import ExamRepository
from src.crud.lecture import LectureRepository
from src.crud.test import TestRepository
from src.enums import LessonType
from src.models import CourseOrm, ExamOrm, ExamQuestionOrm, LectureOrm, LessonOrm, TestOrm, TestQuestionOrm
from src.schemas.lesson import LessonCreate


def create_lesson_db(db: Session, data: LessonCreate) -> LessonOrm:
    new_lesson = LessonOrm(**data.dict())
    db.add(new_lesson)
    db.commit()
    db.refresh(new_lesson)
    return new_lesson


def create_lecture_db(db: Session, lesson_id: int):
    new_lecture = LectureOrm(lesson_id=lesson_id)
    db.add(new_lecture)
    db.commit()
    db.refresh(new_lecture)
    return new_lecture


def create_test_db(db: Session, lesson_id: int):
    new_test = TestOrm(lesson_id=lesson_id, score=40, attempts=10)
    db.add(new_test)
    db.commit()
    db.refresh(new_test)
    return new_test


def create_exam_db(db: Session, lesson_id: int, course_id: int):
    count_test = (db.query(LessonOrm)
                  .filter(LessonOrm.course_id == course_id, LessonOrm.type == LessonType.test.value)
                  .count())
    exam_score = 200

    if count_test > 0:
        test_lesson_ids = (db.query(LessonOrm.id.label("id")).
                           filter(LessonOrm.course_id == course_id, LessonOrm.type == LessonType.test.value)
                           .all())

        lesson_ids = [test_lesson.id for test_lesson in test_lesson_ids]
        test_total_score = db.query(func.sum(TestOrm.score)).filter(TestOrm.lesson_id.in_(lesson_ids)).scalar()
        exam_score -= test_total_score

    new_exam = ExamOrm(score=exam_score, attempts=10, timer=40, lesson_id=lesson_id)
    db.add(new_exam)
    db.commit()
    db.refresh(new_exam)
    return new_exam


def select_lesson_db(db: Session, lesson_id: int, student_id: int = None):
    lesson = db.query(LessonOrm).filter(LessonOrm.id == lesson_id).first()
    if not isinstance(lesson, LessonOrm):
        return {"message": "Lesson not found"}

    if lesson.type == LessonType.lecture.value:
        repository = LectureRepository(db=db)
        return repository.select_lecture_data(lesson=lesson)

    elif lesson.type == LessonType.test.value:
        repository = TestRepository(db=db)
        return repository.select_test_data(lesson=lesson, student_id=student_id)

    else:
        repository = ExamRepository(db=db)
        return repository.select_exam_data(lesson=lesson)


def select_lessons_by_course_db(db: Session, course_id: int):
    return db.query(LessonOrm).filter(LessonOrm.course_id == course_id).order_by(asc(LessonOrm.number)).all()


def select_lesson_by_id_db(db: Session, lesson_id: int):
    return db.query(LessonOrm).filter(LessonOrm.id == lesson_id).first()


def select_lesson_by_number_and_course_id_db(db: Session, number: int, course_id: int):
    return db.query(LessonOrm).filter(LessonOrm.number == number, LessonOrm.course_id == course_id).first()


def select_lesson_by_type_and_title_db(db: Session, lesson_type: LessonType, lesson_title: str):
    return db.query(LessonOrm).filter(LessonOrm.type == lesson_type, LessonOrm.title == lesson_title).first()


def check_lesson_number_db(db: Session, course_id: int, number: int):
    return db.query(LessonOrm).filter(LessonOrm.course_id == course_id, LessonOrm.number == number).count()


def update_lesson_number_db(db: Session, number: int, course_id: int):
    (db.query(LessonOrm).filter(LessonOrm.course_id == course_id, LessonOrm.number >= number).
     update({LessonOrm.number: LessonOrm.number + 1}, synchronize_session=False))

    db.commit()


def check_validity_lesson(db: Session, course_id: int):
    total_test_score = (db.query(func.sum(TestOrm.score))
                        .join(LessonOrm)
                        .filter(LessonOrm.course_id == course_id, LessonOrm.type == LessonType.test.value)
                        .scalar())

    total_exam_score = (db.query(func.sum(ExamOrm.score))
                        .join(LessonOrm)
                        .filter(LessonOrm.course_id == course_id, LessonOrm.type == LessonType.exam.value)
                        .scalar())

    if total_test_score + total_exam_score != 200:
        return {"result": False, "message": "Course max score less than 200"}

    tests = db.query(TestOrm).join(LessonOrm).filter(LessonOrm.course_id == course_id).all()
    for test in tests:
        test_question_scores = (db.query(func.sum(TestQuestionOrm.q_score))
                                .filter(TestQuestionOrm.test_id == test.id)
                                .scalar())

        if test_question_scores != test.score:
            return {"result": False, "message": f"Sum for all question in test {test.id} not equal {test.score}"}

    exam = db.query(ExamOrm).join(LessonOrm).filter(LessonOrm.course_id == course_id).first()
    exam_question_score = (db.query(func.sum(ExamQuestionOrm.q_score))
                           .filter(ExamQuestionOrm.exam_id == exam.id)
                           .scalar())

    if exam_question_score != total_exam_score:
        return {"result": False, "message": f"Sum for all question in exam {exam.id} not equal {exam.score}"}
    else:
        db.query(CourseOrm).filter(CourseOrm.id == course_id).update({CourseOrm.is_published: True})
        return {"result": True, "message": "Course successfully published"}


def search_lesson(db: Session, query: str):
    regex_query = fr"\y{query}.*"
    return db.query(LessonOrm).filter(LessonOrm.title.op('~*')(regex_query)).all()


def get_lesson_info(db: Session, lessons: List[LessonOrm]):
    for lesson in lessons:
        if lesson.type == LessonType.test.value:
            test_id = db.query(TestOrm.id).filter(TestOrm.lesson_id == lesson.id).scalar()
            count_questions = db.query(TestQuestionOrm).filter(TestQuestionOrm.test_id == test_id).count()
            setattr(lesson, "count_questions", count_questions)

        elif lesson.type == LessonType.exam.value:
            exam_id = db.query(ExamOrm.id).filter(ExamOrm.lesson_id == lesson.id).scalar()
            count_questions = db.query(ExamQuestionOrm).filter(ExamQuestionOrm.exam_id == exam_id).count()
            setattr(lesson, "count_questions", count_questions)
