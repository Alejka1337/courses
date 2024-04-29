from sqlalchemy import asc, func
from sqlalchemy.orm import Session

from src.crud.exam import ExamRepository
from src.crud.test import select_test_answers_db
from src.enums import LectureAttributeType, LessonType, QuestionTypeOption
from src.models import (CourseOrm, ExamMatchingLeftOrm, ExamMatchingRightOrm, ExamOrm, ExamQuestionOrm,
                        LectureAttributeOrm, LectureOrm, LessonOrm, TestMatchingLeftOrm, TestMatchingRightOrm, TestOrm,
                        TestQuestionOrm, UserOrm)
from src.schemas.lesson import LessonCreate


def create_lesson_db(db: Session, data: LessonCreate) -> LessonOrm:
    new_lesson = LessonOrm(**data.dict())
    db.add(new_lesson)
    db.commit()
    db.refresh(new_lesson)
    return new_lesson


def create_lecture_db(db: Session, lesson_id: int):
    new_lecture = LectureOrm(lesson_id=lesson_id)
    db.add(new_lecture)
    db.commit()
    db.refresh(new_lecture)
    return new_lecture


def create_test_db(db: Session, lesson_id: int):
    new_test = TestOrm(lesson_id=lesson_id, score=40, attempts=10)
    db.add(new_test)
    db.commit()
    db.refresh(new_test)
    return new_test


def create_exam_db(db: Session, lesson_id: int, course_id: int):
    count_test = (db.query(LessonOrm)
                  .filter(LessonOrm.course_id == course_id, LessonOrm.type == LessonType.test.value)
                  .count())
    exam_score = 200

    if count_test > 0:
        test_lesson_ids = (db.query(LessonOrm.id.label("id")).
                           filter(LessonOrm.course_id == course_id, LessonOrm.type == LessonType.test.value)
                           .all())

        lesson_ids = [test_lesson.id for test_lesson in test_lesson_ids]
        test_total_score = db.query(func.sum(TestOrm.score)).filter(TestOrm.lesson_id.in_(lesson_ids)).scalar()
        exam_score -= test_total_score

    new_exam = ExamOrm(score=exam_score, attempts=10, timer=40, lesson_id=lesson_id)
    db.add(new_exam)
    db.commit()
    db.refresh(new_exam)
    return new_exam


