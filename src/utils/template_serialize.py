from typing import Type

from src.models import LessonTemplateOrm
from src.enums import QuestionTypeOption
from src.schemas.template import (
    LectureTemplateResponse,
    PracticalTemplateResponse
)

from src.schemas.lecture import (
    LectureAttributeResponse,
    FileResponse,
    LinkResponse
)

from src.schemas.practical import (
    QuestionResponse,
    AnswerResponse,
    MatchingResponse,
    MatchingItem
)


def serialize_lecture_response(template_db_data: Type[LessonTemplateOrm]) -> LectureTemplateResponse:
    attribute_list = []

    for lecture_attr in template_db_data.lecture_template:
        files_list = []
        links_list = []

        if len(lecture_attr.files) >= 1:
            for file in lecture_attr.files:
                files_list.append(FileResponse.from_orm(file))

        if len(lecture_attr.links) >= 1:
            for link in lecture_attr.links:
                links_list.append(LinkResponse.from_orm(link))

        attribute_list.append(
            LectureAttributeResponse(
                a_id=lecture_attr.id,
                a_type=lecture_attr.a_type,
                a_number=lecture_attr.a_number,
                a_title=lecture_attr.a_title,
                a_text=lecture_attr.a_text,
                hidden=lecture_attr.hidden,
                files=files_list,
                links=links_list)
        )

    return LectureTemplateResponse(
        id=template_db_data.id,
        title=template_db_data.title,
        type=template_db_data.type,
        lecture_template=attribute_list
    )


def serialize_practical_response(template_db_data: Type[LessonTemplateOrm]) -> PracticalTemplateResponse:
    result = []

    for question_data in template_db_data.practical_template:
        answer_list = []

        if question_data.q_type != QuestionTypeOption.matching.value:
            for answer in question_data.answers:
                answer_list.append(AnswerResponse.from_orm(answer))

        else:
            left_list = []
            right_list = []

            for left, right in zip(question_data.left_option, question_data.right_option):
                left_list.append(MatchingItem(id=left.id, value=left.text))
                right_list.append(MatchingItem(id=right.id, value=right.text))

            answer_list.append(MatchingResponse(left=left_list, right=right_list))

        q_response = QuestionResponse(
            q_id=question_data.id,
            q_text=question_data.q_text,
            q_number=question_data.q_number,
            q_score=question_data.q_score,
            q_type=question_data.q_type,
            hidden=question_data.hidden,
            image_path=question_data.image_path,
            answers=answer_list
        )

        result.append(q_response)

    return PracticalTemplateResponse(
        id=template_db_data.id,
        title=template_db_data.title,
        type=template_db_data.type,
        practical_template=result
    )
