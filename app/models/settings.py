from typing import Optional
from sqlmodel import SQLModel, Field, Relationship

# 导入 TYPE_CHECKING 避免循环导入
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.user import User

# 通用模型
class SettingsBase(SQLModel):
    # 默认 AI 改写受众 (例如: none, elderly, student, worker)
    default_audience: str = Field(default="none", description="默认 AI 改写受众")
    
    # 明暗主题 (例如: light, dark, system)
    theme_mode: str = Field(default="light", description="整体明暗主题")

    # 全局品牌色系 (例如: classic, wine-coral)
    color_scheme: str = Field(default="classic", description="全局品牌色系")
    
    # 系统通知提醒 (布尔值)
    system_notifications: bool = Field(default=True, description="是否接收系统通知")
    
    # 外键：关联的用户ID (对应 User 表的 uid)
    user_id: int = Field(foreign_key="user.uid")

# 数据库模型
class Settings(SettingsBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # 建立与 User 的关系 (通常是一对一，因为一个用户只有一套设置)
    user: Optional["User"] = Relationship(back_populates="settings")
