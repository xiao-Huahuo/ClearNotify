import json
import logging
import os
import subprocess
import shutil # Import shutil
from datetime import datetime # 导入 datetime
from pathlib import Path
from typing import Any, List, Optional

from fastapi import UploadFile
from sqlmodel import Session, select

from app.ai.analysis_agent import analyze_complexity_and_type
from app.ai.document_parser import rewrite_document
from app.core.config import GlobalConfig
from app.models.chat_message import ChatMessage
from app.services import rag_service


logger = logging.getLogger(__name__)
DIFFICULTY_SCORE = {"低": 1, "中": 2, "高": 3}


def _parse_chat_analysis(chat_analysis: Any) -> dict[str, Any]:
    if isinstance(chat_analysis, dict):
        return chat_analysis
    if not chat_analysis:
        return {}
    try:
        return json.loads(chat_analysis)
    except (TypeError, json.JSONDecodeError):
        return {}


def estimate_message_time_saved(message: ChatMessage) -> int:
    word_count = len(message.original_text or "")
    read_time_original = max(word_count / 150, 3)
    saved = max(int(read_time_original - 1), 2)
    return min(saved, 30)


def serialize_message(message: ChatMessage) -> dict[str, Any]:
    data = message.model_dump()
    # 遍历字典，将所有 datetime 对象转换为 ISO 格式的字符串
    for key, value in data.items():
        if isinstance(value, datetime):
            data[key] = value.isoformat()
    data["chat_analysis"] = _parse_chat_analysis(message.chat_analysis)
    data["estimated_time_saved_minutes"] = estimate_message_time_saved(message)
    return data


def _ensure_export_dir(user_id: int) -> Path:
    export_dir = GlobalConfig.CHAT_EXPORT_DIR / f"user_{user_id}"
    export_dir.mkdir(parents=True, exist_ok=True)
    return export_dir


def persist_message_snapshot(session: Session, message: ChatMessage) -> Path:
    export_dir = _ensure_export_dir(message.user_id)
    export_path = export_dir / f"chat_{message.id}.json"
    payload = {
        "version": 1,
        "exported_at": message.created_time.isoformat(),
        "message": serialize_message(message),
    }
    try:
        export_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except (IOError, OSError) as e:
        logger.error(f"Failed to write export file {export_path}: {e}")
        # Re-raise the exception to be caught by the API endpoint
        raise e

    message.session_json_path = str(export_path)
    session.add(message)
    session.commit()
    session.refresh(message)
    return export_path


def create_message_from_payload(
    session: Session,
    message_payload: dict[str, Any],
    user_id: int,
    source_chat_id: Optional[int] = None,
) -> ChatMessage:
    if isinstance(message_payload.get("chat_analysis"), dict):
        message_payload["chat_analysis"] = json.dumps(
            message_payload["chat_analysis"],
            ensure_ascii=False,
        )

    db_message = ChatMessage.model_validate(
        {
            **message_payload,
            "user_id": user_id,
            "source_chat_id": source_chat_id,
        }
    )
    session.add(db_message)
    session.commit()
    session.refresh(db_message)
    persist_message_snapshot(session, db_message)
    return db_message


def get_message_by_id(
    session: Session, user_id: int, message_id: int
) -> Optional[ChatMessage]:
    message = session.get(ChatMessage, message_id)
    if not message or message.user_id != user_id or message.is_deleted:
        return None
    return message


def get_messages(
    session: Session,
    user_id: int,
    id: Optional[int] = None,
    original_text: Optional[str] = None,
    target_audience: Optional[str] = None,
    handling_matter: Optional[str] = None,
    time_deadline: Optional[str] = None,
    location_entrance: Optional[str] = None,
    required_materials: Optional[str] = None,
    handling_process: Optional[str] = None,
    precautions: Optional[str] = None,
    risk_warnings: Optional[str] = None,
    original_text_mapping: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    sort_by: str = "created_time",
    sort_order: str = "desc",
    handling_only: bool = False,
) -> List[ChatMessage]:
    statement = select(ChatMessage).where(
        ChatMessage.user_id == user_id,
        ChatMessage.is_deleted == False,
    )

    if id is not None:
        statement = statement.where(ChatMessage.id == id)
    else:
        if original_text:
            statement = statement.where(ChatMessage.original_text.contains(original_text))
        if target_audience:
            statement = statement.where(ChatMessage.target_audience.contains(target_audience))
        if handling_matter:
            statement = statement.where(ChatMessage.handling_matter.contains(handling_matter))
        if time_deadline:
            statement = statement.where(ChatMessage.time_deadline.contains(time_deadline))
        if location_entrance:
            statement = statement.where(ChatMessage.location_entrance.contains(location_entrance))
        if required_materials:
            statement = statement.where(
                ChatMessage.required_materials.contains(required_materials)
            )
        if handling_process:
            statement = statement.where(ChatMessage.handling_process.contains(handling_process))
        if precautions:
            statement = statement.where(ChatMessage.precautions.contains(precautions))
        if risk_warnings:
            statement = statement.where(ChatMessage.risk_warnings.contains(risk_warnings))
        if original_text_mapping:
            statement = statement.where(
                ChatMessage.original_text_mapping.contains(original_text_mapping)
            )

    messages = list(session.exec(statement).all())
    if handling_only:
        messages = [
            message
            for message in messages
            if (message.handling_matter or "").strip()
        ]

    reverse = sort_order != "asc"

    def sort_key(message: ChatMessage):
        analysis = _parse_chat_analysis(message.chat_analysis)
        if sort_by == "difficulty":
            return max(
                DIFFICULTY_SCORE.get(analysis.get("language_complexity", "低"), 1),
                DIFFICULTY_SCORE.get(analysis.get("handling_complexity", "低"), 1),
                DIFFICULTY_SCORE.get(analysis.get("risk_level", "低"), 1),
            )
        if sort_by == "saved_time":
            return estimate_message_time_saved(message)
        if sort_by == "notice_type":
            return analysis.get("notice_type", "")
        return message.created_time

    messages.sort(key=sort_key, reverse=reverse)
    return messages[skip : skip + limit]


