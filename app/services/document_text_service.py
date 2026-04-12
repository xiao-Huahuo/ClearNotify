from __future__ import annotations

import logging
from pathlib import Path

from app.services.document_extractor import (
    count_docx_inline_images,
    extract_text_from_docx,
    extract_text_from_excel,
)
from app.services.ocr_service import perform_kimi_ocr
from app.services.pdf_extractor import extract_pdf_with_ai


logger = logging.getLogger(__name__)

DOCX_INLINE_IMAGE_LLM_FALLBACK_THRESHOLD = 4
DOCX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


async def extract_supported_document_text(
    file_path: Path,
    *,
    original_filename: str = "",
) -> str:
    suffix = file_path.suffix.lower()
    filename = original_filename or file_path.name

    if suffix == ".pdf":
        return await extract_pdf_with_ai(file_path)

    if suffix == ".docx":
        return await _extract_docx_text(file_path, original_filename=filename)

    if suffix == ".doc":
        return extract_text_from_docx(file_path)

    if suffix in {".xlsx", ".xls"}:
        return extract_text_from_excel(file_path)

    raise ValueError(f"UNSUPPORTED_DOCUMENT_SUFFIX:{suffix}")


async def _extract_docx_text(file_path: Path, *, original_filename: str) -> str:
    image_count = count_docx_inline_images(file_path)
    if image_count < DOCX_INLINE_IMAGE_LLM_FALLBACK_THRESHOLD:
        return extract_text_from_docx(file_path)

    logger.info(
        "DOCX %s contains %s inline images, using whole-file Kimi extract fallback.",
        file_path,
        image_count,
    )
    extracted_text = await perform_kimi_ocr(
        file_path=file_path,
        content_type=DOCX_CONTENT_TYPE,
        original_filename=original_filename,
    )
    if extracted_text and extracted_text.strip():
        return extracted_text

    logger.warning(
        "Whole-file Kimi extract returned empty text for image-heavy DOCX %s, fallback to local parser.",
        file_path,
    )
    return extract_text_from_docx(file_path)
