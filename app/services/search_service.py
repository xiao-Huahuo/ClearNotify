from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np
from sqlmodel import Session, or_, select

from app.models.history_event import HistoryEvent
from app.models.search_index_item import SearchIndexItem
from app.models.user import User
from app.services.news_crawler import get_central_docs, get_hot_news
from app.services.search_vector_service import deserialize_embedding, encode_text

SOURCE_TERMS = {
    "history": ["history", "record", "parse", "历史", "记录", "解析", "办理"],
    "agent": ["agent", "conversation", "chat", "智能体", "对话", "会话"],
    "policy": ["policy", "document", "政策", "文件", "政策文档"],
    "news": ["news", "article", "新闻", "文章", "时事"],
}

DOMAIN_TERMS = {
    "document_parse": ["document_parse", "parse", "解析", "办理", "通知"],
    "agent_chat": ["agent", "conversation", "智能体", "对话", "会话"],
    "policy_publish": ["policy", "publish", "政策", "发布", "审核"],
    "policy_browse": ["policy", "browse", "政策", "浏览"],
    "article_browse": ["article", "news", "文章", "新闻", "时事"],
    "favorite": ["favorite", "收藏", "收藏夹"],
    "todo": ["todo", "待办", "任务", "清单"],
    "search": ["search", "搜索", "检索"],
}

VALID_SOURCE_TYPES = frozenset(SOURCE_TERMS.keys())
SOURCE_TYPE_ALIASES = {
    "history": "history",
    "record": "history",
    "records": "history",
    "agent": "agent",
    "agents": "agent",
    "chat": "agent",
    "conversation": "agent",
    "conversations": "agent",
    "policy": "policy",
    "policies": "policy",
    "document": "policy",
    "documents": "policy",
    "news": "news",
    "article": "news",
    "articles": "news",
}


@dataclass
class SearchCandidate:
    source_type: str
    title: str
    action_type: str
    domain: Optional[str] = None
    subtitle: Optional[str] = None
    description: Optional[str] = None
    route_path: Optional[str] = None
    external_url: Optional[str] = None
    subject_type: Optional[str] = None
    subject_id: Optional[int] = None
    published_at: Optional[str] = None
    extra: dict[str, Any] = field(default_factory=dict)
    searchable_text: str = ""
    embedding: Optional[np.ndarray] = None


