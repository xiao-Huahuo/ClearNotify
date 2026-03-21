from typing import List, Optional
from pydantic import BaseModel, Field


class AgentConversationCreate(BaseModel):
    title: Optional[str] = Field(default="新对话")


class AgentConversationRead(BaseModel):
    id: int
    title: str
    created_time: str
    updated_time: str


class AgentMessageRead(BaseModel):
    id: int
    role: str
    content: str
    created_time: str


class AgentMessageCreate(BaseModel):
    content: str
