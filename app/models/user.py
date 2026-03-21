from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.chat_message import ChatMessage
    from app.models.stats_analysis import StatsAnalysis
    from app.models.settings import Settings
    from app.models.favorite import Favorite
    from app.models.todo import TodoItem

class UserBase(SQLModel):
    uname: str = Field(index=True)
    email: str = Field(unique=True, index=True)
    phone: Optional[str] = Field(default=None)
    avatar_url: Optional[str] = Field(default=None)
    is_admin: bool = Field(default=False)

class User(UserBase, table=True):
    uid: Optional[int] = Field(default=None, primary_key=True)
    hashed_pwd: str
    created_time: datetime = Field(default_factory=datetime.now)
    last_login: datetime = Field(default_factory=datetime.now)
    email_verified: bool = Field(default=False)
    email_verification_code: Optional[str] = Field(default=None)
    email_verification_sent_at: Optional[datetime] = Field(default=None)

    chat_messages: List["ChatMessage"] = Relationship(back_populates="user")
    stats_analyses: List["StatsAnalysis"] = Relationship(back_populates="user")
    settings: Optional["Settings"] = Relationship(back_populates="user")
    favorites: List["Favorite"] = Relationship(back_populates="user")
    todos: List["TodoItem"] = Relationship(back_populates="user")
