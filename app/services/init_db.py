import os
import json
import logging
from sqlmodel import Session, select
from app.core.database import create_db_and_tables, engine
from app.models.user import User, UserRole
from app.models.chat_message import ChatMessage
from app.models.todo import TodoItem
from app.models.policy_document import PolicyDocument, DocStatus
from app.models.opinion import Opinion, OpinionType
from app.core.security import get_password_hash
from app.core.config import GlobalConfig

logger = logging.getLogger(__name__)


def init_db_and_admin():
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

    from sqlalchemy import text
    with engine.connect() as conn:
        for sql in [
            "ALTER TABLE user ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT 0",
            "ALTER TABLE user ADD COLUMN email_verified BOOLEAN NOT NULL DEFAULT 0",
            "ALTER TABLE user ADD COLUMN email_verification_code VARCHAR",
            "ALTER TABLE user ADD COLUMN email_verification_sent_at DATETIME",
            "ALTER TABLE user ADD COLUMN role VARCHAR NOT NULL DEFAULT 'normal'",
            "ALTER TABLE chatmessage ADD COLUMN source_chat_id INTEGER REFERENCES chatmessage(id)",
            "ALTER TABLE chatmessage ADD COLUMN session_json_path VARCHAR",
            "ALTER TABLE agentmemory ADD COLUMN updated_time DATETIME",
            "ALTER TABLE policydocument ADD COLUMN view_count INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE policydocument ADD COLUMN like_count INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE user ADD COLUMN last_ip VARCHAR",
            "ALTER TABLE user ADD COLUMN profession VARCHAR",
        ]:
            try:
                conn.execute(text(sql))
                conn.commit()
            except Exception:
                pass

    admin_email = os.getenv("ADMIN_EMAIL", GlobalConfig.DEFAULT_ADMIN_EMAIL)
    admin_username = os.getenv("ADMIN_USERNAME", GlobalConfig.DEFAULT_ADMIN_USERNAME)
    admin_password = os.getenv("ADMIN_PASSWORD", GlobalConfig.DEFAULT_ADMIN_PASSWORD)

    if not admin_email:
        return

    with Session(engine) as session:
        existing = session.exec(select(User).where(User.email == admin_email)).first()
        if existing:
            if existing.role != UserRole.admin or not existing.email_verified:
                existing.role = UserRole.admin
                existing.email_verified = True
                session.add(existing)
                session.commit()
                print(f"Migrated admin: {existing.email}")
            else:
                print(f"Admin already exists: {existing.email}")
        else:
            print(f"Creating admin: {admin_username} ({admin_email})")
            admin = User(
                uname=admin_username,
                email=admin_email,
                hashed_pwd=get_password_hash(admin_password),
                role=UserRole.admin,
                email_verified=True,
            )
            session.add(admin)
            session.commit()
            session.refresh(admin)
            print(f"Admin created. Password: {admin_password}")
            import_admin_original_data(session, admin.uid)
            seed_demo_data(session, admin.uid)


def import_admin_original_data(session: Session, admin_uid: int):
    """从 admin_original_data.json 导入初始解析记录"""
    data_file = GlobalConfig.PROJECT_ROOT / "admin_original_data.json"
    if not data_file.exists():
        print(f"No admin_original_data.json found, skipping.")
        return
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for item in data:
            chat_analysis = item.get("chat_analysis", "{}")
            if isinstance(chat_analysis, dict):
                chat_analysis = json.dumps(chat_analysis, ensure_ascii=False)
            session.add(ChatMessage(
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
                chat_analysis=chat_analysis,
            ))
        session.commit()
        print(f"Imported {len(data)} records from admin_original_data.json")
    except Exception as e:
        print(f"Failed to import admin_original_data.json: {e}")


def seed_demo_data(session: Session, admin_uid: int):
    """从 DB_INIT_DATA_PATH 导入演示数据"""
    from datetime import datetime

    seed_file = GlobalConfig.DB_INIT_DATA_PATH
    if not seed_file.exists():
        print("No database initiation file found, skipping demo data.")
        return

    with open(seed_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 1. 创建认证主体用户
    for u in data.get("certified_users", []):
        session.add(User(
            uname=u["uname"], email=u["email"],
            hashed_pwd=get_password_hash("demo123456"),
            role=UserRole.certified, email_verified=True,
        ))
    session.commit()

    # 2. 创建普通用户
    for u in data.get("normal_users", []):
        session.add(User(
            uname=u["uname"], email=u["email"],
            hashed_pwd=get_password_hash("user123456"),
            role=UserRole.normal, email_verified=True,
        ))
    session.commit()

    # 构建 email -> uid 查找表
    all_emails = (
        [u["email"] for u in data.get("certified_users", [])] +
        [u["email"] for u in data.get("normal_users", [])]
    )
    email_to_uid = {}
    for email in all_emails:
        user = session.exec(select(User).where(User.email == email)).first()
        if user:
            email_to_uid[email] = user.uid

    # 3. 创建政策文件
    title_to_doc_id = {}
    for d in data.get("policy_documents", []):
        uploader_uid = email_to_uid.get(d["uploader_email"], admin_uid)
        doc = PolicyDocument(
            title=d["title"],
            content=d["content"],
            category=d.get("category"),
            tags=d.get("tags"),
            uploader_id=uploader_uid,
            status=DocStatus.approved,
            view_count=d.get("view_count", 0),
            like_count=d.get("like_count", 0),
            reviewed_time=datetime.now(),
        )
        session.add(doc)
        session.commit()
        session.refresh(doc)
        title_to_doc_id[d["title"]] = doc.id

    # 4. 创建民意评议
    type_map = {"review": OpinionType.review, "correction": OpinionType.correction, "message": OpinionType.message}
    for o in data.get("opinions", []):
        doc_id = title_to_doc_id.get(o["doc_title"])
        user_uid = email_to_uid.get(o["user_email"], admin_uid)
        if not doc_id:
            continue
        session.add(Opinion(
            doc_id=doc_id,
            user_id=user_uid,
            opinion_type=type_map.get(o["opinion_type"], OpinionType.review),
            content=o["content"],
            rating=o.get("rating"),
            like_count=o.get("like_count", 0),
        ))
    session.commit()

    # 5. 创建待办事项（归属 admin）
    for t in data.get("todos", []):
        session.add(TodoItem(
            user_id=admin_uid,
            title=t["title"],
            detail=t.get("detail"),
            deadline=t.get("deadline"),
            is_done=t.get("is_done", False),
            is_confirmed=True,
        ))
    session.commit()

    # 6. 创建解析记录（chat messages，归属 admin）
    for m in data.get("chat_messages", []):
        chat_analysis = m.get("chat_analysis", "{}")
        if isinstance(chat_analysis, dict):
            chat_analysis = json.dumps(chat_analysis, ensure_ascii=False)
        session.add(ChatMessage(
            user_id=admin_uid,
            original_text=m["original_text"],
            target_audience=m.get("target_audience"),
            handling_matter=m.get("handling_matter"),
            time_deadline=m.get("time_deadline"),
            location_entrance=m.get("location_entrance"),
            required_materials=m.get("required_materials"),
            handling_process=m.get("handling_process"),
            precautions=m.get("precautions"),
            risk_warnings=m.get("risk_warnings"),
            original_text_mapping=m.get("original_text_mapping"),
            chat_analysis=chat_analysis,
        ))
    session.commit()

    print(f"Demo data seeded from {GlobalConfig.DB_INIT_DATA_PATH}.")
