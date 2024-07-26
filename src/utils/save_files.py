import os
from typing import Literal
from datetime import datetime

from fastapi import UploadFile

from src.config import (CATEGORY_AVATAR_PATH, CHAT_FILES_PATH, COURSE_ICON_PATH, COURSE_IMAGE_PATH,
                        INSTRUCTION_FILES_PATH, LESSON_IMAGE_PATH, STUDENT_AVATAR_PATH)
from src.enums import StaticFileType

MODE = Literal["mp3", "all"]


def save_file(file: UploadFile, file_type: StaticFileType):
    if file_type == StaticFileType.student_avatar.value:
        folder = STUDENT_AVATAR_PATH + datetime.now().strftime("%d-%m-%Y")

    elif file_type == StaticFileType.category_avatar.value:
        folder = CATEGORY_AVATAR_PATH + datetime.now().strftime("%d-%m-%Y")

    elif file_type == StaticFileType.course_image.value:
        folder = COURSE_IMAGE_PATH + datetime.now().strftime("%d-%m-%Y")

    elif file_type == StaticFileType.course_icon.value:
        folder = COURSE_ICON_PATH + datetime.now().strftime("%d-%m-%Y")

    elif file_type == StaticFileType.lesson_image.value:
        folder = LESSON_IMAGE_PATH + datetime.now().strftime("%d-%m-%Y")

    elif file_type == StaticFileType.instruction_file.value:
        folder = INSTRUCTION_FILES_PATH + datetime.now().strftime("%d-%m-%Y")

    else:
        folder = CHAT_FILES_PATH + datetime.now().strftime("%d-%m-%Y")

    file_path = os.path.join(folder, file.filename)
    os.makedirs(folder, exist_ok=True)

    with open(file_path, "wb") as f:
        f.write(file.file.read())

    return file_path


def delete_files_in_directory(directory: str, mode: MODE):
    file_list = os.listdir(directory)
    for file_name in file_list:
        if mode == "all" or (mode == "mp3" and file_name.endswith(".mp3")):
            file_path = os.path.join(directory, file_name)
            try:
                os.remove(file_path)
                print(f"File {file_path} successfully removed")
            except Exception as e:
                print(f"Remove file {file_path} error: {e}")


def delete_file(file_path: str):
    try:
        os.remove(file_path)
    except Exception as e:
        print(f"Remove file {file_path} error: {e}")
