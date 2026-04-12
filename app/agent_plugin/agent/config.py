import os


class AgentConfig:
    BASE_DATA_DIR = "."
    VECTOR_DB_PATH = ""
    RELATIONAL_DB_PATH = ""

    EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
    COLLECTION_NAME = "agent_memory"

    RAG_RAW_FILE_PATH = ""
    RAG_CHUNK_SIZE = 500
    RAG_METADATA_EXTRAS = []
    RAG_FORCE_UPDATE = False
    RAG_TOP_K = 5
    RAG_SCORE_THRESHOLD = 0.7

    LLM_MODEL = ""
    LLM_API_KEY = ""
    LLM_URL_BASE = ""
    LLM_TEMPERATURE = 0.0
    LLM_TIMEOUT = 240
    SYSTEM_PROMPT = ""

    @classmethod
    def setup(cls, **kwargs):
        cls.BASE_DATA_DIR = kwargs.get("BASE_DATA_DIR", ".")
        if not os.path.exists(cls.BASE_DATA_DIR):
            os.makedirs(cls.BASE_DATA_DIR, exist_ok=True)

        def _resolve(raw_value: str, default_value: str) -> str:
            value = str(raw_value or default_value)
            if os.path.isabs(value):
                return value
            return os.path.join(cls.BASE_DATA_DIR, value)

        cls.VECTOR_DB_PATH = _resolve(
            kwargs.get("VECTOR_DB_PATH", "chroma_db_storage"),
            "chroma_db_storage",
        )
        cls.RELATIONAL_DB_PATH = _resolve(
            kwargs.get("RELATIONAL_DB_PATH", "database.db"),
            "database.db",
        )
        cls.RAG_RAW_FILE_PATH = _resolve(
            kwargs.get("RAG_RAW_FILE_PATH", "knowledge_file.json"),
            "knowledge_file.json",
        )

        cls.COLLECTION_NAME = kwargs.get("COLLECTION_NAME", "agent_memory")
        cls.EMBEDDING_MODEL = kwargs.get("EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
        cls.RAG_CHUNK_SIZE = int(kwargs.get("RAG_CHUNK_SIZE", 500))

        extras = kwargs.get("RAG_METADATA_EXTRAS", ["category", "source"])
        cls.RAG_METADATA_EXTRAS = extras if isinstance(extras, list) else str(extras).split(",")

        cls.RAG_FORCE_UPDATE = kwargs.get("RAG_FORCE_UPDATE", False)
        cls.RAG_TOP_K = int(kwargs.get("RAG_TOP_K", 5))
        cls.RAG_SCORE_THRESHOLD = float(kwargs.get("RAG_SCORE_THRESHOLD", 0.7))

        cls.LLM_MODEL = kwargs.get("LLM_MODEL", "")
        cls.LLM_API_KEY = kwargs.get("LLM_API_KEY", "")
        cls.LLM_URL_BASE = kwargs.get("LLM_URL_BASE", "")
        cls.LLM_TEMPERATURE = float(kwargs.get("LLM_TEMPERATURE", 0))
        cls.LLM_TIMEOUT = int(kwargs.get("LLM_TIMEOUT", 240))
        cls.SYSTEM_PROMPT = kwargs.get(
            "SYSTEM_PROMPT",
            "你是一个具备自主能力的 AI 助手。请在必要时调用工具，并给出准确、简洁、可执行的答案。",
        )
