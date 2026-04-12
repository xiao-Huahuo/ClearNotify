from pathlib import Path
import os
from dotenv import load_dotenv
import logging


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
logger = logging.getLogger("ClearNotify")


def _to_bool(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


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
    KNOWLEDGE_BASE_PATH = KNOWLEDGE_DIR / "vector_init" / "policy_knowledge.json"
    EMBEDDING_MODELS_DIR = KNOWLEDGE_DIR / "embedding"
    DEFAULT_AGENT_PLUGIN_EMBEDDING_MODEL = EMBEDDING_MODELS_DIR / "paraphrase-multilingual-MiniLM-L12-v2"
    DEFAULT_PADDLEOCR_MODELS_DIR = KNOWLEDGE_DIR / "paddleocr"
    DB_INIT_DIR = KNOWLEDGE_DIR / "db_init"
    DB_INIT_DATA_PATH = PROJECT_ROOT / "seed_data.json"  # deprecated compatibility only
    LOG_DIR = PROJECT_ROOT / "logs"
    APP_LOG_PATH = LOG_DIR / "app.log"
    MAIL_OUTBOX_DIR = PROJECT_ROOT / "mail_outbox"
    AGENT_GRAPH_SVG_PATH = PROJECT_ROOT / "AgentGraph.svg"

    # Agent plugin storage paths are global constants, not env vars.
    AGENT_DATA_DIR = UPLOAD_DIR / "agent_plugin"
    AGENT_VECTOR_DB_DIRNAME = "chroma"
    AGENT_VECTOR_DB_PATH = AGENT_DATA_DIR / AGENT_VECTOR_DB_DIRNAME

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
    SMTP_USE_SSL = _to_bool(os.getenv("SMTP_USE_SSL"))
    SMTP_USE_TLS = _to_bool(os.getenv("SMTP_USE_TLS"))
    EMAIL_VERIFICATION_CODE_LENGTH = int(os.getenv("EMAIL_VERIFICATION_CODE_LENGTH"))
    EMAIL_VERIFICATION_EXPIRE_MINUTES = int(os.getenv("EMAIL_VERIFICATION_EXPIRE_MINUTES"))

    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
    ADMIN_PHONE = os.getenv("ADMIN_PHONE")
    REALTIME_STREAM_INTERVAL_SECONDS = float(os.getenv("REALTIME_STREAM_INTERVAL_SECONDS"))

    PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL")
    FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL")

    LLM_API_KEY = os.getenv("LLM_API_KEY")
    LLM_BASE_URL = os.getenv("LLM_BASE_URL")
    LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT"))
    LLM_MODEL = os.getenv("LLM_MODEL")
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE"))

    # Agent plugin behavior params from env
    AGENT_PLUGIN_ENABLED = _to_bool(os.getenv("AGENT_PLUGIN_ENABLED"))
    SQLALCHEMY_ECHO = _to_bool(os.getenv("SQLALCHEMY_ECHO"))
    _embedding_model_raw = os.getenv(
        "AGENT_PLUGIN_EMBEDDING_MODEL",
        "paraphrase-multilingual-MiniLM-L12-v2",
    )
    AGENT_PLUGIN_EMBEDDING_MODEL_NAME = Path(_embedding_model_raw).name
    AGENT_PLUGIN_EMBEDDING_MODEL = str(
        EMBEDDING_MODELS_DIR / AGENT_PLUGIN_EMBEDDING_MODEL_NAME
    )
    AGENT_PLUGIN_COLLECTION_NAME = os.getenv("AGENT_PLUGIN_COLLECTION_NAME")
    AGENT_PLUGIN_RAG_RAW_FILE_PATH = str(KNOWLEDGE_BASE_PATH)
    AGENT_PLUGIN_RAG_CHUNK_SIZE = int(os.getenv("AGENT_PLUGIN_RAG_CHUNK_SIZE"))
    AGENT_PLUGIN_RAG_METADATA_EXTRAS = os.getenv("AGENT_PLUGIN_RAG_METADATA_EXTRAS")
    AGENT_PLUGIN_RAG_FORCE_UPDATE = _to_bool(os.getenv("AGENT_PLUGIN_RAG_FORCE_UPDATE"))
    AGENT_PLUGIN_RAG_TOP_K = int(os.getenv("AGENT_PLUGIN_RAG_TOP_K"))
    AGENT_PLUGIN_RAG_SCORE_THRESHOLD = float(os.getenv("AGENT_PLUGIN_RAG_SCORE_THRESHOLD"))
    AGENT_PLUGIN_SYSTEM_PROMPT = os.getenv("AGENT_PLUGIN_SYSTEM_PROMPT")

    # PaddleOCR model bootstrap params from env
    PADDLEOCR_ENABLED = _to_bool(os.getenv("PADDLEOCR_ENABLED"))
    _paddleocr_models_dir_raw = os.getenv("PADDLEOCR_MODELS_DIR", "paddleocr")
    _paddleocr_models_dir_path = Path(_paddleocr_models_dir_raw)
    PADDLEOCR_MODELS_DIR = (
        _paddleocr_models_dir_path
        if _paddleocr_models_dir_path.is_absolute()
        else KNOWLEDGE_DIR / _paddleocr_models_dir_path
    )
    PADDLEOCR_LANG = os.getenv("PADDLEOCR_LANG", "ch")
    PADDLEOCR_USE_ANGLE_CLS = _to_bool(os.getenv("PADDLEOCR_USE_ANGLE_CLS"))
    PADDLEOCR_ENABLE_STRUCTURE = _to_bool(os.getenv("PADDLEOCR_ENABLE_STRUCTURE"))
    PADDLEOCR_DET_MODEL_DIR = str(PADDLEOCR_MODELS_DIR / "det")
    PADDLEOCR_REC_MODEL_DIR = str(PADDLEOCR_MODELS_DIR / "rec")
    PADDLEOCR_CLS_MODEL_DIR = str(PADDLEOCR_MODELS_DIR / "cls")
    PADDLEOCR_LAYOUT_MODEL_DIR = str(PADDLEOCR_MODELS_DIR / "layout")
    PADDLEOCR_TABLE_MODEL_DIR = str(PADDLEOCR_MODELS_DIR / "table")

    @staticmethod
    def _show_config():
        source = "Docker-Compose" if os.getenv("DOCKER_DEPLOYMENT") else ".env"
        print(f"\n{'=' * 20} [DEBUG] GlobalConfig Members ({source}) {'=' * 20}")

        attrs = [
            attr
            for attr in dir(GlobalConfig)
            if not attr.startswith("__") and not callable(getattr(GlobalConfig, attr))
        ]
        for attr in sorted(attrs):
            val = getattr(GlobalConfig, attr)
            print(f"{attr:35} | {val}")
        print(f"{'=' * 75}\n")


GlobalConfig._show_config()
