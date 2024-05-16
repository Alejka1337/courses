import os
from datetime import datetime

from fastapi import UploadFile


def save_student_avatar(file: UploadFile):
    folder = "static/images/" + datetime.now().strftime("%d-%m-%Y")
    file_path = os.path.join(folder, file.filename)
    os.makedirs(folder, exist_ok=True)

    with open(file_path, "wb") as f:
        f.write(file.file.read())

    return file_path


def save_category_course_avatar(file: UploadFile):
    folder = "static/categories/" + datetime.now().strftime("%d-%m-%Y")
    file_path = os.path.join(folder, file.filename)
    os.makedirs(folder, exist_ok=True)

    with open(file_path, "wb") as f:
        f.write(file.file.read())

    return file_path


def save_course_image(file: UploadFile):
    folder = "static/course/image/" + datetime.now().strftime("%d-%m-%Y")
    file_path = os.path.join(folder, file.filename)
    os.makedirs(folder, exist_ok=True)

    with open(file_path, "wb") as f:
        f.write(file.file.read())

    return file_path


def save_course_icon(file: UploadFile):
    folder = "static/course/icon/" + datetime.now().strftime("%d-%m-%Y")
    file_path = os.path.join(folder, file.filename)
    os.makedirs(folder, exist_ok=True)

    with open(file_path, "wb") as f:
        f.write(file.file.read())

    return file_path


def save_lesson_image(file: UploadFile):
    folder = "static/lessons/" + datetime.now().strftime("%d-%m-%Y")
    file_path = os.path.join(folder, file.filename)
    os.makedirs(folder, exist_ok=True)

    with open(file_path, "wb") as f:
        f.write(file.file.read())

    return file_path


def save_instruction_file(file: UploadFile):
    folder = "static/course/instruction/" + datetime.now().strftime("%d-%m-%Y")
    file_path = os.path.join(folder, file.filename)
    os.makedirs(folder, exist_ok=True)

    with open(file_path, "wb") as f:
        f.write(file.file.read())

    return file_path


def save_chat_file(file: UploadFile):
    folder = "static/chatfiles/" + datetime.now().strftime("%d-%m-%Y")
    file_path = os.path.join(folder, file.filename)
    os.makedirs(folder, exist_ok=True)

    with open(file_path, "wb") as f:
        f.write(file.file.read())

    return file_path


def delete_files_in_directory(directory):
    file_list = os.listdir(directory)
    for file_name in file_list:
        file_path = os.path.join(directory, file_name)
        try:
            os.remove(file_path)
            print(f"Файл {file_path} успешно удален")
        except Exception as e:
            print(f"Ошибка при удалении файла {file_path}: {e}")


def delete_file(file_path: str):
    try:
        os.remove(file_path)
    except Exception as e:
        print(f"Ошибка при удалении файла {file_path}: {e}")
