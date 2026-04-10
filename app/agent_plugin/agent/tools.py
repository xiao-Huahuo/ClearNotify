import json
from pathlib import Path
from typing import Any

from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from sqlmodel import Session, select

from app.agent_plugin.agent.memory import get_long_term_memory
from app.core.database import engine
from app.models.chat_message import ChatMessage
from app.models.favorite import Favorite
from app.models.policy_document import DocStatus, PolicyDocument
from app.models.settings import Settings
from app.models.todo import TodoItem
from app.models.user import User
from app.services import chat_message_service, stats_service
from app.services.news_crawler import get_daily_gov_summary, search_news


def _uid(user_id: str) -> int:
    return int(str(user_id))


def _ok(payload: dict[str, Any]) -> str:
    payload.setdefault("ok", True)
    return json.dumps(payload, ensure_ascii=False)


def _err(code: str, message: str) -> str:
    return json.dumps(
        {"ok": False, "error": {"code": code, "message": message}},
        ensure_ascii=False,
    )


def _todo_to_dict(item: TodoItem) -> dict[str, Any]:
    return {
        "id": item.id,
        "title": item.title,
        "detail": item.detail,
        "deadline": item.deadline,
        "is_done": item.is_done,
        "is_confirmed": item.is_confirmed,
        "source_chat_id": item.source_chat_id,
        "created_time": item.created_time.isoformat() if item.created_time else None,
        "updated_time": item.updated_time.isoformat() if item.updated_time else None,
    }


def _doc_to_dict(doc: PolicyDocument, uploader_name: str | None = None) -> dict[str, Any]:
    return {
        "id": doc.id,
        "title": doc.title,
        "category": doc.category,
        "tags": doc.tags,
        "status": str(doc.status),
        "view_count": doc.view_count,
        "like_count": doc.like_count,
        "created_time": doc.created_time.isoformat() if doc.created_time else None,
        "uploader_id": doc.uploader_id,
        "uploader_name": uploader_name,
    }


def _message_to_dict(msg: ChatMessage) -> dict[str, Any]:
    return {
        "id": msg.id,
        "original_text": msg.original_text,
        "file_url": msg.file_url,
        "target_audience": msg.target_audience,
        "handling_matter": msg.handling_matter,
        "time_deadline": msg.time_deadline,
        "required_materials": msg.required_materials,
        "handling_process": msg.handling_process,
        "precautions": msg.precautions,
        "risk_warnings": msg.risk_warnings,
        "created_time": msg.created_time.isoformat() if msg.created_time else None,
    }


def _favorite_to_dict(fav: Favorite) -> dict[str, Any]:
    return {
        "id": fav.id,
        "chat_message_id": fav.chat_message_id,
        "note": fav.note,
        "created_time": fav.created_time.isoformat() if fav.created_time else None,
    }


@tool
def query_long_term_memory(query: str, user_id: str):
    """当需要检索用户长期记忆（偏好、背景、历史事实）时调用。"""
    long_term_memory = get_long_term_memory()
    results = long_term_memory.rag_query_top_k(query=query, user_id=user_id)
    return _ok({"items": results, "meta": {"query": query, "count": len(results)}})


@tool
def parse_local_file(file_name: str, user_id: str = ""):
    """读取本地文本文件内容（受项目目录约束）并返回前 3000 字符。"""
    candidate = Path(file_name)
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate

    candidate = candidate.resolve()
    root = Path.cwd().resolve()
    if root not in candidate.parents and candidate != root:
        return _err("OUTSIDE_PROJECT", "文件路径不在当前项目目录下，拒绝读取。")

    if not candidate.exists() or not candidate.is_file():
        return _err("FILE_NOT_FOUND", f"未找到文件: {candidate}")

    if candidate.suffix.lower() not in {".txt", ".md", ".json", ".log", ".py", ".yaml", ".yml"}:
        return _err("UNSUPPORTED_FILE_TYPE", f"暂不支持该类型: {candidate.suffix}")

    try:
        content = candidate.read_text(encoding="utf-8", errors="ignore")
    except Exception as exc:
        return _err("FILE_READ_FAILED", f"读取失败: {exc}")

    return _ok(
        {
            "item": {
                "file": str(candidate),
                "content_preview": content[:3000],
            }
        }
    )


