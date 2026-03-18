import os
import json
from sqlmodel import Session, select
from app.core.database import create_db_and_tables, engine
from app.models.user import User
from app.models.chat_message import ChatMessage
from app.core.security import get_password_hash
from app.core.config import GlobalConfig

def init_db_and_admin():
    """
    初始化数据库表并检查/创建默认管理员用户
    """
    # 1. 创建数据库表
    create_db_and_tables()
    
    # 2. 自动创建管理员
    # 优先从环境变量获取，否则使用默认配置
    admin_email = os.getenv("ADMIN_EMAIL", GlobalConfig.DEFAULT_ADMIN_EMAIL)
    admin_username = os.getenv("ADMIN_USERNAME", GlobalConfig.DEFAULT_ADMIN_USERNAME)
    admin_password = os.getenv("ADMIN_PASSWORD", GlobalConfig.DEFAULT_ADMIN_PASSWORD)
    
    if admin_email:
        with Session(engine) as session:
            statement = select(User).where(User.email == admin_email)
            existing_user = session.exec(statement).first()
            
            if not existing_user:
                print(f"Initializing admin user: {admin_username} ({admin_email})")
                
                hashed_pwd = get_password_hash(admin_password)
                new_admin = User(
                    uname=admin_username,
                    email=admin_email,
                    hashed_pwd=hashed_pwd
                )
                session.add(new_admin)
                session.commit()
                session.refresh(new_admin)
                print(f"Admin user created successfully. Password: {admin_password}")
                
                # 3. 导入初始数据
                import_admin_original_data(session, new_admin.uid)
                
            else:
                print(f"Admin user check: {existing_user.email} already exists.")

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