def select_lesson_db(db: Session, lesson_id: int, user: UserOrm):
    lesson = db.query(LessonOrm).filter(LessonOrm.id == lesson_id).first()
    if lesson is None:
        return None

    elif lesson.type == LessonType.lecture.value:
        lecture = db.query(LectureOrm).filter(LectureOrm.lesson_id == lesson_id).first()

        if lecture:
            lecture_attributes = (db.query(LectureAttributeOrm)
                                  .filter(LectureAttributeOrm.lecture_id == lecture.id).all())

            lecture_data = {"lecture_id": lecture.id, "lecture_speeches": lecture.audios, "attributes": []}

            for attr in lecture_attributes:
                files = []
                links = []

                if attr.a_type in [LectureAttributeType.present, LectureAttributeType.audio, LectureAttributeType.video,
                                   LectureAttributeType.picture, LectureAttributeType.file]:
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
                    "files": [{
                        "file_id": file.id,
                        "filename": file.filename,
                        "file_path": file.file_path,
                        "file_size": file.file_size,
                        "file_description": file.file_description,
                        "download_allowed": file.download_allowed
                    } for file in files if files],
                    "links": [{
                        "link_id": link.id,
                        "link": link.link,
                        "anchor": link.anchor
                    } for link in links if links]
                }

                lecture_data["attributes"].append(attribute_data)

            setattr(lesson, "lecture_info", lecture_data)
            return lesson

        else:
            return lesson

    elif lesson.type == LessonType.test.value:
        test = db.query(TestOrm).filter(TestOrm.lesson_id == lesson_id).first()

        if test:
            test_questions = db.query(TestQuestionOrm).filter(TestQuestionOrm.test_id == test.id).all()
            test_data = {"test_id": test.id, "score": test.score, "attempts": test.attempts, "questions": []}

            for question in test_questions:

                question_data = {
                    "q_id": question.id,
                    "q_text": question.q_text,
                    "q_number": question.q_number,
                    "q_score": question.q_score,
                    "q_type": question.q_type,
                    "hidden": question.hidden,
                    "image_path": None,
                    "answers": []
                }

                # if user.usertype == UserType.student.value:
                #     student_score = db.query(StudentTestQuestionOrm.score).filter(
                #         StudentTestQuestionOrm.question_id == question.id,
                #         StudentTestQuestionOrm.student_id == user.student.id).scalar()
                #     question_data["current_score"] = student_score if student_score else None

                if question.q_type in [QuestionTypeOption.test.value, QuestionTypeOption.boolean.value]:
                    answers = select_test_answers_db(db=db, question_id=question.id)

                    for answer in answers:
                        answer_data = {"a_id": answer.id, "a_text": answer.a_text, "is_correct": answer.is_correct}
                        question_data["answers"].append(answer_data)

                elif question.q_type == QuestionTypeOption.answer_with_photo.value:
                    answers = select_test_answers_db(db=db, question_id=question.id)

                    for answer in answers:
                        answer_data = {"a_id": answer.id, "a_text": answer.a_text, "is_correct": answer.is_correct,
                                       "image_path": answer.image_path}
                        question_data["answers"].append(answer_data)

                elif question.q_type == QuestionTypeOption.question_with_photo.value:
                    question_data["image_path"] = question.image_path
                    answers = select_test_answers_db(db=db, question_id=question.id)

                    for answer in answers:
                        answer_data = {"a_id": answer.id, "a_text": answer.a_text, "is_correct": answer.is_correct}
                        question_data["answers"].append(answer_data)

                elif question.q_type == QuestionTypeOption.multiple_choice.value:
                    answers = select_test_answers_db(db=db, question_id=question.id)
                    counter = 0

                    for answer in answers:
                        if answer.is_correct:
                            counter += 1

                        answer_data = {"a_id": answer.id, "a_text": answer.a_text, "is_correct": answer.is_correct}
                        question_data["answers"].append(answer_data)
                        question_data["count_correct"] = counter

                else:
                    left_options = (db.query(TestMatchingLeftOrm)
                                    .filter(TestMatchingLeftOrm.question_id == question.id).all())

                    right_options = (db.query(TestMatchingRightOrm)
                                     .filter(TestMatchingRightOrm.question_id == question.id).all())

                    question_data["answers"] = {
                        "left": [{"value": left_option.text, "id": left_option.id} for left_option in left_options],
                        "right": [{"value": right_option.text, "id": right_option.id} for right_option in right_options]
                    }

                test_data["questions"].append(question_data)

            setattr(lesson, "test_data", test_data)
            return lesson

        else:
            return lesson

    else:
        exam_repository = ExamRepository(db=db)
        exam = db.query(ExamOrm).filter(ExamOrm.lesson_id == lesson_id).first()

        if exam:
            exam_questions = db.query(ExamQuestionOrm).filter(ExamQuestionOrm.exam_id == exam.id).all()
            exam_data = {"exam_id": exam.id, "score": exam.score, "attempts": exam.attempts, "questions": []}

            for question in exam_questions:
                question_data = {"q_id": question.id, "q_text": question.q_text, "q_number": question.q_number,
                                 "q_score": question.q_score, "q_type": question.q_type, "hidden": question.hidden,
                                 "image_path": None, "answers": []}

                if question.q_type in [QuestionTypeOption.test.value, QuestionTypeOption.boolean.value]:
                    answers = exam_repository.select_exam_answers(question_id=question.id)

                    for answer in answers:
                        answer_data = {"a_id": answer.id, "a_text": answer.a_text, "is_correct": answer.is_correct}
                        question_data["answers"].append(answer_data)

                elif question.q_type == QuestionTypeOption.answer_with_photo.value:
                    answers = exam_repository.select_exam_answers(question_id=question.id)

                    for answer in answers:
                        answer_data = {"a_id": answer.id, "a_text": answer.a_text, "is_correct": answer.is_correct,
                                       "image_path": answer.image_path}
                        question_data["answers"].append(answer_data)

                elif question.q_type == QuestionTypeOption.question_with_photo.value:
                    question_data["image_path"] = question.image_path
                    answers = exam_repository.select_exam_answers(question_id=question.id)

                    for answer in answers:
                        answer_data = {"a_id": answer.id, "a_text": answer.a_text, "is_correct": answer.is_correct}
                        question_data["answers"].append(answer_data)

                elif question.q_type == QuestionTypeOption.multiple_choice.value:
                    answers = exam_repository.select_exam_answers(question_id=question.id)

                    for answer in answers:
                        counter = 0
                        if answer.is_correct:
                            counter += 1

                        answer_data = {"a_id": answer.id, "a_text": answer.a_text, "is_correct": answer.is_correct}
                        question_data["answers"].append(answer_data)
                        question_data["count_correct"] = counter

                else:
                    left_options = (db.query(ExamMatchingLeftOrm)
                                    .filter(ExamMatchingLeftOrm.question_id == question.id).all())

                    right_options = (db.query(ExamMatchingRightOrm)
                                     .filter(ExamMatchingRightOrm.question_id == question.id).all())

                    question_data["answers"] = {
                        "left": [
                            {"value": left_option.text, "id": left_option.id} for left_option in left_options],
                        "right": [
                            {"value": right_option.text, "id": right_option.id} for right_option in right_options]
                    }

                exam_data["questions"].append(question_data)
            setattr(lesson, "exam_data", exam_data)
            return lesson
        else:
            return lesson


