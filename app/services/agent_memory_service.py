from typing import Dict, Optional
from datetime import datetime

from sqlmodel import Session, select

from app.core.database import engine
from app.models.agent_memory import AgentMemory


def get_or_create_session_memory(user_id: int, conversation_id: int) -> Dict[str, str]:
    with Session(engine) as session:
        item = session.exec(
            select(AgentMemory).where(
                AgentMemory.user_id == user_id,
                AgentMemory.conversation_id == conversation_id,
            )
        ).first()
        if not item:
            item = AgentMemory(
                user_id=user_id,
                conversation_id=conversation_id,
                summary="",
                updated_time=datetime.now(),
            )
            session.add(item)
            session.commit()
            session.refresh(item)
        return {"summary": item.summary or ""}


def update_session_memory(user_id: int, conversation_id: int, summary: str) -> None:
    with Session(engine) as session:
        item = session.exec(
            select(AgentMemory).where(
                AgentMemory.user_id == user_id,
                AgentMemory.conversation_id == conversation_id,
            )
        ).first()
        if not item:
            item = AgentMemory(
                user_id=user_id,
                conversation_id=conversation_id,
                summary=summary,
                updated_time=datetime.now(),
            )
            session.add(item)
        else:
            item.summary = summary
            item.updated_time = datetime.now()
            session.add(item)
        session.commit()


def build_session_summary(user_input: str, assistant_reply: str, previous_summary: str) -> str:
    user_input = (user_input or "").strip()
    assistant_reply = (assistant_reply or "").strip()
    previous_summary = (previous_summary or "").strip()
    if not user_input and not assistant_reply:
        return previous_summary
    combined = "\n".join(
        item
        for item in [
            previous_summary,
            f"用户：{user_input}" if user_input else "",
            f"助手：{assistant_reply}" if assistant_reply else "",
        ]
        if item
    )
    if len(combined) <= 1200:
        return combined
    return combined[-1200:]
