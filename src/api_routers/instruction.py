from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from src.crud.instruction import (create_instruction_db, create_instruction_file_db, select_course_instruction_db,
                                  select_general_instruction_db)
from src.enums import UserType
from src.models import UserOrm
from src.schemas.instruction import InstructionCreate, InstructionUpdate
from src.session import get_db
from src.utils.get_user import get_current_user
from src.utils.save_files import save_instruction_file

router = APIRouter(prefix="/instruction")


@router.post("/upload")
async def upload_instruction_file(
        file: UploadFile = File(...),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        file_path = save_instruction_file(file=file)
        return {
            "file_path": file_path, "file_size": file.size, "file_name": file.filename,
            "file_type": file.filename.split(".")[-1]
        }
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")


@router.post("/create")
async def create_instruction(
        data: Annotated[InstructionCreate, Depends()],
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        instruction = create_instruction_db(db=db, data=data)
        if data.files:
            for file_data in data.files:
                create_instruction_file_db(db=db, file_data=file_data.dict(), instruction_id=instruction.id)
        return instruction
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")


@router.get("/general")
async def get_general_instruction(db: Session = Depends(get_db)):
    result = select_general_instruction_db(db=db)
    return result


@router.get("/courses")
async def get_courses_instruction(
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.student.value:
        categories = set()
        courses = user.student.courses
        for course in courses:
            categories.add(course.category_id)

        result = select_course_instruction_db(db=db, categories=list(categories))
        return result

    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@router.put("/update/{instruction_id}")
async def update_instruction(
        data: Annotated[InstructionUpdate, Depends()],
        instruction_id: int,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    pass


@router.delete("/delete/{instruction_id}")
async def delete_instruction(
        instruction_id: int,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    pass
