from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.core.database import get_session
from app.api.deps import get_current_user
from app.models.user import User
from app.models.todo import TodoItem
from app.services import history_service

router = APIRouter()

# ── 查询当前用户的 Todo 列表 ──────────────────────────────────────────────────
@router.get("/", response_model=List[TodoItem])
def get_todos(
    confirmed_only: bool = True,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    stmt = select(TodoItem).where(TodoItem.user_id == current_user.uid)
    if confirmed_only:
        stmt = stmt.where(TodoItem.is_confirmed == True)
    return session.exec(stmt.order_by(TodoItem.created_time.desc())).all()

# ── 创建 Todo（手动或从对话生成的草稿）────────────────────────────────────────
@router.post("/", response_model=TodoItem)
def create_todo(
    title: str,
    detail: Optional[str] = None,
    deadline: Optional[str] = None,
    source_chat_id: Optional[int] = None,
    is_confirmed: bool = True,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    todo = TodoItem(
        user_id=current_user.uid,
        title=title,
        detail=detail,
        deadline=deadline,
        source_chat_id=source_chat_id,
        is_confirmed=is_confirmed
    )
    session.add(todo)
    session.commit()
    session.refresh(todo)
    history_service.record_todo_event(
        session,
        todo=todo,
        event_type="created",
        dedupe_key=f"todo:create:{todo.id}",
    )
    return todo

# ── 批量从对话生成 Todo 草稿 ──────────────────────────────────────────────────
@router.post("/from-chat", response_model=List[TodoItem])
def create_todos_from_chat(
    items: List[dict],
    source_chat_id: Optional[int] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """items: [{title, detail, deadline}, ...]，is_confirmed=False 表示待用户确认"""
    todos = []
    for item in items:
        todo = TodoItem(
            user_id=current_user.uid,
            title=item.get("title", ""),
            detail=item.get("detail"),
            deadline=item.get("deadline"),
            source_chat_id=source_chat_id,
            is_confirmed=False
        )
        session.add(todo)
        todos.append(todo)
    session.commit()
    for t in todos:
        session.refresh(t)
        history_service.record_todo_event(
            session,
            todo=t,
            event_type="created",
            dedupe_key=f"todo:create:{t.id}",
        )
    return todos

# ── 确认草稿 Todo ─────────────────────────────────────────────────────────────
@router.patch("/{todo_id}/confirm", response_model=TodoItem)
def confirm_todo(
    todo_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    todo = session.get(TodoItem, todo_id)
    if not todo or todo.user_id != current_user.uid:
        raise HTTPException(status_code=404, detail="Todo not found")
    todo.is_confirmed = True
    todo.updated_time = datetime.now()
    session.add(todo)
    session.commit()
    session.refresh(todo)
    history_service.record_todo_event(
        session,
        todo=todo,
        event_type="confirmed",
        dedupe_key=f"todo:confirm:{todo.id}",
    )
    return todo

# ── 切换完成状态 ──────────────────────────────────────────────────────────────
@router.patch("/{todo_id}/toggle", response_model=TodoItem)
def toggle_todo(
    todo_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    todo = session.get(TodoItem, todo_id)
    if not todo or todo.user_id != current_user.uid:
        raise HTTPException(status_code=404, detail="Todo not found")
    todo.is_done = not todo.is_done
    todo.updated_time = datetime.now()
    session.add(todo)
    session.commit()
    session.refresh(todo)
    history_service.record_todo_event(
        session,
        todo=todo,
        event_type="completed" if todo.is_done else "reopened",
        dedupe_key=f"todo:{'complete' if todo.is_done else 'reopen'}:{todo.id}",
    )
    return todo

# ── 删除 Todo ─────────────────────────────────────────────────────────────────
@router.delete("/{todo_id}")
def delete_todo(
    todo_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    todo = session.get(TodoItem, todo_id)
    if not todo or todo.user_id != current_user.uid:
        raise HTTPException(status_code=404, detail="Todo not found")
    history_service.record_todo_event(
        session,
        todo=todo,
        event_type="deleted",
        dedupe_key=f"todo:deleted:{todo.id}",
    )
    session.delete(todo)
    session.commit()
    return {"ok": True}
