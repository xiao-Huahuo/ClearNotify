import json
from collections import Counter
from typing import Any, Dict, List

import jieba
from sqlmodel import Session, select

from app.models.chat_message import ChatMessage
from app.models.rag_usage import RagUsage
from app.services import rag_service


STOP_WORDS = {
    "的",
    "了",
    "和",
    "是",
    "就",
    "都",
    "而",
    "及",
    "与",
    "着",
    "或",
    "一个",
    "没有",
    "我们",
    "你们",
    "他们",
    "这",
    "那",
    "有",
    "在",
    "需要",
    "提供",
    "原件",
    "复印件",
    "提交",
    "相关",
    "办理",
    "申请",
    "证明",
    "必须",
    "或者",
    "以及",
    "本人",
    "材料",
    "并",
    "等",
    "进行",
    "可以",
    "请",
    "带上",
    "出具",
    "复印",
    "要求",
}


def extract_keywords_from_texts(texts: List[str], top_n: int = 20) -> Dict[str, int]:
    if not texts:
        return {}

    combined_text = " ".join(
        str(text)
        for text in texts
        if text and str(text).strip() not in {"None", "无"}
    )
    if not combined_text:
        return {}

    words = jieba.cut(combined_text)
    filtered_words = [
        word.strip()
        for word in words
        if len(word.strip()) > 1 and word.strip() not in STOP_WORDS
    ]

    return dict(Counter(filtered_words).most_common(top_n))


def estimate_time_saved(messages: List[ChatMessage]) -> Dict[str, Any]:
    total_saved = 0
    distribution: Dict[str, int] = {}

    sorted_messages = sorted(messages, key=lambda msg: msg.created_time)
    for idx, message in enumerate(sorted_messages, start=1):
        word_count = len(message.original_text) if message.original_text else 0
        read_time_original = max(word_count / 150, 3)
        saved = max(int(read_time_original - 1), 2)
        saved = min(saved, 30)

        total_saved += saved
        distribution[f"第{idx}次"] = saved

    avg_saved = int(total_saved / len(messages)) if messages else 0
    return {
        "total_time_saved_minutes": total_saved,
        "avg_time_saved_minutes": avg_saved,
        "time_saved_distribution": distribution,
    }


def aggregate_analysis_data(messages: List[ChatMessage]) -> Dict[str, Any]:
    complexity_dist = {
        "language_complexity": {"高": 0, "中": 0, "低": 0},
        "handling_complexity": {"高": 0, "中": 0, "低": 0},
        "risk_level": {"高": 0, "中": 0, "低": 0},
    }
    notice_type_dist: Counter[str] = Counter()

    for message in messages:
        if not message.chat_analysis:
            continue

        try:
            analysis = json.loads(message.chat_analysis)
        except (json.JSONDecodeError, TypeError):
            continue

        for key, default_level in (
            ("language_complexity", "中"),
            ("handling_complexity", "中"),
            ("risk_level", "低"),
        ):
            level = analysis.get(key, default_level)
            if level in complexity_dist[key]:
                complexity_dist[key][level] += 1

        notice_type = analysis.get("notice_type")
        if notice_type:
            notice_type_dist[notice_type] += 1

    flattened_complexity = {
        f"{category}-{level}": count
        for category, levels in complexity_dist.items()
        for level, count in levels.items()
    }

    return {
        "flattened_complexity": flattened_complexity,
        "notice_type_distribution": dict(notice_type_dist.most_common(5)),
    }


def _parse_chat_analysis(raw: Any) -> Dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return {}


def _empty_rag_payload() -> Dict[str, Any]:
    return {
        "rag_metrics": {
            "query_count": 0,
            "hit_rate": 0,
            "avg_score": 0,
            "empty_rate": 0,
        },
        "rag_series": {},
    }


def _build_rag_stats_from_usage(
    usages: List[RagUsage],
    mode: str,
) -> Dict[str, Any]:
    if not usages:
        return _empty_rag_payload()

    total = len(usages)
    hits = sum(1 for item in usages if (item.result_count or 0) > 0)
    score_sum = sum(float(item.avg_score or 0) for item in usages)
    hit_rate_total = hits / max(total, 1)
    avg_score_total = score_sum / max(total, 1)

    rag_series: Dict[str, Dict[str, float]] = {}
    if mode == "sequence":
        ordered = sorted(usages, key=lambda item: item.created_time)
        for idx, item in enumerate(ordered, start=1):
            rag_series[str(idx)] = {
                "count": 1,
                "hit_rate": 1.0 if (item.result_count or 0) > 0 else 0.0,
                "avg_score": round(float(item.avg_score or 0), 3),
            }
    elif mode == "hour":
        series_bucket: Dict[str, Dict[str, float]] = {}
        for item in usages:
            hour_key = item.created_time.replace(
                minute=0, second=0, microsecond=0
            ).strftime("%Y-%m-%d %H:00")
            bucket = series_bucket.setdefault(hour_key, {"count": 0, "hits": 0, "score_sum": 0.0})
            bucket["count"] += 1
            bucket["hits"] += 1 if (item.result_count or 0) > 0 else 0
            bucket["score_sum"] += float(item.avg_score or 0)

        for hour_key in sorted(series_bucket.keys()):
            bucket = series_bucket[hour_key]
            count = max(int(bucket["count"]), 1)
            rag_series[hour_key] = {
                "count": int(bucket["count"]),
                "hit_rate": round(bucket["hits"] / count, 3),
                "avg_score": round(bucket["score_sum"] / count, 3),
            }

    return {
        "rag_metrics": {
            "query_count": total,
            "hit_rate": round(hit_rate_total, 3),
            "avg_score": round(avg_score_total, 3),
            "empty_rate": round(1 - hit_rate_total, 3),
        },
        "rag_series": rag_series,
    }


