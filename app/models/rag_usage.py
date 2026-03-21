from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.user import User


class RagUsage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.uid")
    created_time: datetime = Field(default_factory=datetime.now)
    query: str = Field(default="")
    top_k: int = Field(default=5)
    result_count: int = Field(default=0)
    avg_score: float = Field(default=0.0)
    source: str = Field(default="unknown")

    user: Optional["User"] = Relationship()
