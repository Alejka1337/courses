import uvicorn
# from debug_toolbar.middleware import DebugToolbarMiddleware
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import ORJSONResponse
from fastapi.security import HTTPBearer

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

http_bearer = HTTPBearer(auto_error=False)

app = FastAPI(debug=True, default_response_class=ORJSONResponse)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(
    user_router, prefix=API_PREFIX, tags=["User"], dependencies=[Depends(http_bearer)]
)
app.include_router(
    notification_router, prefix=API_PREFIX, tags=["Notification"], dependencies=[Depends(http_bearer)]
)
app.include_router(
    category_router, prefix=API_PREFIX, tags=["Category"], dependencies=[Depends(http_bearer)]
)
app.include_router(
    course_router, prefix=API_PREFIX, tags=["Course"], dependencies=[Depends(http_bearer)]
)
app.include_router(
    lesson_router, prefix=API_PREFIX, tags=["Lesson"], dependencies=[Depends(http_bearer)]
)
app.include_router(
    lecture_router, prefix=API_PREFIX, tags=["Lecture"], dependencies=[Depends(http_bearer)]
)
app.include_router(
    test_router, prefix=API_PREFIX, tags=["Test"], dependencies=[Depends(http_bearer)]
)
app.include_router(
    exam_router, prefix=API_PREFIX, tags=["Exam"], dependencies=[Depends(http_bearer)]
)
app.include_router(
    student_test_router, prefix=API_PREFIX, tags=["Student Test"], dependencies=[Depends(http_bearer)]
)
app.include_router(
    student_exam_router, prefix=API_PREFIX, tags=["Student Exam"], dependencies=[Depends(http_bearer)]
)
app.include_router(
    instruction_router, prefix=API_PREFIX, tags=["Instruction"], dependencies=[Depends(http_bearer)]
)
app.include_router(
    chat_router, prefix=API_PREFIX, tags=["Chat"], dependencies=[Depends(http_bearer)]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# app.add_middleware(
#     DebugToolbarMiddleware,
#     panels=["debug_toolbar.panels.sqlalchemy.SQLAlchemyPanel"],
# )


@app.get("/")
async def ping():
    return {"message": "I'm working right now"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000)
