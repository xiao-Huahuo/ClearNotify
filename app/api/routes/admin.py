from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, func
from typing import List
from app.core.database import get_session
from app.api.deps import get_current_user
from app.models.user import User
from app.models.chat_message import ChatMessage
from app.models.stats_analysis import StatsAnalysis
from app.services import stats_service

router = APIRouter()

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    return current_user

@router.get("/users", response_model=List[dict])
def list_users(
    session: Session = Depends(get_session),
    admin: User = Depends(require_admin)
):
    users = session.exec(select(User)).all()
    return [
        {
            "uid": u.uid,
            "uname": u.uname,
            "email": u.email,
            "is_admin": u.is_admin,
            "created_time": str(u.created_time),
            "last_login": str(u.last_login),
            "avatar_url": u.avatar_url,
        }
        for u in users
    ]

@router.get("/stats")
def admin_stats(
    session: Session = Depends(get_session),
    admin: User = Depends(require_admin)
):
    total_users = session.exec(select(func.count(User.uid))).one()
    total_messages = session.exec(select(func.count(ChatMessage.id))).one()
    active_users = session.exec(
        select(func.count(func.distinct(ChatMessage.user_id)))
    ).one()
    # 每个用户的消息数
    user_msg_counts = session.exec(
        select(ChatMessage.user_id, func.count(ChatMessage.id))
        .group_by(ChatMessage.user_id)
    ).all()
    return {
        "total_users": total_users,
        "total_messages": total_messages,
        "active_users": active_users,
        "user_message_counts": [
            {"user_id": uid, "count": cnt} for uid, cnt in user_msg_counts
        ]
    }

@router.patch("/users/{uid}/toggle-admin", response_model=dict)
def toggle_admin(
    uid: int,
    session: Session = Depends(get_session),
    admin: User = Depends(require_admin)
):
    user = session.get(User, uid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.uid == admin.uid:
        raise HTTPException(status_code=400, detail="Cannot modify yourself")
    user.is_admin = not user.is_admin
    session.add(user)
    session.commit()
    return {"uid": user.uid, "is_admin": user.is_admin}

@router.delete("/users/{uid}")
def delete_user(
    uid: int,
    session: Session = Depends(get_session),
    admin: User = Depends(require_admin)
):
    user = session.get(User, uid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.uid == admin.uid:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    session.delete(user)
    session.commit()
    return {"ok": True}


@router.get("/analysis/all")
def admin_analysis_all(
    session: Session = Depends(get_session),
    admin: User = Depends(require_admin)
):
    """获取所有用户的汇总统计数据"""
    return stats_service.generate_all_users_stats(session)


@router.get("/users/{uid}/avatar")
def get_user_avatar(
    uid: int,
    session: Session = Depends(get_session),
    admin: User = Depends(require_admin)
):
    """获取指定用户的头像URL"""
    user = session.get(User, uid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"uid": uid, "avatar_url": user.avatar_url}