def _build_vector_scatter(messages: List[ChatMessage], limit: int = 120) -> List[Dict[str, Any]]:
    if not messages:
        return []
    recent = sorted(messages, key=lambda msg: msg.created_time, reverse=True)[:limit]
    points: List[Dict[str, Any]] = []
    for message in recent:
        analysis = _parse_chat_analysis(message.chat_analysis)
        difficulty = max(
            1,
            3 if analysis.get("language_complexity") == "高" else 1,
            2 if analysis.get("language_complexity") == "中" else 1,
            3 if analysis.get("handling_complexity") == "高" else 1,
            2 if analysis.get("handling_complexity") == "中" else 1,
            3 if analysis.get("risk_level") == "高" else 1,
            2 if analysis.get("risk_level") == "中" else 1,
        )
        word_count = len(message.original_text or "")
        materials_count = len(str(message.required_materials or "").split("、")) if message.required_materials else 0
        points.append(
            {
                "x": word_count,
                "y": difficulty,
                "size": min(8 + materials_count * 3, 28),
                "label": analysis.get("notice_type") or "其他",
            }
        )
    return points


def _build_rag_query_from_message(message: ChatMessage) -> str:
    return "\n".join(
        filter(
            None,
            [
                message.handling_matter,
                message.required_materials,
                message.risk_warnings,
                message.original_text[:500] if message.original_text else "",
            ],
        )
    )


def _build_stats(messages: List[ChatMessage], rag_payload: Dict[str, Any]) -> Dict[str, Any]:
    total_count = len(messages)
    if total_count == 0:
        return {
            "total_parsed_count": 0,
            "materials_freq": {},
            "risks_freq": {},
            "complexity_distribution": {},
            "notice_type_distribution": {},
            "total_time_saved_minutes": 0,
            "avg_time_saved_minutes": 0,
            "time_saved_distribution": {},
            "rag_metrics": rag_payload.get("rag_metrics", {}),
            "rag_series": rag_payload.get("rag_series", {}),
            "vector_scatter": [],
        }

    materials_texts = [
        message.required_materials for message in messages if message.required_materials
    ]
    risks_texts = [message.risk_warnings for message in messages if message.risk_warnings]

    time_stats = estimate_time_saved(messages)
    analysis_agg = aggregate_analysis_data(messages)

    return {
        "total_parsed_count": total_count,
        "materials_freq": extract_keywords_from_texts(materials_texts, top_n=20),
        "risks_freq": extract_keywords_from_texts(risks_texts, top_n=10),
        "complexity_distribution": analysis_agg["flattened_complexity"],
        "notice_type_distribution": analysis_agg["notice_type_distribution"],
        "total_time_saved_minutes": time_stats["total_time_saved_minutes"],
        "avg_time_saved_minutes": time_stats["avg_time_saved_minutes"],
        "time_saved_distribution": time_stats["time_saved_distribution"],
        "rag_metrics": rag_payload["rag_metrics"],
        "rag_series": rag_payload["rag_series"],
        "vector_scatter": _build_vector_scatter(messages),
    }


def generate_user_stats(session: Session, user_id: int) -> Dict[str, Any]:
    messages = list(session.exec(
        select(ChatMessage).where(
            ChatMessage.user_id == user_id,
            ChatMessage.is_deleted == False,
        )
    ).all())
    usages = list(session.exec(
        select(RagUsage).where(RagUsage.user_id == user_id)
    ).all())
    if not usages and messages:
        recent = sorted(messages, key=lambda msg: msg.created_time, reverse=True)[:20]
        for message in recent:
            query = _build_rag_query_from_message(message)
            if not query.strip():
                continue
            try:
                rag_service.search_related_context(
                    query,
                    top_k=3,
                    user_id=user_id,
                    source="stats_backfill",
                )
            except Exception:
                pass
        usages = list(session.exec(
            select(RagUsage).where(RagUsage.user_id == user_id)
        ).all())
    rag_payload = _build_rag_stats_from_usage(usages, mode="sequence")
    return _build_stats(messages, rag_payload)


def generate_all_users_stats(session: Session) -> Dict[str, Any]:
    messages = list(session.exec(
        select(ChatMessage).where(ChatMessage.is_deleted == False)
    ).all())
    usages = list(session.exec(select(RagUsage)).all())
    rag_payload = _build_rag_stats_from_usage(usages, mode="hour")
    return _build_stats(messages, rag_payload)
