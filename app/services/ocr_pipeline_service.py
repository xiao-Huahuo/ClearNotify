from __future__ import annotations

import logging
from pathlib import Path

from app.services.local_ocr_service import (
    extract_text_from_image_bytes,
    extract_text_from_image_path,
)
from app.services.ocr_service import perform_kimi_ocr, perform_kimi_ocr_from_bytes_sync
from app.services.pdf_extractor import extract_pdf_with_ai


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


def _perform_kimi_vision_ocr_from_bytes(
    image_bytes: bytes,
    *,
    content_type: str,
) -> str:
    if not image_bytes:
        return ""

    return _normalize_ocr_text(
        perform_kimi_ocr_from_bytes_sync(
            image_bytes,
            content_type=content_type,
            original_filename="inline_ocr_image",
        )
    )


def extract_text_from_image_bytes_with_fallback(
    image_bytes: bytes,
    *,
    content_type: str = "image/png",
) -> str:
    local_text = _normalize_ocr_text(extract_text_from_image_bytes(image_bytes))
    if local_text:
        return local_text

    logger.info("Local OCR returned empty result for image bytes, fallback to Kimi file-extract OCR.")
    return _perform_kimi_vision_ocr_from_bytes(image_bytes, content_type=content_type)


async def extract_text_from_file_with_fallback(
    file_path: Path,
    *,
    content_type: str,
    original_filename: str,
) -> str:
    suffix = file_path.suffix.lower()

    if content_type == "application/pdf" or suffix == ".pdf":
        return _normalize_ocr_text(await extract_pdf_with_ai(file_path))

    local_text = _normalize_ocr_text(extract_text_from_image_path(file_path))
    if local_text:
        logger.info("Local OCR succeeded for %s.", file_path)
        return local_text

    logger.info("Local OCR unavailable or empty for %s, fallback to Kimi OCR.", file_path)
    return _normalize_ocr_text(
        await perform_kimi_ocr(
            file_path=file_path,
            content_type=content_type,
            original_filename=original_filename,
        )
    )
