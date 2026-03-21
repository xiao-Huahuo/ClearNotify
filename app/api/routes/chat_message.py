from typing import List, Optional
import json

from fastapi import APIRouter, Body, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlmodel import Session

from app.ai.document_parser import parse_document
from app.api.deps import get_current_user
from app.core.database import get_session
from app.models.user import User
from app.schemas.chat_message import ChatMessageCreate, ChatMessageRead, ChatMessageUpdate
from app.services import chat_message_service


router = APIRouter()


@router.post("/", response_model=ChatMessageRead)
def create_chat_message(
    chat_in: ChatMessageCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    parsed_base, parse_mode = parse_document(chat_in.original_text, current_user.uid)
    parsed_payload = parsed_base.model_dump()
    parsed_payload["file_url"] = chat_in.file_url or parsed_payload.get("file_url")

    analysis_json_str = chat_message_service.evaluate_notice_difficulty(
        original_text=parsed_base.original_text,
        handling_matter=parsed_base.handling_matter,
        time_deadline=parsed_base.time_deadline,
        required_materials=parsed_base.required_materials,
        risk_warnings=parsed_base.risk_warnings,
    )
    try:
        analysis_payload = json.loads(analysis_json_str)
    except (TypeError, json.JSONDecodeError):
        analysis_payload = {}
    analysis_payload["parse_mode"] = parse_mode
    parsed_payload["chat_analysis"] = analysis_payload

    db_message = chat_message_service.create_message_from_payload(
        session=session,
        message_payload=parsed_payload,
        user_id=current_user.uid,
    )
    return ChatMessageRead(**chat_message_service.serialize_message(db_message))


@router.get("/", response_model=List[ChatMessageRead])
def read_chat_messages(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
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
    sort_by: str = Query("created_time"),
    sort_order: str = Query("desc"),
    handling_only: bool = False,
):
    messages = chat_message_service.get_messages(
        session=session,
        user_id=current_user.uid,
        id=id,
        original_text=original_text,
        target_audience=target_audience,
        handling_matter=handling_matter,
        time_deadline=time_deadline,
        location_entrance=location_entrance,
        required_materials=required_materials,
        handling_process=handling_process,
        precautions=precautions,
        risk_warnings=risk_warnings,
        original_text_mapping=original_text_mapping,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        handling_only=handling_only,
    )
    return [ChatMessageRead(**chat_message_service.serialize_message(msg)) for msg in messages]


@router.post("/import", response_model=ChatMessageRead)
def import_chat_message(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        message = chat_message_service.import_message_from_file(
            session=session,
            user_id=current_user.uid,
            upload_file=file,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=400, detail="导入文件不是合法的 JSON")
    return ChatMessageRead(**chat_message_service.serialize_message(message))


@router.get("/{message_id}", response_model=ChatMessageRead)
def read_chat_message(
    message_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    message = chat_message_service.get_message_by_id(session, current_user.uid, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return ChatMessageRead(**chat_message_service.serialize_message(message))


@router.patch("/{message_id}", response_model=ChatMessageRead)
def update_chat_message_audience(
    message_id: int,
    chat_in: ChatMessageUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    updated_message = chat_message_service.update_message_audience_via_ai(
        session,
        current_user.uid,
        message_id,
        chat_in.target_audience,
    )
    if not updated_message:
        raise HTTPException(
            status_code=404,
            detail="Message not found or you don't have permission",
        )
    return ChatMessageRead(**chat_message_service.serialize_message(updated_message))


@router.get("/{message_id}/export")
def export_chat_message(
    message_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    message = chat_message_service.get_message_by_id(session, current_user.uid, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    export_path = chat_message_service.get_export_file_path(message)
    if export_path is None or not export_path.exists():
        export_path = chat_message_service.persist_message_snapshot(session, message)

    return FileResponse(
        path=str(export_path),
        filename=f"chat_{message.id}.json",
        media_type="application/json",
    )


@router.get("/{message_id}/open-folder")
def open_chat_message_folder(
    message_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    message = chat_message_service.get_message_by_id(session, current_user.uid, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return chat_message_service.open_message_folder(message)


@router.get("/{message_id}/rag-context")
def get_chat_message_rag_context(
    message_id: int,
    top_k: int = Query(5, ge=1, le=10),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    message = chat_message_service.get_message_by_id(session, current_user.uid, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return {"items": chat_message_service.get_rag_context_for_message(message, top_k=top_k)}


@router.delete("/{message_id}")
def delete_chat_message(
    message_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    message = chat_message_service.delete_message_by_id(session, current_user.uid, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return {"message": "Message deleted successfully"}


@router.post("/batch-delete")
def delete_chat_messages(
    message_ids: List[int] = Body(..., embed=True),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    count = chat_message_service.delete_messages_by_ids(
        session,
        current_user.uid,
        message_ids,
    )
    return {"message": f"{count} messages deleted successfully"}
