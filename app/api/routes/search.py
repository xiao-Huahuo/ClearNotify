from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.api.deps import get_optional_current_user
from app.core.database import get_session
from app.models.user import User
from app.schemas.search import (
    SearchSuggestItem,
    SearchSuggestResponse,
    SearchSuggestionResponse,
    UnifiedSearchItem,
    UnifiedSearchResponse,
)
from app.services import history_service, search_service


router = APIRouter()


@router.get("/unified", response_model=UnifiedSearchResponse)
def unified_search(
    q: str = Query(default=""),
    limit: int = Query(default=20, ge=1, le=60),
    types: str = Query(default=""),
    track: bool = Query(default=False),
    session: Session = Depends(get_session),
    current_user: User | None = Depends(get_optional_current_user),
):
    selected_types = search_service.normalize_source_types(types)
    items = search_service.unified_search(
        session,
        current_user=current_user,
        query=q,
        limit=limit,
        types=selected_types,
    )
    if track and current_user and q.strip():
        history_service.record_search_event(
            session,
            user_id=current_user.uid,
            query=q,
            source="unified_search",
            result_count=len(items),
            types=selected_types,
        )
    return UnifiedSearchResponse(
        query=q,
        items=[UnifiedSearchItem(**item) for item in items],
    )


@router.get("/suggest-index", response_model=SearchSuggestionResponse)
def get_suggestion_index(
    limit: int = Query(default=240, ge=20, le=500),
    session: Session = Depends(get_session),
    current_user: User | None = Depends(get_optional_current_user),
):
    items = search_service.suggestion_index(
        session,
        current_user=current_user,
        limit=limit,
    )
    return SearchSuggestionResponse(items=[UnifiedSearchItem(**item) for item in items])


@router.get("/suggest", response_model=SearchSuggestResponse)
def get_search_suggestions(
    q: str = Query(default=""),
    limit: int = Query(default=18, ge=1, le=40),
    types: str = Query(default=""),
    session: Session = Depends(get_session),
    current_user: User | None = Depends(get_optional_current_user),
):
    result = search_service.suggest(
        session,
        current_user=current_user,
        query=q,
        limit=limit,
        types=search_service.normalize_source_types(types),
    )
    return SearchSuggestResponse(
        query=result.get("query", ""),
        items=[SearchSuggestItem(**item) for item in result.get("items", [])],
        groups=result.get("groups", {}),
    )
