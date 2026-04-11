import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.api.deps import get_current_user, get_optional_current_user
from app.core.database import get_session
from app.models.policy_document import PolicyDocument, DocStatus
from app.models.user import User, UserRole
from app.schemas.policy_document import (
    PolicyDocumentCreate, PolicyDocumentOut, PolicyDocumentReview, PolicyDocumentUpdate
)
from app.services import history_service, search_index_service

logger = logging.getLogger(__name__)

router = APIRouter()


def require_certified_or_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in (UserRole.certified, UserRole.admin):
        raise HTTPException(status_code=403, detail="需要认证主体或管理员权限")
    return current_user


def _doc_to_out(doc: PolicyDocument, session: Session) -> PolicyDocumentOut:
    uploader = session.get(User, doc.uploader_id)
    return PolicyDocumentOut(
        **doc.model_dump(),
        uploader_name=uploader.uname if uploader else None,
    )


# 认证主体上传政务文件
@router.post("/", response_model=PolicyDocumentOut)
def create_document(
    doc_in: PolicyDocumentCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_certified_or_admin),
):
    doc = PolicyDocument(**doc_in.model_dump(), uploader_id=current_user.uid)
    session.add(doc)
    session.commit()
    session.refresh(doc)
    search_index_service.upsert_policy_document(session, doc, commit=True)
    history_service.record_policy_document_event(
        session,
        doc,
        event_type="created",
        user_id=current_user.uid,
        actor_user_id=current_user.uid,
        dedupe_key=f"policy:create:{doc.id}",
        occurred_time=doc.created_time,
    )
    logger.info(f"用户 {current_user.uid} 上传政务文件: {doc.title}")
    return _doc_to_out(doc, session)


# 公开获取已审核通过的政务文件列表（全景政策广场）
@router.get("/approved", response_model=List[PolicyDocumentOut])
def list_approved_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    session: Session = Depends(get_session),
):
    q = select(PolicyDocument).where(PolicyDocument.status == DocStatus.approved)
    if category:
        q = q.where(PolicyDocument.category == category)
    q = q.order_by(PolicyDocument.created_time.desc()).offset(skip).limit(limit)
    docs = session.exec(q).all()
    return [_doc_to_out(d, session) for d in docs]


# 认证主体查看自己的文件
@router.get("/mine", response_model=List[PolicyDocumentOut])
def list_my_documents(
    session: Session = Depends(get_session),
    current_user: User = Depends(require_certified_or_admin),
):
    docs = session.exec(
        select(PolicyDocument).where(PolicyDocument.uploader_id == current_user.uid)
        .order_by(PolicyDocument.created_time.desc())
    ).all()
    return [_doc_to_out(d, session) for d in docs]


