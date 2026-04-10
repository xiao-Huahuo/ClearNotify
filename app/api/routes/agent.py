import asyncio
import json
import logging
from typing import Any, Callable, List

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlmodel import Session

from app.api.deps import get_current_user, get_current_user_from_token_value
from app.core.database import get_session, engine
from app.models.user import User
from app.schemas.agent import AgentRunRequest, AgentRunResponse
from app.schemas.agent_chat import (
    AgentConversationCreate,
    AgentConversationRead,
    AgentMessageRead,
)
from app.services import agent_service, agent_chat_service

router = APIRouter()

_STREAM_BREAK_CHARS = {
    "\n",
    "\u3002",
    "\uff01",
    "\uff1f",
    "\uff1b",
    "\uff1a",
    "\uff0c",
    "\u3001",
    ".",
    "!",
    "?",
    ";",
    ":",
    ",",
    ")",
    "]",
    "\u3011",
    "\uff09",
}

_STREAM_MAX_CHUNK_SIZE = 9
_STREAM_CHUNK_DELAY_SECONDS = 0.018
_TRACE_QUEUE_DONE = object()


def _iter_stream_chunks(text: str, max_chunk_size: int = _STREAM_MAX_CHUNK_SIZE):
    buffer: list[str] = []
    for ch in text or "":
        buffer.append(ch)
        if ch in _STREAM_BREAK_CHARS or len(buffer) >= max_chunk_size:
            yield "".join(buffer)
            buffer.clear()
    if buffer:
        yield "".join(buffer)


def _build_trace_callback(
    loop: asyncio.AbstractEventLoop,
    trace_queue: asyncio.Queue[Any],
) -> Callable[[dict[str, Any]], None]:
    trace_seen: set[str] = set()

    def _trace_callback(entry: dict[str, Any]) -> None:
        try:
            normalized = dict(entry or {})
            signature = json.dumps(normalized, ensure_ascii=False, sort_keys=True)
            if signature in trace_seen:
                return
            trace_seen.add(signature)
            loop.call_soon_threadsafe(trace_queue.put_nowait, normalized)
        except Exception:
            pass

    return _trace_callback


def _run_agent_in_worker(
    *,
    user_id: int,
    original_text: str,
    file_url: str | None,
    goal: str | None,
    scene: str | None,
    mode: str,
    use_rag: bool,
    top_k: int,
    conversation_id: int,
    trace_callback: Callable[[dict[str, Any]], None] | None,
) -> dict[str, Any]:
    with Session(engine) as worker_session:
        return agent_service.run_agent(
            session=worker_session,
            user_id=user_id,
            original_text=original_text,
            file_url=file_url,
            goal=goal,
            scene=scene,
            mode=mode,
            use_rag=use_rag,
            top_k=top_k,
            save_to_history=True,
            conversation_id=conversation_id,
            trace_callback=trace_callback,
        )


def _run_agent_with_trace_queue(
    *,
    loop: asyncio.AbstractEventLoop,
    trace_queue: asyncio.Queue[Any],
    user_id: int,
    original_text: str,
    file_url: str | None,
    goal: str | None,
    scene: str | None,
    mode: str,
    use_rag: bool,
    top_k: int,
    conversation_id: int,
    trace_callback: Callable[[dict[str, Any]], None] | None,
) -> dict[str, Any]:
    try:
        return _run_agent_in_worker(
            user_id=user_id,
            original_text=original_text,
            file_url=file_url,
            goal=goal,
            scene=scene,
            mode=mode,
            use_rag=use_rag,
            top_k=top_k,
            conversation_id=conversation_id,
            trace_callback=trace_callback,
        )
    finally:
        loop.call_soon_threadsafe(trace_queue.put_nowait, _TRACE_QUEUE_DONE)


async def _stream_trace_events(
    websocket: WebSocket,
    trace_queue: asyncio.Queue[Any],
) -> None:
    while True:
        entry = await trace_queue.get()
        if entry is _TRACE_QUEUE_DONE:
            break
        await websocket.send_json({"type": "trace_step", "tool_call": entry})


