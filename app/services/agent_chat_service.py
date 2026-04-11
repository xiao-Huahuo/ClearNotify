from datetime import datetime
from typing import List, Optional

from sqlmodel import Session, select

from app.models.agent_conversation import AgentConversation
from app.models.agent_message import AgentMessage
from app.services import history_service


def create_conversation(session: Session, user_id: int, title: str) -> AgentConversation:
    convo = AgentConversation(user_id=user_id, title=title, updated_time=datetime.now())
    session.add(convo)
    session.commit()
    session.refresh(convo)
    history_service.record_agent_conversation_event(
        session,
        convo,
        event_type="created",
        actor_user_id=user_id,
        dedupe_key=f"agent:create:{convo.id}",
        occurred_time=convo.created_time,
    )
    return convo


def list_conversations(session: Session, user_id: int) -> List[AgentConversation]:
    statement = select(AgentConversation).where(AgentConversation.user_id == user_id)
    conversations = list(session.exec(statement).all())
    conversations.sort(key=lambda item: item.updated_time, reverse=True)
    return conversations


def get_conversation(session: Session, user_id: int, conversation_id: int) -> Optional[AgentConversation]:
    convo = session.get(AgentConversation, conversation_id)
    if not convo or convo.user_id != user_id:
        return None
    return convo


def delete_conversation(session: Session, user_id: int, conversation_id: int) -> bool:
    convo = get_conversation(session, user_id, conversation_id)
    if not convo:
        return False
    history_service.record_agent_conversation_event(
        session,
        convo,
        event_type="deleted",
        actor_user_id=user_id,
        summary="会话已删除",
        dedupe_key=f"agent:deleted:{convo.id}",
        occurred_time=datetime.now(),
    )
    messages = list(
        session.exec(
            select(AgentMessage).where(AgentMessage.conversation_id == conversation_id)
        ).all()
    )
    for msg in messages:
        session.delete(msg)
    session.delete(convo)
    session.commit()
    return True


def add_message(
    session: Session,
    user_id: int,
    conversation_id: int,
    role: str,
    content: str,
) -> AgentMessage:
    msg = AgentMessage(
        conversation_id=conversation_id,
        user_id=user_id,
        role=role,
        content=content,
    )
    session.add(msg)
    convo = session.get(AgentConversation, conversation_id)
    if convo:
        convo.updated_time = datetime.now()
        session.add(convo)
    session.commit()
    session.refresh(msg)
    if convo and role == "assistant":
        history_service.record_agent_conversation_event(
            session,
            convo,
            event_type="continued",
            actor_user_id=user_id,
            summary=content,
            dedupe_key=f"agent:continued:{conversation_id}:{msg.id}",
            occurred_time=msg.created_time,
            extra={"message_id": msg.id},
        )
    return msg


def get_messages(
    session: Session,
    user_id: int,
    conversation_id: int,
) -> List[AgentMessage]:
    convo = get_conversation(session, user_id, conversation_id)
    if not convo:
        return []
    statement = select(AgentMessage).where(AgentMessage.conversation_id == conversation_id)
    messages = list(session.exec(statement).all())
    messages.sort(key=lambda item: item.created_time)
    return messages
