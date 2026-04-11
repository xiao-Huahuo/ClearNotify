from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.api.deps import get_current_user
from app.core.database import get_session
from app.models.user import User
from app.schemas.history_event import (
    HistoryEventRead,
    HistoryFacetItem,
    HistoryFacetResponse,
    HistoryTrackCreate,
)
from app.services import history_service


router = APIRouter()


@router.get("/feed", response_model=list[HistoryEventRead])
def get_history_feed(
    domain: Optional[str] = Query(default="all"),
    q: str = Query(default=""),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=30, ge=1, le=100),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    events = history_service.list_events(
        session,
        user_id=current_user.uid,
        domain=domain,
        q=q,
        skip=skip,
        limit=limit,
    )
    return [HistoryEventRead(**history_service.serialize_event(item)) for item in events]


@router.get("/facets", response_model=HistoryFacetResponse)
def get_history_facets(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    counts = history_service.get_facets(session, user_id=current_user.uid)
    items = [
        HistoryFacetItem(domain=domain, count=count)
        for domain, count in counts.items()
        if domain != "all"
    ]
    items.sort(key=lambda item: item.count, reverse=True)
    return HistoryFacetResponse(total=counts.get("all", 0), items=items)


@router.post("/track", response_model=HistoryEventRead)
def track_history_event(
    payload: HistoryTrackCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    event = history_service.record_event(
        session,
        user_id=current_user.uid,
        actor_user_id=current_user.uid,
        domain=payload.domain,
        event_type=payload.event_type,
        subject_type=payload.subject_type,
        subject_id=payload.subject_id,
        title=payload.title,
        subtitle=payload.subtitle,
        summary=payload.summary,
        content_excerpt=payload.content_excerpt,
        route_path=payload.route_path,
        external_url=payload.external_url,
        icon=payload.icon,
        status=payload.status,
        is_restorable=payload.is_restorable,
        visibility=payload.visibility,
        dedupe_key=payload.dedupe_key,
        search_text=payload.search_text,
        extra=payload.extra,
    )
    return HistoryEventRead(**history_service.serialize_event(event))
