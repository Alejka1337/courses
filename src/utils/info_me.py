from typing import Set

from src.models import ImageOrm, StudentCourseAssociation, StudentOrm, UserOrm


def set_info_me(user: UserOrm, student: StudentOrm, image: ImageOrm, courses: list[StudentCourseAssociation]):
    result = {
        "user_id": user.id,
        "user_type": user.usertype,
        "username": user.username,
        "email": student.email,
        "name": student.name,
        "surname": student.surname,
        "phone": student.phone,
        "country": student.country,
        "balance": student.balance,
        "studying_time": student.studying_time,
        "image": image.path if image else None,
        "changed_name": student.changed_name,
        "changed_surname": student.changed_surname,
        "courses": [],
        "chats": student.chats
    }

    for course in courses:
        course_info = {
            "course_id": course.course_id,
            "status": course.status,
            "progress": course.progress,
            "grade": course.grade
        }

        result["courses"].append(course_info)

    return result
