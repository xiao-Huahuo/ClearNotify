from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List, Optional
from app.core.database import get_session
from app.api.deps import get_current_user
from app.models.user import User
from app.models.favorite import Favorite
from app.models.chat_message import ChatMessage
from app.services import history_service

router = APIRouter()

@router.get("/", response_model=List[Favorite])
def get_favorites(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Favorite).where(Favorite.user_id == current_user.uid).order_by(Favorite.created_time.desc())
    return session.exec(stmt).all()

@router.post("/", response_model=Favorite)
def add_favorite(
    chat_message_id: int,
    note: Optional[str] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # 检查消息存在且属于当前用户
    msg = session.get(ChatMessage, chat_message_id)
    if not msg or msg.user_id != current_user.uid:
        raise HTTPException(status_code=404, detail="Message not found")
    # 防止重复收藏
    existing = session.exec(
        select(Favorite).where(
            Favorite.user_id == current_user.uid,
            Favorite.chat_message_id == chat_message_id
        )
    ).first()
    if existing:
        return existing
    fav = Favorite(user_id=current_user.uid, chat_message_id=chat_message_id, note=note)
    session.add(fav)
    session.commit()
    session.refresh(fav)
    history_service.record_favorite_event(
        session,
        favorite=fav,
        message=msg,
        event_type="added",
        dedupe_key=f"favorite:add:{fav.id}",
    )
    return fav

@router.delete("/{fav_id}")
def remove_favorite(
    fav_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    fav = session.get(Favorite, fav_id)
    if not fav or fav.user_id != current_user.uid:
        raise HTTPException(status_code=404, detail="Favorite not found")
    msg = session.get(ChatMessage, fav.chat_message_id)
    if msg:
        history_service.record_favorite_event(
            session,
            favorite=fav,
            message=msg,
            event_type="removed",
            dedupe_key=f"favorite:removed:{fav.id}",
        )
    session.delete(fav)
    session.commit()
    return {"ok": True}
