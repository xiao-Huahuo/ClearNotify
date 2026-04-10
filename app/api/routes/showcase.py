from collections import defaultdict
from datetime import datetime, timedelta
import ipaddress

from fastapi import APIRouter, Depends
from sqlmodel import Session, func, select

from app.core.database import get_session
from app.models.chat_message import ChatMessage
from app.models.opinion import Opinion
from app.models.policy_document import DocStatus, PolicyDocument
from app.models.user import User, UserRole

router = APIRouter()

PROVINCES = [
    "广东", "北京", "上海", "浙江", "江苏", "四川", "湖北", "湖南",
    "山东", "河南", "福建", "陕西", "辽宁", "河北", "安徽", "重庆",
    "云南", "贵州", "江西", "黑龙江", "吉林", "内蒙古", "广西", "新疆",
    "甘肃", "山西", "天津", "海南", "宁夏", "青海", "西藏",
]

ROLE_LABELS = {
    UserRole.normal: "普通用户",
    UserRole.certified: "认证主体",
    UserRole.admin: "管理员",
}

OPINION_LABELS = {
    "review": "落地评价",
    "correction": "解析纠错",
    "message": "办事留言",
}


def _bucket_last_24_hours(items):
    now = datetime.now().replace(minute=0, second=0, microsecond=0)
    buckets = [(now - timedelta(hours=offset)) for offset in range(23, -1, -1)]
    counter = defaultdict(int)

    for dt in items:
        if not dt:
            continue
        point = dt.replace(minute=0, second=0, microsecond=0)
        if point < buckets[0]:
            continue
        counter[point] += 1

    return [
        {"label": bucket.strftime("%H:00"), "value": counter.get(bucket, 0)}
        for bucket in buckets
    ]


def _build_geo_dist(users):
    dist = {}
    for user in users:
        ip = user.last_ip
        if not ip:
            continue
        try:
            addr = ipaddress.ip_address(ip)
            if addr.is_private or addr.is_loopback:
                province = PROVINCES[user.uid % len(PROVINCES)]
            else:
                province = PROVINCES[int(ip.split(".")[-1]) % len(PROVINCES)]
        except Exception:
            continue
        dist[province] = dist.get(province, 0) + 1

    return [{"name": name, "value": value} for name, value in dist.items()]


def _build_feed(messages, documents, opinions):
    events = []

    for message in messages:
        events.append({
            "time": message.created_time,
            "type": "解析流",
            "text": f"用户 #{message.user_id} 完成一次智能解析",
        })

    for document in documents:
        status_text = "已公开" if document.status == DocStatus.approved else "待审核"
        events.append({
            "time": document.created_time,
            "type": "政策流",
            "text": f"《{document.title[:16]}》进入展示链路，状态：{status_text}",
        })

    for opinion in opinions:
        label = OPINION_LABELS.get(opinion.opinion_type.value if hasattr(opinion.opinion_type, "value") else str(opinion.opinion_type), "公众反馈")
        events.append({
            "time": opinion.created_time,
            "type": "评议流",
            "text": f"新增一条{label}，评分：{opinion.rating or '—'}",
        })

    events.sort(key=lambda item: item["time"] or datetime.min, reverse=True)
    if not events:
        return [
            {"type": "系统流", "text": "公共数据大屏已就绪，等待实时数据进入", "time_label": datetime.now().strftime("%H:%M:%S")}
        ]

    return [
        {
            "type": item["type"],
            "text": item["text"],
            "time_label": (item["time"] or datetime.now()).strftime("%H:%M:%S"),
        }
        for item in events[:10]
    ]


@router.get("/landing-stats")
def get_showcase_landing_stats(session: Session = Depends(get_session)):
    total_users = session.exec(select(func.count(User.uid))).one()
    certified_users = session.exec(
        select(func.count(User.uid)).where(User.role.in_([UserRole.certified, UserRole.admin]))
    ).one()
    total_messages = session.exec(
        select(func.count(ChatMessage.id)).where(ChatMessage.is_deleted == False)
    ).one()
    active_users = session.exec(
        select(func.count(func.distinct(ChatMessage.user_id))).where(ChatMessage.is_deleted == False)
    ).one()
    total_opinions = session.exec(select(func.count(Opinion.id))).one()
    total_docs = session.exec(select(func.count(PolicyDocument.id))).one()
    approved_docs = session.exec(
        select(func.count(PolicyDocument.id)).where(PolicyDocument.status == DocStatus.approved)
    ).one()
    pending_docs = session.exec(
        select(func.count(PolicyDocument.id)).where(PolicyDocument.status == DocStatus.pending)
    ).one()

    return {
        "total_users": total_users,
        "certified_users": certified_users,
        "total_messages": total_messages,
        "active_users": active_users,
        "total_opinions": total_opinions,
        "total_docs": total_docs,
        "approved_docs": approved_docs,
        "pending_docs": pending_docs,
    }


@router.get("/screen-data")
def get_showcase_screen_data(session: Session = Depends(get_session)):
    users = session.exec(select(User)).all()
    messages = session.exec(select(ChatMessage).where(ChatMessage.is_deleted == False)).all()
    opinions = session.exec(select(Opinion)).all()
    documents = session.exec(select(PolicyDocument)).all()

    role_dist = {}
    for user in users:
        role_key = user.role.value if hasattr(user.role, "value") else str(user.role)
        role_dist[role_key] = role_dist.get(role_key, 0) + 1

    opinion_type_dist = {}
    rating_dist = {str(index): 0 for index in range(1, 6)}
    for opinion in opinions:
        op_key = opinion.opinion_type.value if hasattr(opinion.opinion_type, "value") else str(opinion.opinion_type)
        opinion_type_dist[op_key] = opinion_type_dist.get(op_key, 0) + 1
        if opinion.rating:
            rating = max(1, min(5, int(opinion.rating)))
            rating_dist[str(rating)] += 1

    geo_dist = _build_geo_dist(users)
    latest_messages = sorted(messages, key=lambda item: item.created_time, reverse=True)[:4]
    latest_documents = sorted(documents, key=lambda item: item.created_time, reverse=True)[:4]
    latest_opinions = sorted(opinions, key=lambda item: item.created_time, reverse=True)[:4]

    approved_docs = sum(1 for doc in documents if doc.status == DocStatus.approved)
    pending_docs = sum(1 for doc in documents if doc.status == DocStatus.pending)

    return {
        "summary": {
            "total_users": len(users),
            "certified_users": sum(1 for user in users if user.role in (UserRole.certified, UserRole.admin)),
            "total_messages": len(messages),
            "active_users": len({message.user_id for message in messages}),
            "total_opinions": len(opinions),
            "total_docs": len(documents),
            "approved_docs": approved_docs,
            "pending_docs": pending_docs,
        },
        "role_dist": role_dist,
        "role_labels": {role.value: label for role, label in ROLE_LABELS.items()},
        "geo_dist": geo_dist,
        "opinion_type_dist": opinion_type_dist,
        "opinion_labels": OPINION_LABELS,
        "rating_dist": rating_dist,
        "hourly_trend": _bucket_last_24_hours([message.created_time for message in messages]),
        "hourly_opinion_trend": _bucket_last_24_hours([opinion.created_time for opinion in opinions]),
        "feed": _build_feed(latest_messages, latest_documents, latest_opinions),
    }
