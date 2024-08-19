from collections import defaultdict

from src.enums import QuestionTypeOption
from src.models import (
    StudentExamAnswerOrm,
    StudentExamMatchingOrm,
    StudentTestAnswerOrm,
    StudentTestMatchingOrm
)


def serialize_attempt_data(
        answers: list[StudentExamAnswerOrm | StudentTestAnswerOrm],
        matching: list[StudentExamMatchingOrm | StudentTestMatchingOrm]
) -> list[dict]:

    result = []

    for answer in answers:
        if answer.question_type == QuestionTypeOption.multiple_choice:
            data = {
                "q_id": answer.question_id,
                "q_type": answer.question_type,
                "a_ids": answer.answer_ids
            }
            result.append(data)
        else:
            data = {
                "q_id": answer.question_id,
                "q_type": answer.question_type,
                "a_id": answer.answer_id
            }
            result.append(data)

    grouped_answers = defaultdict(list)
    for match in matching:
        grouped_answers[match.question_id].append({
            "left_id": match.left_id,
            "right_id": match.right_id
        })

    for question_id, answers in grouped_answers.items():
        data = {
            "q_id": question_id,
            "q_type": "matching",
            "matching": answers
        }
        result.append(data)

    return result
