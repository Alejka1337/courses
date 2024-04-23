from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.crud.exam import (create_exam_answer_db, create_exam_answer_with_photo_db, create_exam_matching_db,
                           create_exam_question_db, create_exam_question_with_photo_db)
from src.models import UserOrm
from src.schemas.test import TestQuestionBase
from src.session import get_db
from src.utils.get_user import get_current_user

router = APIRouter(prefix="/exam")


@router.post("/create")
async def create_exam(
        exam_id: int,
        data: List[TestQuestionBase],
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == "moder":
        for question_data in data:
            if question_data.q_type in ["boolean", "test", "multiple_choice"]:
                question = create_exam_question_db(
                    db=db,
                    q_text=question_data.q_text,
                    q_number=question_data.q_number,
                    q_type=question_data.q_type,
                    q_score=question_data.q_score,
                    hidden=question_data.hidden,
                    exam_id=exam_id
                )

                for answer_data in question_data.answers:
                    create_exam_answer_db(
                        db=db,
                        question_id=question.id,
                        a_text=answer_data.a_text,
                        is_correct=answer_data.is_correct
                    )

            elif question_data.q_type == "answer_with_photo":
                question = create_exam_question_db(
                    db=db,
                    q_text=question_data.q_text,
                    q_number=question_data.q_number,
                    q_type=question_data.q_type,
                    q_score=question_data.q_score,
                    hidden=question_data.hidden,
                    exam_id=exam_id
                )

                for answer_data in question_data.answers:
                    create_exam_answer_with_photo_db(
                        db=db,
                        question_id=question.id,
                        a_text=answer_data.a_text,
                        is_correct=answer_data.is_correct,
                        image_path=answer_data.image_path
                    )

            elif question_data.q_type == "question_with_photo":
                question = create_exam_question_with_photo_db(
                    db=db,
                    q_text=question_data.q_text,
                    q_number=question_data.q_number,
                    q_type=question_data.q_type,
                    q_score=question_data.q_score,
                    hidden=question_data.hidden,
                    exam_id=exam_id,
                    image_path=question_data.image_path
                )

                for answer_data in question_data.answers:
                    create_exam_answer_db(
                        db=db,
                        question_id=question.id,
                        a_text=answer_data.a_text,
                        is_correct=answer_data.is_correct
                    )

            else:
                question = create_exam_question_db(
                    db=db,
                    q_text=question_data.q_text,
                    q_number=question_data.q_number,
                    q_type=question_data.q_type,
                    q_score=question_data.q_score,
                    hidden=question_data.hidden,
                    exam_id=exam_id
                )

                for answer_data in question_data.answers:
                    create_exam_matching_db(
                        db=db,
                        left_text=answer_data.left_text,
                        right_text=answer_data.right_text,
                        question_id=question.id
                    )

        return {"message": "Exam data have been saved"}

    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
