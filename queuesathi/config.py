import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")

    DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"

    REFRESH_INTERVAL = 10000

    DEFAULT_SERVICE_SECONDS = 300

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    WTF_CSRF_ENABLED = True
