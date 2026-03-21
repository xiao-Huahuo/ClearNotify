from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.user import User


class AgentConversation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.uid")
    title: str = Field(default="新对话")
    created_time: datetime = Field(default_factory=datetime.now)
    updated_time: datetime = Field(default_factory=datetime.now)

    user: Optional["User"] = Relationship()
