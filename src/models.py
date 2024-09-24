from datetime import date, datetime
from typing import Annotated, Optional

from sqlalchemy import (
    ARRAY,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from src.enums import (
    ChatStatusType,
    CourseStatus,
    InstructionType,
    LectureAttributeType,
    LessonStatus,
    LessonTemplateType,
    LessonType,
    MessageSenderType,
    NotificationType,
    QuestionTypeOption,
    UserType,
)


class Base(DeclarativeBase):

    repr_cols = tuple()
    repr_cols_number = 3

    def __repr__(self):
        cols = []
        for idx, col in enumerate(self.__table__.columns.keys()):
            if col in self.repr_cols or idx < self.repr_cols_number:
                cols.append(f"{col}={getattr(self, col)}")

        return f"<{self.__class__.__name__} {', '.join(cols)}>"


intpk = Annotated[int, mapped_column(primary_key=True, index=True)]


class UserOrm(Base):
    __tablename__ = "users"

    id: Mapped[intpk]
    usertype: Mapped[UserType]
    username: Mapped[str] = mapped_column(unique=True)
    access_token: Mapped[Optional[str]]
    refresh_token: Mapped[Optional[str]]
    hashed_pass: Mapped[str]
    is_active: Mapped[Optional[bool]]
    exp_token: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_active: Mapped[Optional[date]] = mapped_column(Date)

    images: Mapped[list["ImageOrm"]] = relationship(back_populates="user")
    student: Mapped["StudentOrm"] = relationship(back_populates="user")
    moder: Mapped["ModeratorOrm"] = relationship(back_populates="user")
    activate_code: Mapped["ActivateCodeOrm"] = relationship(back_populates="user")
    reset_link: Mapped["ResetPasswordLinkOrm"] = relationship(back_populates="user")

    sent_messages: Mapped[list["ChatMessageOrm"]] = relationship(back_populates="sender",
                                                                 foreign_keys="ChatMessageOrm.sender_id",)
    received_messages: Mapped[list["ChatMessageOrm"]] = relationship(back_populates="recipient",
                                                                     foreign_keys="ChatMessageOrm.recipient_id")

    @property
    def is_moder(self):
        if self.usertype == UserType.moder.value:
            return True
        return False

    @property
    def is_student(self):
        if self.usertype == UserType.student.value:
            return True
        return False


class ImageOrm(Base):
    __tablename__ = "images"

    id: Mapped[intpk]
    path: Mapped[str]
    is_main: Mapped[bool] = mapped_column(default=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    user: Mapped["UserOrm"] = relationship(back_populates="images")


class ActivateCodeOrm(Base):
    __tablename__ = "activate_codes"

    id: Mapped[intpk]
    code: Mapped[str] = mapped_column(unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    user: Mapped["UserOrm"] = relationship(back_populates="activate_code")


class ResetPasswordLinkOrm(Base):
    __tablename__ = "reset_password_links"

    id: Mapped[intpk]
    link: Mapped[str] = mapped_column(unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    user: Mapped["UserOrm"] = relationship(back_populates="reset_link")


class StudentOrm(Base):
    __tablename__ = "students"

    id: Mapped[intpk]
    name: Mapped[str]
    surname: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    phone: Mapped[Optional[str]] = mapped_column(unique=True)
    country: Mapped[Optional[str]]
    balance: Mapped[int] = mapped_column(default=0)
    studying_time: Mapped[int] = mapped_column(default=0)
    changed_name: Mapped[bool] = mapped_column(default=False)
    changed_surname: Mapped[bool] = mapped_column(default=False)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["UserOrm"] = relationship(back_populates="student")

    courses: Mapped[list["CourseOrm"]] = relationship(
        back_populates="students", secondary="student_course_association")

    student_lesson: Mapped[list["StudentLessonOrm"]] = relationship(back_populates="student")
    student_test_attempts: Mapped[list["StudentTestAttemptsOrm"]] = relationship(back_populates="student")
    student_exam_attempts: Mapped[list["StudentExamAttemptsOrm"]] = relationship(back_populates="student")

    course_certificates: Mapped[list["CourseCertificateOrm"]] = relationship(back_populates="student")
    category_certificates: Mapped[list["CategoryCertificateOrm"]] = relationship(back_populates="student")

    folders: Mapped[list["FolderOrm"]] = relationship(back_populates="student")
    chats: Mapped[list["ChatOrm"]] = relationship(back_populates="initiator")
    notifications: Mapped[list["StudentNotification"]] = relationship(back_populates="student")

    @hybrid_property
    def fullname(self):
        return self.name + " " + self.surname

    __table_args__ = (
        CheckConstraint("balance >= 0", name="positive_balance"),
    )


class StudentNotification(Base):
    __tablename__ = "student_notifications"

    id: Mapped[intpk]
    message: Mapped[str]
    type: Mapped[NotificationType]
    sent: Mapped[bool] = mapped_column(default=False)
    expires: Mapped[Optional[datetime]] = mapped_column(DateTime)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)

    student: Mapped["StudentOrm"] = relationship(back_populates="notifications")


class StudentCourseAssociation(Base):
    __tablename__ = "student_course_association"

    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True, primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True,  primary_key=True)
    grade: Mapped[int] = mapped_column(default=0)
    progress: Mapped[int] = mapped_column(default=0)
    status: Mapped[CourseStatus]

    __table_args__ = (
        CheckConstraint("progress <= 100", name="progress_less_then_100_present"),
        CheckConstraint("grade <= 200", name="grade_less_then_200")
    )


class StudentLessonOrm(Base):
    __tablename__ = "student_lessons"

    id: Mapped[intpk]
    status: Mapped[LessonStatus]
    score: Mapped[Optional[int]]
    attempt: Mapped[Optional[int]] = mapped_column(default=0)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id"))
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"))

    student: Mapped["StudentOrm"] = relationship(back_populates="student_lesson")
    lesson: Mapped["LessonOrm"] = relationship(back_populates="student_lesson")


class StudentTestAttemptsOrm(Base):
    __tablename__ = "student_test_attempts"

    id: Mapped[intpk]
    attempt_number: Mapped[int]
    attempt_score: Mapped[Optional[int]]
    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id"))
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"))

    test: Mapped["TestOrm"] = relationship(back_populates="student_test_attempts")
    student: Mapped["StudentOrm"] = relationship(back_populates="student_test_attempts")

    student_test_answers: Mapped[list["StudentTestAnswerOrm"]] = relationship(back_populates="student_attempt")
    student_test_matching: Mapped[list["StudentTestMatchingOrm"]] = relationship(back_populates="student_attempt")


class StudentTestAnswerOrm(Base):
    __tablename__ = "student_test_answers"

    id: Mapped[intpk]
    score: Mapped[int]
    question_id: Mapped[int] = mapped_column(ForeignKey("test_questions.id"))
    question_type: Mapped[QuestionTypeOption]
    answer_id: Mapped[Optional[int]]
    answer_ids = Column(ARRAY(Integer), nullable=True)
    student_attempt_id: Mapped[int] = mapped_column(ForeignKey("student_test_attempts.id"))

    question: Mapped["TestQuestionOrm"] = relationship(back_populates="student_answers")
    student_attempt: Mapped["StudentTestAttemptsOrm"] = relationship(back_populates="student_test_answers")


class StudentTestMatchingOrm(Base):
    __tablename__ = "student_test_matching"

    id: Mapped[intpk]
    score: Mapped[float]
    question_id: Mapped[int] = mapped_column(ForeignKey("test_questions.id"))
    question_type: Mapped[QuestionTypeOption]
    left_id: Mapped[int] = mapped_column(ForeignKey("test_matching_left.id"))
    right_id: Mapped[int] = mapped_column(ForeignKey("test_matching_right.id"))
    student_attempt_id: Mapped[int] = mapped_column(ForeignKey("student_test_attempts.id"))

    question: Mapped["TestQuestionOrm"] = relationship(back_populates="student_matching")
    student_attempt: Mapped["StudentTestAttemptsOrm"] = relationship(back_populates="student_test_matching")

    right_option: Mapped["TestMatchingRightOrm"] = relationship(back_populates="student_test_matching")
    left_option: Mapped["TestMatchingLeftOrm"] = relationship(back_populates="student_test_matching")


class StudentExamAttemptsOrm(Base):
    __tablename__ = "student_exam_attempts"

    id: Mapped[intpk]
    attempt_number: Mapped[int]
    attempt_score: Mapped[Optional[int]]
    exam_id: Mapped[int] = mapped_column(ForeignKey("exams.id"))
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"))

    exam: Mapped["ExamOrm"] = relationship(back_populates="student_exam_attempts")
    student: Mapped["StudentOrm"] = relationship(back_populates="student_exam_attempts")

    student_exam_answers: Mapped[list["StudentExamAnswerOrm"]] = relationship(back_populates="student_attempt")
    student_exam_matching: Mapped[list["StudentExamMatchingOrm"]] = relationship(back_populates="student_attempt")


class StudentExamAnswerOrm(Base):
    __tablename__ = "student_exam_answers"

    id: Mapped[intpk]
    score: Mapped[int]
    question_id: Mapped[int] = mapped_column(ForeignKey("exam_questions.id"))
    question_type: Mapped[QuestionTypeOption]
    answer_id: Mapped[Optional[int]]
    answer_ids = Column(ARRAY(Integer), nullable=True)
    student_attempt_id: Mapped[int] = mapped_column(ForeignKey("student_exam_attempts.id"))

    question: Mapped["ExamQuestionOrm"] = relationship(back_populates="student_answers")
    student_attempt: Mapped["StudentExamAttemptsOrm"] = relationship(back_populates="student_exam_answers")


class StudentExamMatchingOrm(Base):
    __tablename__ = "student_exam_matching"

    id: Mapped[intpk]
    score: Mapped[float]
    question_id: Mapped[int] = mapped_column(ForeignKey("exam_questions.id"))
    question_type: Mapped[QuestionTypeOption]
    left_id: Mapped[int] = mapped_column(ForeignKey("exam_matching_left.id"))
    right_id: Mapped[int] = mapped_column(ForeignKey("exam_matching_right.id"))
    student_attempt_id: Mapped[int] = mapped_column(ForeignKey("student_exam_attempts.id"))

    question: Mapped["ExamQuestionOrm"] = relationship(back_populates="student_matching")
    student_attempt: Mapped["StudentExamAttemptsOrm"] = relationship(back_populates="student_exam_matching")

    right_option: Mapped["ExamMatchingRightOrm"] = relationship(back_populates="student_exam_matching")
    left_option: Mapped["ExamMatchingLeftOrm"] = relationship(back_populates="student_exam_matching")


class ModeratorOrm(Base):
    __tablename__ = "moderators"

    id: Mapped[intpk]
    name: Mapped[Optional[str]]
    surname: Mapped[Optional[str]]
    phone: Mapped[Optional[str]] = mapped_column(unique=True)
    email: Mapped[Optional[str]] = mapped_column(unique=True)
    country: Mapped[Optional[str]]

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["UserOrm"] = relationship(back_populates="moder")

    @hybrid_property
    def fullname(self):
        if self.name and self.surname:
            return self.name + " " + self.surname
        else:
            return None


class CategoryOrm(Base):
    __tablename__ = "categories"

    id: Mapped[intpk]
    title: Mapped[str] = mapped_column(unique=True)
    description: Mapped[Optional[str]]
    image_path: Mapped[Optional[str]]
    discount: Mapped[int] = mapped_column(default=10)
    is_published: Mapped[bool] = mapped_column(default=False)
    timestamp_add: Mapped[datetime]
    timestamp_change: Mapped[datetime]

    courses: Mapped[list["CourseOrm"]] = relationship(back_populates="category")
    instruction: Mapped["InstructionOrm"] = relationship(back_populates="category")
    certificates: Mapped[list["CategoryCertificateOrm"]] = relationship(back_populates="category")


class CourseOrm(Base):
    __tablename__ = "courses"

    id: Mapped[intpk]
    title: Mapped[str] = mapped_column(unique=True)
    image_path: Mapped[Optional[str]]
    price: Mapped[Optional[float]]
    old_price: Mapped[Optional[float]]
    is_published: Mapped[bool] = mapped_column(default=False)

    quantity_lecture: Mapped[Optional[int]]
    quantity_test: Mapped[Optional[int]]

    c_type: Mapped[Optional[str]] = mapped_column(default="Online course")
    c_duration: Mapped[Optional[str]] = mapped_column(default="3 hours (self-paced)")
    c_award: Mapped[Optional[str]] = mapped_column(default="Certificate")
    c_language: Mapped[Optional[str]] = mapped_column(default="Full audio & text")
    c_level: Mapped[Optional[str]] = mapped_column(default="Introductory")
    c_access: Mapped[Optional[str]] = mapped_column(default="Lifetime access")

    intro_text: Mapped[str]
    skills_text: Mapped[str]
    about_text: Mapped[str]

    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))

    category: Mapped["CategoryOrm"] = relationship(back_populates="courses", uselist=True)

    students: Mapped[list["StudentOrm"]] = relationship(
        back_populates="courses", secondary="student_course_association")

    certificates: Mapped[list["CourseCertificateOrm"]] = relationship(back_populates="course")

    icons: Mapped[list["CourseIconOrm"]] = relationship(back_populates="course")
    lessons: Mapped[list["LessonOrm"]] = relationship(back_populates="course")

    @hybrid_property
    def total_quantity(self):
        return self.quantity_lecture + self.quantity_test


