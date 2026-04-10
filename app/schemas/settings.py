from typing import Optional
from sqlmodel import SQLModel
from app.models.settings import SettingsBase

# 创建设置时的 DTO
class SettingsCreate(SQLModel):
    default_audience: Optional[str] = "none"
    theme_mode: Optional[str] = "light"
    color_scheme: Optional[str] = "classic"
    system_notifications: Optional[bool] = True

# 更新设置时的 DTO (字段全为可选)
class SettingsUpdate(SQLModel):
    default_audience: Optional[str] = None
    theme_mode: Optional[str] = None
    color_scheme: Optional[str] = None
    system_notifications: Optional[bool] = None

# 返回设置数据时的 DTO
class SettingsRead(SettingsBase):
    id: int
