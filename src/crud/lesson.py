from typing import List

from sqlalchemy import asc
from sqlalchemy.orm import Session

from src.crud.exam import ExamRepository
from src.crud.lecture import LectureRepository
from src.crud.test import TestRepository
from src.enums import LessonType
from src.models import LessonOrm
from src.schemas.lesson import LessonCreate, LessonUpdate


class LessonRepository:
    _test_repo = None
    _exam_repo = None
    _lecture_repo = None

    def __init__(self, db: Session):
        self.db = db
        self.lesson_model = LessonOrm

    @property
    def test_repo(self):
        if self._test_repo is None:
            self._test_repo = TestRepository(db=self.db)
        return self._test_repo

    @property
    def exam_repo(self):
        if self._exam_repo is None:
            self._exam_repo = ExamRepository(db=self.db)
        return self._exam_repo

    @property
    def lecture_repo(self):
        if self._lecture_repo is None:
            self._lecture_repo = LectureRepository(db=self.db)
        return self._lecture_repo

    def create_lesson_db(self, data: LessonCreate) -> LessonOrm:
        new_lesson = self.lesson_model(**data.dict())
        self.db.add(new_lesson)
        self.db.commit()
        self.db.refresh(new_lesson)
        return new_lesson

    def select_lesson_db(self, lesson_id: int, student_id: int = None):
        lesson = self.db.query(self.lesson_model).filter(self.lesson_model.id == lesson_id).first()
        if not isinstance(lesson, LessonOrm):
            return {"message": "Lesson not found"}

        if lesson.type == LessonType.lecture.value:
            return self.lecture_repo.select_lecture_data(lesson=lesson)

        elif lesson.type == LessonType.test.value:
            return self.test_repo.select_test_data(lesson=lesson, student_id=student_id)

        else:
            return self.exam_repo.select_exam_data(lesson=lesson, student_id=student_id)

    def select_lessons_by_course_db(self, course_id: int):
        return (self.db.query(self.lesson_model)
                .filter(self.lesson_model.course_id == course_id)
                .order_by(asc(self.lesson_model.number))
                .all())

    def select_lesson_by_id_db(self, lesson_id: int):
        return self.db.query(self.lesson_model).filter(self.lesson_model.id == lesson_id).first()

    def select_lesson_by_number_and_course_id_db(self, number: int, course_id: int):
        return (self.db.query(self.lesson_model)
                .filter(self.lesson_model.number == number,
                        self.lesson_model.course_id == course_id)
                .first())

    def select_lesson_by_type_and_title_db(self, lesson_type: LessonType, lesson_title: str):
        return (self.db.query(self.lesson_model)
                .filter(self.lesson_model.type == lesson_type,
                        self.lesson_model.title == lesson_title)
                .first())

    def check_lesson_number_db(self, course_id: int, number: int):
        return (self.db.query(self.lesson_model)
                .filter(self.lesson_model.course_id == course_id,
                        self.lesson_model.number == number)
                .count())

    def update_lesson_number_db(self, number: int, course_id: int):
        (self.db.query(self.lesson_model)
         .filter(self.lesson_model.course_id == course_id,
                 self.lesson_model.number >= number)
         .update(
            {self.lesson_model.number: self.lesson_model.number + 1}, synchronize_session=False))

        self.db.commit()

    def update_lesson(self, lesson_id: int, data: LessonUpdate):
        lesson = self.db.query(self.lesson_model).filter(self.lesson_model.id == lesson_id).first()

        for key, value in data.dict().items():
            if value:
                setattr(lesson, key, value)

        self.db.commit()

    def search_lesson(self, query: str):
        regex_query = fr"\y{query}.*"
        return self.db.query(self.lesson_model).filter(self.lesson_model.title.op('~*')(regex_query)).all()

    def get_lesson_info(self, lessons: List[LessonOrm]):
        for lesson in lessons:
            if lesson.type == LessonType.exam.value:
                count_questions = self.exam_repo.select_quantity_question(lesson_id=lesson.id)
                setattr(lesson, "count_questions", count_questions)

            elif lesson.type == LessonType.test.value:
                count_questions = self.test_repo.select_quantity_question(lesson_id=lesson.id)
                setattr(lesson, "count_questions", count_questions)

            else:
                continue

    def check_validity_lessons(self, course_id: int):
        tests_score = self.test_repo.select_test_sum_scores(course_id=course_id)
        exam_orm = self.exam_repo.select_exam_score(course_id=course_id)

        if exam_orm is None:
            return {
                "result": False,
                "message": "Create exam before publishing course"
            }

        tests = self.test_repo.select_tests_in_course(course_id=course_id)
        for test in tests:
            test_question_scores = self.test_repo.select_sum_questions_score(test_id=test.id)
            if test_question_scores != test.score:
                return {
                    "result": False,
                    "message": f"Sum for all question in test not equal its score",
                    "test_info": {
                        "test_id": test.id,
                        "test_score": test.score,
                        "lesson_id": test.lesson_id
                    }
                }

        exam_question_score = self.exam_repo.select_sum_questions_score(exam_id=exam_orm.id)
        if exam_question_score != exam_orm.score:
            return {
                "result": False,
                "message": f"Sum for all question in exam not equal its score",
                "exam_info": {
                    "exam_id": exam_orm.id,
                    "exam_score": exam_orm.score,
                    "lesson_id": exam_orm.lesson_id
                }
            }

        if tests_score + exam_orm.score != 200:
            return {
                "result": False,
                "message": "Course score not equals 200",
                "exam_info": {
                    "exam_id": exam_orm.id,
                    "exam_score": exam_orm.score,
                    "lesson_id": exam_orm.lesson_id
                },
                "test_info": [
                    {
                        "test_id": test.id,
                        "test_score": test.score,
                        "lesson_id": test.lesson_id
                    } for test in tests
                ]
            }

        else:
            return {
                "result": True,
                "message": "Course successfully published"
            }
