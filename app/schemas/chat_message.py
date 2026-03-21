from datetime import datetime
from typing import Any, Dict, Optional

from sqlmodel import SQLModel


class ChatMessageCreate(SQLModel):
    original_text: str
    file_url: Optional[str] = None


class ChatMessageRead(SQLModel):
    id: int
    created_time: datetime
    original_text: str
    file_url: Optional[str] = None
    target_audience: Optional[str] = None
    handling_matter: Optional[str] = None
    time_deadline: Optional[str] = None
    location_entrance: Optional[str] = None
    required_materials: Optional[str] = None
    handling_process: Optional[str] = None
    precautions: Optional[str] = None
    risk_warnings: Optional[str] = None
    original_text_mapping: Optional[str] = None
    chat_analysis: Dict[str, Any] = {}
    user_id: int
    source_chat_id: Optional[int] = None
    session_json_path: Optional[str] = None
    estimated_time_saved_minutes: int = 0


class ChatMessageUpdate(SQLModel):
    target_audience: str
