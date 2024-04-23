import re


def create_notification_text_for_update_course(course_name: str, lesson_type: str, lesson_title: str):
    return (f"Your course – {course_name} has been changed. "
            f"Was added new {lesson_type} with title – {lesson_title}. "
            f"Would you like to upgrade your course program?")


def parse_notification_text(message: str):
    lecture_type_pattern = r"Was added new (\w+)"
    lecture_title_pattern = r"with title – (.+?)\."

    lecture_type_match = re.search(lecture_type_pattern, message)
    lecture_title_match = re.search(lecture_title_pattern, message)

    return {"lesson_type": lecture_type_match.group(1), "lesson_title": lecture_title_match.group(1)}


def create_notification_text_for_add_new_course(course_name: str, category_name: str):
    return (f"In the category {category_name} added new course – {course_name}. "
            f"We offer 10% discount on new course purchase")
