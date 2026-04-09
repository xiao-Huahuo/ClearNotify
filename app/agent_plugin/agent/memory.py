import hashlib
import json
import logging
import os
import threading
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional

import chromadb
from chromadb.utils import embedding_functions

from app.agent_plugin.agent.config import AgentConfig


logger = logging.getLogger(__name__)
GLOBAL_KNOWLEDGE_USER_ID = "__global_knowledge__"


def _dir_size_mb(path: Path) -> float:
    if not path.exists():
        return 0.0
    total = 0
    for fp in path.rglob("*"):
        if fp.is_file():
            try:
                total += fp.stat().st_size
            except OSError:
                continue
    return round(total / (1024 * 1024), 2)


class _ProgressHeartbeat:
    def __init__(self, model_path: Path, interval_seconds: int = 3):
        self.model_path = model_path
        self.interval_seconds = interval_seconds
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self.started_at = time.time()

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=0.5)

    def _run(self) -> None:
        while not self._stop.wait(self.interval_seconds):
            elapsed = int(time.time() - self.started_at)
            size_mb = _dir_size_mb(self.model_path)
            logger.info(
                "Embedding 模型加载中: path=%s, elapsed=%ss, local_size=%.2fMB",
                self.model_path,
                elapsed,
                size_mb,
            )


class LongTermMemory:
    local_ef: embedding_functions.SentenceTransformerEmbeddingFunction
    chroma_client: chromadb.ClientAPI
    collection: chromadb.Collection

    def __init__(self):
        model_path = Path(str(AgentConfig.EMBEDDING_MODEL))
        logger.info("初始化 Embedding 模型: %s", model_path)
        if not model_path.exists():
            logger.info("Embedding 本地模型目录不存在，准备触发下载: %s", model_path)
        else:
            logger.info(
                "Embedding 本地模型目录已存在: %s (size=%.2fMB)",
                model_path,
                _dir_size_mb(model_path),
            )

        heartbeat = _ProgressHeartbeat(model_path=model_path)
        heartbeat.start()
        try:
            self.local_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=AgentConfig.EMBEDDING_MODEL
            )
        finally:
            heartbeat.stop()

        logger.info(
            "Embedding 模型加载完成: %s (size=%.2fMB, elapsed=%ss)",
            model_path,
            _dir_size_mb(model_path),
            int(time.time() - heartbeat.started_at),
        )

        self.chroma_client = chromadb.PersistentClient(path=AgentConfig.VECTOR_DB_PATH)
        self.collection = self.chroma_client.get_or_create_collection(
            name=AgentConfig.COLLECTION_NAME,
            embedding_function=self.local_ef,
        )

    def _calculate_md5(self, data: List[Dict[str, str]]) -> str:
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.md5(data_str.encode("utf-8")).hexdigest()

    def rag_ingest(self, user_id: str, raw_data: Optional[List[Dict[str, str]]] = None):
        final_ingest_data = []

        if os.path.exists(AgentConfig.RAG_RAW_FILE_PATH):
            try:
                with open(AgentConfig.RAG_RAW_FILE_PATH, "r", encoding="utf-8") as f:
                    file_data = json.load(f)
                    if isinstance(file_data, list):
                        final_ingest_data.extend(file_data)
                        logger.info(
                            "[长期记忆] 已从 %s 加载 %s 条初始知识",
                            AgentConfig.RAG_RAW_FILE_PATH,
                            len(file_data),
                        )
            except Exception as e:
                logger.exception("[长期记忆] 读取本地知识文件失败: %s", e)

        if raw_data:
            final_ingest_data.extend(raw_data)

        if not final_ingest_data:
            logger.info("[长期记忆] 无需同步的数据")
            return

        current_hash = self._calculate_md5(final_ingest_data)

        lock_id = f"data_lock_{user_id}"
        existing_lock = self.collection.get(ids=[lock_id])

        last_hash = None
        if existing_lock and existing_lock.get("metadatas") and len(existing_lock["metadatas"]) > 0:
            last_hash = existing_lock["metadatas"][0].get("hash_lock")

        if current_hash != last_hash or AgentConfig.RAG_FORCE_UPDATE:
            logger.info("[长期记忆] 检测到变更，开始同步 (user=%s)", user_id)

            if self.collection.count() > 0:
                self.collection.delete(where={"user_id": user_id})

            documents = []
            metadatas = []
            ids = []

            for item in final_ingest_data:
                content = str(item.get("content", "")).strip()
                if not content:
                    continue
                documents.append(content)

                meta = {"user_id": user_id}
                for key, value in item.items():
                    if key != "content":
                        meta[key] = value

                metadatas.append(meta)
                ids.append(str(uuid.uuid4()))

            if documents:
                self.collection.add(documents=documents, metadatas=metadatas, ids=ids)

            self.collection.upsert(
                ids=[lock_id],
                documents=["HASH_LOCK_MARKER"],
                metadatas=[{"hash_lock": current_hash, "user_id": user_id}],
            )
            logger.info("[长期记忆] 同步完成，共 %s 条", len(documents))
        else:
            logger.info("[长期记忆] 内容未变化，跳过同步")

    def rag_query_top_k(self, query: str, user_id: str, rag_top_k: Optional[int] = None) -> List[str]:
        top_k = rag_top_k if rag_top_k is not None else AgentConfig.RAG_TOP_K
        threshold = AgentConfig.RAG_SCORE_THRESHOLD
        owners = [str(user_id)]
        if str(user_id) != GLOBAL_KNOWLEDGE_USER_ID:
            owners.append(GLOBAL_KNOWLEDGE_USER_ID)

        merged: List[str] = []
        seen = set()

        for owner in owners:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                where={"user_id": owner},
                include=["documents", "distances"],
            )
            documents = (results.get("documents") or [[]])[0]
            distances = (results.get("distances") or [[]])[0]
            for index, doc in enumerate(documents):
                if not isinstance(doc, str):
                    continue
                normalized = doc.strip()
                if not normalized or normalized in seen:
                    continue

                if distances:
                    distance = distances[index] if index < len(distances) else None
                    score = 1 - float(distance) if distance is not None else 0.0
                    if score < threshold:
                        continue

                seen.add(normalized)
                merged.append(normalized)
                if len(merged) >= top_k:
                    return merged
        return merged

    # 兼容旧命名
    def rag_query_tok_k(self, query: str, user_id: str, rag_top_k: Optional[int] = None) -> List[str]:
        return self.rag_query_top_k(query=query, user_id=user_id, rag_top_k=rag_top_k)

    def summarize_and_store_knowledge(self, user_id: str, content: str):
        if not content or content.upper() == "NONE":
            return

        logger.info("[系统自动提炼新记忆] %s", content)

        self.collection.add(
            documents=[content],
            metadatas=[{"category": "AUTO_EXTRACTED", "user_id": user_id}],
            ids=[str(uuid.uuid4())],
        )

        lock_id = f"data_lock_{user_id}"
        self.collection.upsert(
            ids=[lock_id],
            documents=["HASH_LOCK_MARKER"],
            metadatas=[{"hash_lock": "FORCE_UPDATE_STALE", "user_id": user_id}],
        )

    def close(self):
        # ChromaDB Python 客户端当前无需显式 close，保留占位供后续扩展。
        return


_global_memory_instance = None


def get_long_term_memory():
    global _global_memory_instance
    if _global_memory_instance is None:
        _global_memory_instance = LongTermMemory()
    return _global_memory_instance
