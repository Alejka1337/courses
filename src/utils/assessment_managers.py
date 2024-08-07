from abc import ABC, abstractmethod


from sqlalchemy.orm import Session

from src.schemas.student_exam import StudentExam, ExamNewAttempt, StudentAnswerDetail, StudentExamAnswer, \
    StudentExamAnswers, StudentAnswersDetail, StudentMatchingDetail, StudentExamMatching
from src.crud.exam import ExamRepository
from src.crud.student_exam import StudentExamRepository
from src.enums import QuestionTypeOption


# class AssessmentManagerABC(ABC):
#
#     @abstractmethod
#     def get_attempt_number(self) -> int:
#         pass
#
#     @abstractmethod
#     def format_attempt_data(self, number: int):
#         pass
#
#     @abstractmethod
#     def create_new_attempt(self):
#         pass
#
#     @abstractmethod
#     def update_attempt_score(self):
#         pass
#
#     @abstractmethod
#     def inspect_match_question(self, q_id: int, student_matching: list):
#         pass
#
#     @abstractmethod
#     def inspect_multiple_question(self, q_id: int, a_ids: list[int]):
#         pass
#
#     @abstractmethod
#     def inspect_classic_question(self, q_id: int, a_id: int):
#         pass
#
#     @abstractmethod
#     def start_inspect(self): pass
#
#     @abstractmethod
#     def create_student_answer(self): pass
#
#     @abstractmethod
#     def create_student_answers(self): pass
#
#     @abstractmethod
#     def create_student_matching(self): pass


class ExamManager:
    _repository = None
    _student_repository = None

    def __init__(self, student_id: int, data: StudentExam, db: Session):
        self._lesson_id = data.lesson_id
        self._answers = data.student_answers
        self._db = db
        self._student_id = student_id
        self._final_score = 0
        self._exam_id = self.get_exam_id()

    @property
    def repository(self):
        if self._repository is None:
            self._repository = ExamRepository(db=self._db)
        return self._repository

    @property
    def student_repository(self):
        if self._student_repository is None:
            self._student_repository = StudentExamRepository(db=self._db)
        return self._student_repository

    def get_exam_id(self):
        exam_id = self._repository.select_exam_id(lesson_id=self._lesson_id)
        return exam_id

    def get_attempt_number(self) -> int:
        last_attempt = self._student_repository.select_last_attempt_number(
            student_id=self._student_id,
            exam_id=self._exam_id
        )

        attempt_number = last_attempt + 1 if last_attempt else 1
        return attempt_number

    def format_attempt_data(self, number: int) -> ExamNewAttempt:
        new_attempt_detail = ExamNewAttempt(
            number=number,
            score=self._final_score,
            exam_id=self._exam_id,
            student_id=self._student_id
        )

        return new_attempt_detail

    def create_new_attempt(self, attempt_data: ExamNewAttempt):
        new_attempt = self.student_repository.create_attempt(attempt_detail=attempt_data)
        return new_attempt.id

    def update_attempt_score(self):
        pass

    def start_inspect(self):
        attempt_number = self.get_attempt_number()
        attempt_data = self.format_attempt_data(attempt_number)
        new_attempt_id = self.create_new_attempt(attempt_data=attempt_data)

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
                self.create_student_answers(new_attempt_id=new_attempt_id, question_score=question_score, answer=answer)

            else:
                question_score = self.inspect_classic_question(q_id=answer.q_id, a_id=answer.a_id)
                self._final_score += question_score
                self.create_student_answer(new_attempt_id=new_attempt_id, question_score=question_score, answer=answer)

        pass

    def inspect_match_question(self, q_id: int, student_matching: list):
        question = self.repository.select_exam_question(question_id=q_id)
        total_score = 0
        score_for_match = int(question.q_score / 4)

        for match in student_matching:
            correct_right = self.repository.select_correct_right_option(left_id=match.left_id)
            if match.right_id == correct_right:
                total_score += score_for_match

        return total_score

    def inspect_multiple_question(self, q_id: int, a_ids: list[int]):
        question = self.repository.select_exam_question(question_id=q_id)
        count_correct = self.repository.select_count_correct_answers(question_id=question.id)
        correct_answers_ids = self.repository.select_correct_answers(question_id=question.id)
        score_for_correct = int(question.q_score / count_correct)
        count_student_answer = len(a_ids)
        total_score = 0

        for a_id in a_ids:
            if a_id in correct_answers_ids:
                total_score += score_for_correct

        if count_student_answer > count_correct:
            diff = count_student_answer - count_correct
            total_score = total_score - (diff * score_for_correct)
            return total_score if total_score >= 0 else 0

        return total_score

    def inspect_classic_question(self, q_id: int, a_id: int):
        question = self.repository.select_exam_question(question_id=q_id)
        answer_id = self.repository.select_correct_answer(question_id=question.id)
        if answer_id != a_id:
            return 0
        else:
            return question.q_score

    def create_student_answer(self, new_attempt_id: int, question_score: int, answer: StudentExamAnswer):
        answer_to_db = StudentAnswerDetail(
            score=question_score,
            question_id=answer.q_id,
            question_type=answer.q_type,
            attempt_id=new_attempt_id,
            answer=answer.a_id
        )

        self.student_repository.create_student_exam_answer(answer_data=answer_to_db)

    def create_student_answers(self, new_attempt_id: int, question_score: int, answer: StudentExamAnswers):
        answers_to_db = StudentAnswersDetail(
            score=question_score,
            question_id=answer.q_id,
            question_type=answer.q_type,
            attempt_id=new_attempt_id,
            answer=answer.a_ids
        )

        self.student_repository.create_student_exam_answers(answers_data=answers_to_db)

    def create_student_matching(self, new_attempt_id: int, question_score: int, answer: StudentExamMatching):
        for match in answer.matchings:
            match_to_db = StudentMatchingDetail(
                score=(question_score/4),
                question_id=answer.q_id,
                question_type=answer.q_type,
                attempt_id=new_attempt_id,
                left_id=match.left_id,
                right_id=match.right_id
            )

            self.student_repository.create_student_exam_matching(matching_data=match_to_db)