@router.post("/run", response_model=AgentRunResponse)
def run_agent(
    payload: AgentRunRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if not payload.original_text or not payload.original_text.strip():
        raise HTTPException(status_code=400, detail="请输入需要解析的通知内容")

    result = agent_service.run_agent(
        session=session,
        user_id=current_user.uid,
        original_text=payload.original_text,
        file_url=payload.file_url,
        goal=payload.goal,
        scene=payload.scene,
        mode=payload.mode,
        use_rag=payload.use_rag,
        top_k=payload.top_k,
        save_to_history=payload.save_to_history,
    )
    return AgentRunResponse(**result)


@router.get("/conversations", response_model=List[AgentConversationRead])
def list_conversations(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    conversations = agent_chat_service.list_conversations(session, current_user.uid)
    return [
        AgentConversationRead(
            id=item.id,
            title=item.title,
            created_time=item.created_time.isoformat(),
            updated_time=item.updated_time.isoformat(),
        )
        for item in conversations
    ]


@router.post("/conversations", response_model=AgentConversationRead)
def create_conversation(
    payload: AgentConversationCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    convo = agent_chat_service.create_conversation(
        session,
        current_user.uid,
        payload.title or "新对话",
    )
    return AgentConversationRead(
        id=convo.id,
        title=convo.title,
        created_time=convo.created_time.isoformat(),
        updated_time=convo.updated_time.isoformat(),
    )


@router.delete("/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    ok = agent_chat_service.delete_conversation(session, current_user.uid, conversation_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"ok": True}


@router.get("/conversations/{conversation_id}/messages", response_model=List[AgentMessageRead])
def list_messages(
    conversation_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    messages = agent_chat_service.get_messages(session, current_user.uid, conversation_id)
    return [
        AgentMessageRead(
            id=item.id,
            role=item.role,
            content=item.content,
            created_time=item.created_time.isoformat(),
        )
        for item in messages
    ]


@router.websocket("/ws")
async def agent_ws(websocket: WebSocket, token: str = Query(...)):
    await websocket.accept()
    logger = logging.getLogger("agent_ws")
    logger.info("agent ws connect")
    with Session(engine) as session:
        user = get_current_user_from_token_value(session, token)
        logger.info("agent ws auth ok user_id=%s", user.uid)
        try:
            while True:
                payload = await websocket.receive_text()
                logger.info("agent ws recv %s", payload[:2000])
                data = json.loads(payload)
                message = (data.get("message") or "").strip()
                if not message:
                    continue

                conversation_id = data.get("conversation_id")
                if not conversation_id:
                    from datetime import datetime
                    title = datetime.now().strftime("%Y-%m-%d %H:%M 对话")
                    convo = agent_chat_service.create_conversation(session, user.uid, title)
                    conversation_id = convo.id
                    await websocket.send_json(
                        {"type": "conversation", "conversation_id": conversation_id, "title": convo.title}
                    )
                    logger.info("agent ws conversation %s", conversation_id)

                agent_chat_service.add_message(
                    session, user.uid, conversation_id, role="user", content=message
                )

                trace_queue: asyncio.Queue[Any] = asyncio.Queue()
                loop = asyncio.get_running_loop()
                mode = str(data.get("mode") or "agent")
                trace_callback = _build_trace_callback(loop, trace_queue)
                result_task = asyncio.create_task(
                    asyncio.to_thread(
                        _run_agent_with_trace_queue,
                        loop=loop,
                        trace_queue=trace_queue,
                        user_id=user.uid,
                        original_text=message,
                        file_url=data.get("file_url"),
                        goal=data.get("goal"),
                        scene=data.get("scene"),
                        mode=mode,
                        use_rag=data.get("use_rag", True),
                        top_k=int(data.get("top_k", 5)),
                        conversation_id=int(conversation_id),
                        trace_callback=trace_callback,
                    )
                )
                await _stream_trace_events(websocket, trace_queue)
                result = await result_task
                reply_text = result.get("assistant_reply") or agent_service.build_agent_reply(result, message)
                agent_chat_service.add_message(
                    session, user.uid, conversation_id, role="assistant", content=reply_text
                )

                await websocket.send_json({"type": "trace_done"})
                await websocket.send_json(
                    {"type": "result", "conversation_id": conversation_id, "agent_result": result}
                )
                logger.info("agent ws result sent %s", conversation_id)
                for ch in _iter_stream_chunks(reply_text):
                    await websocket.send_json({"type": "chunk", "content": ch})
                    await asyncio.sleep(_STREAM_CHUNK_DELAY_SECONDS)
                await websocket.send_json({"type": "done"})
                logger.info("agent ws done %s", conversation_id)
        except WebSocketDisconnect:
            logger.info("agent ws disconnect")
            return
