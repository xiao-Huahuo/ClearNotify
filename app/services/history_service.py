import json
from datetime import datetime
from typing import Any, Iterable, Optional
from urllib.parse import urlencode

from sqlmodel import Session, select

from app.models.agent_conversation import AgentConversation
from app.models.chat_message import ChatMessage
from app.models.favorite import Favorite
from app.models.history_event import HistoryEvent
from app.models.policy_document import DocStatus, PolicyDocument
from app.models.todo import TodoItem


DOMAIN_LABELS = {
    "document_parse": "解析记录",
    "agent_chat": "智能体对话",
    "policy_publish": "政策发布",
    "policy_browse": "政策浏览",
    "article_browse": "文章浏览",
    "search": "搜索记录",
    "favorite": "收藏记录",
    "todo": "待办记录",
}


def _compact_text(value: Any, limit: int = 220) -> str:
    text = " ".join(str(value or "").split()).strip()
    if not text:
        return ""
    return text if len(text) <= limit else f"{text[: limit - 3]}..."


def _json_dump(payload: dict[str, Any]) -> str:
    return json.dumps(payload or {}, ensure_ascii=False)


def _json_load(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        data = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _build_search_text(parts: Iterable[Any]) -> str:
    normalized: list[str] = []
    seen: set[str] = set()
    for part in parts:
        text = _compact_text(part, limit=600)
        if not text:
            continue
        lowered = text.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        normalized.append(text)
    return "\n".join(normalized)


def serialize_event(event: HistoryEvent) -> dict[str, Any]:
    data = event.model_dump()
    data["extra"] = _json_load(event.extra_json)
    data.pop("extra_json", None)
    return data


def record_event(
    session: Session,
    *,
    user_id: int,
    domain: str,
    event_type: str,
    subject_type: str,
    title: str,
    actor_user_id: Optional[int] = None,
    subject_id: Optional[int] = None,
    subtitle: Optional[str] = None,
    summary: Optional[str] = None,
    content_excerpt: Optional[str] = None,
    route_path: Optional[str] = None,
    external_url: Optional[str] = None,
    icon: Optional[str] = None,
    status: Optional[str] = None,
    is_restorable: bool = False,
    visibility: str = "private",
    dedupe_key: Optional[str] = None,
    occurred_time: Optional[datetime] = None,
    search_text: str = "",
    extra: Optional[dict[str, Any]] = None,
    commit: bool = True,
) -> HistoryEvent:
    existing = None
    if dedupe_key:
        existing = session.exec(
            select(HistoryEvent).where(
                HistoryEvent.user_id == user_id,
                HistoryEvent.dedupe_key == dedupe_key,
            )
        ).first()
    if existing:
        if commit:
            from app.services import search_index_service

            search_index_service.upsert_history_event(session, existing, commit=True)
        return existing

    event = HistoryEvent(
        user_id=user_id,
        actor_user_id=actor_user_id,
        domain=domain,
        event_type=event_type,
        subject_type=subject_type,
        subject_id=subject_id,
        title=_compact_text(title, limit=180) or DOMAIN_LABELS.get(domain, "历史记录"),
        subtitle=_compact_text(subtitle, limit=120) or None,
        summary=_compact_text(summary, limit=240) or None,
        content_excerpt=_compact_text(content_excerpt, limit=400) or None,
        route_path=route_path,
        external_url=external_url,
        icon=icon,
        status=status,
        is_restorable=is_restorable,
        visibility=visibility,
        dedupe_key=dedupe_key,
        occurred_time=occurred_time or datetime.now(),
        search_text=_compact_text(search_text, limit=800),
        extra_json=_json_dump(extra or {}),
    )
    session.add(event)
    if commit:
        session.commit()
        session.refresh(event)
        from app.services import search_index_service

        search_index_service.upsert_history_event(session, event, commit=True)
    return event


def list_events(
    session: Session,
    *,
    user_id: int,
    domain: Optional[str] = None,
    q: str = "",
    skip: int = 0,
    limit: int = 30,
) -> list[HistoryEvent]:
    statement = select(HistoryEvent).where(HistoryEvent.user_id == user_id)
    if domain and domain != "all":
        statement = statement.where(HistoryEvent.domain == domain)
    items = list(session.exec(statement).all())
    if q.strip():
        keyword = q.strip().lower()
        items = [
            item
            for item in items
            if keyword in (item.title or "").lower()
            or keyword in (item.summary or "").lower()
            or keyword in (item.search_text or "").lower()
        ]
    items.sort(key=lambda item: item.occurred_time, reverse=True)
    return items[skip : skip + limit]


def _matches_event_query(event: HistoryEvent, query: str) -> bool:
    keyword = query.strip().lower()
    if not keyword:
        return True
    return (
        keyword in (event.title or "").lower()
        or keyword in (event.summary or "").lower()
        or keyword in (event.search_text or "").lower()
    )


def list_recent_search_events(
    session: Session,
    *,
    user_id: int,
    limit: int = 6,
    q: str = "",
) -> list[HistoryEvent]:
    items = list(
        session.exec(
            select(HistoryEvent).where(
                HistoryEvent.user_id == user_id,
                HistoryEvent.domain == "search",
                HistoryEvent.event_type == "searched",
            )
        ).all()
    )
    items.sort(key=lambda item: item.occurred_time, reverse=True)

    results: list[HistoryEvent] = []
    seen: set[str] = set()
    for item in items:
        if not _matches_event_query(item, q):
            continue
        dedupe_key = (item.title or "").strip().lower()
        if not dedupe_key or dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        results.append(item)
        if len(results) >= limit:
            break
    return results


def list_recent_history_events(
    session: Session,
    *,
    user_id: int,
    limit: int = 6,
    q: str = "",
) -> list[HistoryEvent]:
    items = list(
        session.exec(
            select(HistoryEvent).where(
                HistoryEvent.user_id == user_id,
                HistoryEvent.domain != "search",
            )
        ).all()
    )
    items.sort(key=lambda item: item.occurred_time, reverse=True)

    results: list[HistoryEvent] = []
    seen: set[str] = set()
    for item in items:
        if not _matches_event_query(item, q):
            continue
        dedupe_key = "|".join(
            [
                item.domain or "",
                item.event_type or "",
                item.subject_type or "",
                str(item.subject_id or ""),
                (item.title or "").strip().lower(),
                (item.route_path or "").strip().lower(),
                (item.external_url or "").strip().lower(),
            ]
        )
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        results.append(item)
        if len(results) >= limit:
            break
    return results


def get_facets(session: Session, *, user_id: int) -> dict[str, int]:
    items = list(session.exec(select(HistoryEvent).where(HistoryEvent.user_id == user_id)).all())
    counts: dict[str, int] = {"all": len(items)}
    for item in items:
        counts[item.domain] = counts.get(item.domain, 0) + 1
    return counts


def record_search_event(
    session: Session,
    *,
    user_id: int,
    query: str,
    source: str = "search_page",
    result_count: Optional[int] = None,
    types: Optional[list[str]] = None,
) -> Optional[HistoryEvent]:
    cleaned_query = _compact_text(query, limit=120)
    if not cleaned_query:
        return None
    normalized_types = [str(item).strip() for item in (types or []) if str(item).strip()]
    route_params = {"q": cleaned_query}
    if normalized_types:
        route_params["types"] = ",".join(normalized_types)
    type_key = ",".join(normalized_types) if normalized_types else "all"
    return record_event(
        session,
        user_id=user_id,
        domain="search",
        event_type="searched",
        subject_type="search_query",
        title=cleaned_query,
        summary=f"搜索: {cleaned_query}",
        route_path=f"/search?{urlencode(route_params)}",
        icon="search",
        dedupe_key=f"search:{user_id}:{source}:{type_key}:{cleaned_query.lower()}",
        search_text=cleaned_query,
        extra={
            "query": cleaned_query,
            "source": source,
            "result_count": result_count,
            "types": normalized_types,
        },
    )


def record_chat_message_event(
    session: Session,
    message: ChatMessage,
    *,
    event_type: str,
    actor_user_id: Optional[int] = None,
    dedupe_key: Optional[str] = None,
) -> HistoryEvent:
    title = message.handling_matter or message.target_audience or "通知解析"
    summary = message.target_audience or message.original_text
    return record_event(
        session,
        user_id=message.user_id,
        actor_user_id=actor_user_id,
        domain="document_parse",
        event_type=event_type,
        subject_type="chat_message",
        subject_id=message.id,
        title=title,
        subtitle=DOMAIN_LABELS["document_parse"],
        summary=summary,
        content_excerpt=message.original_text,
        route_path="/home",
        icon="history",
        is_restorable=True,
        dedupe_key=dedupe_key,
        occurred_time=message.created_time,
        search_text=_build_search_text(
            [
                message.handling_matter,
                message.target_audience,
                message.required_materials,
                message.risk_warnings,
                message.original_text,
            ]
        ),
        extra={"chat_message_id": message.id},
    )


def record_agent_conversation_event(
    session: Session,
    convo: AgentConversation,
    *,
    event_type: str,
    actor_user_id: Optional[int] = None,
    summary: Optional[str] = None,
    dedupe_key: Optional[str] = None,
    occurred_time: Optional[datetime] = None,
    extra: Optional[dict[str, Any]] = None,
) -> HistoryEvent:
    return record_event(
        session,
        user_id=convo.user_id,
        actor_user_id=actor_user_id,
        domain="agent_chat",
        event_type=event_type,
        subject_type="agent_conversation",
        subject_id=convo.id,
        title=convo.title,
        subtitle=DOMAIN_LABELS["agent_chat"],
        summary=summary or "继续智能体对话",
        route_path=f"/agent?conversation_id={convo.id}",
        icon="agent",
        is_restorable=True,
        dedupe_key=dedupe_key,
        occurred_time=occurred_time or convo.updated_time,
        search_text=_build_search_text([convo.title, summary]),
        extra={"conversation_id": convo.id, **(extra or {})},
    )


def record_policy_document_event(
    session: Session,
    doc: PolicyDocument,
    *,
    event_type: str,
    user_id: Optional[int] = None,
    actor_user_id: Optional[int] = None,
    dedupe_key: Optional[str] = None,
    occurred_time: Optional[datetime] = None,
    summary: Optional[str] = None,
) -> HistoryEvent:
    owner_user_id = user_id or doc.uploader_id
    return record_event(
        session,
        user_id=owner_user_id,
        actor_user_id=actor_user_id,
        domain="policy_publish" if event_type in {"created", "approved", "rejected"} else "policy_browse",
        event_type=event_type,
        subject_type="policy_document",
        subject_id=doc.id,
        title=doc.title,
        subtitle=doc.category or DOMAIN_LABELS.get("policy_publish"),
        summary=summary or _compact_text(doc.content, limit=200),
        content_excerpt=doc.content,
        route_path=f"/policy-swipe?doc_id={doc.id}",
        icon="policy",
        status=str(doc.status),
        dedupe_key=dedupe_key,
        occurred_time=occurred_time or doc.reviewed_time or doc.created_time,
        search_text=_build_search_text([doc.title, doc.category, doc.tags, doc.content]),
        extra={"policy_document_id": doc.id},
    )


def record_favorite_event(
    session: Session,
    *,
    favorite: Favorite,
    message: ChatMessage,
    event_type: str,
    dedupe_key: Optional[str] = None,
) -> HistoryEvent:
    note = favorite.note or message.handling_matter or "解析收藏"
    return record_event(
        session,
        user_id=favorite.user_id,
        domain="favorite",
        event_type=event_type,
        subject_type="favorite",
        subject_id=favorite.id,
        title=note,
        subtitle=DOMAIN_LABELS["favorite"],
        summary=message.original_text,
        route_path="/favorites",
        icon="favorite",
        dedupe_key=dedupe_key,
        occurred_time=favorite.created_time,
        search_text=_build_search_text([note, message.original_text]),
        extra={"chat_message_id": favorite.chat_message_id},
    )


def record_todo_event(
    session: Session,
    *,
    todo: TodoItem,
    event_type: str,
    dedupe_key: Optional[str] = None,
) -> HistoryEvent:
    summary = todo.detail or todo.deadline or "待办事项更新"
    return record_event(
        session,
        user_id=todo.user_id,
        domain="todo",
        event_type=event_type,
        subject_type="todo",
        subject_id=todo.id,
        title=todo.title,
        subtitle=DOMAIN_LABELS["todo"],
        summary=summary,
        route_path="/todo",
        icon="todo",
        status="done" if todo.is_done else ("confirmed" if todo.is_confirmed else "draft"),
        dedupe_key=dedupe_key,
        occurred_time=todo.updated_time if event_type != "created" else todo.created_time,
        search_text=_build_search_text([todo.title, todo.detail, todo.deadline]),
        extra={"todo_id": todo.id},
    )


def backfill_core_history(session: Session) -> int:
    existing_keys = {
        item
        for item in session.exec(select(HistoryEvent.dedupe_key).where(HistoryEvent.dedupe_key.is_not(None))).all()
        if item
    }
    created = 0

    def add_if_missing(key: str, factory) -> None:
        nonlocal created
        if key in existing_keys:
            return
        factory()
        existing_keys.add(key)
        created += 1

    for message in session.exec(select(ChatMessage).where(ChatMessage.is_deleted == False)).all():
        add_if_missing(
            f"chat:create:{message.id}",
            lambda message=message: record_chat_message_event(
                session,
                message,
                event_type="created",
                dedupe_key=f"chat:create:{message.id}",
                actor_user_id=message.user_id,
                ),
        )

    for convo in session.exec(select(AgentConversation)).all():
        add_if_missing(
            f"agent:create:{convo.id}",
            lambda convo=convo: record_agent_conversation_event(
                session,
                convo,
                event_type="created",
                actor_user_id=convo.user_id,
                dedupe_key=f"agent:create:{convo.id}",
                occurred_time=convo.created_time,
            ),
        )

    for doc in session.exec(select(PolicyDocument)).all():
        add_if_missing(
            f"policy:create:{doc.id}",
            lambda doc=doc: record_policy_document_event(
                session,
                doc,
                event_type="created",
                user_id=doc.uploader_id,
                actor_user_id=doc.uploader_id,
                dedupe_key=f"policy:create:{doc.id}",
                occurred_time=doc.created_time,
            ),
        )
        if doc.status == DocStatus.approved and doc.reviewed_time:
            add_if_missing(
                f"policy:approved:{doc.id}",
                lambda doc=doc: record_policy_document_event(
                    session,
                    doc,
                    event_type="approved",
                    user_id=doc.uploader_id,
                    dedupe_key=f"policy:approved:{doc.id}",
                    occurred_time=doc.reviewed_time,
                    summary="政策文档已审核通过",
                ),
            )
        if doc.status == DocStatus.rejected and doc.reviewed_time:
            add_if_missing(
                f"policy:rejected:{doc.id}",
                lambda doc=doc: record_policy_document_event(
                    session,
                    doc,
                    event_type="rejected",
                    user_id=doc.uploader_id,
                    dedupe_key=f"policy:rejected:{doc.id}",
                    occurred_time=doc.reviewed_time,
                    summary="政策文档已驳回",
                ),
            )

    favorites = list(session.exec(select(Favorite)).all())
    message_map = {
        item.id: item
        for item in session.exec(select(ChatMessage).where(ChatMessage.is_deleted == False)).all()
    }
    for favorite in favorites:
        message = message_map.get(favorite.chat_message_id)
        if not message:
            continue
        add_if_missing(
            f"favorite:add:{favorite.id}",
            lambda favorite=favorite, message=message: record_favorite_event(
                session,
                favorite=favorite,
                message=message,
                event_type="added",
                dedupe_key=f"favorite:add:{favorite.id}",
            ),
        )

    for todo in session.exec(select(TodoItem)).all():
        add_if_missing(
            f"todo:create:{todo.id}",
            lambda todo=todo: record_todo_event(
                session,
                todo=todo,
                event_type="created",
                dedupe_key=f"todo:create:{todo.id}",
            ),
        )
        if todo.is_confirmed:
            add_if_missing(
                f"todo:confirm:{todo.id}",
                lambda todo=todo: record_todo_event(
                    session,
                    todo=todo,
                    event_type="confirmed",
                    dedupe_key=f"todo:confirm:{todo.id}",
                ),
            )
        if todo.is_done:
            add_if_missing(
                f"todo:complete:{todo.id}",
                lambda todo=todo: record_todo_event(
                    session,
                    todo=todo,
                    event_type="completed",
                    dedupe_key=f"todo:complete:{todo.id}",
                ),
            )

    if created:
        session.commit()
    return created