@tool
def get_my_todos(user_id: str, confirmed_only: bool = True):
    """查询当前用户待办列表。"""
    try:
        uid = _uid(user_id)
        with Session(engine) as session:
            stmt = select(TodoItem).where(TodoItem.user_id == uid)
            if confirmed_only:
                stmt = stmt.where(TodoItem.is_confirmed == True)
            stmt = stmt.order_by(TodoItem.created_time.desc())
            items = list(session.exec(stmt).all())
            return _ok({"items": [_todo_to_dict(item) for item in items]})
    except Exception as exc:
        return _err("TODO_QUERY_FAILED", str(exc))


@tool
def create_todos_from_chat(
    user_id: str,
    items: list[dict[str, Any]],
    source_chat_id: int | None = None,
    confirm: bool = False,
):
    """批量从聊天内容创建待办。confirm=false 时仅返回草稿，不写库。"""
    if not items:
        return _err("EMPTY_ITEMS", "items 不能为空。")
    try:
        uid = _uid(user_id)
        if not confirm:
            drafts = []
            for item in items[:20]:
                drafts.append(
                    {
                        "title": str(item.get("title", "")).strip(),
                        "detail": item.get("detail"),
                        "deadline": item.get("deadline"),
                        "source_chat_id": source_chat_id,
                        "is_confirmed": False,
                    }
                )
            return _ok({"items": drafts, "pending_confirm": True})

        created: list[dict[str, Any]] = []
        with Session(engine) as session:
            for item in items[:20]:
                title = str(item.get("title", "")).strip()
                if not title:
                    continue
                todo = TodoItem(
                    user_id=uid,
                    title=title,
                    detail=item.get("detail"),
                    deadline=item.get("deadline"),
                    source_chat_id=source_chat_id,
                    is_confirmed=False,
                )
                session.add(todo)
                created.append(todo)
            session.commit()
            for todo in created:
                session.refresh(todo)
            return _ok(
                {
                    "items": [_todo_to_dict(item) for item in created],
                    "pending_confirm": False,
                }
            )
    except Exception as exc:
        return _err("TODO_CREATE_FAILED", str(exc))


@tool
def confirm_todo(user_id: str, todo_id: int, confirm: bool = False):
    """确认单条待办草稿。confirm=false 时仅提示需确认。"""
    if not confirm:
        return _ok({"pending_confirm": True, "todo_id": todo_id})
    try:
        uid = _uid(user_id)
        with Session(engine) as session:
            todo = session.get(TodoItem, todo_id)
            if not todo or todo.user_id != uid:
                return _err("TODO_NOT_FOUND", "Todo not found")
            todo.is_confirmed = True
            session.add(todo)
            session.commit()
            session.refresh(todo)
            return _ok({"item": _todo_to_dict(todo), "pending_confirm": False})
    except Exception as exc:
        return _err("TODO_CONFIRM_FAILED", str(exc))


@tool
def search_policy_documents(
    user_id: str,
    category: str = "",
    skip: int = 0,
    limit: int = 20,
):
    """检索已审核通过的政策文档。"""
    try:
        with Session(engine) as session:
            q = select(PolicyDocument).where(PolicyDocument.status == DocStatus.approved)
            if category:
                q = q.where(PolicyDocument.category == category)
            q = q.order_by(PolicyDocument.created_time.desc()).offset(max(skip, 0)).limit(max(1, min(limit, 50)))
            docs = list(session.exec(q).all())
            result = []
            for doc in docs:
                uploader = session.get(User, doc.uploader_id)
                result.append(_doc_to_dict(doc, uploader.uname if uploader else None))
            return _ok({"items": result})
    except Exception as exc:
        return _err("POLICY_SEARCH_FAILED", str(exc))


