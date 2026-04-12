from __future__ import annotations

import asyncio
import logging
import re
from pathlib import Path
from typing import Any

from app.services.local_ocr_service import extract_text_from_image_bytes
from app.services.ocr_service import perform_kimi_ocr, perform_kimi_ocr_from_bytes_sync


logger = logging.getLogger(__name__)


def _clean_pdf_block_text(text: str) -> str:
    if not text:
        return ""
    normalized = (
        text.replace("\\r\\n", "\n")
        .replace("\\n", "\n")
        .replace("\\r", "\n")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in normalized.split("\n")]
    return "\n".join(line for line in lines if line)


def _extract_pdf_text_block(block: dict[str, Any]) -> str:
    lines: list[str] = []
    for line in block.get("lines", []):
        spans = []
        for span in line.get("spans", []):
            text = str(span.get("text") or "")
            if text:
                spans.append(text)
        merged = _clean_pdf_block_text("".join(spans))
        if merged:
            lines.append(merged)
    return "\n".join(lines).strip()


def _extract_pdf_image_block_text(image_bytes: bytes) -> str:
    local_text = _clean_pdf_block_text(extract_text_from_image_bytes(image_bytes))
    if local_text:
        return local_text

    return _clean_pdf_block_text(
        perform_kimi_ocr_from_bytes_sync(
            image_bytes,
            content_type="image/png",
            original_filename="pdf_inline_image.png",
        )
    )


def _extract_pdf_mixed_text(file_path: Path) -> str:
    try:
        import fitz  # type: ignore
    except Exception as exc:
        logger.warning("PyMuPDF is unavailable, skip mixed PDF extraction: %s", exc)
        return ""

    page_texts: list[str] = []
    with fitz.open(file_path) as pdf:
        for page_index, page in enumerate(pdf, start=1):
            try:
                page_dict = page.get_text("dict")
            except Exception as exc:
                logger.warning(
                    "Failed to read PDF page %s for %s: %s",
                    page_index,
                    file_path,
                    exc,
                    exc_info=True,
                )
                continue

            page_items: list[dict[str, Any]] = []
            page_area = max(float(page.rect.width * page.rect.height), 1.0)

            for block in page_dict.get("blocks", []):
                bbox = tuple(block.get("bbox") or (0, 0, 0, 0))
                block_type = int(block.get("type", -1))

                if block_type == 0:
                    text = _extract_pdf_text_block(block)
                    if text:
                        page_items.append({"kind": "text", "bbox": bbox, "text": text})
                    continue

                if block_type != 1:
                    continue

                width = max(float(bbox[2] - bbox[0]), 0.0)
                height = max(float(bbox[3] - bbox[1]), 0.0)
                if width < 24 or height < 24:
                    continue

                has_text_on_page = any(item["kind"] == "text" for item in page_items)
                image_area = width * height
                if has_text_on_page and image_area / page_area >= 0.6:
                    continue

                image_bytes = block.get("image")
                if not isinstance(image_bytes, (bytes, bytearray)) or not image_bytes:
                    xref = block.get("xref")
                    if xref:
                        try:
                            image_bytes = fitz.Pixmap(pdf, int(xref)).tobytes("png")
                        except Exception:
                            image_bytes = b""
                if not image_bytes:
                    continue

                ocr_text = _extract_pdf_image_block_text(bytes(image_bytes))
                if ocr_text:
                    page_items.append({"kind": "image", "bbox": bbox, "text": ocr_text})

            page_items.sort(key=lambda item: (round(float(item["bbox"][1]) / 10.0), float(item["bbox"][0])))
            page_text = "\n".join(item["text"] for item in page_items if str(item.get("text") or "").strip()).strip()
            if page_text:
                page_texts.append(page_text)

    return "\n\n".join(page_texts).strip()


async def extract_pdf_with_ai(file_path: Path) -> str:
    full_text: list[str] = []
    has_text = False

    try:
        mixed_text = await asyncio.to_thread(_extract_pdf_mixed_text, file_path)
        if mixed_text:
            logger.info("Successfully extracted mixed text and OCR blocks from PDF %s.", file_path)
            return mixed_text

        try:
            import pdfplumber
        except ImportError:
            pdfplumber = None

        if pdfplumber is not None:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text and text.strip():
                        full_text.append(text)
                        has_text = True

        if has_text:
            logger.info("Successfully extracted text from PDF %s using pdfplumber fallback.", file_path)
            return "\n".join(full_text)

        logger.info("No readable text blocks found in %s. Attempting OCR via Kimi.", file_path)

        extracted_text_from_ocr = await perform_kimi_ocr(
            file_path=file_path,
            content_type="application/pdf",
            original_filename=file_path.name,
        )

        if extracted_text_from_ocr and extracted_text_from_ocr.strip():
            logger.info("Successfully extracted text from %s using Kimi OCR.", file_path)
            return extracted_text_from_ocr

        logger.warning("Kimi OCR also failed to extract text from %s.", file_path)
        return "No readable text could be extracted from this file."

    except Exception as exc:
        logger.error("PDF parsing or OCR failed for %s: %s", file_path, exc, exc_info=True)
        return f"PDF parse failed: {exc}"
