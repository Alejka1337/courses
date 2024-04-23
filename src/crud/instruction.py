from datetime import date

from sqlalchemy.orm import Session, joinedload

from src.enums import InstructionType
from src.models import InstructionFilesOrm, InstructionOrm
from src.schemas.instruction import InstructionCreate


def create_instruction_db(db: Session, data: InstructionCreate):
    new_instruction = InstructionOrm(
        name=data.name,
        type=data.type,
        title=data.title,
        text=data.text,
        category_id=data.category_id,
        last_update=date.today()
    )
    db.add(new_instruction)
    db.commit()
    db.refresh(new_instruction)
    return new_instruction


def create_instruction_file_db(db: Session, file_data: dict, instruction_id: int):
    new_file = InstructionFilesOrm(
        instruction_id=instruction_id,
        file_type=file_data["file_type"],
        file_size=file_data["file_size"],
        file_path=file_data["file_path"],
        file_name=file_data["file_name"]
    )
    db.add(new_file)
    db.commit()
    db.refresh(new_file)


def select_general_instruction_db(db: Session):
    return (db.query(InstructionOrm)
            .filter(InstructionOrm.type == InstructionType.general.value)
            .options(joinedload(InstructionOrm.files))
            .all())


def select_course_instruction_db(db: Session, categories: list):
    return (db.query(InstructionOrm)
            .filter(InstructionOrm.type == InstructionType.course.value,
                    InstructionOrm.category_id.in_(categories))
            .options(joinedload(InstructionOrm.files))
            .all())