def delete_message_by_id(
    session: Session, user_id: int, message_id: int
) -> Optional[ChatMessage]:
    message = session.get(ChatMessage, message_id)
    if not message:
        return None

    message.is_deleted = True
    session.add(message)
    session.commit()
    session.refresh(message)
    return message


def delete_messages_by_ids(session: Session, user_id: int, message_ids: List[int]) -> int:
    statement = select(ChatMessage).where(
        ChatMessage.user_id == user_id,
        ChatMessage.id.in_(message_ids),
        ChatMessage.is_deleted == False,
    )
    messages_to_delete = session.exec(statement).all()
    if not messages_to_delete:
        return 0

    for message in messages_to_delete:
        message.is_deleted = True
        session.add(message)
    session.commit()
    return len(messages_to_delete)


def update_message_audience_via_ai(
    session: Session, user_id: int, message_id: int, new_audience: str
) -> Optional[ChatMessage]:
    message = get_message_by_id(session, user_id, message_id)
    if not message:
        return None

    rewritten_base = rewrite_document(message.original_text, new_audience, user_id)
    update_data = rewritten_base.model_dump(exclude_unset=True, exclude_none=True)
    if "target_audience" not in update_data or not update_data["target_audience"]:
        update_data["target_audience"] = new_audience

    message.sqlmodel_update(update_data)
    session.add(message)
    session.commit()
    session.refresh(message)
    persist_message_snapshot(session, message)
    return message


def import_message_from_file(
    session: Session, user_id: int, upload_file: UploadFile
) -> ChatMessage:
    payload = json.loads(upload_file.file.read().decode("utf-8"))
    message_data = payload.get("message", payload)
    allowed_fields = {
        "original_text",
        "file_url",
        "target_audience",
        "handling_matter",
        "time_deadline",
        "location_entrance",
        "required_materials",
        "handling_process",
        "precautions",
        "risk_warnings",
        "original_text_mapping",
        "chat_analysis",
    }
    clean_payload = {
        key: value for key, value in message_data.items() if key in allowed_fields
    }
    if not clean_payload.get("original_text"):
        raise ValueError("导入的会话文件缺少 original_text")
    return create_message_from_payload(session, clean_payload, user_id)


def get_export_file_path(message: ChatMessage) -> Optional[Path]:
    if message.session_json_path:
        export_path = Path(message.session_json_path)
        if export_path.exists():
            return export_path
    return None


def open_message_folder(message: ChatMessage) -> dict[str, Any]:
    if not message.session_json_path:
        logger.warning("Attempted to open folder for message with no session_json_path.")
        return {"opened": False, "path": None, "error": "No export path found for message."}

    folder_path = str(Path(message.session_json_path).parent)
    opened = False
    error_message = None
    try:
        if os.name == "nt":
            os.startfile(folder_path)  # type: ignore[attr-defined]
            opened = True
        elif os.name == "posix":
            if shutil.which("xdg-open"):
                subprocess.Popen(["xdg-open", folder_path])
                opened = True
            else:
                error_message = "xdg-open command not found. Cannot open folder on POSIX system."
                logger.warning(error_message)
        else:
            error_message = f"Unsupported operating system: {os.name}. Cannot open folder."
            logger.warning(error_message)
    except Exception as exc:
        error_message = f"Failed to open session folder: {exc}"
        logger.warning(error_message)
    return {"opened": opened, "path": folder_path, "error": error_message}


def get_rag_context_for_message(
    message: ChatMessage, top_k: int = 5
) -> list[dict[str, Any]]:
    query = "\n".join(
        filter(
            None,
            [
                message.handling_matter,
                message.required_materials,
                message.risk_warnings,
                message.original_text[:500] if message.original_text else "",
            ],
        )
    )
    return rag_service.search_related_context(query, top_k=top_k)


def evaluate_notice_difficulty(
    original_text: str,
    handling_matter: str,
    time_deadline: str,
    required_materials: str,
    risk_warnings: str,
) -> str:
    ai_analysis = analyze_complexity_and_type(original_text)
    notice_type = ai_analysis.get("notice_type", "其他通知")
    language_complexity = ai_analysis.get("complexity", "中")

    materials_count = (
        len(str(required_materials).split("、")) + len(str(required_materials).split("，"))
        if required_materials
        else 0
    )
    matter_length = len(str(handling_matter)) if handling_matter else 0

    if materials_count > 5 or matter_length > 50:
        handling_complexity = "高"
    elif materials_count > 2 or matter_length > 20:
        handling_complexity = "中"
    else:
        handling_complexity = "低"

    risk_length = len(str(risk_warnings)) if risk_warnings and str(risk_warnings) != "无" else 0
    if risk_length > 50:
        risk_level = "高"
    elif risk_length > 10:
        risk_level = "中"
    else:
        risk_level = "低"

    analysis_dict = {
        "language_complexity": language_complexity,
        "handling_complexity": handling_complexity,
        "risk_level": risk_level,
        "notice_type": notice_type,
    }
    return json.dumps(analysis_dict, ensure_ascii=False)
