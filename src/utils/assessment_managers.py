from sqlalchemy.orm import Session

from src.crud.exam import ExamRepository
from src.crud.student_exam import StudentExamRepository
from src.crud.student_test import StudentTestRepository
from src.crud.test import TestRepository
from src.enums import QuestionTypeOption
from src.models import StudentExamAttemptsOrm, StudentTestAttemptsOrm
from src.schemas.student_practical import (
    ExamNewAttempt,
    StudentAnswer,
    StudentAnswerDetail,
    StudentAnswers,
    StudentAnswersDetail,
    StudentMatchingDetail,
    StudentMatchingList,
    StudentPractical,
    TestNewAttempt,
)
from src.utils.exceptions import MaxAttemptException


class AssessmentManager:
    _repository = None
    _student_repository = None

    def __init__(self, student_id: int, data: StudentPractical, db: Session):
        self._lesson_id = data.lesson_id
        self._answers = data.student_answers
        self._db = db
        self._student_id = student_id
        self._final_score = 0
        self._assessment_id = self.get_assessment_id()

    @property
    def repository(self):
        if self._repository is None:
            self._repository = self.get_repository()
        return self._repository

    @property
    def student_repository(self):
        if self._student_repository is None:
            self._student_repository = self.get_student_repository()
        return self._student_repository

    def get_assessment_id(self):
        raise NotImplementedError("This method should be implemented in subclasses")

    def get_repository(self):
        raise NotImplementedError("This method should be implemented in subclasses")

    def get_student_repository(self):
        raise NotImplementedError("This method should be implemented in subclasses")

    def get_attempt_number(self) -> int:
        raise NotImplementedError("This method should be implemented in subclasses")

    def format_attempt_data(self, number: int):
        raise NotImplementedError("This method should be implemented in subclasses")

    def create_new_attempt(self, number: int) -> int:
        format_data = self.format_attempt_data(number=number)
        new_attempt = self.student_repository.create_attempt(attempt_data=format_data)
        return new_attempt.id

    def update_attempt_score(self, attempt_id: int):
        raise NotImplementedError("This method should be implemented in subclasses")

    def start_inspect(self) -> StudentExamAttemptsOrm | StudentTestAttemptsOrm:
        attempt_number = self.get_attempt_number()
        new_attempt_id = self.create_new_attempt(attempt_number)

        for answer in self._answers:
            if answer.q_type == QuestionTypeOption.matching.value:
                question_score = self.inspect_match_question(q_id=answer.q_id, student_matching=answer.matching)
                self._final_score += question_score
                self.create_student_matching(
                    new_attempt_id=new_attempt_id, question_score=question_score, answer=answer
                )

            elif answer.q_type == QuestionTypeOption.multiple_choice.value:
                question_score = self.inspect_multiple_question(q_id=answer.q_id, a_ids=answer.a_ids)
                self._final_score += question_score
                self.create_student_answers(
                    new_attempt_id=new_attempt_id, question_score=question_score, answer=answer
                )

            else:
                question_score = self.inspect_classic_question(q_id=answer.q_id, a_id=answer.a_id)
                self._final_score += question_score
                self.create_student_answer(
                    new_attempt_id=new_attempt_id, question_score=question_score, answer=answer
                )

        attempt = self.update_attempt_score(attempt_id=new_attempt_id)
        return attempt

    def inspect_match_question(self, q_id: int, student_matching: list) -> int:
        question = self.repository.select_question(question_id=q_id)
        total_score = 0
        score_for_match = question.q_score / 4

        for match in student_matching:
            correct_right = self.repository.select_correct_right_option(left_id=match.left_id)
            if match.right_id == correct_right:
                total_score += score_for_match

        return round(total_score)

    def inspect_multiple_question(self, q_id: int, a_ids: list[int]) -> int:
        question = self.repository.select_question(question_id=q_id)
        count_correct = self.repository.select_count_correct_answers(question_id=question.id)
        correct_answers_ids = self.repository.select_correct_answers(question_id=question.id)
        score_for_correct = question.q_score / count_correct
        count_student_answer = len(a_ids)
        total_score = 0

        for a_id in a_ids:
            if a_id in correct_answers_ids:
                total_score += score_for_correct

        if count_student_answer > count_correct:
            diff = count_student_answer - count_correct
            total_score = total_score - (diff * score_for_correct)
            return round(total_score) if total_score > 0 else 0

        return round(total_score)

    def inspect_classic_question(self, q_id: int, a_id: int) -> int:
        question = self.repository.select_question(question_id=q_id)
        answer_id = self.repository.select_correct_answer(question_id=question.id)
        if answer_id != a_id:
            return 0
        else:
            return question.q_score

    def create_student_answer(self, new_attempt_id: int, question_score: int, answer: StudentAnswer) -> None:
        answer_to_db = StudentAnswerDetail(
            score=question_score,
            question_id=answer.q_id,
            question_type=answer.q_type,
            student_attempt_id=new_attempt_id,
            answer_id=answer.a_id
        )

        self.student_repository.create_student_answer(answer_data=answer_to_db)

    def create_student_answers(self, new_attempt_id: int, question_score: int, answer: StudentAnswers) -> None:
        answers_to_db = StudentAnswersDetail(
            score=question_score,
            question_id=answer.q_id,
            question_type=answer.q_type,
            student_attempt_id=new_attempt_id,
            answer_ids=answer.a_ids
        )

        self.student_repository.create_student_answers(answers_data=answers_to_db)

    def create_student_matching(self, new_attempt_id: int, question_score: int, answer: StudentMatchingList) -> None:
        for match in answer.matching:
            match_to_db = StudentMatchingDetail(
                score=(question_score / 4),
                question_id=answer.q_id,
                question_type=answer.q_type,
                student_attempt_id=new_attempt_id,
                left_id=match.left_id,
                right_id=match.right_id
            )

            self.student_repository.create_student_matching(matching_data=match_to_db)