def select_lessons_by_course_db(db: Session, course_id: int):
    return db.query(LessonOrm).filter(LessonOrm.course_id == course_id).order_by(asc(LessonOrm.number)).all()


def select_lesson_by_id_db(db: Session, lesson_id: int):
    return db.query(LessonOrm).filter(LessonOrm.id == lesson_id).first()


def select_lesson_by_number_and_course_id_db(db: Session, number: int, course_id: int):
    return db.query(LessonOrm).filter(LessonOrm.number == number, LessonOrm.course_id == course_id).first()


def select_lesson_by_type_and_title_db(db: Session, lesson_type: LessonType, lesson_title: str):
    return db.query(LessonOrm).filter(LessonOrm.type == lesson_type, LessonOrm.title == lesson_title).first()


def check_lesson_number_db(db: Session, course_id: int, number: int):
    return db.query(LessonOrm).filter(LessonOrm.course_id == course_id, LessonOrm.number == number).count()


def update_lesson_number_db(db: Session, number: int, course_id: int):
    (db.query(LessonOrm).filter(LessonOrm.course_id == course_id, LessonOrm.number >= number).
     update({LessonOrm.number: LessonOrm.number + 1}, synchronize_session=False))

    db.commit()


def check_validity_lesson(db: Session, course_id: int):
    total_test_score = (db.query(func.sum(TestOrm.score))
                        .join(LessonOrm)
                        .filter(LessonOrm.course_id == course_id, LessonOrm.type == LessonType.test.value)
                        .scalar())

    total_exam_score = (db.query(func.sum(ExamOrm.score))
                        .join(LessonOrm)
                        .filter(LessonOrm.course_id == course_id, LessonOrm.type == LessonType.exam.value)
                        .scalar())

    if total_test_score + total_exam_score != 200:
        return {"result": False, "message": "Course max score less than 200"}

    tests = db.query(TestOrm).join(LessonOrm).filter(LessonOrm.course_id == course_id).all()
    for test in tests:
        test_question_scores = (db.query(func.sum(TestQuestionOrm.q_score))
                                .filter(TestQuestionOrm.test_id == test.id)
                                .scalar())

        if test_question_scores != test.score:
            return {"result": False, "message": f"Sum for all question in test {test.id} not equal {test.score}"}

    exam = db.query(ExamOrm).join(LessonOrm).filter(LessonOrm.course_id == course_id).first()
    exam_question_score = (db.query(func.sum(ExamQuestionOrm.q_score))
                           .filter(ExamQuestionOrm.exam_id == exam.id)
                           .scalar())

    if exam_question_score != total_exam_score:
        return {"result": False, "message": f"Sum for all question in exam {exam.id} not equal {exam.score}"}
    else:
        db.query(CourseOrm).filter(CourseOrm.id == course_id).update({CourseOrm.is_published: True})
        return {"result": True, "message": "Course successfully published"}
