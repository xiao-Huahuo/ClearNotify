from __future__ import annotations

import inspect
import io
import logging
import os
import threading
from pathlib import Path
from typing import Any

from app.core.config import GlobalConfig
from app.scripts.download_paddleocr_models import ensure_paddleocr_models_ready


logger = logging.getLogger(__name__)

_PADDLE_OCR_INSTANCE: Any | None = None
_PADDLE_OCR_ERROR: Exception | None = None
_PADDLE_OCR_INIT_LOCK = threading.Lock()
_PADDLE_OCR_RUN_LOCK = threading.Lock()


def _filter_supported_kwargs(factory, kwargs: dict[str, object]) -> dict[str, object]:
    try:
        parameters = inspect.signature(factory).parameters
    except (TypeError, ValueError):
        return kwargs
    supported = set(parameters.keys())
    accepts_var_kwargs = any(param.kind == inspect.Parameter.VAR_KEYWORD for param in parameters.values())
    passthrough_kwargs = {"enable_mkldnn", "enable_hpi", "device", "cpu_threads"}
    return {
        key: value
        for key, value in kwargs.items()
        if value is not None and (key in supported or (accepts_var_kwargs and key in passthrough_kwargs))
    }


def _build_paddleocr_instance() -> Any:
    try:
        from paddleocr import PaddleOCR  # type: ignore
    except Exception as exc:
        raise RuntimeError("PaddleOCR import failed") from exc

    paths = ensure_paddleocr_models_ready(
        skip_if_disabled=False,
        allow_download=not os.getenv("DOCKER_DEPLOYMENT"),
    )

    def _build_kwargs(use_angle_cls: bool) -> dict[str, object]:
        return _filter_supported_kwargs(
            PaddleOCR,
            {
                "lang": GlobalConfig.PADDLEOCR_LANG,
                "use_angle_cls": use_angle_cls,
                "use_textline_orientation": use_angle_cls,
                "use_doc_orientation_classify": False,
                "use_doc_unwarping": False,
                "enable_mkldnn": False,
                "det_model_dir": str(paths["det"]),
                "rec_model_dir": str(paths["rec"]),
                "cls_model_dir": str(paths["cls"]),
                "show_log": False,
            },
        )

    try:
        return PaddleOCR(**_build_kwargs(GlobalConfig.PADDLEOCR_USE_ANGLE_CLS))
    except Exception as exc:
        if not GlobalConfig.PADDLEOCR_USE_ANGLE_CLS:
            raise
        logger.warning(
            "PaddleOCR runtime init with angle classification failed, retry without it: %s",
            exc,
        )
        return PaddleOCR(**_build_kwargs(False))


def get_paddleocr_instance() -> Any | None:
    global _PADDLE_OCR_INSTANCE, _PADDLE_OCR_ERROR

    if not GlobalConfig.PADDLEOCR_ENABLED:
        return None
    if _PADDLE_OCR_INSTANCE is not None:
        return _PADDLE_OCR_INSTANCE
    if _PADDLE_OCR_ERROR is not None:
        return None

    with _PADDLE_OCR_INIT_LOCK:
        if _PADDLE_OCR_INSTANCE is not None:
            return _PADDLE_OCR_INSTANCE
        if _PADDLE_OCR_ERROR is not None:
            return None
        try:
            _PADDLE_OCR_INSTANCE = _build_paddleocr_instance()
            logger.info("PaddleOCR runtime initialized successfully.")
        except Exception as exc:
            _PADDLE_OCR_ERROR = exc
            logger.warning("PaddleOCR runtime initialization failed: %s", exc, exc_info=True)
            return None
    return _PADDLE_OCR_INSTANCE


def _load_image_array(*, image_bytes: bytes | None = None, image_path: Path | None = None):
    try:
        import numpy as np
        from PIL import Image
    except Exception as exc:
        logger.warning("Local OCR image dependencies are unavailable: %s", exc, exc_info=True)
        return None

    if image_bytes is None and image_path is None:
        return None

    source = io.BytesIO(image_bytes) if image_bytes is not None else image_path
    try:
        with Image.open(source) as image:
            if image.mode not in {"RGB", "L"}:
                image = image.convert("RGB")
            return np.array(image)
    except Exception as exc:
        logger.warning("Failed to load image for local OCR: %s", exc, exc_info=True)
        return None


