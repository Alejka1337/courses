from sqlalchemy import func
from sqlalchemy.orm import Session

from src.enums import LessonStatus, LessonType, QuestionTypeOption
from src.models import (
    ExamAnswerOrm,
    ExamMatchingLeftOrm,
    ExamMatchingRightOrm,
    ExamOrm,
    ExamQuestionOrm,
    LessonOrm,
    StudentLessonOrm,
    TestOrm,
)
from src.schemas.practical import (
    ExamAnswerUpdate,
    ExamConfigUpdate,
    ExamMatchingUpdate,
    ExamQuestionUpdate,
)


class ExamRepository:
    def __init__(self, db: Session):
        self.db = db
        self.exam_model = ExamOrm
        self.test_model = TestOrm
        self.lesson_model = LessonOrm
        self.student_lesson_model = StudentLessonOrm
        self.question_model = ExamQuestionOrm
        self.answer_model = ExamAnswerOrm
        self.matching_left_model = ExamMatchingLeftOrm
        self.matching_right_model = ExamMatchingRightOrm

    def create_exam(self, lesson_id: int, course_id: int):
        count_test = (self.db.query(self.lesson_model)
                      .filter(self.lesson_model.course_id == course_id,
                              self.lesson_model.type == LessonType.test.value)
                      .count())

        exam_score = 200
        if count_test > 0:
            test_lesson_ids = (self.db.query(self.lesson_model.id.label("id")).
                               filter(self.lesson_model.course_id == course_id,
                                      self.lesson_model.type == LessonType.test.value)
                               .all())

            lesson_ids = [test_lesson.id for test_lesson in test_lesson_ids]

            test_total_score = (self.db.query(func.sum(self.test_model.score))
                                .filter(self.test_model.lesson_id.in_(lesson_ids))
                                .scalar())

            exam_score -= test_total_score

        new_exam = ExamOrm(score=exam_score, attempts=10, timer=40, lesson_id=lesson_id, min_score=int(exam_score/2))
        self.db.add(new_exam)
        self.db.commit()
        self.db.refresh(new_exam)
        return new_exam

    def create_exam_question(
            self,
            q_text: str,
            q_number: int,
            q_type: str,
            q_score: int,
            hidden: bool,
            exam_id: int,
            image_path: str = None
    ) -> ExamQuestionOrm:

        question = self.question_model(
            q_text=q_text,
            q_type=q_type,
            q_number=q_number,
            q_score=q_score,
            hidden=hidden,
            exam_id=exam_id,
            image_path=image_path if image_path else None,
        )
        self.db.add(question)
        self.db.commit()
        self.db.refresh(question)
        return question

    def create_exam_answer(
            self,
            question_id: int,
            a_text: str,
            is_correct: bool,
            image_path: str = None
    ) -> ExamAnswerOrm:

        answer = self.answer_model(
            a_text=a_text,
            is_correct=is_correct,
            question_id=question_id,
            image_path=image_path if image_path else None
        )
        self.db.add(answer)
        self.db.commit()
        self.db.refresh(answer)
        return answer

    def create_exam_matching(
            self,
            left_text: str,
            right_text: str,
            question_id: int
    ) -> tuple[ExamMatchingLeftOrm, ExamMatchingRightOrm]:

        right_option = self.matching_right_model(text=right_text, question_id=question_id)
        self.db.add(right_option)
        self.db.commit()

        left_option = self.matching_left_model(text=left_text, question_id=question_id, right_id=right_option.id)
        self.db.add(left_option)
        self.db.commit()

        self.db.refresh(right_option)
        self.db.refresh(left_option)
        return left_option, right_option

    def select_question(self, question_id: int):
        return self.db.query(self.question_model).filter(self.question_model.id == question_id).first()

    def select_exam_score(self, course_id: int):
        lesson_id = (self.db.query(self.lesson_model.id)
                     .filter(self.lesson_model.course_id == course_id,
                             self.lesson_model.type == LessonType.exam.value)
                     .scalar())

        exam = (self.db.query(self.exam_model.score.label("score"),
                              self.exam_model.id.label("id"),
                              self.exam_model.lesson_id.label("lesson_id"))
                .filter(self.exam_model.lesson_id == lesson_id)
                .first())
        return exam

    def select_sum_questions_score(self, exam_id: int):
        return (self.db.query(func.sum(self.question_model.q_score))
                .filter(self.question_model.exam_id == exam_id)
                .scalar())

    def select_correct_answer(self, question_id: int) -> int:
        return (self.db.query(self.answer_model.id)
                .filter(self.answer_model.question_id == question_id)
                .filter(self.answer_model.is_correct)
                .scalar())

    def select_count_correct_answers(self, question_id: int) -> int:
        return (self.db.query(self.answer_model.id.label("id"))
                .filter(self.answer_model.question_id == question_id)
                .filter(self.answer_model.is_correct)
                .count())

    def select_correct_answers(self, question_id: int) -> list:
        answers_ids = (self.db.query(self.answer_model.id.label("id"))
                       .filter(self.answer_model.question_id == question_id)
                       .filter(self.answer_model.is_correct)
                       .all())

        answers = [answer.id for answer in answers_ids]
        return answers

    def select_correct_right_option(self, left_id: int) -> int:
        return self.db.query(self.matching_left_model.right_id).filter(self.matching_left_model.id == left_id).scalar()

    def select_exam_answers(self, question_id: int):
        return self.db.query(self.answer_model).filter(self.answer_model.question_id == question_id).all()

    def select_exam_id(self, lesson_id: int):
        return self.db.query(self.exam_model.id).filter(self.exam_model.lesson_id == lesson_id).scalar()

    def select_count_attempt(self, lesson_id: int):
        return self.db.query(self.exam_model.attempts).filter(self.exam_model.lesson_id == lesson_id).scalar()

    def select_quantity_question(self, lesson_id: int):
        quantity_question = (
            self.db.query(self.question_model.id)
            .select_from(self.exam_model)
            .join(self.question_model, self.exam_model.id == self.question_model.exam_id)
            .filter(self.exam_model.lesson_id == lesson_id)
            .count()
        )

        return quantity_question

    def update_exam_config(self, exam_id: int, data: ExamConfigUpdate):
        exam = self.db.query(self.exam_model).filter(self.exam_model.id == exam_id).first()

        for field, value in data.dict(exclude_unset=True).items():
            setattr(exam, field, value)

        self.db.commit()
        self.db.refresh(exam)

    def update_question(self, question_id: int, data: ExamQuestionUpdate):
        question = self.db.query(self.question_model).filter(self.question_model.id == question_id).first()

        for field, value in data.dict(exclude_unset=True).items():
            setattr(question, field, value)

        self.db.commit()
        self.db.refresh(question)

    def delete_question(self, question_id: int):
        question = self.select_question(question_id=question_id)

        if question.q_type == QuestionTypeOption.matching:
            match_left = (self.db.query(self.matching_left_model)
                          .filter(self.matching_left_model.question_id == question.id)
                          .all())

            match_right = (self.db.query(self.matching_right_model)
                           .filter(self.matching_right_model.question_id == question.id)
                           .all())

            for ml in match_left:
                self.db.delete(ml)

            for mr in match_right:
                self.db.delete(mr)

        else:
            answers = self.select_exam_answers(question_id=question.id)
            for answer in answers:
                self.db.delete(answer)

        self.db.delete(question)
        self.db.commit()

    def update_answer(self, answer_id: int, data: ExamAnswerUpdate):
        answer = self.db.query(self.answer_model).filter(self.answer_model.id == answer_id).first()

        for field, value in data.dict(exclude_unset=True).items():
            setattr(answer, field, value)

        self.db.commit()
        self.db.refresh(answer)

    def delete_answer(self, answer_id: int):
        answer = self.db.query(self.answer_model).filter(self.answer_model.id == answer_id).first()
        self.db.delete(answer)
        self.db.commit()

    def update_matching(self, left_id: int, data: ExamMatchingUpdate):
        left = self.db.query(self.matching_left_model).filter(self.matching_left_model.id == left_id).first()

        if data.left_text:
            left.text = data.left_text

        if data.right_text:
            right = (self.db.query(self.matching_right_model)
                     .filter(self.matching_right_model.id == left.right_id)
                     .first())
            right.text = data.right_text

        self.db.commit()
        self.db.refresh(left)

    def delete_matching(self, left_id: int) -> None:
        left = self.db.query(self.matching_left_model).filter(self.matching_left_model.id == left_id).first()
        right = self.db.query(self.matching_right_model).filter(self.matching_right_model.id == left.right_id).first()

        try:
            self.db.delete(left)
            self.db.delete(right)
            self.db.commit()
        except Exception as e:
            self.db.rollback()

    def select_exam_data(self, lesson: LessonOrm, student_id: int = None):
        exam = self.db.query(self.exam_model).filter(self.exam_model.lesson_id == lesson.id).first()

        if exam:
            exam_questions = self.db.query(self.question_model).filter(self.question_model.exam_id == exam.id).all()
            exam_data = {
                "exam_id": exam.id,
                "score": exam.score,
                "attempts": exam.attempts,
                "timer": exam.timer,
                "min_score": exam.min_score,
                "questions": []
            }

            if student_id:
                student_exam_info = (self.db.query(self.student_lesson_model)
                                     .filter(self.student_lesson_model.lesson_id == lesson.id)
                                     .filter(self.student_lesson_model.student_id == student_id)
                                     .first())

                if student_exam_info.status == LessonStatus.completed.value:
                    exam_data["my_score"] = student_exam_info.score
                    exam_data["my_attempt_id"] = student_exam_info.attempt

            for question in exam_questions:
                question_data = {
                    "q_id": question.id,
                    "q_text": question.q_text,
                    "q_number": question.q_number,
                    "q_score": question.q_score,
                    "q_type": question.q_type,
                    "hidden": question.hidden,
                    "image_path": None,
                    "answers": []
                }

                if question.q_type in [QuestionTypeOption.test.value, QuestionTypeOption.boolean.value]:
                    answers = self.select_exam_answers(question_id=question.id)

                    for answer in answers:
                        answer_data = {"a_id": answer.id, "a_text": answer.a_text, "is_correct": answer.is_correct}
                        question_data["answers"].append(answer_data)

                elif question.q_type == QuestionTypeOption.answer_with_photo.value:
                    answers = self.select_exam_answers(question_id=question.id)

                    for answer in answers:
                        answer_data = {
                            "a_id": answer.id,
                            "a_text": answer.a_text,
                            "is_correct": answer.is_correct,
                            "image_path": answer.image_path
                        }
                        question_data["answers"].append(answer_data)

                elif question.q_type == QuestionTypeOption.question_with_photo.value:
                    question_data["image_path"] = question.image_path
                    answers = self.select_exam_answers(question_id=question.id)

                    for answer in answers:
                        answer_data = {"a_id": answer.id, "a_text": answer.a_text, "is_correct": answer.is_correct}
                        question_data["answers"].append(answer_data)

                elif question.q_type == QuestionTypeOption.multiple_choice.value:
                    answers = self.select_exam_answers(question_id=question.id)

                    for answer in answers:
                        counter = 0
                        if answer.is_correct:
                            counter += 1

                        answer_data = {"a_id": answer.id, "a_text": answer.a_text, "is_correct": answer.is_correct}
                        question_data["answers"].append(answer_data)
                        question_data["count_correct"] = counter

                else:
                    left_options = (self.db.query(self.matching_left_model)
                                    .filter(self.matching_left_model.question_id == question.id).all())

                    right_options = (self.db.query(self.matching_right_model)
                                     .filter(self.matching_right_model.question_id == question.id).all())

                    question_data["answers"] = {
                        "left": [
                            {
                                "value": left_option.text,
                                "id": left_option.id
                            } for left_option in left_options
                        ],
                        "right": [
                            {
                                "value": right_option.text,
                                "id": right_option.id
                            } for right_option in right_options
                        ]
                    }

                exam_data["questions"].append(question_data)
            setattr(lesson, "exam_data", exam_data)
            return lesson
        else:
            return lesson