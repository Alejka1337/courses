from sqlalchemy.orm import Session, joinedload

from src.schemas.lecture import LectureAttributeCreate, FileBase, LinkBase
from src.schemas.practical import QuestionBase, AnswerBase, MatchingBase
from src.enums import LessonTemplateType, QuestionTypeOption
from src.models import (
    LessonTemplateOrm,
    LectureTemplateAttributeOrm,
    LectureTemplateFileOrm,
    LectureTemplateLinkOrm,
    PracticalTemplateQuestionOrm,
    PracticalTemplateAnswerOrm,
    PracticalTemplateMatchingRightOrm,
    PracticalTemplateMatchingLeftOrm
)


class TemplateRepository:

    def __init__(self, db: Session):
        self.db = db
        self.model = LessonTemplateOrm

        self.lecture_attr_model = None
        self.lecture_file_model = None
        self.lecture_link_model = None

        self.practical_question_model = None
        self.practical_answer_model = None
        self.practical_matching_left_model = None
        self.practical_matching_right_model = None

    def init_lecture_model(self):
        self.lecture_attr_model = LectureTemplateAttributeOrm
        self.lecture_file_model = LectureTemplateFileOrm
        self.lecture_link_model = LectureTemplateLinkOrm

    def init_practical_model(self):
        self.practical_question_model = PracticalTemplateQuestionOrm
        self.practical_answer_model = PracticalTemplateAnswerOrm
        self.practical_matching_left_model = PracticalTemplateMatchingLeftOrm
        self.practical_matching_right_model = PracticalTemplateMatchingRightOrm

    def create_new_template(self, title: str, t_type: LessonTemplateType) -> LessonTemplateOrm:
        new_template = self.model(title=title, type=t_type)
        self.db.add(new_template)
        self.db.commit()
        self.db.refresh(new_template)
        return new_template

    def create_lecture_template_attrs(self, template_data: list[LectureAttributeCreate], template_id: int):
        for template_attr in template_data:
            dict_to_db = template_attr.model_dump(exclude={"files", "links"})
            dict_to_db.update({"template_id": template_id})
            new_attr = self.lecture_attr_model(**dict_to_db)
            self.db.add(new_attr)
            self.db.commit()

            if template_attr.files is not None:
                self.create_lecture_template_files(files=template_attr.files, attr_id=new_attr.id)

            if template_attr.links is not None:
                self.create_lecture_template_links(links=template_attr.links, attr_id=new_attr.id)

            self.db.refresh(new_attr)

    def create_lecture_template_files(self, files: list[FileBase], attr_id: int):
        for file in files:
            dict_to_db = file.model_dump()
            dict_to_db["file_path"] = str(dict_to_db["file_path"])
            dict_to_db.update({"lecture_template_attr_id": attr_id})
            new_file = self.lecture_file_model(**dict_to_db)
            self.db.add(new_file)
            self.db.commit()

    def create_lecture_template_links(self, links: list[LinkBase], attr_id: int):
        for link in links:
            dict_to_db = link.model_dump()
            dict_to_db.update({"lecture_template_attr_id": attr_id})
            new_link = self.lecture_link_model(**dict_to_db)
            self.db.add(new_link)
            self.db.commit()

    def create_practical_template_question(self, template_data: list[QuestionBase], template_id: int):
        for template_question in template_data:
            dict_to_db = template_question.model_dump(exclude={"answers"})
            dict_to_db.update({"template_id": template_id})
            new_question = self.practical_question_model(**dict_to_db)
            self.db.add(new_question)
            self.db.commit()

            self.create_practical_template_answers(
                answers=template_question.answers, question_id=new_question.id
            )

    def create_practical_template_answers(self, answers: list[AnswerBase | MatchingBase], question_id: int):
        for answer in answers:
            if isinstance(answer, AnswerBase):
                dict_to_db = answer.model_dump()
                dict_to_db.update({"question_id": question_id})
                new_answer = self.practical_answer_model(**dict_to_db)
                self.db.add(new_answer)
                self.db.commit()

            else:
                right_option = self.practical_matching_right_model(text=answer.right_text, question_id=question_id)
                self.db.add(right_option)
                self.db.commit()

                left_option = self.practical_matching_left_model(
                    text=answer.left_text, right_id=right_option.id, question_id=question_id
                )
                self.db.add(left_option)
                self.db.commit()

    def select_templates(self) -> list[type[LessonTemplateOrm]]:
        return self.db.query(self.model).all()

    def select_template_by_id(self, template_id: int, t_type: LessonTemplateType):
        if t_type == LessonTemplateType.lecture:
            self.init_lecture_model()

            template_data = (self.db.query(self.model)
                             .filter(self.model.id == template_id)
                             .options(joinedload(self.model.lecture_template))
                             .first())

        else:
            self.init_practical_model()
            template_data = (self.db.query(self.model)
                             .filter(self.model.id == template_id)
                             .options(joinedload(self.model.practical_template))
                             .first())

        return template_data

    def delete_template_by_id(self, template_id: int):
        template = self.db.query(self.model).filter(self.model.id == template_id).first()

        if template.type == LessonTemplateType.lecture:
            self.init_lecture_model()
            self.delete_lecture_template(template_id=template.id)
        else:
            self.init_practical_model()
            self.delete_practical_template(template_id=template.id)

        self.db.delete(template)
        self.db.commit()

    def delete_lecture_template(self, template_id: int):
        attributes = (self.db.query(self.lecture_attr_model)
                      .filter(self.lecture_attr_model.template_id == template_id)
                      .options(joinedload(self.lecture_attr_model.files))
                      .options(joinedload(self.lecture_attr_model.links))
                      .all())

        for attribute in attributes:

            if attribute.files is not None:
                for file in attribute.files:
                    self.db.delete(file)
                    self.db.commit()

            if attribute.links is not None:
                for link in attribute.links:
                    self.db.delete(link)
                    self.db.commit()

            self.db.delete(attribute)
            self.db.commit()

    def delete_practical_template(self, template_id: int):
        questions = (self.db.query(self.practical_question_model)
                     .filter(self.practical_question_model.template_id == template_id)
                     .all())

        for question in questions:
            if question.q_type != QuestionTypeOption.matching:
                for answer in question.answers:
                    self.db.delete(answer)
                    self.db.commit()

            else:
                for left in question.left_option:
                    self.db.delete(left)
                    self.db.commit()

                for right in question.right_option:
                    self.db.delete(right)
                    self.db.commit()

            self.db.delete(question)
            self.db.commit()

    def check_exist_lecture_file(self, file_path: str):
        res = (self.db.query(self.lecture_file_model)
               .filter(self.lecture_file_model.file_path == file_path)
               .first())
        if res is None:
            return False
        return True

