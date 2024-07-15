import os

from dotenv import load_dotenv

load_dotenv()

# Base
API_PREFIX = os.getenv("API_PREFIX")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE = int(os.getenv("ACCESS_TOKEN_EXPIRE"))
REFRESH_TOKEN_EXPIRE = int(os.getenv("REFRESH_TOKEN_EXPIRE"))
GOOGLE_AUTH_SECRET = os.getenv("GOOGLE_AUTH_SECRET")

# Postgres
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")
DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
# DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Redis
BROKER_URL = os.getenv("BROKER_URL")

# SMTP
SMTP_PASS = os.getenv("SMTP_PASSWORD")
SMTP_USER = os.getenv("SMTP_USERNAME")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
SMTP_SERVER = os.getenv("SMTP_SERVER")

# TextToSpeech
SPEECHES_DIR = "static/speeches"
MALE_VOICES = [
    "com.apple.speech.synthesis.voice.Alex",
    "com.apple.speech.synthesis.voice.daniel",
    "com.apple.speech.synthesis.voice.rishi"
]
FEMALE_VOICE = [
    "com.apple.speech.synthesis.voice.karen",
    "com.apple.speech.synthesis.voice.moira",
    "com.apple.speech.synthesis.voice.samantha"
]

# STATIC FILES DIRS
STUDENT_AVATAR_PATH = "static/images/"
CATEGORY_AVATAR_PATH = "static/categories/"
COURSE_IMAGE_PATH = "static/course/image/"
COURSE_ICON_PATH = "static/course/icon/"
LESSON_IMAGE_PATH = "static/lessons/"
INSTRUCTION_FILES_PATH = "static/course/instruction/"
CHAT_FILES_PATH = "static/chatfiles/"
