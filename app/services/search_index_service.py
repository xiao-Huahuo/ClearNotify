from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Iterable

from sqlmodel import Session, select

from app.models.history_event import HistoryEvent
from app.models.policy_document import DocStatus, PolicyDocument
from app.models.search_index_item import SearchIndexItem
from app.services.search_vector_service import encode_text, serialize_embedding


def _compact_text(value: Any, limit: int = 400) -> str:
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
        text = _compact_text(part, limit=1200)
        if not text:
            continue
        lowered = text.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        normalized.append(text)
    return "\n".join(normalized)


def _build_embedding_text(parts: Iterable[Any], total_limit: int = 360) -> str:
    chunks: list[str] = []
    seen: set[str] = set()
    used = 0

    for part in parts:
        text = _compact_text(part, limit=180)
        if not text:
            continue
        lowered = text.lower()
        if lowered in seen:
            continue
        remaining = total_limit - used
        if remaining <= 0:
            break
        if len(text) > remaining:
            text = text[:remaining].strip()
        if not text:
            continue
        seen.add(lowered)
        chunks.append(text)
        used += len(text)

    return "\n".join(chunks)


def _history_result_type(event: HistoryEvent) -> str:
    if event.domain == "agent_chat":
        return "agent"
    if event.domain in {"policy_publish", "policy_browse"}:
        return "policy"
    if event.domain == "article_browse":
        return "news"
    return "history"


def _history_action_type(event: HistoryEvent) -> str:
    if event.external_url:
        return "external"
    if (
        event.subject_type == "chat_message"
        and event.is_restorable
        and event.event_type not in {"deleted", "batch_deleted"}
    ):
        return "restore_chat"
    return "route"


def _upsert_index_item(
    session: Session,
    *,
    dedupe_key: str,
    payload: dict[str, Any],
    commit: bool = True,
) -> SearchIndexItem:
    item = session.exec(
        select(SearchIndexItem).where(SearchIndexItem.dedupe_key == dedupe_key)
    ).first()

    payload = dict(payload)
    payload["dedupe_key"] = dedupe_key
    payload["updated_time"] = datetime.now()

    search_text = payload.get("search_text") or ""
    embedding_text = payload.pop("embedding_text", None) or search_text
    payload["embedding_json"] = serialize_embedding(encode_text(embedding_text))

    if item:
        for key, value in payload.items():
            setattr(item, key, value)
    else:
        item = SearchIndexItem(**payload)
        session.add(item)

    if commit:
        session.commit()
        session.refresh(item)
    return item


def upsert_history_event(
    session: Session,
    event: HistoryEvent,
    *,
    commit: bool = True,
) -> SearchIndexItem:
    extra = _json_load(event.extra_json)
    search_text = _build_search_text(
        [
            event.title,
            event.subtitle,
            event.summary,
            event.content_excerpt,
            event.search_text,
            extra.get("query"),
            extra.get("source"),
        ]
    )
    payload = {
        "source_type": "history_event",
        "source_id": event.id,
        "owner_user_id": event.user_id,
        "visibility": event.visibility or "private",
        "result_type": _history_result_type(event),
        "domain": event.domain,
        "action_type": _history_action_type(event),
        "subject_type": event.subject_type,
        "subject_id": event.subject_id,
        "title": event.title,
        "subtitle": event.subtitle,
        "summary": event.summary,
        "body": event.content_excerpt,
        "keywords": extra.get("query"),
        "route_path": event.route_path,
        "external_url": event.external_url,
        "icon": event.icon,
        "status": event.status,
        "published_at": event.occurred_time,
        "search_text": search_text,
        "embedding_text": _build_embedding_text(
            [
                event.title,
                event.subtitle,
                event.summary,
                event.content_excerpt,
                extra.get("query"),
                event.search_text,
            ]
        ),
        "extra_json": _json_dump(
            {
                **extra,
                "event_type": event.event_type,
                "domain": event.domain,
            }
        ),
    }
    return _upsert_index_item(
        session,
        dedupe_key=f"history_event:{event.id}",
        payload=payload,
        commit=commit,
    )


def upsert_policy_document(
    session: Session,
    doc: PolicyDocument,
    *,
    commit: bool = True,
) -> SearchIndexItem:
    visibility = "public" if doc.status == DocStatus.approved else "private"
    search_text = _build_search_text(
        [
            doc.title,
            doc.category,
            doc.tags,
            doc.content,
            doc.reject_reason,
            "policy",
            "document",
        ]
    )
    payload = {
        "source_type": "policy_document",
        "source_id": doc.id,
        "owner_user_id": doc.uploader_id,
        "visibility": visibility,
        "result_type": "policy",
        "domain": "policy_publish" if doc.status != DocStatus.approved else "policy",
        "action_type": "route",
        "subject_type": "policy_document",
        "subject_id": doc.id,
        "title": doc.title,
        "subtitle": doc.category or doc.status.value,
        "summary": _compact_text(doc.content, limit=260) or None,
        "body": doc.content,
        "keywords": doc.tags,
        "route_path": f"/policy-swipe?doc_id={doc.id}",
        "external_url": None,
        "icon": "policy",
        "status": doc.status.value,
        "published_at": doc.reviewed_time or doc.created_time,
        "search_text": search_text,
        "embedding_text": _build_embedding_text(
            [
                doc.title,
                doc.category,
                doc.tags,
                _compact_text(doc.content, limit=220),
                doc.reject_reason,
                "policy",
                "document",
            ]
        ),
        "extra_json": _json_dump(
            {
                "category": doc.category,
                "tags": doc.tags,
                "view_count": doc.view_count,
                "like_count": doc.like_count,
            }
        ),
    }
    return _upsert_index_item(
        session,
        dedupe_key=f"policy_document:{doc.id}",
        payload=payload,
        commit=commit,
    )


def backfill_search_index(session: Session) -> dict[str, int]:
    history_count = 0
    policy_count = 0

    for event in session.exec(select(HistoryEvent)).all():
        upsert_history_event(session, event, commit=False)
        history_count += 1

    for doc in session.exec(select(PolicyDocument)).all():
        upsert_policy_document(session, doc, commit=False)
        policy_count += 1

    if history_count or policy_count:
        session.commit()

    return {
        "history_events": history_count,
        "policy_documents": policy_count,
        "total": history_count + policy_count,
    }
