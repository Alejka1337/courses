import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.api_routers.category import router as category_router
from src.api_routers.chat import router as chat_router
from src.api_routers.course import router as course_router
from src.api_routers.exam import router as exam_router
from src.api_routers.instruction import router as instruction_router
from src.api_routers.lecture import router as lecture_router
from src.api_routers.lesson import router as lesson_router
from src.api_routers.notifications import router as notification_router
from src.api_routers.student_exam import router as student_exam_router
from src.api_routers.student_test import router as student_test_router
from src.api_routers.test import router as test_router
from src.api_routers.user import router as user_router
from src.config import API_PREFIX

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(user_router, prefix=API_PREFIX, tags=["User"])
app.include_router(notification_router, prefix=API_PREFIX, tags=["Notification"])
app.include_router(category_router, prefix=API_PREFIX, tags=["Category"])
app.include_router(course_router, prefix=API_PREFIX, tags=["Course"])
app.include_router(lesson_router, prefix=API_PREFIX, tags=["Lesson"])
app.include_router(lecture_router, prefix=API_PREFIX, tags=["Lecture"])
app.include_router(test_router, prefix=API_PREFIX, tags=["Test"])
app.include_router(exam_router, prefix=API_PREFIX, tags=["Exam"])
app.include_router(student_test_router, prefix=API_PREFIX, tags=["Student Test"])
app.include_router(student_exam_router, prefix=API_PREFIX, tags=["Student Exam"])
app.include_router(instruction_router, prefix=API_PREFIX, tags=["Instruction"])
app.include_router(chat_router, prefix=API_PREFIX, tags=["Chat"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/")
async def ping():
    return {"message": "I'm working right now"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000)