@tool
def recommend_policy_documents(
    user_id: str,
    for_me: bool = True,
    skip: int = 0,
    limit: int = 10,
):
    """推荐政策文档。for_me=true 时尽量按用户职业偏好推荐。"""
    try:
        uid = _uid(user_id)
        limit = max(1, min(limit, 50))
        skip = max(skip, 0)
        with Session(engine) as session:
            base_q = select(PolicyDocument).where(PolicyDocument.status == DocStatus.approved)
            docs: list[PolicyDocument] = []
            if for_me:
                user = session.get(User, uid)
                matched_cat = None
                if user and user.profession:
                    category_map = {
                        "医": "医疗卫生",
                        "教": "教育",
                        "农": "乡村振兴",
                        "企": "惠企政策",
                        "环": "环境保护",
                        "交": "交通建设",
                    }
                    matched_cat = next((v for k, v in category_map.items() if k in user.profession), None)
                if matched_cat:
                    prio = list(
                        session.exec(
                            base_q.where(PolicyDocument.category == matched_cat)
                            .order_by(PolicyDocument.view_count.desc())
                            .limit(max(1, limit // 2))
                        ).all()
                    )
                    rest = list(
                        session.exec(
                            base_q.where(PolicyDocument.category != matched_cat)
                            .order_by(PolicyDocument.view_count.desc())
                            .offset(skip)
                            .limit(limit)
                        ).all()
                    )
                    docs = (prio + rest)[:limit]
            if not docs:
                docs = list(
                    session.exec(
                        base_q.order_by(PolicyDocument.view_count.desc())
                        .offset(skip)
                        .limit(limit)
                    ).all()
                )
            result = []
            for doc in docs:
                uploader = session.get(User, doc.uploader_id)
                result.append(_doc_to_dict(doc, uploader.uname if uploader else None))
            return _ok({"items": result})
    except Exception as exc:
        return _err("POLICY_RECOMMEND_FAILED", str(exc))


@tool
def get_user_settings(user_id: str):
    """获取当前用户设置。"""
    try:
        uid = _uid(user_id)
        with Session(engine) as session:
            settings = session.exec(select(Settings).where(Settings.user_id == uid)).first()
            if not settings:
                settings = Settings(user_id=uid)
                session.add(settings)
                session.commit()
                session.refresh(settings)
            return _ok({"item": settings.model_dump()})
    except Exception as exc:
        return _err("SETTINGS_QUERY_FAILED", str(exc))


@tool
def update_user_settings(
    user_id: str,
    default_audience: str = "",
    theme_mode: str = "",
    color_scheme: str = "",
    system_notifications: bool | None = None,
    confirm: bool = False,
):
    """更新当前用户设置。confirm=false 时只返回待确认变更。"""
    patch = {}
    if default_audience:
        patch["default_audience"] = default_audience
    if theme_mode:
        patch["theme_mode"] = theme_mode
    if color_scheme:
        patch["color_scheme"] = color_scheme
    if system_notifications is not None:
        patch["system_notifications"] = bool(system_notifications)

    if not patch:
        return _err("EMPTY_PATCH", "没有可更新字段。")

    if not confirm:
        return _ok({"pending_confirm": True, "patch": patch})

    try:
        uid = _uid(user_id)
        with Session(engine) as session:
            settings = session.exec(select(Settings).where(Settings.user_id == uid)).first()
            if not settings:
                settings = Settings(user_id=uid)
            settings.sqlmodel_update(patch)
            session.add(settings)
            session.commit()
            session.refresh(settings)
            return _ok({"item": settings.model_dump(), "pending_confirm": False})
    except Exception as exc:
        return _err("SETTINGS_UPDATE_FAILED", str(exc))


@tool
def search_chat_history(
    user_id: str,
    query: str = "",
    skip: int = 0,
    limit: int = 20,
    handling_only: bool = False,
):
    """检索当前用户历史解析消息。"""
    try:
        uid = _uid(user_id)
        with Session(engine) as session:
            stmt = select(ChatMessage).where(
                ChatMessage.user_id == uid,
                ChatMessage.is_deleted == False,
            )
            if query:
                stmt = stmt.where(ChatMessage.original_text.contains(query))
            stmt = stmt.order_by(ChatMessage.created_time.desc()).offset(max(skip, 0)).limit(max(1, min(limit, 50)))
            items = list(session.exec(stmt).all())
            if handling_only:
                items = [item for item in items if (item.handling_matter or "").strip()]
            return _ok({"items": [_message_to_dict(item) for item in items]})
    except Exception as exc:
        return _err("CHAT_HISTORY_SEARCH_FAILED", str(exc))


@tool
def get_chat_message_detail(user_id: str, message_id: int):
    """获取单条历史解析消息详情。"""
    try:
        uid = _uid(user_id)
        with Session(engine) as session:
            message = session.get(ChatMessage, message_id)
            if not message or message.user_id != uid or message.is_deleted:
                return _err("MESSAGE_NOT_FOUND", "Message not found")
            return _ok({"item": _message_to_dict(message)})
    except Exception as exc:
        return _err("CHAT_MESSAGE_DETAIL_FAILED", str(exc))


@tool
def get_news_digest(user_id: str = ""):
    """获取政务热点日报摘要。"""
    try:
        summary = get_daily_gov_summary()
        return _ok({"item": summary})
    except Exception as exc:
        return _err("NEWS_DIGEST_FAILED", str(exc))


@tool
def search_news_tool(query: str, limit: int = 10, user_id: str = ""):
    """按关键词检索新闻。"""
    try:
        limit = max(1, min(limit, 30))
        items = search_news(query, limit=limit)
        return _ok({"items": items, "meta": {"query": query, "limit": limit}})
    except Exception as exc:
        return _err("NEWS_SEARCH_FAILED", str(exc))


@tool
def list_favorites(user_id: str):
    """查询当前用户收藏列表。"""
    try:
        uid = _uid(user_id)
        with Session(engine) as session:
            stmt = (
                select(Favorite)
                .where(Favorite.user_id == uid)
                .order_by(Favorite.created_time.desc())
            )
            items = list(session.exec(stmt).all())
            return _ok({"items": [_favorite_to_dict(item) for item in items]})
    except Exception as exc:
        return _err("FAVORITE_LIST_FAILED", str(exc))


@tool
def add_favorite(
    user_id: str,
    chat_message_id: int,
    note: str = "",
    confirm: bool = False,
):
    """收藏解析记录。confirm=false 时仅返回待确认动作。"""
    if not confirm:
        return _ok(
            {
                "pending_confirm": True,
                "chat_message_id": chat_message_id,
                "note": note or None,
            }
        )
    try:
        uid = _uid(user_id)
        with Session(engine) as session:
            msg = session.get(ChatMessage, chat_message_id)
            if not msg or msg.user_id != uid or msg.is_deleted:
                return _err("MESSAGE_NOT_FOUND", "Message not found")

            existing = session.exec(
                select(Favorite).where(
                    Favorite.user_id == uid,
                    Favorite.chat_message_id == chat_message_id,
                )
            ).first()
            if existing:
                return _ok({"item": _favorite_to_dict(existing), "pending_confirm": False})

            fav = Favorite(
                user_id=uid,
                chat_message_id=chat_message_id,
                note=(note or None),
            )
            session.add(fav)
            session.commit()
            session.refresh(fav)
            return _ok({"item": _favorite_to_dict(fav), "pending_confirm": False})
    except Exception as exc:
        return _err("FAVORITE_ADD_FAILED", str(exc))


@tool
def get_my_stats(user_id: str):
    """获取当前用户解析统计。"""
    try:
        uid = _uid(user_id)
        with Session(engine) as session:
            stats = stats_service.generate_user_stats(session, uid)
            return _ok({"item": stats})
    except Exception as exc:
        return _err("STATS_QUERY_FAILED", str(exc))


@tool
def rewrite_for_audience(
    user_id: str,
    message_id: int,
    target_audience: str,
    confirm: bool = False,
):
    """按人群改写历史消息。confirm=false 时仅返回待确认动作。"""
    if not target_audience:
        return _err("EMPTY_TARGET_AUDIENCE", "target_audience 不能为空。")
    if not confirm:
        return _ok(
            {
                "pending_confirm": True,
                "message_id": message_id,
                "target_audience": target_audience,
            }
        )
    try:
        uid = _uid(user_id)
        with Session(engine) as session:
            updated = chat_message_service.update_message_audience_via_ai(
                session=session,
                user_id=uid,
                message_id=message_id,
                new_audience=target_audience,
            )
            if not updated:
                return _err("MESSAGE_NOT_FOUND", "Message not found")
            return _ok({"item": _message_to_dict(updated), "pending_confirm": False})
    except Exception as exc:
        return _err("REWRITE_FAILED", str(exc))


tools = [
    query_long_term_memory,
    parse_local_file,
    get_my_todos,
    create_todos_from_chat,
    confirm_todo,
    search_policy_documents,
    recommend_policy_documents,
    get_user_settings,
    update_user_settings,
    search_chat_history,
    get_chat_message_detail,
    get_news_digest,
    search_news_tool,
    list_favorites,
    add_favorite,
    get_my_stats,
    rewrite_for_audience,
]
tool_node = ToolNode(tools)
