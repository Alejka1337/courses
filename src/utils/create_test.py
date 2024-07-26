from typing import List

from src.crud.test import TestRepository
from src.schemas.test import (TestQuestionBase, QuestionListResponse, TestQuestionResponse, TestAnswerResponse,
                              MatchingLeft, MatchingRight, MatchingItem)
from src.enums import QuestionTypeOption


def create_test_logic(repository: TestRepository,  data: List[TestQuestionBase], test_id: int) -> QuestionListResponse:
    response_list = []

    for question_data in data:
        question_orm = repository.create_test_question(
            q_text=question_data.q_text,
            q_number=question_data.q_number,
            q_type=question_data.q_type,
            q_score=question_data.q_score,
            hidden=question_data.hidden,
            image_path=question_data.image_path if question_data.image_path else None,
            test_id=test_id
        )

        answers = []

        if question_data.q_type != QuestionTypeOption.matching.value:

            for answer_data in question_data.answers:
                answer_orm = repository.create_test_answer(
                    question_id=question_orm.id,
                    a_text=answer_data.a_text,
                    is_correct=answer_data.is_correct
                )

                answers.append(TestAnswerResponse.from_orm(answer_orm))

            question_response = TestQuestionResponse(
                q_id=question_orm.id,
                q_text=question_orm.q_text,
                q_number=question_orm.q_number,
                q_score=question_orm.q_score,
                q_type=question_orm.q_type,
                hidden=question_orm.hidden,
                image_path=question_orm.image_path,
                answers=answers
            )

            response_list.append(question_response)

        else:
            left = []
            right = []

            for answer_data in question_data.answers:
                left_orm, right_orm = repository.create_test_matching(
                    left_text=answer_data.left_text,
                    right_text=answer_data.right_text,
                    question_id=question_orm.id
                )

                left_item = MatchingItem(id=left_orm.id, value=left_orm.text)
                left.append(left_item)

                right_item = MatchingItem(id=right_orm.id, value=right_orm.text)
                right.append(right_item)

            answers.append(MatchingLeft(left=left))
            answers.append(MatchingRight(right=right))

            question_response = TestQuestionResponse(
                q_id=question_orm.id,
                q_text=question_orm.q_text,
                q_number=question_orm.q_number,
                q_score=question_orm.q_score,
                q_type=question_orm.q_type,
                hidden=question_orm.hidden,
                image_path=question_orm.image_path,
                answers=answers
            )

            response_list.append(question_response)

    return QuestionListResponse(questions=response_list)
