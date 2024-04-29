from src.crud.exam import ExamRepository
from src.models import ExamQuestionOrm


class StudentExamService:
    def __init__(self, repository: ExamRepository):
        self.repository = repository

    def check_student_exam_matching(self, student_matching: list, question: ExamQuestionOrm):
        total_score = 0
        score_for_match = int(question.q_score / 4)

        for match in student_matching:
            correct_right = self.repository.select_correct_right_option(left_id=match.left_id)
            if match.right_id == correct_right:
                total_score += score_for_match

        return total_score

    def check_student_multiple_choice_exam(self, question: ExamQuestionOrm, student_answers: list):
        count_correct = self.repository.select_count_correct_answers(question_id=question.id)
        correct_answers = self.repository.select_correct_answers(question_id=question.id)
        score_for_correct = int(question.q_score / count_correct)
        count_student_answer = len(student_answers)
        total_score = 0

        if count_student_answer == count_correct:
            for student_answer in student_answers:
                if student_answer in correct_answers:
                    total_score += score_for_correct
            return total_score

        else:
            for student_answer in student_answers:
                if student_answer in correct_answers:
                    total_score += score_for_correct

            if count_student_answer > count_correct:
                diff = count_student_answer - count_correct
                total_score = total_score - (diff * score_for_correct)
                return total_score if total_score >= 0 else 0

    def check_student_default_exam(self, question: ExamQuestionOrm, student_answer: int):
        answer_id = self.repository.select_correct_answer(question_id=question.id)
        if answer_id != student_answer:
            return 0
        else:
            return question.q_score
