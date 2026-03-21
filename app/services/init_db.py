import os
import json
import logging
from sqlmodel import Session, select
from app.core.database import create_db_and_tables, engine
from app.models.user import User
from app.models.chat_message import ChatMessage
from app.models.favorite import Favorite
from app.models.todo import TodoItem
from app.core.security import get_password_hash
from app.core.config import GlobalConfig

logger = logging.getLogger(__name__)

def init_db_and_admin():
    # 1. 创建数据库表
    create_db_and_tables()

    for path in (
        GlobalConfig.AVATAR_UPLOAD_DIR,
        GlobalConfig.DOCS_UPLOAD_DIR,
        GlobalConfig.IMAGES_UPLOAD_DIR,
        GlobalConfig.CHAT_EXPORT_DIR,
        GlobalConfig.LOG_DIR,
        GlobalConfig.MAIL_OUTBOX_DIR,
        GlobalConfig.KNOWLEDGE_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)

    # 2. 迁移旧库：补充新列
    from sqlalchemy import text
    with engine.connect() as conn:
        for sql in [
            "ALTER TABLE user ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT 0",
            "ALTER TABLE user ADD COLUMN email_verified BOOLEAN NOT NULL DEFAULT 0",
            "ALTER TABLE user ADD COLUMN email_verification_code VARCHAR",
            "ALTER TABLE user ADD COLUMN email_verification_sent_at DATETIME",
            "ALTER TABLE chatmessage ADD COLUMN source_chat_id INTEGER REFERENCES chatmessage(id)",
            "ALTER TABLE chatmessage ADD COLUMN session_json_path VARCHAR",
        ]:
            try:
                conn.execute(text(sql))
                conn.commit()
            except Exception:
                pass

    # 3. 自动创建/修复管理员
    admin_email = os.getenv("ADMIN_EMAIL", GlobalConfig.DEFAULT_ADMIN_EMAIL)
    admin_username = os.getenv("ADMIN_USERNAME", GlobalConfig.DEFAULT_ADMIN_USERNAME)
    admin_password = os.getenv("ADMIN_PASSWORD", GlobalConfig.DEFAULT_ADMIN_PASSWORD)

    if not admin_email:
        return

    with Session(engine) as session:
        existing_user = session.exec(select(User).where(User.email == admin_email)).first()

        if existing_user:
            if not existing_user.is_admin:
                existing_user.is_admin = True
                existing_user.email_verified = True
                session.add(existing_user)
                session.commit()
                print(f"Migrated admin flag for {existing_user.email}")
            else:
                print(f"Admin user check: {existing_user.email} already exists.")
            if not existing_user.email_verified:
                existing_user.email_verified = True
                session.add(existing_user)
                session.commit()
        else:
            print(f"Initializing admin user: {admin_username} ({admin_email})")
            new_admin = User(
                uname=admin_username,
                email=admin_email,
                hashed_pwd=get_password_hash(admin_password),
                is_admin=True,
                email_verified=True,
            )
            session.add(new_admin)
            session.commit()
            session.refresh(new_admin)
            print(f"Admin user created successfully. Password: {admin_password}")
            import_admin_original_data(session, new_admin.uid)


def import_admin_original_data(session: Session, admin_uid: int):
    """
    从项目根目录的 admin_original_data.json 导入初始测试数据
    """
    data_file_path = GlobalConfig.PROJECT_ROOT / "admin_original_data.json"
    
    if not data_file_path.exists():
        print(f"No original data file found at {data_file_path}. Skipping initial data import.")
        return
        
    try:
        with open(data_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        print(f"Importing {len(data)} initial records for admin...")
        for item in data:
            # 确保 chat_analysis 是字符串
            chat_analysis = item.get("chat_analysis", "{}")
            if isinstance(chat_analysis, dict):
                chat_analysis = json.dumps(chat_analysis, ensure_ascii=False)
                
            msg = ChatMessage(
                user_id=admin_uid,
                original_text=item.get("original_text", ""),
                target_audience=item.get("target_audience"),
                handling_matter=item.get("handling_matter"),
                time_deadline=item.get("time_deadline"),
                location_entrance=item.get("location_entrance"),
                required_materials=item.get("required_materials"),
                handling_process=item.get("handling_process"),
                precautions=item.get("precautions"),
                risk_warnings=item.get("risk_warnings"),
                original_text_mapping=item.get("original_text_mapping"),
                chat_analysis=chat_analysis
            )
            session.add(msg)
            
        session.commit()
        print("Initial data imported successfully.")
    except Exception as e:
        print(f"Failed to import initial data: {e}")
