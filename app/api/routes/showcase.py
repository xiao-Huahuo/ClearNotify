from fastapi import APIRouter, Depends
from sqlmodel import Session, func, select

from app.core.database import get_session
from app.models.chat_message import ChatMessage
from app.models.opinion import Opinion
from app.models.policy_document import DocStatus, PolicyDocument
from app.models.user import User, UserRole

router = APIRouter()


@router.get("/landing-stats")
def get_showcase_landing_stats(session: Session = Depends(get_session)):
    total_users = session.exec(select(func.count(User.uid))).one()
    certified_users = session.exec(
        select(func.count(User.uid)).where(User.role.in_([UserRole.certified, UserRole.admin]))
    ).one()
    total_messages = session.exec(
        select(func.count(ChatMessage.id)).where(ChatMessage.is_deleted == False)
    ).one()
    active_users = session.exec(
        select(func.count(func.distinct(ChatMessage.user_id))).where(ChatMessage.is_deleted == False)
    ).one()
    total_opinions = session.exec(select(func.count(Opinion.id))).one()
    total_docs = session.exec(select(func.count(PolicyDocument.id))).one()
    approved_docs = session.exec(
        select(func.count(PolicyDocument.id)).where(PolicyDocument.status == DocStatus.approved)
    ).one()
    pending_docs = session.exec(
        select(func.count(PolicyDocument.id)).where(PolicyDocument.status == DocStatus.pending)
    ).one()

    return {
        "total_users": total_users,
        "certified_users": certified_users,
        "total_messages": total_messages,
        "active_users": active_users,
        "total_opinions": total_opinions,
        "total_docs": total_docs,
        "approved_docs": approved_docs,
        "pending_docs": pending_docs,
    }
