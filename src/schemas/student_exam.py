from typing import List, Union

from pydantic import BaseModel

from src.enums import QuestionTypeOption


class StudentAnswerBase(BaseModel):
    q_id: int
    q_type: QuestionTypeOption


class StudentExamAnswer(StudentAnswerBase):
    a_id: int


class StudentExamAnswers(StudentAnswerBase):
    a_ids: List[int]


class StudentMatchingBase(BaseModel):
    left_id: int
    right_id: int


class StudentExamMatching(StudentAnswerBase):
    matching: List[StudentMatchingBase]


class StudentExam(BaseModel):
    lesson_id: int
    student_answers: List[Union[StudentExamAnswer, StudentExamAnswers, StudentExamMatching]]


class SubmitStudentExam(BaseModel):
    attempt_id: int
    student_id: int
    lesson_id: int


class ExamNewAttempt(BaseModel):
    attempt_number: int
    attempt_score: int
    exam_id: int
    student_id: int


class StudentAnswerBase(BaseModel):
    score: int
    question_id: int
    question_type: QuestionTypeOption
    attempt_id: int


class StudentAnswerDetail(StudentAnswerBase):
    answer: int


class StudentAnswersDetail(StudentAnswerBase):
    answers: List[int]


class StudentMatchingDetail(StudentAnswerBase):
    left_id: int
    right_id: int