def _extract_standard_lines(result: Any) -> list[str]:
    lines: list[str] = []
    if not isinstance(result, list):
        return lines

    for page_result in result:
        if isinstance(page_result, dict):
            rec_text = str(page_result.get("rec_text") or "").strip()
            if rec_text:
                lines.append(rec_text)
            rec_texts = page_result.get("rec_texts")
            if isinstance(rec_texts, (list, tuple)):
                for item in rec_texts:
                    text = str(item or "").strip()
                    if text:
                        lines.append(text)
            continue
        if not isinstance(page_result, list):
            continue
        for entry in page_result:
            if not isinstance(entry, (list, tuple)) or len(entry) < 2:
                continue
            text_info = entry[1]
            if not isinstance(text_info, (list, tuple)) or not text_info:
                continue
            text = str(text_info[0] or "").strip()
            if text:
                lines.append(text)
    return lines


def _collect_text_candidates(node: Any, output: list[str]) -> None:
    if isinstance(node, dict):
        text = str(node.get("text") or "").strip()
        if text:
            output.append(text)
        rec_text = str(node.get("rec_text") or "").strip()
        if rec_text:
            output.append(rec_text)
        rec_texts = node.get("rec_texts")
        if isinstance(rec_texts, (list, tuple)):
            for item in rec_texts:
                text_item = str(item or "").strip()
                if text_item:
                    output.append(text_item)
        for value in node.values():
            _collect_text_candidates(value, output)
        return

    if isinstance(node, (list, tuple)):
        if len(node) == 2 and isinstance(node[0], str) and isinstance(node[1], (int, float)):
            text = node[0].strip()
            if text:
                output.append(text)
            return
        for item in node:
            _collect_text_candidates(item, output)


def _ocr_result_to_text(result: Any) -> str:
    candidates = _extract_standard_lines(result)
    if not candidates:
        _collect_text_candidates(result, candidates)

    lines: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        normalized = (
            candidate.replace("\\r\\n", "\n")
            .replace("\\n", "\n")
            .replace("\\r", "\n")
            .replace("\r\n", "\n")
            .replace("\r", "\n")
            .strip()
        )
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        lines.append(normalized)
    return "\n".join(lines).strip()


def _has_parameter(factory, name: str) -> bool:
    try:
        return name in inspect.signature(factory).parameters
    except (TypeError, ValueError):
        return False


def _run_paddleocr(ocr: Any, image_array: Any) -> Any:
    legacy_runner = getattr(ocr, "ocr", None)
    if callable(legacy_runner) and _has_parameter(legacy_runner, "cls"):
        return legacy_runner(image_array, cls=GlobalConfig.PADDLEOCR_USE_ANGLE_CLS)

    predict_runner = getattr(ocr, "predict", None)
    if callable(predict_runner):
        kwargs: dict[str, object] = {}
        if _has_parameter(predict_runner, "use_textline_orientation"):
            kwargs["use_textline_orientation"] = GlobalConfig.PADDLEOCR_USE_ANGLE_CLS
        return predict_runner(image_array, **kwargs)

    if callable(legacy_runner):
        return legacy_runner(image_array)

    raise AttributeError("PaddleOCR instance exposes neither predict() nor ocr().")


def extract_text_from_image_bytes(image_bytes: bytes) -> str:
    if not image_bytes:
        return ""

    ocr = get_paddleocr_instance()
    if ocr is None:
        return ""

    image_array = _load_image_array(image_bytes=image_bytes)
    if image_array is None:
        return ""

    try:
        with _PADDLE_OCR_RUN_LOCK:
            result = _run_paddleocr(ocr, image_array)
    except Exception as exc:
        logger.warning("PaddleOCR image recognition failed: %s", exc, exc_info=True)
        return ""
    return _ocr_result_to_text(result)


def extract_text_from_image_path(image_path: Path) -> str:
    image_array = _load_image_array(image_path=image_path)
    if image_array is None:
        return ""

    ocr = get_paddleocr_instance()
    if ocr is None:
        return ""

    try:
        with _PADDLE_OCR_RUN_LOCK:
            result = _run_paddleocr(ocr, image_array)
    except Exception as exc:
        logger.warning("PaddleOCR file recognition failed for %s: %s", image_path, exc, exc_info=True)
        return ""
    return _ocr_result_to_text(result)
