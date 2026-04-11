from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class UnifiedSearchItem(BaseModel):
    source_type: str
    title: str
    subtitle: Optional[str] = None
    description: Optional[str] = None
    action_type: str
    route_path: Optional[str] = None
    external_url: Optional[str] = None
    subject_type: Optional[str] = None
    subject_id: Optional[int] = None
    published_at: Optional[str] = None
    score: float = 0.0
    extra: Dict[str, Any] = Field(default_factory=dict)


class UnifiedSearchResponse(BaseModel):
    query: str = ""
    items: List[UnifiedSearchItem] = Field(default_factory=list)


class SearchSuggestionResponse(BaseModel):
    items: List[UnifiedSearchItem] = Field(default_factory=list)


class SearchSuggestItem(UnifiedSearchItem):
    group: str = "semantic"


class SearchSuggestResponse(BaseModel):
    query: str = ""
    items: List[SearchSuggestItem] = Field(default_factory=list)
    groups: Dict[str, int] = Field(default_factory=dict)
