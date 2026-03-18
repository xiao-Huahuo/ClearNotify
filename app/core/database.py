from sqlmodel import SQLModel, create_engine, Session
from app.core.config import GlobalConfig

# 1. 数据库连接配置 (使用 GlobalConfig 中定义的绝对路径)
SQLALCHEMY_DATABASE_URL = f"sqlite:///{GlobalConfig.DB_PATH}"

# 2. 创建 Engine
# connect_args={"check_same_thread": False} 是 SQLite 特有的配置，允许在多线程环境中使用同一个连接
engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True, connect_args={"check_same_thread": False})


# 3. 初始化数据库函数
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


# 4. 获取 Session 的依赖函数
def get_session():
    with Session(engine) as session:
        yield session
