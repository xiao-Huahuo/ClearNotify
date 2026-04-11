from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class HistoryEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, foreign_key="user.uid")
    actor_user_id: Optional[int] = Field(default=None, index=True)
    domain: str = Field(index=True)
    event_type: str = Field(index=True)
    subject_type: str = Field(index=True)
    subject_id: Optional[int] = Field(default=None, index=True)
    title: str = Field(default="")
    subtitle: Optional[str] = Field(default=None)
    summary: Optional[str] = Field(default=None)
    content_excerpt: Optional[str] = Field(default=None)
    route_path: Optional[str] = Field(default=None)
    external_url: Optional[str] = Field(default=None)
    icon: Optional[str] = Field(default=None)
    status: Optional[str] = Field(default=None, index=True)
    is_restorable: bool = Field(default=False)
    visibility: str = Field(default="private", index=True)
    dedupe_key: Optional[str] = Field(default=None, index=True)
    occurred_time: datetime = Field(default_factory=datetime.now, index=True)
    created_time: datetime = Field(default_factory=datetime.now)
    search_text: str = Field(default="")
    extra_json: str = Field(default="{}")
