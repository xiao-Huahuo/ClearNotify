from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class HistoryEventRead(BaseModel):
    id: int
    user_id: int
    actor_user_id: Optional[int] = None
    domain: str
    event_type: str
    subject_type: str
    subject_id: Optional[int] = None
    title: str
    subtitle: Optional[str] = None
    summary: Optional[str] = None
    content_excerpt: Optional[str] = None
    route_path: Optional[str] = None
    external_url: Optional[str] = None
    icon: Optional[str] = None
    status: Optional[str] = None
    is_restorable: bool = False
    visibility: str = "private"
    dedupe_key: Optional[str] = None
    occurred_time: datetime
    created_time: datetime
    search_text: str = ""
    extra: Dict[str, Any] = Field(default_factory=dict)


class HistoryFacetItem(BaseModel):
    domain: str
    count: int


class HistoryFacetResponse(BaseModel):
    total: int
    items: List[HistoryFacetItem] = Field(default_factory=list)


class HistoryTrackCreate(BaseModel):
    domain: str
    event_type: str
    subject_type: str
    subject_id: Optional[int] = None
    title: str
    subtitle: Optional[str] = None
    summary: Optional[str] = None
    content_excerpt: Optional[str] = None
    route_path: Optional[str] = None
    external_url: Optional[str] = None
    icon: Optional[str] = None
    status: Optional[str] = None
    is_restorable: bool = False
    visibility: str = "private"
    dedupe_key: Optional[str] = None
    search_text: str = ""
    extra: Dict[str, Any] = Field(default_factory=dict)
