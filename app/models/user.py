from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional

# 导入 TYPE_CHECKING 避免循环导入
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.chat_message import ChatMessage
    from app.models.stats_analysis import StatsAnalysis
    from app.models.settings import Settings

#通用模型,无需存入数据库
class UserBase(SQLModel):
    uname:str=Field(index=True) #用户名
    email:str=Field(unique=True,index=True)  #邮箱,不可重复,建立索引便于查找
    # 修改：手机号不再唯一，且可选
    phone:Optional[str]=Field(default=None)

#数据库模型
class User(UserBase,table=True):
    uid: Optional[int] = Field(default=None, primary_key=True)  #uid作为自增主键
    hashed_pwd:str #哈希加密后的密码
    created_time:datetime=Field(default_factory=datetime.now)  #账户创建时间
    last_login:datetime=Field(default_factory=datetime.now)  #最后登录时间

    # 建立一对多关联关系：一个用户对应多个聊天记录
    chat_messages: List["ChatMessage"] = Relationship(back_populates="user")
    
    # 建立一对一(或一对多)关联关系：一个用户对应其个人的统计分析数据
    stats_analyses: List["StatsAnalysis"] = Relationship(back_populates="user")
    
    # 建立一对一关联关系：一个用户对应一套个人设置
    settings: Optional["Settings"] = Relationship(back_populates="user")
