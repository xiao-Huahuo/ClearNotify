from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.agent_conversation import AgentConversation
    from app.models.user import User


class AgentMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="agentconversation.id")
    user_id: int = Field(foreign_key="user.uid")
    role: str = Field(default="user")
    content: str = Field(default="")
    created_time: datetime = Field(default_factory=datetime.now)

    conversation: Optional["AgentConversation"] = Relationship()
    user: Optional["User"] = Relationship()