def _normalize_text(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


def _lower_text(value: Any) -> str:
    return _normalize_text(value).lower()


def _compact_text(value: Any, limit: int = 240) -> str:
    text = _normalize_text(value)
    if not text:
        return ""
    return text if len(text) <= limit else f"{text[: limit - 3]}..."


def normalize_source_types(types: Any) -> list[str]:
    if not types:
        return []

    raw_values = types if isinstance(types, list) else [types]
    normalized: list[str] = []
    seen: set[str] = set()

    for raw_value in raw_values:
        for part in str(raw_value or "").replace("|", ",").split(","):
            key = _lower_text(part)
            if not key:
                continue
            mapped = SOURCE_TYPE_ALIASES.get(key, key if key in VALID_SOURCE_TYPES else "")
            if not mapped or mapped in seen:
                continue
            seen.add(mapped)
            normalized.append(mapped)

    return normalized


def _load_extra_json(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _build_searchable_text(parts: list[Any]) -> str:
    normalized: list[str] = []
    seen: set[str] = set()
    for part in parts:
        text = _normalize_text(part)
        if not text:
            continue
        lowered = text.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        normalized.append(text)
    return "\n".join(normalized)


def _build_candidate(**kwargs) -> SearchCandidate:
    candidate = SearchCandidate(**kwargs)
    candidate.searchable_text = _build_searchable_text(
        [
            candidate.title,
            candidate.subtitle,
            candidate.description,
            *SOURCE_TERMS.get(candidate.source_type, []),
            *DOMAIN_TERMS.get(candidate.domain or "", []),
            candidate.route_path,
            candidate.external_url,
            *(candidate.extra.values() if candidate.extra else []),
        ]
    )
    return candidate


def _matches_selected_types(source_type: str, selected_types: list[str] | None) -> bool:
    return not selected_types or source_type in selected_types


def _stored_index_candidates(session: Session, current_user: User | None) -> list[SearchCandidate]:
    statement = select(SearchIndexItem)
    if current_user:
        statement = statement.where(
            or_(
                SearchIndexItem.visibility == "public",
                SearchIndexItem.owner_user_id == current_user.uid,
            )
        )
    else:
        statement = statement.where(SearchIndexItem.visibility == "public")

    items = session.exec(
        statement.order_by(SearchIndexItem.updated_time.desc()).limit(600)
    ).all()

    candidates: list[SearchCandidate] = []
    for item in items:
        extra = _load_extra_json(item.extra_json)
        candidate = _build_candidate(
            source_type=item.result_type,
            title=item.title,
            domain=item.domain,
            subtitle=item.subtitle,
            description=item.summary or _compact_text(item.body, limit=240),
            action_type=item.action_type,
            route_path=item.route_path,
            external_url=item.external_url,
            subject_type=item.subject_type,
            subject_id=item.subject_id,
            published_at=item.published_at.isoformat() if item.published_at else None,
            extra=extra,
        )
        candidate.embedding = deserialize_embedding(item.embedding_json)
        if item.search_text:
            candidate.searchable_text = item.search_text
        candidates.append(candidate)
    return candidates


def _external_policy_candidates(limit: int = 24) -> list[SearchCandidate]:
    items = get_central_docs(limit) or []
    return [
        _build_candidate(
            source_type="policy",
            title=item.get("title") or "中央文件",
            domain="policy_browse",
            subtitle="中央文件",
            description=_compact_text(item.get("description"), limit=240),
            action_type="external",
            external_url=item.get("link"),
            subject_type="external_policy_article",
            published_at=item.get("pubDate"),
            extra={"publisher": "gov.cn"},
        )
        for item in items[:limit]
    ]


def _external_news_candidates(limit: int = 30) -> list[SearchCandidate]:
    items = get_hot_news(limit) or []
    return [
        _build_candidate(
            source_type="news",
            title=item.get("title") or "时事热点",
            domain="article_browse",
            subtitle="时事热点",
            description=_compact_text(item.get("description"), limit=240),
            action_type="external",
            external_url=item.get("link"),
            subject_type="news_article",
            published_at=item.get("pubDate"),
        )
        for item in items[:limit]
    ]


def _dedupe_candidates(candidates: list[SearchCandidate]) -> list[SearchCandidate]:
    results: list[SearchCandidate] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = "|".join(
            [
                candidate.source_type,
                str(candidate.subject_id or ""),
                _lower_text(candidate.title),
                _lower_text(candidate.external_url),
                _lower_text(candidate.route_path),
            ]
        )
        if key in seen:
            continue
        seen.add(key)
        results.append(candidate)
    return results


def _semantic_similarity(query: str, candidate: SearchCandidate) -> float:
    query_vec = encode_text(query)
    candidate_vec = (
        candidate.embedding
        if candidate.embedding is not None
        else encode_text(candidate.searchable_text)
    )
    if query_vec is None or candidate_vec is None:
        return 0.0
    return float(np.dot(query_vec, candidate_vec))


def _lexical_score(query: str, candidate: SearchCandidate) -> tuple[float, str]:
    normalized_query = _lower_text(query)
    if not normalized_query:
        return 0.0, "none"

    title = _lower_text(candidate.title)
    text = _lower_text(candidate.searchable_text)
    tokens = [token for token in normalized_query.split(" ") if token] or [normalized_query]

    prefix_score = 0.0
    if title.startswith(normalized_query):
        prefix_score = 1.7
    elif any(part.startswith(normalized_query) for part in title.split(" ")):
        prefix_score = 1.2

    substring_score = 1.0 if normalized_query in text else 0.0
    token_hits = sum(1 for token in tokens if token in text)
    token_score = token_hits / max(len(tokens), 1)

    score = prefix_score + substring_score + token_score
    if prefix_score:
        matched_by = "prefix"
    elif substring_score or token_score:
        matched_by = "lexical"
    else:
        matched_by = "none"
    return score, matched_by


def _contains_any(query: str, terms: list[str]) -> bool:
    return any(term in query for term in terms)


def _query_length(query: str) -> int:
    return len(_normalize_text(query).replace(" ", ""))


def _semantic_threshold(query: str, lexical_score: float) -> float:
    if lexical_score > 0:
        return 0.24

    query_len = _query_length(query)
    if query_len <= 2:
        return 0.28
    if query_len <= 4:
        return 0.32
    return 0.4


def _intent_boost(query: str, candidate: SearchCandidate) -> float:
    lowered = _lower_text(query)
    if not lowered:
        return 0.0

    boost = 0.0

    if _contains_any(lowered, ["政策", "政策文档", "文件", "政务", "发布", "审核", "policy", "document"]):
        if candidate.source_type == "policy":
            boost += 0.75
        elif candidate.domain in {"policy_publish", "policy_browse"}:
            boost += 0.45
        elif candidate.domain == "document_parse":
            boost -= 0.2

    if _contains_any(lowered, ["智能体", "对话", "会话", "聊天", "agent", "chat", "conversation"]):
        if candidate.source_type == "agent" or candidate.domain == "agent_chat":
            boost += 0.75
        elif candidate.source_type == "history":
            boost -= 0.12

    if _contains_any(lowered, ["收藏", "收藏夹", "favorite"]):
        if candidate.domain == "favorite":
            boost += 0.9
        else:
            boost -= 0.18

    if _contains_any(lowered, ["待办", "任务", "清单", "todo"]):
        if candidate.domain == "todo":
            boost += 0.85
        elif candidate.domain == "document_parse":
            boost -= 0.18

    if _contains_any(lowered, ["解析", "办理", "文档", "通知", "history", "record", "parse"]):
        if candidate.domain == "document_parse":
            boost += 0.7
        elif candidate.source_type == "history":
            boost += 0.2

    if _contains_any(lowered, ["搜索", "检索", "查过", "search"]):
        if candidate.domain == "search":
            boost += 0.85

    if _contains_any(lowered, ["新闻", "文章", "时事", "news", "article"]):
        if candidate.source_type == "news" or candidate.domain == "article_browse":
            boost += 0.72

    if _contains_any(lowered, ["食品", "食物", "餐饮", "饮食", "吃"]):
        if _contains_any(_lower_text(candidate.searchable_text), ["食品", "食物", "餐饮", "饮食", "吃"]):
            boost += 0.2

    return boost


def _score_candidate(query: str, candidate: SearchCandidate) -> tuple[float, str]:
    lexical_score, lexical_mode = _lexical_score(query, candidate)
    semantic_score = _semantic_similarity(query, candidate)
    intent_boost = _intent_boost(query, candidate)

    semantic_threshold = _semantic_threshold(query, lexical_score)
    if lexical_score <= 0 and semantic_score < semantic_threshold:
        return 0.0, "none"

    if lexical_score > 0 and semantic_score > 0.24:
        matched_by = "hybrid"
    elif lexical_score > 0:
        matched_by = lexical_mode
    else:
        matched_by = "semantic"

    total_score = lexical_score + max(semantic_score, 0.0) * 1.45 + intent_boost
    return total_score, matched_by


def collect_candidates(
    session: Session,
    current_user: User | None,
    selected_types: list[str] | None = None,
) -> list[SearchCandidate]:
    return _dedupe_candidates(
        [
            *_stored_index_candidates(session, current_user),
            *_external_policy_candidates(),
            *_external_news_candidates(),
        ]
    )


def _filter_candidates_by_types(
    candidates: list[SearchCandidate],
    selected_types: list[str] | None,
) -> list[SearchCandidate]:
    if not selected_types:
        return candidates
    return [candidate for candidate in candidates if _matches_selected_types(candidate.source_type, selected_types)]


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


def _history_event_to_item(event: HistoryEvent, *, group: str) -> dict[str, Any]:
    extra = {}
    try:
        extra = json.loads(event.extra_json or "{}")
    except (TypeError, json.JSONDecodeError):
        extra = {}
    if not isinstance(extra, dict):
        extra = {}

    return {
        "group": group,
        "source_type": _history_result_type(event),
        "title": event.title,
        "subtitle": event.subtitle,
        "description": event.summary or _compact_text(event.content_excerpt, limit=240),
        "action_type": _history_action_type(event),
        "route_path": event.route_path,
        "external_url": event.external_url,
        "subject_type": event.subject_type,
        "subject_id": event.subject_id,
        "published_at": event.occurred_time.isoformat() if event.occurred_time else None,
        "score": 0.0,
        "extra": {
            **extra,
            "event_type": event.event_type,
            "history_domain": event.domain,
        },
    }


def _item_dedupe_key(item: dict[str, Any]) -> str:
    return "|".join(
        [
            str(item.get("source_type") or ""),
            str(item.get("subject_type") or ""),
            str(item.get("subject_id") or ""),
            _lower_text(item.get("title")),
            _lower_text(item.get("route_path")),
            _lower_text(item.get("external_url")),
            str(item.get("action_type") or ""),
        ]
    )


def _merge_grouped_items(
    target: list[dict[str, Any]],
    *,
    seen: set[str],
    groups: dict[str, int],
    group: str,
    items: list[dict[str, Any]],
    limit: int,
) -> None:
    if not items:
        return
    groups[group] = len(items)
    for item in items:
        key = _item_dedupe_key(item)
        if key in seen:
            continue
        seen.add(key)
        target.append(item)
        if len(target) >= limit:
            break


def unified_search(
    session: Session,
    current_user: User | None,
    query: str,
    limit: int = 20,
    types: list[str] | None = None,
) -> list[dict[str, Any]]:
    cleaned_query = _normalize_text(query)
    if not cleaned_query:
        return []

    selected_types = normalize_source_types(types)
    results: list[dict[str, Any]] = []
    candidates = _filter_candidates_by_types(
        collect_candidates(session, current_user),
        selected_types,
    )
    for candidate in candidates:
        score, matched_by = _score_candidate(cleaned_query, candidate)
        if score <= 0:
            continue
        results.append(
            {
                "source_type": candidate.source_type,
                "title": candidate.title,
                "subtitle": candidate.subtitle,
                "description": candidate.description,
                "action_type": candidate.action_type,
                "route_path": candidate.route_path,
                "external_url": candidate.external_url,
                "subject_type": candidate.subject_type,
                "subject_id": candidate.subject_id,
                "published_at": candidate.published_at,
                "score": round(score, 4),
                "extra": {
                    **candidate.extra,
                    "matched_by": matched_by,
                },
            }
        )

    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:limit]


def suggest(
    session: Session,
    current_user: User | None,
    query: str,
    limit: int = 18,
    types: list[str] | None = None,
) -> dict[str, Any]:
    from app.services import history_service

    cleaned_query = _normalize_text(query)
    selected_types = normalize_source_types(types)
    grouped_items: list[dict[str, Any]] = []
    groups: dict[str, int] = {}
    seen: set[str] = set()

    if not cleaned_query:
        if current_user:
            recent_search = [
                _history_event_to_item(item, group="recent_search")
                for item in history_service.list_recent_search_events(
                    session,
                    user_id=current_user.uid,
                    limit=min(limit, 6),
                )
            ]
            _merge_grouped_items(
                grouped_items,
                seen=seen,
                groups=groups,
                group="recent_search",
                items=recent_search,
                limit=limit,
            )

            recent_history = [
                _history_event_to_item(item, group="recent_history")
                for item in history_service.list_recent_history_events(
                    session,
                    user_id=current_user.uid,
                    limit=min(limit, 8),
                )
            ]
            if selected_types:
                recent_history = [
                    item for item in recent_history if _matches_selected_types(item.get("source_type") or "", selected_types)
                ]
            _merge_grouped_items(
                grouped_items,
                seen=seen,
                groups=groups,
                group="recent_history",
                items=recent_history,
                limit=limit,
            )

        quick_access = [
            {
                **item,
                "group": "quick_access",
            }
            for item in suggestion_index(
                session,
                current_user,
                limit=max(limit, 12),
                types=selected_types,
            )
        ]
        _merge_grouped_items(
            grouped_items,
            seen=seen,
            groups=groups,
            group="quick_access",
            items=quick_access,
            limit=limit,
        )
        return {
            "query": "",
            "items": grouped_items[:limit],
            "groups": groups,
        }

    if current_user:
        recent_search = [
            _history_event_to_item(item, group="recent_search")
            for item in history_service.list_recent_search_events(
                session,
                user_id=current_user.uid,
                limit=3,
                q=cleaned_query,
            )
        ]
        _merge_grouped_items(
            grouped_items,
            seen=seen,
            groups=groups,
            group="recent_search",
            items=recent_search,
            limit=limit,
        )

        recent_history = [
            _history_event_to_item(item, group="recent_history")
            for item in history_service.list_recent_history_events(
                session,
                user_id=current_user.uid,
                limit=4,
                q=cleaned_query,
            )
        ]
        if selected_types:
            recent_history = [
                item for item in recent_history if _matches_selected_types(item.get("source_type") or "", selected_types)
            ]
        _merge_grouped_items(
            grouped_items,
            seen=seen,
            groups=groups,
            group="recent_history",
            items=recent_history,
            limit=limit,
        )

    semantic_items = [
        {
            **item,
            "group": "semantic",
        }
        for item in unified_search(
            session,
            current_user,
            cleaned_query,
            limit=max(limit * 2, 12),
            types=selected_types,
        )
    ]
    _merge_grouped_items(
        grouped_items,
        seen=seen,
        groups=groups,
        group="semantic",
        items=semantic_items,
        limit=limit,
    )

    return {
        "query": cleaned_query,
        "items": grouped_items[:limit],
        "groups": groups,
    }


def suggestion_index(
    session: Session,
    current_user: User | None,
    limit: int = 240,
    types: list[str] | None = None,
) -> list[dict[str, Any]]:
    source_priority = {"history": 0, "agent": 1, "policy": 2, "news": 3}
    selected_types = normalize_source_types(types)
    suggestions: list[dict[str, Any]] = []
    seen_labels: set[str] = set()

    for candidate in sorted(
        _filter_candidates_by_types(collect_candidates(session, current_user), selected_types),
        key=lambda item: (source_priority.get(item.source_type, 99), _lower_text(item.title)),
    ):
        label_key = f"{candidate.source_type}|{_lower_text(candidate.title)}|{candidate.action_type}"
        if label_key in seen_labels:
            continue
        seen_labels.add(label_key)
        suggestions.append(
            {
                "source_type": candidate.source_type,
                "title": candidate.title,
                "subtitle": candidate.subtitle,
                "description": candidate.description,
                "action_type": candidate.action_type,
                "route_path": candidate.route_path,
                "external_url": candidate.external_url,
                "subject_type": candidate.subject_type,
                "subject_id": candidate.subject_id,
                "published_at": candidate.published_at,
                "score": 0.0,
                "extra": candidate.extra,
            }
        )
        if len(suggestions) >= limit:
            break

    return suggestions
