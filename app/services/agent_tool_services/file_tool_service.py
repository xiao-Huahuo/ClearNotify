from __future__ import annotations

from pathlib import Path

from sqlmodel import Session

from app.ai.document_parser import parse_document
from app.core.config import GlobalConfig
from app.models.chat_message import ChatMessage
from app.services import chat_message_service
from app.services.document_text_service import extract_supported_document_text
from app.services.ocr_pipeline_service import extract_text_from_file_with_fallback
from app.services.agent_tool_services.base import (
    compact_text,
    file_item_payload,
    knowledge_graph_display,
    media_url_for_path,
    ok_item_payload,
    ok_list_payload,
    original_text_display,
    resolve_user_file_reference,
    run_async,
    table_display,
)


TEXT_SUFFIXES = {".txt", ".md", ".json", ".log", ".py", ".yaml", ".yml"}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff", ".tif"}


def _file_kind(path: Path) -> str:
    name = path.name.lower()
    if name.startswith("ocr_"):
        return "ocr"
    if name.startswith("doc_"):
        return "document"
    if path.suffix.lower() == ".json" and "chat_exports" in str(path).lower():
        return "chat_export"
    if name.startswith("user_"):
        return "avatar"
    return "file"


def list_user_uploaded_files_payload(user_id: int, *, limit: int = 20) -> dict[str, object]:
    docs = sorted(
        list(GlobalConfig.DOCS_UPLOAD_DIR.glob(f"doc_{user_id}_*")) + list(GlobalConfig.DOCS_UPLOAD_DIR.glob(f"ocr_{user_id}_*")),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    chat_dir = GlobalConfig.CHAT_EXPORT_DIR / f"user_{user_id}"
    exports = sorted(
        list(chat_dir.glob("chat_*.json")) if chat_dir.exists() else [],
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    avatar_files = sorted(
        list(GlobalConfig.AVATAR_UPLOAD_DIR.glob(f"user_{user_id}_*")),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    all_files = [*docs, *exports, *avatar_files]
    all_files.sort(key=lambda item: item.stat().st_mtime, reverse=True)
    selected = all_files[: max(1, min(limit, 50))]
    items = [file_item_payload(path, kind=_file_kind(path), file_url=media_url_for_path(path)) for path in selected]

    display = []
    if items:
        display.append(
            table_display(
                title="最近文件",
                columns=[
                    {"key": "name", "label": "文件名"},
                    {"key": "kind", "label": "类型"},
                    {"key": "suffix", "label": "后缀"},
                    {"key": "size_bytes", "label": "大小"},
                ],
                rows=items[:12],
            )
        )
    return ok_list_payload(
        items,
        total=len(items),
        source_total=len(all_files),
        applied_filters={"limit": max(1, min(limit, 50))},
        suggested_tools=["parse_uploaded_document", "parse_uploaded_image_ocr"],
        display=display,
    )


def _read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _extract_document_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in TEXT_SUFFIXES:
        return _read_text_file(path)
    if suffix in {".pdf", ".doc", ".docx", ".xls", ".xlsx"}:
        return str(run_async(extract_supported_document_text(path, original_filename=path.name)))
    raise ValueError(f"UNSUPPORTED_DOCUMENT_SUFFIX:{suffix}")


def parse_uploaded_document_payload(user_id: int, *, file_ref: str) -> dict[str, object]:
    path = resolve_user_file_reference(user_id, file_ref)
    suffix = path.suffix.lower()
    if suffix in IMAGE_SUFFIXES:
        raise ValueError("IMAGE_FILE_REQUIRES_OCR")
    text = _extract_document_text(path)
    file_url = media_url_for_path(path)
    item = {
        "file": file_item_payload(path, kind=_file_kind(path), file_url=file_url),
        "text_length": len(text or ""),
        "content_preview": compact_text(text, limit=3000),
        "content": text[:12000],
    }
    display = [original_text_display(title=f"文档预览 · {path.name}", content=item["content"], file_url=file_url)]
    return ok_item_payload(item, meta={"file_ref": file_ref, "suffix": suffix}, display=display)


def parse_uploaded_image_ocr_payload(user_id: int, *, file_ref: str) -> dict[str, object]:
    path = resolve_user_file_reference(user_id, file_ref)
    suffix = path.suffix.lower()
    if suffix not in IMAGE_SUFFIXES:
        raise ValueError("UNSUPPORTED_IMAGE_SUFFIX")
    mime = {
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
        ".bmp": "image/bmp",
        ".tiff": "image/tiff",
        ".tif": "image/tiff",
    }.get(suffix, "image/jpeg")
    text = str(
        run_async(
            extract_text_from_file_with_fallback(
                path,
                content_type=mime,
                original_filename=path.name,
            )
        )
    )
    return ok_item_payload(
        {
            "file": file_item_payload(path, kind=_file_kind(path), file_url=media_url_for_path(path)),
            "text_length": len(text or ""),
            "content_preview": compact_text(text, limit=3000),
            "content": text[:12000],
        },
        meta={"file_ref": file_ref, "suffix": suffix},
        display=[original_text_display(title=f"OCR 结果 · {path.name}", content=text[:12000], file_url=media_url_for_path(path))],
    )


def build_document_knowledge_graph_payload(user_id: int, *, original_text: str, title: str = "") -> dict[str, object]:
    parsed, parse_mode = parse_document(original_text, user_id)
    graph_title = title or compact_text(parsed.get("content") or original_text, limit=36) or "知识图谱"
    item = {
        "title": graph_title,
        "parse_mode": parse_mode,
        "content": parsed.get("content") or "",
        "nodes": parsed.get("nodes") or [],
        "links": parsed.get("links") or [],
        "dynamic_payload": parsed.get("dynamic_payload") or {},
        "visual_config": parsed.get("visual_config") or {},
    }
    display = [
        knowledge_graph_display(
            title=graph_title,
            content=item["content"],
            nodes=item["nodes"],
            links=item["links"],
            dynamic_payload=item["dynamic_payload"],
            visual_config=item["visual_config"],
        )
    ]
    return ok_item_payload(item, meta={"parse_mode": parse_mode, "node_count": len(item["nodes"]), "link_count": len(item["links"])}, display=display)


def get_message_knowledge_graph_payload(session: Session, user_id: int, *, message_id: int) -> dict[str, object]:
    message = session.get(ChatMessage, message_id)
    if not message or message.user_id != user_id or message.is_deleted:
        raise PermissionError("MESSAGE_NOT_FOUND")
    serialized = chat_message_service.serialize_message(message)
    title = compact_text(serialized.get("handling_matter") or serialized.get("original_text") or f"消息 {message_id}", limit=36)
    item = {
        "message_id": message.id,
        "title": title,
        "content": serialized.get("content") or serialized.get("original_text") or "",
        "nodes": serialized.get("nodes") or [],
        "links": serialized.get("links") or [],
        "dynamic_payload": serialized.get("dynamic_payload") or {},
        "visual_config": serialized.get("visual_config") or {},
    }
    display = [
        knowledge_graph_display(
            title=title,
            content=item["content"],
            nodes=item["nodes"],
            links=item["links"],
            dynamic_payload=item["dynamic_payload"],
            visual_config=item["visual_config"],
        )
    ]
    return ok_item_payload(
        item,
        meta={"message_id": message.id, "node_count": len(item["nodes"]), "link_count": len(item["links"])},
        display=display,
    )


def show_knowledge_graph_modal_payload(
    session: Session,
    user_id: int,
    *,
    message_id: int | None = None,
    original_text: str = "",
    title: str = "",
) -> dict[str, object]:
    if message_id:
        return get_message_knowledge_graph_payload(session, user_id, message_id=message_id)
    if original_text.strip():
        return build_document_knowledge_graph_payload(user_id, original_text=original_text, title=title)
    raise ValueError("GRAPH_SOURCE_REQUIRED")
