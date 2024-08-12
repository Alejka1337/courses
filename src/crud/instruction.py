from typing import Union, List, TypeVar, Type
from datetime import date

from sqlalchemy.orm import Session, joinedload

from src.enums import InstructionType
from src.models import InstructionFilesOrm, InstructionOrm
from src.schemas.instruction import InstructionCreate, InstructionFileBase, InstructionUpdate
from src.utils.save_files import delete_file


T = TypeVar("T", bound=InstructionOrm)


class InstructionRepository:
    def __init__(self, db: Session):
        self.db = db
        self.model = InstructionOrm
        self.file_model = InstructionFilesOrm

    def create_instruction(self, data: InstructionCreate) -> InstructionOrm:
        new_instruction = self.model(
            name=data.name,
            type=data.type,
            title=data.title,
            text=data.text,
            category_id=data.category_id,
            last_update=date.today()
        )
        self.db.add(new_instruction)
        self.db.commit()
        self.db.refresh(new_instruction)
        return new_instruction

    def create_instruction_file(self, data: InstructionFileBase, instruction_id: int) -> None:
        new_file = self.file_model(
            instruction_id=instruction_id,
            file_type=data.file_type,
            file_size=data.file_size,
            file_path=data.file_path,
            file_name=data.file_name
        )
        self.db.add(new_file)
        self.db.commit()

    def select_general_instruction(self) -> Union[List[Type[T]], None]:
        return (self.db.query(self.model)
                .filter(self.model.type == InstructionType.general.value)
                .options(joinedload(self.model.files))
                .all())

    def select_course_instruction_for_student(self, categories: set = None) -> Union[List[Type[T]], None]:
        return (self.db.query(self.model)
                .filter(self.model.type == InstructionType.course.value)
                .filter(self.model.category_id.in_(categories))
                .options(joinedload(self.model.files))
                .all())

    def select_course_instruction_for_admin(self) -> Union[List[Type[T]], None]:
        return (self.db.query(self.model)
                .filter(self.model.type == InstructionType.course.value)
                .options(joinedload(self.model.files))
                .all())

    def update_instruction(self, instruction_id: int, data: InstructionUpdate) -> Type[T]:
        instruction = self.db.query(self.model).filter(self.model.id == instruction_id).first()

        if instruction:
            for field, value in data.dict(exclude_unset=True).items():
                if field != 'files':
                    setattr(instruction, field, value)

        self.db.commit()
        self.db.refresh(instruction)
        return instruction

    def delete_instruction(self, instruction_id: int) -> None:
        instruction = (self.db.query(self.model)
                       .filter(self.model.id == instruction_id)
                       .options(joinedload(self.model.files))
                       .first())

        if instruction.files:
            self.delete_instruction_files(instruction_id=instruction_id)

        self.db.delete(instruction)
        self.db.commit()

    def delete_instruction_files(self, instruction_id: int) -> None:
        files = self.db.query(self.file_model).filter(self.file_model.instruction_id == instruction_id).all()
        for file in files:
            delete_file(file.file_path)
            self.db.delete(file)

        self.db.commit()
