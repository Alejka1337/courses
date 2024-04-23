from sqlalchemy.orm import Session

from src.enums import LectureAttributeType
from src.models import LectureAttributeOrm, LectureFilesOrm, LectureLinksOrm, LectureOrm


def create_attribute_base_db(db: Session, lecture_id: int, a_type: LectureAttributeType, a_title: str, a_number: int,
                             a_text: str | None, hidden: bool):
    new_attr = LectureAttributeOrm(
        a_type=a_type,
        a_title=a_title,
        a_number=a_number,
        a_text=a_text,
        hidden=hidden,
        lecture_id=lecture_id
    )
    db.add(new_attr)
    db.commit()
    db.refresh(new_attr)
    return new_attr


def create_attribute_file_db(
        db: Session,
        attribute_id: int,
        filename: str,
        file_path: str,
        file_size: int,
        file_description: str | None,
        download_allowed: bool
):
    file = LectureFilesOrm(
        filename=filename,
        file_path=file_path,
        file_size=file_size,
        file_description=file_description,
        download_allowed=download_allowed,
        attribute_id=attribute_id
    )
    db.add(file)
    db.commit()
    db.refresh(file)


def create_attribute_link_db(
        db: Session,
        attribute_id: int,
        link: str,
        anchor: str | None
):
    link = LectureLinksOrm(
        attribute_id=attribute_id,
        link=link,
        anchor=anchor
    )
    db.add(link)
    db.commit()
    db.refresh(link)


def select_lecture_attrs_db(db: Session, lecture_id: int):
    return (db.query(LectureAttributeOrm.a_title.label("title"), LectureAttributeOrm.a_text.label("text"))
            .filter(LectureAttributeOrm.lecture_id == lecture_id)
            .order_by(LectureAttributeOrm.a_number)
            .all())


def update_lecture_audio(db: Session, lecture_id: int, audios: list):
    (db.query(LectureOrm)
     .filter(LectureOrm.id == lecture_id)
     .update({LectureOrm.audios: audios}, synchronize_session=False))
    db.commit()
