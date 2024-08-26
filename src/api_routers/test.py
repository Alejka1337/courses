from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.crud.test import TestRepository
from src.models import UserOrm
from src.schemas.practical import (
    DeleteMessageResponse,
    MatchingResponseAfterAdd,
    MatchingTuple,
    QuestionListResponse,
    TestAnswerAdd,
    TestAnswerResponse,
    TestAnswerUpdate,
    TestConfigUpdate,
    TestMatchingAdd,
    TestMatchingUpdate,
    TestQuestionBase,
    TestQuestionUpdate,
    UpdateMessageResponse,
)
from src.session import get_db
from src.utils.create_practical import CreatePracticalLesson
from src.utils.exceptions import PermissionDeniedException
from src.utils.get_user import get_current_user

router = APIRouter(prefix="/test")


@router.patch("/update", response_model=UpdateMessageResponse)
async def update_test(
        test_id: int,
        data: TestConfigUpdate,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.is_moder:
        repository = TestRepository(db=db)
        repository.update_test_config(test_id=test_id, data=data)
        return UpdateMessageResponse()

    else:
        raise PermissionDeniedException()


@router.post("/question/add", response_model=QuestionListResponse)
async def create_test(
        test_id: int,
        data: List[TestQuestionBase],
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.is_moder:
        # repository = TestRepository(db=db)
        practical_worker = CreatePracticalLesson(
            mode="test",
            db=db,
            questions_data=data,
            practical_id=test_id
        )
        return practical_worker.start_creating()
    else:
        raise PermissionDeniedException()


@router.delete("/question/delete", response_model=DeleteMessageResponse)
async def delete_test_question(
        question_id: int,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.is_moder:
        repository = TestRepository(db=db)
        repository.delete_question(question_id=question_id)
        return DeleteMessageResponse()

    else:
        raise PermissionDeniedException()


@router.patch("/question/update", response_model=UpdateMessageResponse)
async def update_test_question(
        question_id: int,
        data: TestQuestionUpdate,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.is_moder:
        repository = TestRepository(db=db)
        repository.update_question(question_id=question_id, data=data)
        return UpdateMessageResponse()

    else:
        raise PermissionDeniedException()


@router.post("/answer/add", response_model=TestAnswerResponse)
async def add_test_answer(
        data: TestAnswerAdd,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.is_moder:
        repository = TestRepository(db=db)
        answer_orm = repository.create_test_answer(
            question_id=data.question_id,
            a_text=data.a_text,
            is_correct=data.is_correct,
            image_path=data.image_path
        )

        return TestAnswerResponse.from_orm(answer_orm)
    else:
        raise PermissionDeniedException()


@router.delete("/answer/delete", response_model=DeleteMessageResponse)
async def delete_test_answer(
        answer_id: int,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.is_moder:
        repository = TestRepository(db=db)
        repository.delete_answer(answer_id=answer_id)
        return DeleteMessageResponse()
    else:
        raise PermissionDeniedException()


@router.patch("/answer/update", response_model=UpdateMessageResponse)
async def update_test_answer(
        answer_id: int,
        data: TestAnswerUpdate,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.is_moder:
        repository = TestRepository(db=db)
        repository.update_answer(answer_id=answer_id, data=data)
        return UpdateMessageResponse()

    else:
        raise PermissionDeniedException()


@router.post("/matching/add", response_model=MatchingResponseAfterAdd)
async def add_test_matching(
        data: TestMatchingAdd,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.is_moder:
        repository = TestRepository(db=db)
        left_option, right_option = repository.create_test_matching(
            left_text=data.left_text,
            right_text=data.right_text,
            question_id=data.question_id
        )

        return MatchingResponseAfterAdd.from_orm(
            MatchingTuple(
                left_option.id, left_option.text, right_option.id, right_option.text
            )
        )

    else:
        raise PermissionDeniedException()


@router.patch("/matching/update", response_model=UpdateMessageResponse)
async def update_test_matching(
        left_option_id: int,
        data: TestMatchingUpdate,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.is_moder:
        repository = TestRepository(db=db)
        repository.update_matching(left_id=left_option_id, data=data)
        return UpdateMessageResponse()

    else:
        raise PermissionDeniedException()


@router.delete("/matching/delete", response_model=DeleteMessageResponse)
async def delete_test_matching(
        left_option_id: int,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.is_moder:
        repository = TestRepository(db=db)
        repository.delete_matching(left_id=left_option_id)
        return DeleteMessageResponse()

    else:
        raise PermissionDeniedException()
