import logging
import uvicorn

# from debug_toolbar.middleware import DebugToolbarMiddleware
from fastapi import Depends, FastAPI, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from fastapi.security import HTTPBearer
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
from src.api_routers.template import router as template_router
from src.api_routers.notes import router as note_router
from src.api_routers.stripe import router as stripe_router
from src.api_routers.certificates import router as certificates_router
from src.config import API_PREFIX

http_bearer = HTTPBearer(auto_error=False)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler("headers.log")
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

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
    chat_router, prefix=API_PREFIX, tags=["Chat"]
)
app.include_router(
    template_router, prefix=API_PREFIX, tags=["Template"], dependencies=[Depends(http_bearer)]
)

app.include_router(
    note_router, prefix=API_PREFIX, tags=["Note"], dependencies=[Depends(http_bearer)]
)

app.include_router(certificates_router, prefix=API_PREFIX, tags=["Certificates"])
app.include_router(stripe_router, prefix=API_PREFIX, tags=["Stripe"])

origins = [
    "http://localhost",
    "http://localhost:8100",
    "http://localhost:8101",
    "https://localhost",
    "https://vps2.xyz",
    "http://192.168.0.151:8100/",
    "http://localhost:3000/",

]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "TRACE", "HEAD", "CONNECT"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_request_origin(request: Request, call_next):
    print(request.url)
    client = f"{request.client.host}:{request.client.port}"
    headers = dict(request.headers)

    logger.info(f"Recieve request on {request.url} from client – {client} with headers – {headers}")
    response = await call_next(request)
    return response

# app.add_middleware(
#     DebugToolbarMiddleware,
#     panels=["debug_toolbar.panels.sqlalchemy.SQLAlchemyPanel"],
# )


@app.get("/")
async def ping():
    return {"message": "I'm working right now"}


@app.get("/.well-known/apple-developer-merchantid-domain-association")
async def verify():
    with open('.well-known/apple-developer-merchantid-domain-association') as fo:
        return Response(fo.read(), headers={"mimetype": "text/plain"})


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000)
