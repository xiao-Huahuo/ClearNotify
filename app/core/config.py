from pathlib import Path
import os
from dotenv import load_dotenv
import logging

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
# Docker生产环境下,优先加载容器下环境变量,其次再加载开发时.env
logger = logging.getLogger("ClearNotify")
if not os.getenv("DOCKER_DEPLOYMENT"):
    print("==================== PRINT | Environment Variables From .env ====================")
    logger.info("==================== Environment Variables From .env ====================")
    ENV_PATH = PROJECT_ROOT / ".env"
    load_dotenv(dotenv_path=ENV_PATH)
else:
    print("==================== PRINT | Environment Variables From Docker-Compose ====================")
    logger.info("==================== Environment Variables From Docker-Compose ====================")
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

    # 去掉所有 os.getenv 的默认值参数
    SECRET_KEY = os.getenv("SECRET_KEY")
    ALGORITHM = os.getenv("ALGORITHM")
    ACCESS_TOKEN_EXPIRE_DAYS = int(os.getenv("ACCESS_TOKEN_EXPIRE_DAYS"))

    PORT = int(os.getenv("PORT"))
    HOST = os.getenv("HOST")

    REDIS_HOST = os.getenv("REDIS_HOST")
    REDIS_PORT = int(os.getenv("REDIS_PORT"))
    REDIS_DB_CACHE = int(os.getenv("REDIS_DB_CACHE"))
    REDIS_DB_QUEUE = int(os.getenv("REDIS_DB_QUEUE"))
    REDIS_QUEUE_NAME = os.getenv("REDIS_QUEUE_NAME")

    CRAWLER_RATE_LIMIT = int(os.getenv("CRAWLER_RATE_LIMIT"))
    CRAWLER_RATE_WINDOW_SECONDS = int(os.getenv("CRAWLER_RATE_WINDOW_SECONDS"))

    SMTP_HOST = os.getenv("SMTP_HOST")
    SMTP_PORT = int(os.getenv("SMTP_PORT"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    SMTP_SENDER = os.getenv("SMTP_SENDER")
    SMTP_SENDER_NAME = os.getenv("SMTP_SENDER_NAME")
    SMTP_USE_SSL = os.getenv("SMTP_USE_SSL", "").lower() == "true"
    SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "").lower() == "true"
    EMAIL_VERIFICATION_CODE_LENGTH = int(os.getenv("EMAIL_VERIFICATION_CODE_LENGTH"))
    EMAIL_VERIFICATION_EXPIRE_MINUTES = int(os.getenv("EMAIL_VERIFICATION_EXPIRE_MINUTES"))

    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
    ADMIN_PHONE = os.getenv("ADMIN_PHONE")
    REALTIME_STREAM_INTERVAL_SECONDS = float(os.getenv("REALTIME_STREAM_INTERVAL_SECONDS"))

    PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL")
    FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL")

    MOONSHOT_API_KEY = os.getenv("MOONSHOT_API_KEY")
    MOONSHOT_API_TIMEOUT = float(os.getenv("MOONSHOT_API_TIMEOUT"))
    MOONSHOT_MODEL=os.getenv("MOONSHOT_MODEL")

    @staticmethod
    def _show_config():
        """
        调试专用：直接使用 print 输出所有配置成员，确保在 Docker 中可见。
        """
        import os
        source = "Docker-Compose" if os.getenv("DOCKER_DEPLOYMENT") else ".env"

        # 头部：美丽的分割线
        print(f"\n{'=' * 20} [DEBUG] GlobalConfig Members ({source}) {'=' * 20}")

        # 自动获取类成员
        # 过滤掉内置属性(__)和方法(callable)
        attrs = [attr for attr in dir(GlobalConfig) if
                 not attr.startswith('__') and not callable(getattr(GlobalConfig, attr))]

        for attr in sorted(attrs):
            val = getattr(GlobalConfig, attr)
            # 格式化输出：变量名左对齐占 35 位，中间用竖线分隔
            print(f"{attr:35} | {val}")

        # 底部：美丽的分割线
        print(f"{'=' * 75}\n")



# ===== DEBUG: 展示所有环境变量 =====
GlobalConfig._show_config()




