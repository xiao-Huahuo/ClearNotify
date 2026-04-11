from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class SearchIndexItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    source_type: str = Field(index=True)
    source_id: int = Field(index=True)
    owner_user_id: Optional[int] = Field(default=None, index=True)
    visibility: str = Field(default="private", index=True)
    result_type: str = Field(index=True)
    domain: str = Field(default="", index=True)
    action_type: str = Field(default="route")
    subject_type: Optional[str] = Field(default=None, index=True)
    subject_id: Optional[int] = Field(default=None, index=True)
    title: str = Field(default="")
    subtitle: Optional[str] = Field(default=None)
    summary: Optional[str] = Field(default=None)
    body: Optional[str] = Field(default=None)
    keywords: Optional[str] = Field(default=None)
    route_path: Optional[str] = Field(default=None)
    external_url: Optional[str] = Field(default=None)
    icon: Optional[str] = Field(default=None)
    status: Optional[str] = Field(default=None, index=True)
    dedupe_key: str = Field(index=True)
    published_at: Optional[datetime] = Field(default=None, index=True)
    created_time: datetime = Field(default_factory=datetime.now)
    updated_time: datetime = Field(default_factory=datetime.now, index=True)
    search_text: str = Field(default="")
    embedding_json: str = Field(default="[]")
    extra_json: str = Field(default="{}")
