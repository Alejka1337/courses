from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.crud.test import TestRepository
from src.enums import UserType
from src.models import UserOrm
from src.schemas.test import (QuestionListResponse, TestAnswerAdd, TestAnswerUpdate, TestConfigUpdate, TestMatchingAdd,
                              TestMatchingUpdate, TestQuestionBase, TestQuestionUpdate)
from src.session import get_db
from src.utils.create_test import create_test_logic
from src.utils.exceptions import PermissionDeniedException
from src.utils.get_user import get_current_user

router = APIRouter(prefix="/test")


@router.patch("/update")
async def update_test(
        test_id: int,
        data: TestConfigUpdate,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        repository = TestRepository(db=db)
        repository.update_test_config(test_id=test_id, data=data)
        return {"message": "Successfully updated"}

    else:
        raise PermissionDeniedException()


@router.post("/question/add", response_model=QuestionListResponse)
async def create_test(
        test_id: int,
        data: List[TestQuestionBase],
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        repository = TestRepository(db=db)
        return create_test_logic(repository=repository, data=data, test_id=test_id)
    else:
        raise PermissionDeniedException()


@router.delete("/question/delete")
async def delete_test_question(
        question_id: int,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        repository = TestRepository(db=db)
        repository.delete_question(question_id=question_id)
        return {"message": f"Question with id – {question_id} have been deleted"}

    else:
        raise PermissionDeniedException()


@router.patch("/question/update")
async def update_test_question(
        question_id: int,
        data: TestQuestionUpdate,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        repository = TestRepository(db=db)
        repository.update_question(question_id=question_id, data=data)
        return {"message": "Successfully updated"}

    else:
        raise PermissionDeniedException()


@router.post("/answer/add")
async def add_test_answer(
        data: TestAnswerAdd,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        repository = TestRepository(db=db)
        repository.create_test_answer(
            question_id=data.question_id,
            a_text=data.a_text,
            is_correct=data.is_correct,
            image_path=data.image_path
        )
        return {"message": "Answer have been added"}
    else:
        raise PermissionDeniedException()


@router.delete("/answer/delete")
async def delete_test_answer(
        answer_id: int,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        repository = TestRepository(db=db)
        repository.delete_answer(answer_id=answer_id)
        return {"message": f"Answer with id – {answer_id} have been deleted"}
    else:
        raise PermissionDeniedException()


@router.patch("/answer/update")
async def update_test_answer(
        answer_id: int,
        data: TestAnswerUpdate,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        repository = TestRepository(db=db)
        repository.update_answer(answer_id=answer_id, data=data)
        return {"message": "Successfully updated"}

    else:
        raise PermissionDeniedException()


@router.post("/matching/add")
async def add_test_matching(
        data: TestMatchingAdd,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        repository = TestRepository(db=db)
        repository.create_test_matching(
            left_text=data.left_text,
            right_text=data.right_text,
            question_id=data.question_id
        )
        return {"message": "Matching have been added"}

    else:
        raise PermissionDeniedException()


@router.patch("/matching/update")
async def update_test_matching(
        left_option_id: int,
        data: TestMatchingUpdate,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        repository = TestRepository(db=db)
        repository.update_matching(left_id=left_option_id, data=data)
        return {"message": "Successfully updated"}

    else:
        raise PermissionDeniedException()
