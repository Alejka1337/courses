from enum import Enum as EnumType


class UserType(str, EnumType):
    student = "student"
    moder = "moder"


class LessonType(str, EnumType):
    lecture = "lecture"
    test = "test"
    exam = "exam"


class LessonTemplateType(str, EnumType):
    lecture = "lecture"
    practical = "practical"


class LectureAttributeType(str, EnumType):
    text = "text"
    present = "present"
    audio = "audio"
    picture = "picture"
    video = "video"
    file = "file"
    link = "link"


class QuestionTypeOption(str, EnumType):
    test = "test"
    boolean = "boolean"
    answer_with_photo = "answer_with_photo"
    question_with_photo = "question_with_photo"
    matching = "matching"
    multiple_choice = "multiple_choice"


class LessonStatus(str, EnumType):
    completed = "completed"
    active = "active"
    blocked = "blocked"
    new = "new"
    available = "available"


class CourseStatus(str, EnumType):
    completed = "completed"
    in_progress = "in_progress"


class InstructionType(str, EnumType):
    general = "general"
    course = "course"


class ChatStatusType(str, EnumType):
    new = "new"
    active = "active"
    archive = "archive"


class MessageSenderType(str, EnumType):
    student = "student"
    admin = "admin"


class NotificationType(str, EnumType):
    change_course = "change_course"
    added_course = "added_course"


class StaticFileType(str, EnumType):
    student_avatar = "student_avatar"
    category_avatar = "category_avatar"
    course_image = "course_image"
    course_icon = "course_icon"
    lesson_image = "lesson_image"
    instruction_file = "instruction_file"
    chat_file = "chat_file"
