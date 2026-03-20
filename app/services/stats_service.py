import json
from collections import Counter
from typing import Any, Dict, List

import jieba
from sqlmodel import Session, select

from app.models.chat_message import ChatMessage


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


def _build_stats(messages: List[ChatMessage]) -> Dict[str, Any]:
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
    }


def generate_user_stats(session: Session, user_id: int) -> Dict[str, Any]:
    messages = list(session.exec(
        select(ChatMessage).where(
            ChatMessage.user_id == user_id,
            ChatMessage.is_deleted == False,
        )
    ).all())
    return _build_stats(messages)


def generate_all_users_stats(session: Session) -> Dict[str, Any]:
    messages = list(session.exec(
        select(ChatMessage).where(ChatMessage.is_deleted == False)
    ).all())
    return _build_stats(messages)
