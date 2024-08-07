from typing import List, Union

from pydantic import BaseModel, PositiveInt

from src.enums import QuestionTypeOption


class StudentAnswerBase(BaseModel):
    q_id: PositiveInt
    q_type: QuestionTypeOption


class StudentExamAnswer(StudentAnswerBase):
    a_id: PositiveInt


class StudentExamAnswers(StudentAnswerBase):
    a_ids: List[PositiveInt]


class StudentMatchingBase(BaseModel):
    left_id: PositiveInt
    right_id: PositiveInt


class StudentExamMatching(StudentAnswerBase):
    matching: List[StudentMatchingBase]


class StudentExam(BaseModel):
    lesson_id: PositiveInt
    student_answers: List[Union[StudentExamAnswer, StudentExamAnswers, StudentExamMatching]]


class SubmitStudentExam(BaseModel):
    attempt_id: PositiveInt
    student_id: PositiveInt
    lesson_id: PositiveInt


class ExamNewAttempt(BaseModel):
    attempt_number: PositiveInt
    attempt_score: int
    exam_id: PositiveInt
    student_id: PositiveInt


class StudentAnswerBase(BaseModel):
    score: int
    question_id: PositiveInt
    question_type: QuestionTypeOption
    student_attempt_id: PositiveInt


class StudentAnswerDetail(StudentAnswerBase):
    answer_id: PositiveInt


class StudentAnswersDetail(StudentAnswerBase):
    answer_ids: List[PositiveInt]


class StudentMatchingDetail(StudentAnswerBase):
    left_id: PositiveInt
    right_id: PositiveInt
