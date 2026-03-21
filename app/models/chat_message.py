from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

# 导入 TYPE_CHECKING 避免循环导入
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.user import User

# 通用模型, 无需存入数据库
class ChatMessageBase(SQLModel):
    # 输入信息
    original_text: str = Field(description="输入的官方通知原文")
    
    # 新增：原文件的 URL 路径，允许为空（纯文本解析时为空）
    file_url: Optional[str] = Field(default=None, description="原文件的访问URL")
    
    # 结构化输出信息 (由于提取结果可能缺失，全部设为可选)
    target_audience: Optional[str] = Field(default=None, description="适用对象")
    handling_matter: Optional[str] = Field(default=None, description="办理事项")
    time_deadline: Optional[str] = Field(default=None, description="时间/截止时间")
    location_entrance: Optional[str] = Field(default=None, description="地点/入口")
    required_materials: Optional[str] = Field(default=None, description="所需材料")
    handling_process: Optional[str] = Field(default=None, description="办理流程")
    precautions: Optional[str] = Field(default=None, description="注意事项")
    risk_warnings: Optional[str] = Field(default=None, description="风险提醒")
    original_text_mapping: Optional[str] = Field(default=None, description="官方原文对应位置(可能存JSON字符串)")
    
    # 针对通知的独立分析数据（存为 JSON 字符串字典）
    chat_analysis: str = Field(default="{}", description="通知分析：包含难度分级等")
    
    # 外键：关联的用户ID (对应 User 表的 uid)
    user_id: int = Field(foreign_key="user.uid")

# 数据库模型
class ChatMessage(ChatMessageBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_time: datetime = Field(default_factory=datetime.now)
    is_deleted: bool = Field(default=False)
    source_chat_id: Optional[int] = Field(default=None, foreign_key="chatmessage.id")
    session_json_path: Optional[str] = Field(default=None, description="会话快照JSON路径")

    # 建立与 User 的多对一关系
    user: Optional["User"] = Relationship(back_populates="chat_messages")
