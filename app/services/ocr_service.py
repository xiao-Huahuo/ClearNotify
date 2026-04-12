from __future__ import annotations

import asyncio
import json
import logging
import mimetypes
import tempfile
from pathlib import Path

from app.ai.request_llm import RequestLLM


logger = logging.getLogger(__name__)


def _normalize_ocr_text(text: str) -> str:
    return (
        str(text or "")
        .replace("\\r\\n", "\n")
        .replace("\\n", "\n")
        .replace("\\r", "\n")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .strip()
    )


def _extract_text_from_payload(payload: object) -> str:
    if isinstance(payload, str):
        return _normalize_ocr_text(payload)

    if isinstance(payload, list):
        parts: list[str] = []
        for item in payload:
            text = _extract_text_from_payload(item)
            if text:
                parts.append(text)
        return "\n".join(parts).strip()

    if isinstance(payload, dict):
        for key in ("content", "text", "body", "markdown"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return _normalize_ocr_text(value)

        parts: list[str] = []
        for key, value in payload.items():
            if key in {"filename", "file_type", "title", "type"}:
                continue
            text = _extract_text_from_payload(value)
            if text:
                parts.append(text)
        return "\n".join(parts).strip()

    return ""


def _unwrap_file_extract_text(text: str) -> str:
    normalized = _normalize_ocr_text(text)
    if not normalized:
        return ""

    try:
        payload = json.loads(normalized)
    except Exception:
        return normalized

    extracted = _extract_text_from_payload(payload)
    return extracted or normalized


def _guess_suffix(content_type: str, original_filename: str) -> str:
    suffix = Path(str(original_filename or "")).suffix
    if suffix:
        return suffix
    guessed = mimetypes.guess_extension(content_type or "")
    if guessed == ".jpe":
        return ".jpg"
    return guessed or ".bin"


def perform_kimi_ocr_sync(file_path: Path, content_type: str, original_filename: str) -> str:
    extracted_text = ""
    file_id = None
    kimi = RequestLLM()

    try:
        logger.info(
            "Attempting Kimi file-extract OCR for %s (%s).",
            original_filename,
            file_path,
        )
        with open(file_path, "rb") as f:
            upload_resp = kimi.client.files.create(
                file=(original_filename, f, content_type),
                purpose="file-extract",
            )
        file_id = upload_resp.id
        logger.info("Kimi OCR upload succeeded. File ID: %s", file_id)

        logger.info("Reading extracted content for Kimi File ID: %s", file_id)
        file_content_resp = kimi.client.files.content(file_id)
        extracted_text = _unwrap_file_extract_text(getattr(file_content_resp, "text", ""))
        logger.info("Kimi OCR extracted text length: %s", len(extracted_text))

        if not extracted_text:
            logger.warning(
                "Kimi file-extract returned empty text for %s. Skip unsupported chat-vision fallback.",
                original_filename,
            )
    except Exception as exc:
        logger.warning(
            "Kimi OCR failed for %s (%s): %s",
            original_filename,
            file_path,
            exc,
            exc_info=True,
        )
        return ""
    finally:
        if file_id:
            try:
                kimi.client.files.delete(file_id)
                logger.info("Kimi File ID %s deleted successfully.", file_id)
            except Exception as exc:
                logger.warning("Failed to delete Kimi File ID %s: %s", file_id, exc)

    return extracted_text


def perform_kimi_ocr_from_bytes_sync(
    file_bytes: bytes,
    *,
    content_type: str,
    original_filename: str,
) -> str:
    if not file_bytes:
        return ""

    suffix = _guess_suffix(content_type, original_filename)
    upload_name = original_filename if Path(str(original_filename or "")).suffix else f"{original_filename}{suffix}"
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(file_bytes)
            temp_path = Path(temp_file.name)
        return perform_kimi_ocr_sync(temp_path, content_type, upload_name)
    except Exception as exc:
        logger.warning(
            "Kimi OCR temp-file fallback failed for %s: %s",
            original_filename,
            exc,
            exc_info=True,
        )
        return ""
    finally:
        if temp_path and temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                logger.warning("Failed to delete temporary OCR file: %s", temp_path)


async def perform_kimi_ocr(file_path: Path, content_type: str, original_filename: str) -> str:
    return await asyncio.to_thread(
        perform_kimi_ocr_sync,
        file_path,
        content_type,
        original_filename,
    )
