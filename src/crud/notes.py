from sqlalchemy.orm import Session

from src.models import UserNoteOrm, FolderOrm
from src.schemas.notes import CreateNote, CreateFolder


class NotesRepository:
    def __init__(self, db: Session):
        self.db = db
        self.note_model = UserNoteOrm
        self.folder_model = FolderOrm

    def create_folder(self, data: CreateFolder) -> FolderOrm:
        new_folder = self.folder_model(**data.model_dump())
        self.db.add(new_folder)
        self.db.commit()
        self.db.refresh(new_folder)
        return new_folder

    def create_note(self, data: CreateNote) -> UserNoteOrm:
        new_note = self.note_model(**data.model_dump())
        self.db.add(new_note)
        self.db.commit()
        self.db.refresh(new_note)
        return new_note

    def select_folder_with_notes(self, student_id) -> list[dict]:

        def folder_to_dict(folder):
            return {
                "folder_name": folder.name,
                "folder_id": folder.id,
                "parent_id": folder.parent_id,
                "folder_notes": [
                    {
                        "note_id": note.id,
                        "title": note.title,
                        "text": note.text,
                        "folder_id": note.folder_id,
                        "lecture_id": note.lecture_id
                    }
                    for note in folder.notes
                ] if folder.notes else None,
                "children_folders": [
                    folder_to_dict(child) for child in folder.child_folder
                ] if folder.child_folder else None
            }

        student_folders = (self.db.query(self.folder_model)
                           .filter(self.folder_model.parent_id.is_(None))
                           .filter(self.folder_model.student_id == student_id)
                           .all())

        return [folder_to_dict(folder) for folder in student_folders]

    def delete_note(self, note_id: int) -> None:
        note = self.db.query(self.note_model).filter(self.note_model.id == note_id).first()
        self.db.delete(note)
        self.db.commit()

    def delete_folder(self, folder_id: int) -> None:
        def recursion_delete(folder):
            if folder.child_folder:
                for child in folder.child_folder:
                    recursion_delete(child)

            if folder.notes:
                for note in folder.notes:
                    self.delete_note(note_id=note.id)
                    self.db.commit()

            self.db.delete(folder)
            self.db.commit()

        folder = self.db.query(self.folder_model).filter(self.folder_model.id == folder_id).first()

        if folder.child_folder:
            for child in folder.child_folder:
                recursion_delete(child)

        if folder.notes:
            for note in folder.notes:
                self.delete_note(note_id=note.id)
                self.db.commit()

        self.db.delete(folder)
        self.db.commit()