class CourseIconOrm(Base):
    __tablename__ = "course_icons"

    id: Mapped[intpk]
    icon_path: Mapped[str]
    icon_number: Mapped[int]
    icon_title: Mapped[str]
    icon_text: Mapped[str]

    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    course: Mapped["CourseOrm"] = relationship(back_populates="icons")


class LessonOrm(Base):
    __tablename__ = "lessons"

    id: Mapped[intpk]
    type: Mapped[LessonType]
    number: Mapped[int]
    title: Mapped[str]
    description: Mapped[str]
    is_published: Mapped[bool] = mapped_column(default=False)
    scheduled_time: Mapped[Optional[int]]
    image_path: Mapped[Optional[str]]
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))

    course: Mapped["CourseOrm"] = relationship(back_populates="lessons")
    lecture: Mapped["LectureOrm"] = relationship(back_populates="lesson")
    test: Mapped["TestOrm"] = relationship(back_populates="lesson")
    exam: Mapped["ExamOrm"] = relationship(back_populates="lesson")
    student_lesson: Mapped["StudentLessonOrm"] = relationship(back_populates="lesson")


class LectureOrm(Base):
    __tablename__ = "lectures"

    id: Mapped[intpk]
    audios = Column(ARRAY(String), nullable=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id"))
    lesson: Mapped["LessonOrm"] = relationship(back_populates="lecture")

    lecture_attributes: Mapped[list["LectureAttributeOrm"]] = relationship(back_populates="lecture")
    note: Mapped["UserNoteOrm"] = relationship(back_populates="lecture")


class LectureAttributeOrm(Base):
    __tablename__ = "lecture_attributes"

    id: Mapped[intpk]
    a_type: Mapped[LectureAttributeType]
    a_title: Mapped[str]
    a_number: Mapped[int]
    a_text: Mapped[Optional[str]]
    hidden: Mapped[bool] = mapped_column(default=False)
    lecture_id: Mapped[int] = mapped_column(ForeignKey("lectures.id"))

    lecture: Mapped["LectureOrm"] = relationship(back_populates="lecture_attributes")
    files: Mapped[list["LectureFilesOrm"]] = relationship(back_populates="attribute")
    links: Mapped[list["LectureLinksOrm"]] = relationship(back_populates="attribute")

    __table_args__ = (
        CheckConstraint("a_number > 0", name="check_a_number_positive"),
    )


class LectureFilesOrm(Base):
    __tablename__ = "lecture_files"

    id: Mapped[intpk]
    filename: Mapped[str]
    file_path: Mapped[str]
    file_size: Mapped[int]
    file_description: Mapped[Optional[str]]
    download_allowed: Mapped[Optional[bool]] = mapped_column(default=False)
    attribute_id: Mapped[int] = mapped_column(ForeignKey("lecture_attributes.id"))

    attribute: Mapped["LectureAttributeOrm"] = relationship(back_populates="files")


class LectureLinksOrm(Base):
    __tablename__ = "lecture_links"

    id: Mapped[intpk]
    link: Mapped[str]
    anchor: Mapped[Optional[str]]
    attribute_id: Mapped[int] = mapped_column(ForeignKey("lecture_attributes.id"))

    attribute: Mapped["LectureAttributeOrm"] = relationship(back_populates="links")


class TestOrm(Base):
    __tablename__ = "tests"

    id: Mapped[intpk]
    score: Mapped[int] = mapped_column(default=40)
    attempts: Mapped[int] = mapped_column(default=10)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id"))

    lesson: Mapped["LessonOrm"] = relationship(back_populates="test")
    test_questions: Mapped[list["TestQuestionOrm"]] = relationship(back_populates="test")
    student_test_attempts: Mapped[list["StudentTestAttemptsOrm"]] = relationship(back_populates="test")

    __table_args__ = (
        CheckConstraint("score > 0", name="check_score_more_than_0"),
        CheckConstraint("score <= 200", name="check_score_less_than_200"),
    )


class TestQuestionOrm(Base):
    __tablename__ = "test_questions"

    id: Mapped[intpk]
    q_text: Mapped[str]
    q_number: Mapped[int]
    q_score: Mapped[int]
    q_type: Mapped[QuestionTypeOption]
    hidden: Mapped[bool] = mapped_column(default=False)
    image_path: Mapped[Optional[str]]
    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id"))

    test: Mapped["TestOrm"] = relationship(back_populates="test_questions")
    answers: Mapped["TestAnswerOrm"] = relationship(back_populates="question")
    left_option: Mapped["TestMatchingLeftOrm"] = relationship(back_populates="question")
    right_option: Mapped["TestMatchingRightOrm"] = relationship(back_populates="question")

    student_answers: Mapped[list["StudentTestAnswerOrm"]] = relationship(back_populates="question")
    student_matching: Mapped[list["StudentTestMatchingOrm"]] = relationship(back_populates="question")

    __table_args__ = (
        CheckConstraint("q_number > 0", name="check_q_number_positive"),
        CheckConstraint("q_score > 0", name="check_q_score_more_than_0"),
        CheckConstraint("q_score <= 200", name="check_q_score_less_than_200"),
    )


class TestAnswerOrm(Base):
    __tablename__ = "test_answers"

    id: Mapped[intpk]
    a_text: Mapped[str]
    is_correct: Mapped[bool]
    image_path: Mapped[Optional[str]]
    question_id: Mapped[int] = mapped_column(ForeignKey("test_questions.id"))

    question: Mapped["TestQuestionOrm"] = relationship(back_populates="answers")


class TestMatchingRightOrm(Base):
    __tablename__ = "test_matching_right"

    id: Mapped[intpk]
    text: Mapped[str]
    question_id: Mapped[int] = mapped_column(ForeignKey("test_questions.id"))

    question: Mapped["TestQuestionOrm"] = relationship(back_populates="right_option")
    left_option: Mapped["TestMatchingLeftOrm"] = relationship(back_populates="right_option")
    student_test_matching: Mapped["StudentTestMatchingOrm"] = relationship(back_populates="right_option")


class TestMatchingLeftOrm(Base):
    __tablename__ = "test_matching_left"

    id: Mapped[intpk]
    text: Mapped[str]
    right_id: Mapped[int] = mapped_column(ForeignKey("test_matching_right.id"))
    question_id: Mapped[int] = mapped_column(ForeignKey("test_questions.id"))

    question: Mapped["TestQuestionOrm"] = relationship(back_populates="left_option")
    right_option: Mapped["TestMatchingRightOrm"] = relationship(back_populates="left_option")
    student_test_matching: Mapped["StudentTestMatchingOrm"] = relationship(back_populates="left_option")


class ExamOrm(Base):
    __tablename__ = "exams"

    id: Mapped[intpk]
    score: Mapped[int]
    min_score: Mapped[Optional[int]]
    attempts: Mapped[int] = mapped_column(default=10)
    timer: Mapped[int]
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id"))

    lesson: Mapped["LessonOrm"] = relationship(back_populates="exam")
    exam_questions: Mapped[list["ExamQuestionOrm"]] = relationship(back_populates="exam")
    student_exam_attempts: Mapped[list["StudentExamAttemptsOrm"]] = relationship(back_populates="exam")

    __table_args__ = (
        CheckConstraint("score > 0", name="check_score_more_than_0"),
        CheckConstraint("score <= 200", name="check_score_less_than_200"),
    )


class ExamQuestionOrm(Base):
    __tablename__ = "exam_questions"

    id: Mapped[intpk]
    q_text: Mapped[str]
    q_number: Mapped[int]
    q_score: Mapped[int]
    q_type: Mapped[QuestionTypeOption]
    hidden: Mapped[bool] = mapped_column(default=False)
    image_path: Mapped[Optional[str]]
    exam_id: Mapped[int] = mapped_column(ForeignKey("exams.id"))

    exam: Mapped["ExamOrm"] = relationship(back_populates="exam_questions")
    answers: Mapped["ExamAnswerOrm"] = relationship(back_populates="question")
    left_option: Mapped["ExamMatchingLeftOrm"] = relationship(back_populates="question")
    right_option: Mapped["ExamMatchingRightOrm"] = relationship(back_populates="question")

    student_answers: Mapped[list["StudentExamAnswerOrm"]] = relationship(back_populates="question")
    student_matching: Mapped[list["StudentExamMatchingOrm"]] = relationship(back_populates="question")

    __table_args__ = (
        CheckConstraint("q_number > 0", name="check_q_number_positive"),
        CheckConstraint("q_score > 0", name="check_q_score_more_than_0"),
        CheckConstraint("q_score <= 200", name="check_q_score_less_than_200"),
    )


class ExamAnswerOrm(Base):
    __tablename__ = "exam_answers"

    id: Mapped[intpk]
    a_text: Mapped[str]
    is_correct: Mapped[bool]
    image_path: Mapped[Optional[str]]
    question_id: Mapped[int] = mapped_column(ForeignKey("exam_questions.id"))

    question: Mapped["ExamQuestionOrm"] = relationship(back_populates="answers")


class ExamMatchingRightOrm(Base):
    __tablename__ = "exam_matching_right"

    id: Mapped[intpk]
    text: Mapped[str]
    question_id: Mapped[int] = mapped_column(ForeignKey("exam_questions.id"))

    question: Mapped["ExamQuestionOrm"] = relationship(back_populates="right_option")
    left_option: Mapped["ExamMatchingLeftOrm"] = relationship(back_populates="right_option")
    student_exam_matching: Mapped["StudentExamMatchingOrm"] = relationship(back_populates="right_option")


class ExamMatchingLeftOrm(Base):
    __tablename__ = "exam_matching_left"

    id: Mapped[intpk]
    text: Mapped[str]
    right_id: Mapped[int] = mapped_column(ForeignKey("exam_matching_right.id"))
    question_id: Mapped[int] = mapped_column(ForeignKey("exam_questions.id"))

    question: Mapped["ExamQuestionOrm"] = relationship(back_populates="left_option")
    right_option: Mapped["ExamMatchingRightOrm"] = relationship(back_populates="left_option")
    student_exam_matching: Mapped["StudentExamMatchingOrm"] = relationship(back_populates="left_option")


class CourseCertificateOrm(Base):
    __tablename__ = "course_certificates"

    id: Mapped[intpk]
    link: Mapped[str]
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"))
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))

    student: Mapped["StudentOrm"] = relationship(back_populates="course_certificates")
    course: Mapped["CourseOrm"] = relationship(back_populates="certificates")


