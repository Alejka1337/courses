from sqlalchemy.orm import Session

from src.enums import LessonStatus, QuestionTypeOption
from src.models import (LessonOrm, StudentLessonOrm, TestAnswerOrm, TestMatchingLeftOrm, TestMatchingRightOrm, TestOrm,
                        TestQuestionOrm)
from src.schemas.test import TestAnswerUpdate, TestConfigUpdate, TestMatchingUpdate, TestQuestionUpdate


class TestRepository:
    def __init__(self, db: Session):
        self.db = db
        self.model = TestOrm
        self.lesson_model = LessonOrm
        self.student_lesson_model = StudentLessonOrm
        self.question_model = TestQuestionOrm
        self.answer_model = TestAnswerOrm
        self.matching_left_model = TestMatchingLeftOrm
        self.matching_right_model = TestMatchingRightOrm

    def create_test_question(
            self,
            q_text: str,
            q_number: int,
            q_type: str,
            q_score: int,
            hidden: bool,
            test_id: int,
            image_path: str = None
    ):
        question = self.question_model(
            q_text=q_text,
            q_type=q_type,
            q_number=q_number,
            q_score=q_score,
            hidden=hidden,
            test_id=test_id,
            image_path=image_path if image_path else None
        )
        self.db.add(question)
        self.db.commit()
        self.db.refresh(question)
        return question.id

    def create_test_answer(
            self,
            question_id: int,
            a_text: str,
            is_correct: bool,
            image_path: str = None
    ):
        answer = self.answer_model(
            a_text=a_text,
            is_correct=is_correct,
            question_id=question_id,
            image_path=image_path if image_path else None
        )
        self.db.add(answer)
        self.db.commit()
        self.db.refresh(answer)

    def create_test_matching(
            self,
            left_text: str,
            right_text: str,
            question_id: int
    ):
        right_option = self.matching_right_model(text=right_text, question_id=question_id)
        self.db.add(right_option)
        self.db.commit()

        left_option = self.matching_left_model(text=left_text, question_id=question_id, right_id=right_option.id)
        self.db.add(left_option)
        self.db.commit()

        self.db.refresh(right_option)
        self.db.refresh(left_option)

    def select_test_question(self, question_id: int):
        return self.db.query(self.question_model).filter(self.question_model.id == question_id).first()

    def select_test_answers(self, question_id: int):
        return self.db.query(self.answer_model).filter(self.answer_model.question_id == question_id).all()

    def select_correct_answer(self, question_id: int):
        return (self.db.query(self.answer_model.id)
                .filter(self.answer_model.question_id == question_id)
                .filter(self.answer_model.is_correct)
                .scalar())

    def select_correct_answers(self, question_id: int):
        answers_ids = (self.db.query(self.answer_model.id.label("id"))
                       .filter(self.answer_model.question_id == question_id)
                       .filter(self.answer_model.is_correct)
                       .all())

        answers = [answer.id for answer in answers_ids]
        return answers

    def select_total_correct_answers(self, question_id: int):
        total = (self.db.query(self.answer_model.id.label("id"))
                 .filter(self.answer_model.question_id == question_id)
                 .filter(self.answer_model.is_correct)
                 .count())
        return total

    def select_correct_right(self, left_id: int):
        return (self.db.query(self.matching_left_model.right_id)
                .filter(self.matching_left_model.id == left_id)
                .scalar())

    def select_test_id_by_lesson_id(self, lesson_id: int):
        return self.db.query(self.model.id).filter(self.model.lesson_id == lesson_id).scalar()

    def update_test_config(self, test_id: int, data: TestConfigUpdate):
        test = self.db.query(self.model).filter(self.model.id == test_id).first()

        for field, value in data.dict(exclude_unset=True).items():
            setattr(test, field, value)

        self.db.commit()
        self.db.refresh(test)

    def update_question(self, question_id: int, data: TestQuestionUpdate):
        question = self.db.query(self.question_model).filter(self.question_model.id == question_id).first()

        for field, value in data.dict(exclude_unset=True).items():
            setattr(question, field, value)

        self.db.commit()
        self.db.refresh(question)

    def update_answer(self, answer_id: int, data: TestAnswerUpdate):
        answer = self.db.query(self.answer_model).filter(self.answer_model.id == answer_id).first()

        for field, value in data.dict(exclude_unset=True).items():
            setattr(answer, field, value)

        self.db.commit()
        self.db.refresh(answer)

    def update_matching(self, left_id: int, data: TestMatchingUpdate):
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

    def select_test_data(self, lesson: LessonOrm, student_id: int = None):
        test = self.db.query(TestOrm).filter(TestOrm.lesson_id == lesson.id).first()

        if test:
            test_questions = self.db.query(self.question_model).filter(self.question_model.test_id == test.id).all()
            test_data = {"test_id": test.id, "score": test.score, "attempts": test.attempts, "questions": []}

            if student_id:
                student_test_info = (self.db.query(self.student_lesson_model)
                                     .filter(self.student_lesson_model.lesson_id == lesson.id)
                                     .filter(self.student_lesson_model.student_id == student_id)
                                     .first())
                if student_test_info.status == LessonStatus.completed.value:
                    test_data["my_score"] = student_test_info.score

            for question in test_questions:

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
                    answers = self.select_test_answers(question_id=question.id)

                    for answer in answers:
                        answer_data = {"a_id": answer.id, "a_text": answer.a_text, "is_correct": answer.is_correct}
                        question_data["answers"].append(answer_data)

                elif question.q_type == QuestionTypeOption.answer_with_photo.value:
                    answers = self.select_test_answers(question_id=question.id)

                    for answer in answers:
                        answer_data = {"a_id": answer.id, "a_text": answer.a_text, "is_correct": answer.is_correct,
                                       "image_path": answer.image_path}
                        question_data["answers"].append(answer_data)

                elif question.q_type == QuestionTypeOption.question_with_photo.value:
                    question_data["image_path"] = question.image_path
                    answers = self.select_test_answers(question_id=question.id)

                    for answer in answers:
                        answer_data = {"a_id": answer.id, "a_text": answer.a_text, "is_correct": answer.is_correct}
                        question_data["answers"].append(answer_data)

                elif question.q_type == QuestionTypeOption.multiple_choice.value:
                    answers = self.select_test_answers(question_id=question.id)
                    counter = 0

                    for answer in answers:
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

                test_data["questions"].append(question_data)

            setattr(lesson, "test_data", test_data)
            return lesson

        else:
            return lesson
