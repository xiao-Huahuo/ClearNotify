import asyncio
import json
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlmodel import Session, func, select

from app.api.deps import get_current_user, get_current_user_from_token_value
from app.core.config import GlobalConfig
from app.core.database import get_session
from app.models.chat_message import ChatMessage
from app.models.user import User
from app.services import email_service, rag_service, stats_service


router = APIRouter()


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    return current_user


@router.get("/users", response_model=List[dict])
def list_users(
    session: Session = Depends(get_session),
    admin: User = Depends(require_admin),
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
            "email_verified": u.email_verified,
        }
        for u in users
    ]


@router.get("/stats")
def admin_stats(
    session: Session = Depends(get_session),
    admin: User = Depends(require_admin),
):
    total_users = session.exec(select(func.count(User.uid))).one()
    total_messages = session.exec(
        select(func.count(ChatMessage.id)).where(ChatMessage.is_deleted == False)
    ).one()
    active_users = session.exec(
        select(func.count(func.distinct(ChatMessage.user_id))).where(ChatMessage.is_deleted == False)
    ).one()
    user_msg_counts = session.exec(
        select(ChatMessage.user_id, func.count(ChatMessage.id))
        .where(ChatMessage.is_deleted == False)
        .group_by(ChatMessage.user_id)
    ).all()
    return {
        "total_users": total_users,
        "total_messages": total_messages,
        "active_users": active_users,
        "user_message_counts": [
            {"user_id": uid, "count": cnt} for uid, cnt in user_msg_counts
        ],
    }


@router.patch("/users/{uid}/toggle-admin", response_model=dict)
def toggle_admin(
    uid: int,
    session: Session = Depends(get_session),
    admin: User = Depends(require_admin),
):
    user = session.get(User, uid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.uid == admin.uid:
        raise HTTPException(status_code=400, detail="Cannot modify yourself")
    user.is_admin = not user.is_admin
    session.add(user)
    session.commit()
    email_service.send_role_change_email(user, "管理员" if user.is_admin else "普通用户")
    return {"uid": user.uid, "is_admin": user.is_admin}


@router.delete("/users/{uid}")
def delete_user(
    uid: int,
    session: Session = Depends(get_session),
    admin: User = Depends(require_admin),
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
    admin: User = Depends(require_admin),
):
    return stats_service.generate_all_users_stats(session)


@router.get("/stats/stream")
async def admin_stats_stream(
    token: str = Query(...),
    session: Session = Depends(get_session),
):
    admin = get_current_user_from_token_value(session, token)
    if not admin.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")

    async def event_generator():
        while True:
            payload = admin_stats(session=session, admin=admin)
            payload["timestamp"] = asyncio.get_running_loop().time()
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
            await asyncio.sleep(GlobalConfig.REALTIME_STREAM_INTERVAL_SECONDS)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/logs")
def read_logs(
    limit: int = Query(200, ge=20, le=1000),
    admin: User = Depends(require_admin),
):
    log_path = Path(GlobalConfig.APP_LOG_PATH)
    if not log_path.exists():
        return {"items": []}
    lines = log_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    return {"items": lines[-limit:]}


@router.get("/rag/status")
def rag_status(admin: User = Depends(require_admin)):
    return rag_service.get_status()


@router.get("/rag/search")
def rag_search(
    q: str = Query("", description="RAG 查询关键词"),
    top_k: int = Query(5, ge=1, le=10),
    admin: User = Depends(require_admin),
):
    return {"items": rag_service.search_related_context(q, top_k=top_k)}


@router.get("/users/{uid}/avatar")
def get_user_avatar(
    uid: int,
    session: Session = Depends(get_session),
    admin: User = Depends(require_admin),
):
    user = session.get(User, uid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"uid": uid, "avatar_url": user.avatar_url}