@router.get("/{doc_id}", response_model=PolicyDocumentOut)
def get_document(
    doc_id: int,
    session: Session = Depends(get_session),
    current_user: User | None = Depends(get_optional_current_user),
):
    doc = session.get(PolicyDocument, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文件不存在")

    if doc.status != DocStatus.approved:
        if not current_user:
            raise HTTPException(status_code=404, detail="文件不存在")
        is_owner = current_user.uid == doc.uploader_id
        is_admin = current_user.role == UserRole.admin
        if not (is_owner or is_admin):
            raise HTTPException(status_code=403, detail="无权访问该文件")

    return _doc_to_out(doc, session)


# 浏览量+1
@router.post("/{doc_id}/view")
def increment_view(
    doc_id: int,
    session: Session = Depends(get_session),
    current_user: User | None = Depends(get_optional_current_user),
):
    doc = session.get(PolicyDocument, doc_id)
    if not doc or doc.status != DocStatus.approved:
        raise HTTPException(status_code=404, detail="文件不存在")
    doc.view_count += 1
    session.add(doc)
    session.commit()
    if current_user:
        history_service.record_policy_document_event(
            session,
            doc,
            event_type="viewed",
            user_id=current_user.uid,
            actor_user_id=current_user.uid,
            summary="浏览政策文档",
        )
    return {"view_count": doc.view_count}


# 点赞
@router.post("/{doc_id}/like")
def like_document(doc_id: int, session: Session = Depends(get_session)):
    doc = session.get(PolicyDocument, doc_id)
    if not doc or doc.status != DocStatus.approved:
        raise HTTPException(status_code=404, detail="文件不存在")
    doc.like_count += 1
    session.add(doc)
    session.commit()
    return {"like_count": doc.like_count}


# 管理员审核
@router.patch("/{doc_id}/review", response_model=PolicyDocumentOut)
def review_document(
    doc_id: int,
    review: PolicyDocumentReview,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Admin only")
    doc = session.get(PolicyDocument, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文件不存在")
    if review.status not in (DocStatus.approved, DocStatus.rejected):
        raise HTTPException(status_code=400, detail="无效的审核状态")
    doc.status = review.status
    doc.reject_reason = review.reject_reason
    doc.reviewed_time = datetime.now()
    session.add(doc)
    session.commit()
    session.refresh(doc)
    search_index_service.upsert_policy_document(session, doc, commit=True)
    history_service.record_policy_document_event(
        session,
        doc,
        event_type="approved" if review.status == DocStatus.approved else "rejected",
        user_id=doc.uploader_id,
        actor_user_id=current_user.uid,
        dedupe_key=f"policy:{review.status}:{doc.id}",
        occurred_time=doc.reviewed_time,
        summary="政策文档已审核通过" if review.status == DocStatus.approved else "政策文档已驳回",
    )
    logger.info(f"管理员 {current_user.uid} 审核文件 {doc_id}: {review.status}")
    return _doc_to_out(doc, session)


# 管理员获取待审核列表
@router.get("/pending", response_model=List[PolicyDocumentOut])
def list_pending_documents(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Admin only")
    docs = session.exec(
        select(PolicyDocument).where(PolicyDocument.status == DocStatus.pending)
        .order_by(PolicyDocument.created_time.asc())
    ).all()
    return [_doc_to_out(d, session) for d in docs]


# 推荐阅读（刷剧体验）
@router.get("/recommend", response_model=List[PolicyDocumentOut])
def recommend_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    session: Session = Depends(get_session),
):
    return _recommend(skip, limit, session, None)


@router.get("/recommend/me", response_model=List[PolicyDocumentOut])
def recommend_documents_me(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return _recommend(skip, limit, session, current_user)


def _recommend(skip: int, limit: int, session: Session, user):
    q = select(PolicyDocument).where(PolicyDocument.status == DocStatus.approved)
    if user and user.profession:
        category_map = {
            '医': '医疗卫生', '教': '教育', '农': '乡村振兴',
            '企': '惠企政策', '环': '环境保护', '交': '交通建设',
        }
        matched_cat = next((v for k, v in category_map.items() if k in user.profession), None)
        if matched_cat:
            prio = session.exec(q.where(PolicyDocument.category == matched_cat).order_by(PolicyDocument.view_count.desc()).limit(limit // 2)).all()
            rest = session.exec(q.where(PolicyDocument.category != matched_cat).order_by(PolicyDocument.view_count.desc()).offset(skip).limit(limit)).all()
            return [_doc_to_out(d, session) for d in (prio + rest)[:limit]]
    docs = session.exec(q.order_by(PolicyDocument.view_count.desc()).offset(skip).limit(limit)).all()
    return [_doc_to_out(d, session) for d in docs]
@router.get("/my-stats")
def my_document_stats(
    session: Session = Depends(get_session),
    current_user: User = Depends(require_certified_or_admin),
):
    from app.models.opinion import Opinion

    docs = session.exec(
        select(PolicyDocument).where(PolicyDocument.uploader_id == current_user.uid)
    ).all()

    total = len(docs)
    approved = sum(1 for d in docs if d.status == DocStatus.approved)
    pending = sum(1 for d in docs if d.status.value == "pending")
    rejected = sum(1 for d in docs if d.status.value == "rejected")
    total_views = sum(d.view_count for d in docs)
    total_likes = sum(d.like_count for d in docs)

    doc_ids = [d.id for d in docs]
    opinion_count = 0
    rating_avg = 0.0
    opinion_type_dist = {}
    doc_feedback = []

    if doc_ids:
        opinions = session.exec(select(Opinion).where(Opinion.doc_id.in_(doc_ids))).all()
        opinion_count = len(opinions)
        ratings = [o.rating for o in opinions if o.rating]
        rating_avg = round(sum(ratings) / len(ratings), 2) if ratings else 0.0
        for op in opinions:
            opinion_type_dist[op.opinion_type] = opinion_type_dist.get(op.opinion_type, 0) + 1
        for doc in docs:
            doc_ops = [o for o in opinions if o.doc_id == doc.id]
            rated = [o.rating for o in doc_ops if o.rating]
            doc_feedback.append({
                "id": doc.id,
                "title": doc.title,
                "status": doc.status,
                "view_count": doc.view_count,
                "like_count": doc.like_count,
                "opinion_count": len(doc_ops),
                "avg_rating": round(sum(rated) / max(len(rated), 1), 2),
                "created_time": str(doc.created_time),
            })

    all_approved = session.exec(select(PolicyDocument).where(PolicyDocument.status == DocStatus.approved)).all()
    global_avg_views = round(sum(d.view_count for d in all_approved) / max(len(all_approved), 1), 1)
    global_avg_likes = round(sum(d.like_count for d in all_approved) / max(len(all_approved), 1), 1)

    return {
        "total": total, "approved": approved, "pending": pending, "rejected": rejected,
        "total_views": total_views, "total_likes": total_likes,
        "opinion_count": opinion_count, "rating_avg": rating_avg,
        "opinion_type_dist": opinion_type_dist,
        "doc_feedback": doc_feedback,
        "global_avg_views": global_avg_views, "global_avg_likes": global_avg_likes,
    }