class CategoryCertificateOrm(Base):
    __tablename__ = "category_certificates"

    id: Mapped[intpk]
    link: Mapped[str]
    addition_link: Mapped[str]
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"))
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))

    student: Mapped["StudentOrm"] = relationship(back_populates="category_certificates")
    category: Mapped["CategoryOrm"] = relationship(back_populates="certificates")


class InstructionOrm(Base):
    __tablename__ = "instructions"

    id: Mapped[intpk]
    name: Mapped[str]
    type: Mapped[InstructionType]
    title: Mapped[str]
    text: Mapped[str]
    last_update: Mapped[datetime]
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id"))

    category: Mapped["CategoryOrm"] = relationship(back_populates="instruction")
    files: Mapped[list["InstructionFilesOrm"]] = relationship(back_populates="instruction")


class InstructionFilesOrm(Base):
    __tablename__ = "instruction_files"

    id: Mapped[intpk]
    file_type: Mapped[str]
    file_name: Mapped[str]
    file_path: Mapped[str]
    file_size: Mapped[int]
    instruction_id: Mapped[int] = mapped_column(ForeignKey("instructions.id"))

    instruction: Mapped["InstructionOrm"] = relationship(back_populates="files")


class FolderOrm(Base):
    __tablename__ = "user_folders"

    id: Mapped[intpk]
    name: Mapped[str]
    parent_id: Mapped[int] = mapped_column(ForeignKey("user_folders.id"), nullable=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"))

    children: Mapped[list["FolderOrm"]] = relationship(
        "FolderOrm", backref="child_folder", remote_side="FolderOrm.id")

    student: Mapped["StudentOrm"] = relationship(back_populates="folders")
    notes: Mapped[list["UserNoteOrm"]] = relationship(back_populates="folder")


class UserNoteOrm(Base):
    __tablename__ = "user_notes"

    id: Mapped[intpk]
    title: Mapped[str]
    text: Mapped[str]
    folder_id: Mapped[int] = mapped_column(ForeignKey("user_folders.id"))
    lecture_id: Mapped[int] = mapped_column(ForeignKey("lectures.id"))

    folder: Mapped["FolderOrm"] = relationship(back_populates="notes")
    lecture: Mapped["LectureOrm"] = relationship(back_populates="note")


class ChatOrm(Base):
    __tablename__ = "chat"

    id: Mapped[intpk]
    chat_subject: Mapped[str]
    status: Mapped[ChatStatusType]
    initiator_id: Mapped[int] = mapped_column(ForeignKey("students.id"))

    initiator: Mapped["StudentOrm"] = relationship(back_populates="chats")
    messages: Mapped[list["ChatMessageOrm"]] = relationship(back_populates="chat")


class ChatMessageOrm(Base):
    __tablename__ = "chat_messages"

    id: Mapped[intpk]
    message: Mapped[str]
    timestamp: Mapped[datetime]
    chat_id: Mapped[int] = mapped_column(ForeignKey("chat.id"))
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    sender_type: Mapped[MessageSenderType]

    recipient_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    recipient_type: Mapped[MessageSenderType]

    chat: Mapped["ChatOrm"] = relationship(back_populates="messages")
    sender: Mapped["UserOrm"] = relationship(foreign_keys=[sender_id], back_populates="sent_messages")
    recipient: Mapped["UserOrm"] = relationship(foreign_keys=[recipient_id], back_populates="received_messages")
    files: Mapped[list["MessageFilesOrm"]] = relationship(back_populates="message")


class MessageFilesOrm(Base):
    __tablename__ = "message_files"

    id: Mapped[intpk]
    file_type: Mapped[str]
    file_name: Mapped[str]
    file_path: Mapped[str]
    file_size: Mapped[int]
    message_id: Mapped[int] = mapped_column(ForeignKey("chat_messages.id"))

    message: Mapped["ChatMessageOrm"] = relationship(back_populates="files")


class LessonTemplateOrm(Base):
    __tablename__ = "lesson_templates"

    id: Mapped[intpk]
    title: Mapped[str]
    type: Mapped[LessonTemplateType]

    lecture_template: Mapped[list["LectureTemplateAttributeOrm"]] = relationship(back_populates="template")
    practical_template: Mapped[list["PracticalTemplateQuestionOrm"]] = relationship(back_populates="template")


class LectureTemplateAttributeOrm(Base):
    __tablename__ = "lecture_template_attributes"

    id: Mapped[intpk]
    a_type: Mapped[LectureAttributeType]
    a_title: Mapped[str]
    a_number: Mapped[int]
    a_text: Mapped[Optional[str]]
    hidden: Mapped[bool] = mapped_column(default=False)

    template_id: Mapped[int] = mapped_column(ForeignKey("lesson_templates.id"))

    template: Mapped["LessonTemplateOrm"] = relationship(back_populates="lecture_template")
    files: Mapped[list["LectureTemplateFileOrm"]] = relationship(back_populates="lecture_template_attr")
    links: Mapped[list["LectureTemplateLinkOrm"]] = relationship(back_populates="lecture_template_attr")


class LectureTemplateFileOrm(Base):
    __tablename__ = "lecture_template_files"

    id: Mapped[intpk]
    filename: Mapped[str]
    file_path: Mapped[str]
    file_size: Mapped[int]
    file_description: Mapped[Optional[str]]
    download_allowed: Mapped[Optional[bool]] = mapped_column(default=False)
    lecture_template_attr_id: Mapped[int] = mapped_column(ForeignKey("lecture_template_attributes.id"))

    lecture_template_attr: Mapped["LectureTemplateAttributeOrm"] = relationship(back_populates="files")


class LectureTemplateLinkOrm(Base):
    __tablename__ = "lecture_template_links"

    id: Mapped[intpk]
    link: Mapped[str]
    anchor: Mapped[Optional[str]]
    lecture_template_attr_id: Mapped[int] = mapped_column(ForeignKey("lecture_template_attributes.id"))

    lecture_template_attr: Mapped["LectureTemplateAttributeOrm"] = relationship(back_populates="links")


class PracticalTemplateQuestionOrm(Base):
    __tablename__ = "practical_template_questions"

    id: Mapped[intpk]
    q_text: Mapped[str]
    q_number: Mapped[int]
    q_score: Mapped[int]
    q_type: Mapped[QuestionTypeOption]
    hidden: Mapped[bool] = mapped_column(default=False)
    image_path: Mapped[Optional[str]]

    template_id: Mapped[int] = mapped_column(ForeignKey("lesson_templates.id"))

    template: Mapped["LessonTemplateOrm"] = relationship(back_populates="practical_template")
    answers: Mapped[list["PracticalTemplateAnswerOrm"]] = relationship(back_populates="practical_question")
    right_option: Mapped[list["PracticalTemplateMatchingRightOrm"]] = relationship(back_populates="practical_question")
    left_option: Mapped[list["PracticalTemplateMatchingLeftOrm"]] = relationship(back_populates="practical_question")


class PracticalTemplateAnswerOrm(Base):
    __tablename__ = "practical_template_answers"

    id: Mapped[intpk]
    a_text: Mapped[str]
    is_correct: Mapped[bool]
    image_path: Mapped[Optional[str]]
    question_id: Mapped[int] = mapped_column(ForeignKey("practical_template_questions.id"))

    practical_question: Mapped["PracticalTemplateQuestionOrm"] = relationship(back_populates="answers")


class PracticalTemplateMatchingRightOrm(Base):
    __tablename__ = "practical_template_matching_right"

    id: Mapped[intpk]
    text: Mapped[str]
    question_id: Mapped[int] = mapped_column(ForeignKey("practical_template_questions.id"))

    practical_question: Mapped["PracticalTemplateQuestionOrm"] = relationship(back_populates="right_option")
    left_option: Mapped["PracticalTemplateMatchingLeftOrm"] = relationship(back_populates="right_option")


class PracticalTemplateMatchingLeftOrm(Base):
    __tablename__ = "practical_template_matching_left"

    id: Mapped[intpk]
    text: Mapped[str]
    right_id: Mapped[int] = mapped_column(ForeignKey("practical_template_matching_right.id"))
    question_id: Mapped[int] = mapped_column(ForeignKey("practical_template_questions.id"))

    practical_question: Mapped["PracticalTemplateQuestionOrm"] = relationship(back_populates="left_option")
    right_option: Mapped["PracticalTemplateMatchingRightOrm"] = relationship(back_populates="left_option")
