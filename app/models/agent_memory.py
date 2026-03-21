from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field


class AgentMemory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    conversation_id: int = Field(index=True)
    summary: str = Field(default="")
    updated_time: datetime = Field(default_factory=datetime.now)
