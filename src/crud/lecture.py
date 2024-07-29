from sqlalchemy.orm import Session, joinedload

from src.enums import LectureAttributeType
from src.models import LectureAttributeOrm, LectureFilesOrm, LectureLinksOrm, LectureOrm, LessonOrm
from src.schemas.lecture import LectureAttributeUpdate, LectureFileAttributeUpdate
from src.utils.save_files import delete_file


class LectureRepository:
    def __init__(self, db: Session):
        self.db = db
        self.model = LectureOrm
        self.attr_model = LectureAttributeOrm
        self.file_model = LectureFilesOrm
        self.link_model = LectureLinksOrm
        self.lesson_model = LessonOrm

    def create_lecture(self, lesson_id: int):
        new_lecture = self.model(lesson_id=lesson_id)
        self.db.add(new_lecture)
        self.db.commit()
        self.db.refresh(new_lecture)
        return new_lecture

    def create_attribute_base(
            self,
            lecture_id: int,
            a_type: LectureAttributeType,
            a_title: str,
            a_number: int,
            hidden: bool,
            a_text: str | None
    ) -> LectureAttributeOrm:

        new_attr = self.attr_model(
            a_type=a_type,
            a_title=a_title,
            a_number=a_number,
            a_text=a_text,
            hidden=hidden,
            lecture_id=lecture_id
        )
        self.db.add(new_attr)
        self.db.commit()
        self.db.refresh(new_attr)
        return new_attr

    def create_attribute_file(
            self,
            attribute_id: int,
            filename: str,
            file_path: str,
            file_size: int,
            file_description: str | None,
            download_allowed: bool
    ) -> LectureFilesOrm:

        file = self.file_model(
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            file_description=file_description,
            download_allowed=download_allowed,
            attribute_id=attribute_id
        )
        self.db.add(file)
        self.db.commit()
        self.db.refresh(file)
        return file

    def create_attribute_link(
            self,
            attribute_id: int,
            link: str,
            anchor: str | None
    ) -> LectureLinksOrm:

        link = self.link_model(attribute_id=attribute_id, link=link, anchor=anchor)
        self.db.add(link)
        self.db.commit()
        self.db.refresh(link)
        return link

    def select_lecture_attrs(self, lecture_id: int) -> list:
        return (self.db.query(self.attr_model.a_title.label("title"), self.attr_model.a_text.label("text"))
                .filter(self.attr_model.lecture_id == lecture_id)
                .order_by(self.attr_model.a_number)
                .all())

    def update_lecture_audio(self, lecture_id: int, audios: list) -> None:
        (self.db.query(self.model)
         .filter(self.model.id == lecture_id)
         .update({self.model.audios: audios}, synchronize_session=False))

        self.db.commit()

    def update_lecture_attr(
            self,
            attr_id: int,
            a_text: str = None,
            a_title: str = None,
            a_number: int = None,
            hidden: bool = None
    ):
        attribute = self.db.query(self.attr_model).filter(self.attr_model.id == attr_id).first()

        if a_text:
            attribute.a_text = a_text

        if a_title:
            attribute.a_title = a_title

        if a_number:
            attribute.a_number = a_number

        if hidden:
            attribute.hidden = hidden

        self.db.commit()
        self.db.refresh(attribute)

    def update_lecture_file_attr(self, attr_id: int, data: LectureFileAttributeUpdate):
        file = self.db.query(self.file_model).filter(self.file_model.attribute_id == attr_id).first()

        if str(data.file_path) != file.file_path:
            delete_file(file.file_path)

        self.db.delete(file)

        self.create_attribute_file(
            attribute_id=attr_id,
            filename=data.filename,
            file_path=str(data.file_path),
            file_size=data.file_size,
            file_description=data.file_description,
            download_allowed=data.download_allowed
        )

        self.update_lecture_attr(
            attr_id=attr_id,
            a_text=data.a_text,
            a_title=data.a_title,
            a_number=data.a_number,
            hidden=data.hidden
        )

    def update_lecture_files_attr(self, attr_id: int, data: LectureAttributeUpdate):
        files = self.db.query(self.file_model).filter(self.file_model.attribute_id == attr_id).all()
        paths = [f.file_path for f in data.files]
        for file in files:
            if file.file_path in paths:
                delete_file(file.file_path)

            self.db.delete(file)

        for new_file in data.files:
            self.create_attribute_file(
                attribute_id=attr_id,
                filename=new_file.filename,
                file_size=new_file.file_size,
                file_path=str(new_file.file_path),
                file_description=new_file.file_description,
                download_allowed=new_file.download_allowed
            )

        self.update_lecture_attr(
            attr_id=attr_id,
            a_text=data.a_text,
            a_title=data.a_title,
            a_number=data.a_number,
            hidden=data.hidden
        )

    def update_lecture_links_attr(self, attr_id: int, data: LectureAttributeUpdate):
        links = self.db.query(self.link_model).filter(self.link_model.attribute_id == attr_id).all()

        for link in links:
            self.db.delete(link)

        for new_link in data.links:
            self.create_attribute_link(
                attribute_id=attr_id,
                link=new_link.link,
                anchor=new_link.anchor
            )

        self.update_lecture_attr(
            attr_id=attr_id,
            a_text=data.a_text,
            a_title=data.a_title,
            a_number=data.a_number,
            hidden=data.hidden
        )

    def delete_lecture_attr(self, attr_id: int):
        attr = self.db.query(self.attr_model).filter(self.attr_model.id == attr_id).first()

        if attr.a_type == LectureAttributeType.link.value:
            links = self.db.query(self.link_model).filter(self.link_model.attribute_id == attr.id).all()

            for link in links:
                self.db.delete(link)

        else:
            files = self.db.query(self.file_model).filter(self.file_model.attribute_id == attr.id).all()

            for file in files:
                delete_file(file.file_path)
                self.db.delete(file)

        self.db.delete(attr)
        self.db.commit()

    def select_lecture_data(self, lesson: LessonOrm):
        lecture = (
            self.db.query(self.model)
            .filter(self.model.lesson_id == lesson.id)
            .options(joinedload(self.model.lecture_attributes).joinedload(self.attr_model.files))
            .options(joinedload(self.model.lecture_attributes).joinedload(self.attr_model.links))
            .first()
        )

        if lecture:
            lecture_data = {
                "lecture_id": lecture.id,
                "lecture_speeches": lecture.audios,
                "attributes": []
            }

            for attr in lecture.lecture_attributes:
                files = []
                links = []

                if attr.a_type in [
                    LectureAttributeType.present,
                    LectureAttributeType.audio,
                    LectureAttributeType.video,
                    LectureAttributeType.picture,
                    LectureAttributeType.file
                ]:
                    files.extend(attr.files)

                elif attr.a_type == LectureAttributeType.link:
                    links.extend(attr.links)

                attribute_data = {
                    "a_id": attr.id,
                    "a_type": attr.a_type,
                    "a_title": attr.a_title,
                    "a_number": attr.a_number,
                    "a_text": attr.a_text,
                    "hidden": attr.hidden,
                    "files": [
                        {
                            "file_id": file.id,
                            "filename": file.filename,
                            "file_path": file.file_path,
                            "file_size": file.file_size,
                            "file_description": file.file_description,
                            "download_allowed": file.download_allowed
                        } for file in files if files
                    ],
                    "links": [
                        {
                            "link_id": link.id,
                            "link": link.link,
                            "anchor": link.anchor
                        } for link in links if links
                    ]
                }

                lecture_data["attributes"].append(attribute_data)

            setattr(lesson, "lecture_info", lecture_data)
            return lesson

        else:
            return lesson
