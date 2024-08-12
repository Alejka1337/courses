from typing import List

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from src.crud.instruction import InstructionRepository
from src.enums import StaticFileType, UserType
from src.models import UserOrm
from src.schemas.instruction import (InstructionCreate, InstructionUpdate, InstructionFileBase, InstructionResponse,
                                     InstructionDetailResponse, InstructionDeleteResponse)
from src.session import get_db
from src.utils.exceptions import InstructionNotFoundException, PermissionDeniedException
from src.utils.get_user import get_current_user
from src.utils.save_files import save_file

router = APIRouter(prefix="/instruction")


@router.post("/upload", response_model=InstructionFileBase)
async def upload_instruction_file(
        file: UploadFile = File(...),
        user: UserOrm = Depends(get_current_user)
):
    if user.is_moder:
        file_path = save_file(file=file, file_type=StaticFileType.instruction_file.value)
        return InstructionFileBase(
            file_path=file_path,
            file_size=file.size,
            file_name=file.filename,
            file_type=file.filename.split(".")[-1]
        )
    else:
        raise PermissionDeniedException()


@router.post("/create", response_model=InstructionResponse)
async def create_instruction(
        data: InstructionCreate,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.is_moder:
        repository = InstructionRepository(db=db)
        instruction = repository.create_instruction(data=data)

        if data.files:
            for file_data in data.files:
                repository.create_instruction_file(data=file_data, instruction_id=instruction.id)

        return instruction
    else:
        raise PermissionDeniedException()


@router.get("/general", response_model=List[InstructionDetailResponse])
async def get_general_instruction(db: Session = Depends(get_db)):
    repository = InstructionRepository(db=db)
    result = repository.select_general_instruction()
    if not result:
        raise InstructionNotFoundException()
    return result


@router.get("/courses", response_model=list[InstructionDetailResponse])
async def get_courses_instruction(
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)

):
    repository = InstructionRepository(db=db)
    if user.is_student:
        categories = set()
        courses = user.student.courses
        for course in courses:
            categories.add(course.category_id)

        result = repository.select_course_instruction_for_student(categories=categories)
        if not result:
            raise InstructionNotFoundException()
        return result

    else:
        result = repository.select_course_instruction_for_admin()
        if not result:
            raise InstructionNotFoundException()
        return result


@router.put("/update/{instruction_id}", response_model=InstructionResponse)
async def update_instruction(
        data: InstructionUpdate,
        instruction_id: int,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.is_moder:
        repository = InstructionRepository(db=db)
        instruction = repository.update_instruction(instruction_id=instruction_id, data=data)

        if data.files:
            repository.delete_instruction_files(instruction_id=instruction_id)
            for file_data in data.files:
                repository.create_instruction_file(data=file_data, instruction_id=instruction_id)

        return instruction

    else:
        raise PermissionDeniedException()


@router.delete("/delete/{instruction_id}", response_model=InstructionDeleteResponse)
async def delete_instruction(
        instruction_id: int,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        repository = InstructionRepository(db=db)
        repository.delete_instruction(instruction_id=instruction_id)
        return InstructionDeleteResponse()

    else:
        raise InstructionNotFoundException()