class ExamManager(AssessmentManager):

    def get_assessment_id(self) -> int:
        return self.repository.select_exam_id(lesson_id=self._lesson_id)

    def get_repository(self) -> ExamRepository:
        return ExamRepository(db=self._db)

    def get_student_repository(self) -> StudentExamRepository:
        return StudentExamRepository(db=self._db)

    def get_attempt_number(self) -> int:
        last_attempt = self.student_repository.select_last_attempt_number(
            student_id=self._student_id,
            exam_id=self._assessment_id
        )

        attempt_number = last_attempt + 1 if last_attempt else 1
        count_attempt = self.repository.select_count_attempt(lesson_id=self._lesson_id)

        if attempt_number > count_attempt:
            raise MaxAttemptException()

        return attempt_number

    def format_attempt_data(self, number: int) -> ExamNewAttempt:
        new_attempt_detail = ExamNewAttempt(
            attempt_number=number,
            attempt_score=self._final_score,
            exam_id=self._assessment_id,
            student_id=self._student_id
        )
        return new_attempt_detail

    def update_attempt_score(self, attempt_id: int) -> StudentExamAttemptsOrm:
        return self.student_repository.update_attempt_score(attempt_id=attempt_id, score=self._final_score)


class TestManager(AssessmentManager):

    def get_assessment_id(self) -> int:
        return self.repository.select_test_id(lesson_id=self._lesson_id)

    def get_repository(self) -> TestRepository:
        return TestRepository(db=self._db)

    def get_student_repository(self) -> StudentTestRepository:
        return StudentTestRepository(db=self._db)

    def get_attempt_number(self) -> int:
        last_attempt = self.student_repository.select_last_attempt_number(
            student_id=self._student_id,
            test_id=self._assessment_id
        )

        attempt_number = last_attempt + 1 if last_attempt else 1
        count_attempt = self.repository.select_count_attempt(lesson_id=self._lesson_id)

        if attempt_number > count_attempt:
            raise MaxAttemptException()

        return attempt_number

    def format_attempt_data(self, number: int) -> TestNewAttempt:
        new_attempt_detail = TestNewAttempt(
            attempt_number=number,
            attempt_score=self._final_score,
            test_id=self._assessment_id,
            student_id=self._student_id
        )
        return new_attempt_detail

    def update_attempt_score(self, attempt_id: int) -> StudentTestAttemptsOrm:
        return self.student_repository.update_attempt_score(attempt_id=attempt_id, score=self._final_score)
