from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

import numpy as np

from app.core.config import GlobalConfig

logger = logging.getLogger(__name__)

_EMBEDDING_MODEL = None
_EMBEDDING_CACHE: dict[str, np.ndarray] = {}


def normalize_text(value) -> str:
    return " ".join(str(value or "").split()).strip()


def get_embedding_model():
    global _EMBEDDING_MODEL
    if _EMBEDDING_MODEL is not None:
        return _EMBEDDING_MODEL

    try:
        from sentence_transformers import SentenceTransformer

        model_path = Path(str(GlobalConfig.AGENT_PLUGIN_EMBEDDING_MODEL))
        model_source = (
            str(model_path)
            if model_path.exists()
            else str(GlobalConfig.AGENT_PLUGIN_EMBEDDING_MODEL_NAME)
        )
        _EMBEDDING_MODEL = SentenceTransformer(
            model_source,
            cache_folder=str(GlobalConfig.EMBEDDING_MODELS_DIR),
        )
        logger.info("Unified search embedding model ready: %s", model_source)
    except Exception as exc:
        logger.warning("Unified search embedding unavailable, fallback to lexical only: %s", exc)
        _EMBEDDING_MODEL = False

    return _EMBEDDING_MODEL


def encode_text(text: str) -> Optional[np.ndarray]:
    normalized = normalize_text(text)
    if not normalized:
        return None

    cached = _EMBEDDING_CACHE.get(normalized)
    if cached is not None:
        return cached

    model = get_embedding_model()
    if not model:
        return None

    try:
        vector = np.asarray(
            model.encode(normalized, normalize_embeddings=True),
            dtype=np.float32,
        )
    except Exception as exc:
        logger.warning("Unified search embedding failed: %s", exc)
        return None

    _EMBEDDING_CACHE[normalized] = vector
    return vector


def serialize_embedding(vector: Optional[np.ndarray]) -> str:
    if vector is None:
        return "[]"
    return json.dumps(np.asarray(vector, dtype=np.float32).tolist(), ensure_ascii=False)


def deserialize_embedding(value: str | None) -> Optional[np.ndarray]:
    if not value:
        return None
    try:
        data = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return None
    if not isinstance(data, list) or not data:
        return None
    try:
        return np.asarray(data, dtype=np.float32)
    except Exception:
        return None
