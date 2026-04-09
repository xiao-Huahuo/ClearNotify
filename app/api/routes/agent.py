import asyncio
import json
import logging
from typing import List

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

                def _trace_callback(entry: dict):
                    try:
                        asyncio.create_task(
                            websocket.send_json({"type": "trace_step", "tool_call": entry})
                        )
                    except Exception:
                        pass

                result = agent_service.run_agent(
                    session=session,
                    user_id=user.uid,
                    original_text=message,
                    file_url=data.get("file_url"),
                    goal=data.get("goal"),
                    scene=data.get("scene"),
                    mode=str(data.get("mode") or "agent"),
                    use_rag=data.get("use_rag", True),
                    top_k=int(data.get("top_k", 5)),
                    save_to_history=True,
                    conversation_id=conversation_id,
                    trace_callback=_trace_callback,
                )
                reply_text = result.get("assistant_reply") or agent_service.build_agent_reply(result, message)
                agent_chat_service.add_message(
                    session, user.uid, conversation_id, role="assistant", content=reply_text
                )

                await websocket.send_json(
                    {"type": "result", "conversation_id": conversation_id, "agent_result": result}
                )
                if result.get("tool_calls"):
                    await websocket.send_json(
                        {"type": "trace", "tool_calls": result.get("tool_calls", [])}
                    )
                logger.info("agent ws result sent %s", conversation_id)
                for ch in reply_text:
                    await websocket.send_json({"type": "chunk", "content": ch})
                    await asyncio.sleep(0.02)
                await websocket.send_json({"type": "done"})
                logger.info("agent ws done %s", conversation_id)
        except WebSocketDisconnect:
            logger.info("agent ws disconnect")
            return
