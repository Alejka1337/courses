from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from src.crud.instruction import InstructionRepository
from src.enums import StaticFileType, UserType
from src.models import UserOrm
from src.schemas.instruction import InstructionCreate, InstructionUpdate
from src.session import get_db
from src.utils.exceptions import InstructionNotFoundException, PermissionDeniedException
from src.utils.get_user import get_current_user
from src.utils.save_files import save_file

router = APIRouter(prefix="/instruction")


@router.post("/upload")
async def upload_instruction_file(
        file: UploadFile = File(...),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        file_path = save_file(file=file, file_type=StaticFileType.instruction_file.value)
        return {
            "file_path": file_path,
            "file_size": file.size,
            "file_name": file.filename,
            "file_type": file.filename.split(".")[-1]
        }
    else:
        raise PermissionDeniedException()


@router.post("/create")
async def create_instruction(
        data: InstructionCreate,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        repository = InstructionRepository(db=db)
        instruction = repository.create_instruction(data=data)

        if data.files:
            for file_data in data.files:
                repository.create_instruction_file(data=file_data, instruction_id=instruction.id)

        return instruction
    else:
        raise PermissionDeniedException()


@router.get("/general")
async def get_general_instruction(db: Session = Depends(get_db)):
    repository = InstructionRepository(db=db)
    return repository.select_general_instruction()


@router.get("/courses")
async def get_courses_instruction(
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.student.value:
        repository = InstructionRepository(db=db)
        categories = set()
        courses = user.student.courses
        for course in courses:
            categories.add(course.category_id)

        return repository.select_course_instruction(categories=list(categories))

    else:
        raise InstructionNotFoundException()


@router.put("/update/{instruction_id}")
async def update_instruction(
        data: InstructionUpdate,
        instruction_id: int,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        repository = InstructionRepository(db=db)
        instruction = repository.update_instruction(instruction_id=instruction_id, data=data)

        if data.files:
            repository.delete_instruction_files(instruction_id=instruction_id)
            for file_data in data.files:
                repository.create_instruction_file(data=file_data, instruction_id=instruction_id)

        return instruction

    else:
        raise PermissionDeniedException()


@router.delete("/delete/{instruction_id}")
async def delete_instruction(
        instruction_id: int,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        repository = InstructionRepository(db=db)
        repository.delete_instruction(instruction_id=instruction_id)
        return {"message": "Instruction successfully deleted"}

    else:
        raise InstructionNotFoundException()
