from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.crud.exam import ExamRepository
from src.enums import QuestionTypeOption, UserType
from src.models import UserOrm
from src.schemas.test import (ExamAnswerAdd, ExamAnswerUpdate, ExamConfigUpdate, ExamMatchingAdd, ExamMatchingUpdate,
                              ExamQuestionBase, ExamQuestionUpdate)
from src.session import get_db
from src.utils.exceptions import PermissionDeniedException
from src.utils.get_user import get_current_user

router = APIRouter(prefix="/exam")


@router.patch("/update")
async def update_exam(
        exam_id: int,
        data: ExamConfigUpdate,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        repository = ExamRepository(db=db)
        repository.update_exam_config(exam_id=exam_id, data=data)
        return {"message": "Successfully updated"}

    else:
        raise PermissionDeniedException()


@router.post("/question/add")
async def add_question(
        exam_id: int,
        data: List[ExamQuestionBase],
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        repository = ExamRepository(db=db)

        for question_data in data:
            if (question_data.q_type in [
                QuestionTypeOption.boolean.value,
                QuestionTypeOption.test.value,
                QuestionTypeOption.multiple_choice.value
            ]):

                question_id = repository.create_exam_question(
                    q_text=question_data.q_text,
                    q_number=question_data.q_number,
                    q_type=question_data.q_type,
                    q_score=question_data.q_score,
                    hidden=question_data.hidden,
                    exam_id=exam_id
                )

                for answer_data in question_data.answers:
                    repository.create_exam_answer(
                        question_id=question_id,
                        a_text=answer_data.a_text,
                        is_correct=answer_data.is_correct
                    )

            elif question_data.q_type == QuestionTypeOption.answer_with_photo.value:
                question_id = repository.create_exam_question(
                    q_text=question_data.q_text,
                    q_number=question_data.q_number,
                    q_type=question_data.q_type,
                    q_score=question_data.q_score,
                    hidden=question_data.hidden,
                    exam_id=exam_id
                )

                for answer_data in question_data.answers:
                    repository.create_exam_answer(
                        question_id=question_id,
                        a_text=answer_data.a_text,
                        is_correct=answer_data.is_correct,
                        image_path=answer_data.image_path
                    )

            elif question_data.q_type == QuestionTypeOption.question_with_photo.value:
                question_id = repository.create_exam_question(
                    q_text=question_data.q_text,
                    q_number=question_data.q_number,
                    q_type=question_data.q_type,
                    q_score=question_data.q_score,
                    hidden=question_data.hidden,
                    exam_id=exam_id,
                    image_path=question_data.image_path
                )

                for answer_data in question_data.answers:
                    repository.create_exam_answer(
                        question_id=question_id,
                        a_text=answer_data.a_text,
                        is_correct=answer_data.is_correct
                    )

            else:
                question_id = repository.create_exam_question(
                    q_text=question_data.q_text,
                    q_number=question_data.q_number,
                    q_type=question_data.q_type,
                    q_score=question_data.q_score,
                    hidden=question_data.hidden,
                    exam_id=exam_id
                )

                for answer_data in question_data.answers:
                    repository.create_exam_matching(
                        left_text=answer_data.left_text,
                        right_text=answer_data.right_text,
                        question_id=question_id
                    )

        return {"message": "Exam data have been saved"}

    else:
        raise PermissionDeniedException()


@router.delete("/question/delete")
async def delete_question(
        question_id: int,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        repository = ExamRepository(db=db)
        repository.delete_question(question_id=question_id)
        return {"message": f"Question with id – {question_id} have been deleted"}

    else:
        raise PermissionDeniedException()


@router.patch("/question/update")
async def update_question(
        question_id: int,
        data: ExamQuestionUpdate,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        repository = ExamRepository(db=db)
        repository.update_question(question_id=question_id, data=data)
        return {"message": "Successfully updated"}

    else:
        raise PermissionDeniedException()


@router.post("/answer/add")
async def add_answer(
        data: ExamAnswerAdd,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        repository = ExamRepository(db=db)
        repository.create_exam_answer(
            question_id=data.question_id,
            a_text=data.a_text,
            is_correct=data.is_correct,
            image_path=data.image_path
        )
        return {"message": "Answer have been added"}
    else:
        raise PermissionDeniedException()


@router.patch("/answer/update")
async def update_answer(
        answer_id: int,
        data: ExamAnswerUpdate,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        repository = ExamRepository(db=db)
        repository.update_answer(answer_id=answer_id, data=data)
        return {"message": "Successfully updated"}

    else:
        raise PermissionDeniedException()


@router.delete("/answer/delete")
async def delete_answer(
        answer_id: int,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        repository = ExamRepository(db=db)
        repository.delete_answer(answer_id=answer_id)
        return {"message": f"Answer with id – {answer_id} have been deleted"}
    else:
        raise PermissionDeniedException()


@router.post("/matching/add")
async def add_matching(
        data: ExamMatchingAdd,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        repository = ExamRepository(db=db)
        repository.create_exam_matching(
            left_text=data.left_text,
            right_text=data.right_text,
            question_id=data.question_id
        )
        return {"message": "Matching have been added"}

    else:
        raise PermissionDeniedException()


@router.patch("/matching/update")
async def update_matching(
        left_option_id: int,
        data: ExamMatchingUpdate,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        repository = ExamRepository(db=db)
        repository.update_matching(left_id=left_option_id, data=data)
        return {"message": "Successfully updated"}

    else:
        raise PermissionDeniedException()
