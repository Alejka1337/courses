from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.session import get_db
from src.utils.get_user import get_current_user
from src.models import UserOrm
from src.schemas.notes import (
    CreateNote,
    CreateNoteResponse,
    CreateFolder,
    CreateFolderResponse
)
from src.crud.notes import NotesRepository
from src.utils.exceptions import PermissionDeniedException


router = APIRouter(prefix="/notes")


@router.post("/create/folder", status_code=status.HTTP_201_CREATED, response_model=CreateFolderResponse)
async def create_new_folder(
        data: CreateFolder,
        user: UserOrm = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    if user.is_student:
        repository = NotesRepository(db=db)
        folder = repository.create_folder(data=data)
        return folder

    raise PermissionDeniedException()


@router.post("/create/note", status_code=status.HTTP_201_CREATED, response_model=CreateNoteResponse)
async def create_new_note(
        data: CreateNote,
        user: UserOrm = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    if user.is_student:
        repository = NotesRepository(db=db)
        note = repository.create_note(data=data)
        return note

    raise PermissionDeniedException()


@router.delete("/delete/folder")
async def delete_folder(
        folder_id: int,
        user: UserOrm = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    if user.is_student:
        repository = NotesRepository(db=db)
        repository.delete_folder(folder_id=folder_id)
        return {"message": "Successful"}

    raise PermissionDeniedException()


@router.delete("/delete/note")
async def delete_note(
        note_id: int,
        user: UserOrm = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    if user.is_student:
        repository = NotesRepository(db=db)
        repository.delete_note(note_id=note_id)
        return {"message": "Successful"}

    raise PermissionDeniedException()
