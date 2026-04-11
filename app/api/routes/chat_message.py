import asyncio
import json
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from sqlmodel import Session

from app.ai.document_parser import parse_document, build_graph_from_dynamic_payload
from app.api.deps import get_current_user, get_current_user_from_token_value
from app.core.database import get_session
from app.models.user import User
from app.schemas.chat_message import ChatMessageCreate, ChatMessageRead, ChatMessageUpdate
from app.services import chat_message_service, history_service, parse_progress_service


router = APIRouter()


def _to_payload_dict(parsed_payload, original_text: str, user_id: int) -> dict:
    """
    关键兼容层（禁止随意删除/改写）：
    parse_document 历史上既可能返回 dict，也可能返回 ChatMessageBase。
    这里必须统一转成 dict，避免后续下标访问触发 500。
    """
    if isinstance(parsed_payload, dict):
        payload = dict(parsed_payload)
    elif hasattr(parsed_payload, "model_dump"):
        payload = parsed_payload.model_dump()
    elif hasattr(parsed_payload, "dict"):
        payload = parsed_payload.dict()
    else:
        payload = {}

    payload.setdefault("original_text", original_text)
    payload.setdefault("user_id", user_id)
    payload.setdefault("content", payload.get("original_text") or original_text or "")
    # 核心原则（禁止改动）：禁止在这里按固定内容字段推断/补全语义，仅做通用类型兜底。
    payload.setdefault("nodes", [])
    payload.setdefault("links", [])
    # 核心原则（禁止改动）：不得在这里预设任何与内容相关的 dynamic_payload 字段。
    payload.setdefault("dynamic_payload", {})
    payload.setdefault(
        "visual_config",
        {
            "focus_node": None,
            "initial_zoom": 1.0,
            "text_mapping": {},
        },
    )
    return payload


@router.post("/", response_model=ChatMessageRead)
def create_chat_message(
    chat_in: ChatMessageCreate,
    parse_task_id: Optional[str] = Query(default=None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    def emit(progress: int, stage: str, status: Optional[str] = None, message: Optional[str] = None):
        if not parse_task_id:
            return
        parse_progress_service.update_task(
            parse_task_id,
            current_user.uid,
            progress=progress,
            stage=stage,
            status=status,
            message=message,
        )

    emit(10, "请求已接收", "running")
    try:
        parsed_raw, parse_mode = parse_document(
            chat_in.original_text,
            current_user.uid,
            progress_cb=lambda p, s: emit(p, s, "running"),
        )
    except Exception as e:
        emit(100, "解析失败", "failed", str(e))
        parsed_raw, parse_mode = {
            "original_text": chat_in.original_text,
            "content": chat_in.original_text,
            "nodes": [],
            "links": [],
            "dynamic_payload": {},
            "visual_config": {"focus_node": None, "initial_zoom": 1.0, "text_mapping": {}},
        }, "fallback_fast"

    parsed_payload = _to_payload_dict(parsed_raw, chat_in.original_text, current_user.uid)
    emit(84, "写入结果中", "running")
    if not isinstance(parsed_payload.get("dynamic_payload"), dict):
        parsed_payload["dynamic_payload"] = {}
    if (not parsed_payload.get("nodes")) and isinstance(parsed_payload.get("dynamic_payload"), dict) and parsed_payload["dynamic_payload"]:
        nodes, links = build_graph_from_dynamic_payload(parsed_payload["dynamic_payload"])
        parsed_payload["nodes"] = nodes
        parsed_payload["links"] = links
        if not isinstance(parsed_payload.get("visual_config"), dict):
            parsed_payload["visual_config"] = {}
        parsed_payload["visual_config"].setdefault("focus_node", nodes[0]["id"] if nodes else None)
        parsed_payload["visual_config"].setdefault("initial_zoom", 1.0)
        parsed_payload["visual_config"].setdefault("text_mapping", {})
    parsed_payload["file_url"] = chat_in.file_url or parsed_payload.get("file_url")
    analysis_payload = chat_message_service.build_chat_analysis_payload(
        parse_mode=parse_mode,
        content=parsed_payload.get("content") or parsed_payload.get("original_text") or "",
        nodes=parsed_payload.get("nodes") or [],
        links=parsed_payload.get("links") or [],
        dynamic_payload=parsed_payload.get("dynamic_payload") or {},
        visual_config=parsed_payload.get("visual_config") or {},
    )
    parsed_payload["chat_analysis"] = analysis_payload

    db_message = chat_message_service.create_message_from_payload(
        session=session,
        message_payload=parsed_payload,
        user_id=current_user.uid,
    )
    try:
        chat_message_service.get_rag_context_for_message(db_message, top_k=3)
    except Exception:
        pass
    emit(100, "解析完成", "completed")
    return ChatMessageRead(**chat_message_service.serialize_message(db_message))


@router.post("/progress/start")
def start_chat_progress_task(current_user: User = Depends(get_current_user)):
    task_id = parse_progress_service.create_task(current_user.uid)
    return {"task_id": task_id}


@router.get("/progress/stream")
async def stream_chat_progress(
    task_id: str = Query(...),
    token: str = Query(...),
    session: Session = Depends(get_session),
):
    user = get_current_user_from_token_value(session, token)

    async def event_generator():
        last_payload = None
        while True:
            snapshot = parse_progress_service.get_task(task_id, user.uid)
            if snapshot is None:
                missing = {
                    "task_id": task_id,
                    "status": "not_found",
                    "progress": 100,
                    "stage": "任务不存在",
                    "message": "",
                }
                yield f"data: {json.dumps(missing, ensure_ascii=False)}\n\n"
                break

            payload = json.dumps(snapshot, ensure_ascii=False)
            if payload != last_payload:
                yield f"data: {payload}\n\n"
                last_payload = payload

            if snapshot.get("status") in {"completed", "failed"}:
                break
            await asyncio.sleep(0.35)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


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

    history_service.record_chat_message_event(
        session,
        message,
        event_type="exported",
        actor_user_id=current_user.uid,
        dedupe_key=f"chat:exported:{message.id}:{int(datetime.now().timestamp())}",
    )

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
