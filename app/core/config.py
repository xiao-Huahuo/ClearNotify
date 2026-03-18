from pathlib import Path
import os

class GlobalConfig:
    DEFAULT_ADMIN_PASSWORD = "111111"
    DEFAULT_ADMIN_USERNAME="admin"
    DEFAULT_ADMIN_EMAIL="unknown@email.com"
    DEFAULT_ADMIN_PHONE=None

    # 动态获取真正的项目根目录 (ClearNotify 目录)
    # 当前文件是 app/core/config.py
    # .parent 是 app/core
    # .parent.parent 是 app
    # .parent.parent.parent 是 ClearNotify (项目根目录)
    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

    # 数据库配置 (使用绝对路径定位到项目根目录)
    SQLITE_DATABASE_FILENAME = "database.db"  # 数据库文件名
    DB_PATH = PROJECT_ROOT / SQLITE_DATABASE_FILENAME
    
    # 环境变量文件路径
    ENV_PATH = PROJECT_ROOT / ".env"
    
    # 上传文件存放路径 (绝对路径)
    UPLOAD_DIR = PROJECT_ROOT / "uploads"
    AVATAR_UPLOAD_DIR = UPLOAD_DIR / "avatars"

    # JWT配置
    # 常量,应该从环境变量获取,此处开发使用
    SECRET_KEY = "09d25e094faa6ca2556c81"  # 密钥
    ALGORITHM = "HS256"  # 加密算法,采用Hash256
    ACCESS_TOKEN_EXPIRE_DAYS = 30  # token有效期为30天
