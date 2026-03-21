from pathlib import Path
import os

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=ENV_PATH)


class GlobalConfig:
    DEFAULT_ADMIN_PASSWORD = "111111"
    DEFAULT_ADMIN_USERNAME = "admin"
    DEFAULT_ADMIN_EMAIL = "unknown@email.com"
    DEFAULT_ADMIN_PHONE = None

    PROJECT_ROOT = PROJECT_ROOT

    SQLITE_DATABASE_FILENAME = "database.db"
    DB_PATH = PROJECT_ROOT / SQLITE_DATABASE_FILENAME

    UPLOAD_DIR = PROJECT_ROOT / "uploads"
    AVATAR_UPLOAD_DIR = UPLOAD_DIR / "avatars"
    DOCS_UPLOAD_DIR = UPLOAD_DIR / "docs"
    IMAGES_UPLOAD_DIR = UPLOAD_DIR / "images"
    CHAT_EXPORT_DIR = UPLOAD_DIR / "chat_exports"
    KNOWLEDGE_DIR = PROJECT_ROOT / "app" / "resources"
    KNOWLEDGE_BASE_PATH = KNOWLEDGE_DIR / "policy_knowledge.json"
    LOG_DIR = PROJECT_ROOT / "logs"
    APP_LOG_PATH = LOG_DIR / "app.log"
    MAIL_OUTBOX_DIR = PROJECT_ROOT / "mail_outbox"
    CHROMA_DIR = PROJECT_ROOT / "chroma_store"

    SECRET_KEY = os.getenv("SECRET_KEY", "09d25e094faa6ca2556c81")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_DAYS = int(os.getenv("ACCESS_TOKEN_EXPIRE_DAYS", 30))

    PORT = int(os.getenv("PORT", 8080))
    HOST = os.getenv("HOST", "127.0.0.1")

    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB_CACHE = int(os.getenv("REDIS_DB_CACHE", 0))
    REDIS_DB_QUEUE = int(os.getenv("REDIS_DB_QUEUE", 1))
    REDIS_QUEUE_NAME = os.getenv("REDIS_QUEUE_NAME", "crawler_tasks")

    CRAWLER_RATE_LIMIT = int(os.getenv("CRAWLER_RATE_LIMIT", 30))
    CRAWLER_RATE_WINDOW_SECONDS = int(os.getenv("CRAWLER_RATE_WINDOW_SECONDS", 60))

    SMTP_HOST = os.getenv("SMTP_HOST", "")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 465))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SMTP_SENDER = os.getenv("SMTP_SENDER", SMTP_USERNAME or DEFAULT_ADMIN_EMAIL)
    SMTP_SENDER_NAME = os.getenv("SMTP_SENDER_NAME", "ClearNotify")
    SMTP_USE_SSL = os.getenv("SMTP_USE_SSL", "true").lower() == "true"
    SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "false").lower() == "true"

    EMAIL_VERIFICATION_CODE_LENGTH = int(os.getenv("EMAIL_VERIFICATION_CODE_LENGTH", 6))
    EMAIL_VERIFICATION_EXPIRE_MINUTES = int(
        os.getenv("EMAIL_VERIFICATION_EXPIRE_MINUTES", 15)
    )

    REALTIME_STREAM_INTERVAL_SECONDS = int(
        os.getenv("REALTIME_STREAM_INTERVAL_SECONDS", 3)
    )
