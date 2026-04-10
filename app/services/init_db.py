import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from sqlmodel import Session, select
from app.core.database import create_db_and_tables, engine
from app.models.user import User, UserRole
from app.models.chat_message import ChatMessage
from app.models.todo import TodoItem
from app.models.policy_document import PolicyDocument, DocStatus
from app.models.opinion import Opinion, OpinionType
from app.models.favorite import Favorite
from app.models.settings import Settings
from app.models.agent_conversation import AgentConversation
from app.models.agent_message import AgentMessage
from app.models.agent_memory import AgentMemory
from app.models.stats_analysis import StatsAnalysis
from app.core.security import get_password_hash
from app.core.config import GlobalConfig

logger = logging.getLogger(__name__)


def init_db_and_admin():
    """
    数据库初始化主入口
    1. 创建数据库表结构
    2. 创建必要的目录
    3. 执行数据库迁移（兼容旧版本）
    4. 初始化管理员账户
    5. 可选：导入演示数据
    """
    print("\n" + "=" * 80)
    print("开始数据库初始化".center(80))
    print("=" * 80 + "\n")

    # 1. 创建数据库表结构
    print(">>> [1/5] 创建数据库表结构...")
    create_db_and_tables()
    print("✓ 数据库表结构创建完成\n")

    # 2. 创建必要的目录
    print(">>> [2/5] 创建必要的目录...")
    _create_directories()
    print("✓ 目录创建完成\n")

    # 3. 执行数据库迁移（兼容旧版本字段）
    print(">>> [3/5] 执行数据库迁移...")
    _run_migrations()
    print("✓ 数据库迁移完成\n")

    # 4. 初始化管理员账户
    print(">>> [4/5] 初始化管理员账户...")
    admin_uid = _init_admin_user()
    print("✓ 管理员账户初始化完成\n")

    # 5. 导入演示数据（如果存在）
    print(">>> [5/5] 导入演示数据...")
    _import_seed_data(admin_uid)
    print("✓ 演示数据导入完成\n")

    print("=" * 80)
    print("数据库初始化完成".center(80))
    print("=" * 80 + "\n")


def _create_directories():
    """创建必要的目录"""
    directories = [
        GlobalConfig.AVATAR_UPLOAD_DIR,
        GlobalConfig.DOCS_UPLOAD_DIR,
        GlobalConfig.IMAGES_UPLOAD_DIR,
        GlobalConfig.CHAT_EXPORT_DIR,
        GlobalConfig.LOG_DIR,
        GlobalConfig.MAIL_OUTBOX_DIR,
        GlobalConfig.KNOWLEDGE_DIR,
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"  - 创建目录: {directory}")


def _run_migrations():
    """
    执行数据库迁移，添加新字段（兼容旧版本）
    注意：这些 ALTER TABLE 语句在字段已存在时会失败，但不影响系统运行
    """
    from sqlalchemy import text

    migrations = [
        "ALTER TABLE user ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT 0",
        "ALTER TABLE user ADD COLUMN email_verified BOOLEAN NOT NULL DEFAULT 0",
        "ALTER TABLE user ADD COLUMN email_verification_code VARCHAR",
        "ALTER TABLE user ADD COLUMN email_verification_sent_at DATETIME",
        "ALTER TABLE user ADD COLUMN role VARCHAR NOT NULL DEFAULT 'normal'",
        "ALTER TABLE user ADD COLUMN last_ip VARCHAR",
        "ALTER TABLE user ADD COLUMN profession VARCHAR",
        "ALTER TABLE chatmessage ADD COLUMN source_chat_id INTEGER REFERENCES chatmessage(id)",
        "ALTER TABLE chatmessage ADD COLUMN session_json_path VARCHAR",
        "ALTER TABLE agentmemory ADD COLUMN updated_time DATETIME",
        "ALTER TABLE policydocument ADD COLUMN view_count INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE policydocument ADD COLUMN like_count INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE settings ADD COLUMN color_scheme VARCHAR NOT NULL DEFAULT 'classic'",
    ]

    with engine.connect() as conn:
        for sql in migrations:
            try:
                conn.execute(text(sql))
                conn.commit()
                print(f"  ✓ 执行迁移: {sql[:60]}...")
            except Exception as e:
                # 字段已存在，忽略错误
                pass


def _init_admin_user() -> int:
    """
    初始化管理员账户
    返回管理员的 uid
    """
    admin_email = os.getenv("ADMIN_EMAIL", GlobalConfig.DEFAULT_ADMIN_EMAIL)
    admin_username = os.getenv("ADMIN_USERNAME", GlobalConfig.DEFAULT_ADMIN_USERNAME)
    admin_password = os.getenv("ADMIN_PASSWORD", GlobalConfig.DEFAULT_ADMIN_PASSWORD)

    if not admin_email:
        print("  ⚠ 未配置管理员邮箱，跳过管理员初始化")
        return None

    with Session(engine) as session:
        existing = session.exec(select(User).where(User.email == admin_email)).first()

        if existing:
            # 管理员已存在，确保角色和邮箱验证状态正确
            if existing.role != UserRole.admin or not existing.email_verified:
                existing.role = UserRole.admin
                existing.email_verified = True
                session.add(existing)
                session.commit()
                print(f"  ✓ 更新管理员账户: {existing.email}")
            else:
                print(f"  ✓ 管理员账户已存在: {existing.email}")
            return existing.uid
        else:
            # 创建新管理员
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
            print(f"  ✓ 创建管理员账户: {admin_username} ({admin_email})")
            print(f"  ✓ 管理员密码: {admin_password}")
            return admin.uid


def _import_seed_data(admin_uid: int):
    """
    导入演示数据
    从 app/resources/db_init/ 目录读取各个 JSON 文件
    """
    if not admin_uid:
        print("  ⚠ 管理员账户未初始化，跳过演示数据导入")
        return

    seed_dir = GlobalConfig.DB_INIT_DIR
    if not seed_dir.exists():
        print(f"  ⚠ 演示数据目录不存在: {seed_dir}")
        return

    with Session(engine) as session:
        # 检查是否已有数据（除了管理员）
        user_count = session.exec(select(User)).all()
        if len(user_count) > 1:
            print("  ⚠ 数据库已有数据，跳过演示数据导入")
            return

        print(f"  从目录导入演示数据: {seed_dir}\n")

        # 1. 导入用户
        _import_users(session, seed_dir)

        # 2. 导入政策文档
        _import_policy_documents(session, seed_dir)

        # 3. 导入民意评议
        _import_opinions(session, seed_dir)

        # 4. 导入解析记录
        _import_chat_messages(session, seed_dir, admin_uid)

        # 5. 导入待办事项
        _import_todos(session, seed_dir, admin_uid)

        # 6. 导入收藏
        _import_favorites(session, seed_dir)

        # 7. 导入用户设置
        _import_settings(session, seed_dir)

        # 8. 导入智能体对话
        _import_agent_conversations(session, seed_dir)

        # 9. 导入智能体消息
        _import_agent_messages(session, seed_dir)

        # 10. 导入智能体记忆
        _import_agent_memories(session, seed_dir)

        # 11. 导入统计分析
        _import_stats_analyses(session, seed_dir)


def _load_json(file_path: Path) -> Dict[str, Any]:
    """加载 JSON 文件"""
    if not file_path.exists():
        return {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载 JSON 文件失败: {file_path}, 错误: {e}")
        return {}


def _import_users(session: Session, seed_dir: Path):
    """导入用户数据"""
    data = _load_json(seed_dir / "users.json")
    if not data:
        return

    print("  [用户数据]")

    # 导入认证主体用户
    for user_data in data.get("certified_users", []):
        user = User(
            uname=user_data["uname"],
            email=user_data["email"],
            phone=user_data.get("phone"),
            profession=user_data.get("profession"),
            avatar_url=user_data.get("avatar_url"),
            hashed_pwd=get_password_hash("demo123456"),
            role=UserRole.certified,
            email_verified=True,
        )
        session.add(user)
        print(f"    + 认证主体: {user.uname} ({user.email})")

    # 导入普通用户
    for user_data in data.get("normal_users", []):
        user = User(
            uname=user_data["uname"],
            email=user_data["email"],
            phone=user_data.get("phone"),
            profession=user_data.get("profession"),
            avatar_url=user_data.get("avatar_url"),
            hashed_pwd=get_password_hash("user123456"),
            role=UserRole.normal,
            email_verified=True,
        )
        session.add(user)
        print(f"    + 普通用户: {user.uname} ({user.email})")

    session.commit()
    print(f"  ✓ 导入用户: {len(data.get('certified_users', []))} 个认证主体, {len(data.get('normal_users', []))} 个普通用户\n")


def _import_policy_documents(session: Session, seed_dir: Path):
    """导入政策文档"""
    data = _load_json(seed_dir / "policy_documents.json")
    if not data:
        return

    print("  [政策文档]")

    # 构建 email -> uid 映射
    email_to_uid = {}
    users = session.exec(select(User)).all()
    for user in users:
        email_to_uid[user.email] = user.uid

    for doc_data in data.get("documents", []):
        uploader_uid = email_to_uid.get(doc_data["uploader_email"])
        if not uploader_uid:
            continue

        doc = PolicyDocument(
            title=doc_data["title"],
            content=doc_data["content"],
            category=doc_data.get("category"),
            tags=doc_data.get("tags"),
            uploader_id=uploader_uid,
            status=DocStatus[doc_data.get("status", "approved")],
            view_count=doc_data.get("view_count", 0),
            like_count=doc_data.get("like_count", 0),
            reviewed_time=datetime.now(),
        )
        session.add(doc)
        print(f"    + 文档: {doc.title[:30]}...")

    session.commit()
    print(f"  ✓ 导入政策文档: {len(data.get('documents', []))} 篇\n")


def _import_opinions(session: Session, seed_dir: Path):
    """导入民意评议"""
    data = _load_json(seed_dir / "opinions.json")
    if not data:
        return

    print("  [民意评议]")

    # 构建映射
    email_to_uid = {u.email: u.uid for u in session.exec(select(User)).all()}
    title_to_doc_id = {d.title: d.id for d in session.exec(select(PolicyDocument)).all()}

    type_map = {
        "review": OpinionType.review,
        "correction": OpinionType.correction,
        "message": OpinionType.message
    }

    for opinion_data in data.get("opinions", []):
        doc_id = title_to_doc_id.get(opinion_data["doc_title"])
        user_uid = email_to_uid.get(opinion_data["user_email"])

        if not doc_id or not user_uid:
            continue

        opinion = Opinion(
            doc_id=doc_id,
            user_id=user_uid,
            opinion_type=type_map.get(opinion_data["opinion_type"], OpinionType.review),
            content=opinion_data["content"],
            rating=opinion_data.get("rating"),
            like_count=opinion_data.get("like_count", 0),
        )
        session.add(opinion)
        print(f"    + 评议: {opinion_data['opinion_type']} - {opinion_data['content'][:20]}...")

    session.commit()
    print(f"  ✓ 导入民意评议: {len(data.get('opinions', []))} 条\n")


def _import_chat_messages(session: Session, seed_dir: Path, admin_uid: int):
    """导入解析记录"""
    data = _load_json(seed_dir / "chat_messages.json")
    if not data:
        return

    print("  [解析记录]")

    for msg_data in data.get("chat_messages", []):
        chat_analysis = msg_data.get("chat_analysis", "{}")
        if isinstance(chat_analysis, dict):
            chat_analysis = json.dumps(chat_analysis, ensure_ascii=False)

        msg = ChatMessage(
            user_id=admin_uid,
            original_text=msg_data["original_text"],
            file_url=msg_data.get("file_url"),
            target_audience=msg_data.get("target_audience"),
            handling_matter=msg_data.get("handling_matter"),
            time_deadline=msg_data.get("time_deadline"),
            location_entrance=msg_data.get("location_entrance"),
            required_materials=msg_data.get("required_materials"),
            handling_process=msg_data.get("handling_process"),
            precautions=msg_data.get("precautions"),
            risk_warnings=msg_data.get("risk_warnings"),
            original_text_mapping=msg_data.get("original_text_mapping"),
            chat_analysis=chat_analysis,
        )
        session.add(msg)
        print(f"    + 解析: {msg_data['handling_matter'][:30]}...")

    session.commit()
    print(f"  ✓ 导入解析记录: {len(data.get('chat_messages', []))} 条\n")


def _import_todos(session: Session, seed_dir: Path, admin_uid: int):
    """导入待办事项"""
    data = _load_json(seed_dir / "todos.json")
    if not data:
        return

    print("  [待办事项]")

    for todo_data in data.get("todos", []):
        todo = TodoItem(
            user_id=admin_uid,
            title=todo_data["title"],
            detail=todo_data.get("detail"),
            deadline=todo_data.get("deadline"),
            is_done=todo_data.get("is_done", False),
            is_confirmed=todo_data.get("is_confirmed", True),
            source_chat_id=todo_data.get("source_chat_id"),
        )
        session.add(todo)
        print(f"    + 待办: {todo.title[:30]}...")

    session.commit()
    print(f"  ✓ 导入待办事项: {len(data.get('todos', []))} 条\n")


def _import_favorites(session: Session, seed_dir: Path):
    """导入收藏"""
    data = _load_json(seed_dir / "favorites.json")
    if not data:
        return

    print("  [收藏记录]")

    # 构建映射
    email_to_uid = {u.email: u.uid for u in session.exec(select(User)).all()}
    chat_messages = session.exec(select(ChatMessage)).all()

    for fav_data in data.get("favorites", []):
        user_uid = email_to_uid.get(fav_data["user_email"])
        if not user_uid:
            continue

        # 根据索引获取 chat_message_id
        chat_msg_index = fav_data.get("chat_message_index", 0)
        if chat_msg_index < len(chat_messages):
            chat_msg_id = chat_messages[chat_msg_index].id

            fav = Favorite(
                user_id=user_uid,
                chat_message_id=chat_msg_id,
                note=fav_data.get("note"),
            )
            session.add(fav)
            print(f"    + 收藏: {fav_data.get('note', '无备注')[:30]}...")

    session.commit()
    print(f"  ✓ 导入收藏记录: {len(data.get('favorites', []))} 条\n")


def _import_settings(session: Session, seed_dir: Path):
    """导入用户设置"""
    data = _load_json(seed_dir / "settings.json")
    if not data:
        return

    print("  [用户设置]")

    email_to_uid = {u.email: u.uid for u in session.exec(select(User)).all()}

    for setting_data in data.get("settings", []):
        user_uid = email_to_uid.get(setting_data["user_email"])
        if not user_uid:
            continue

        setting = Settings(
            user_id=user_uid,
            default_audience=setting_data.get("default_audience", "none"),
            theme_mode=setting_data.get("theme_mode", "light"),
            color_scheme=setting_data.get("color_scheme", "classic"),
            system_notifications=setting_data.get("system_notifications", True),
        )
        session.add(setting)
        print(f"    + 设置: 用户 {setting_data['user_email']}")

    session.commit()
    print(f"  ✓ 导入用户设置: {len(data.get('settings', []))} 条\n")


def _import_agent_conversations(session: Session, seed_dir: Path):
    """导入智能体对话"""
    data = _load_json(seed_dir / "agent_conversations.json")
    if not data:
        return

    print("  [智能体对话]")

    email_to_uid = {u.email: u.uid for u in session.exec(select(User)).all()}

    for conv_data in data.get("agent_conversations", []):
        user_uid = email_to_uid.get(conv_data["user_email"])
        if not user_uid:
            continue

        conv = AgentConversation(
            user_id=user_uid,
            title=conv_data["title"],
        )
        session.add(conv)
        print(f"    + 对话: {conv.title}")

    session.commit()
    print(f"  ✓ 导入智能体对话: {len(data.get('agent_conversations', []))} 条\n")


def _import_agent_messages(session: Session, seed_dir: Path):
    """导入智能体消息"""
    data = _load_json(seed_dir / "agent_messages.json")
    if not data:
        return

    print("  [智能体消息]")

    email_to_uid = {u.email: u.uid for u in session.exec(select(User)).all()}
    conversations = session.exec(select(AgentConversation)).all()

    for msg_data in data.get("agent_messages", []):
        user_uid = email_to_uid.get(msg_data["user_email"])
        if not user_uid:
            continue

        conv_index = msg_data.get("conversation_index", 0)
        if conv_index < len(conversations):
            conv_id = conversations[conv_index].id

            msg = AgentMessage(
                conversation_id=conv_id,
                user_id=user_uid,
                role=msg_data["role"],
                content=msg_data["content"],
            )
            session.add(msg)
            print(f"    + 消息: {msg_data['role']} - {msg_data['content'][:20]}...")

    session.commit()
    print(f"  ✓ 导入智能体消息: {len(data.get('agent_messages', []))} 条\n")


def _import_agent_memories(session: Session, seed_dir: Path):
    """导入智能体记忆"""
    data = _load_json(seed_dir / "agent_memories.json")
    if not data:
        return

    print("  [智能体记忆]")

    email_to_uid = {u.email: u.uid for u in session.exec(select(User)).all()}
    conversations = session.exec(select(AgentConversation)).all()

    for mem_data in data.get("agent_memories", []):
        user_uid = email_to_uid.get(mem_data["user_email"])
        if not user_uid:
            continue

        conv_index = mem_data.get("conversation_index", 0)
        if conv_index < len(conversations):
            conv_id = conversations[conv_index].id

            mem = AgentMemory(
                user_id=user_uid,
                conversation_id=conv_id,
                summary=mem_data["summary"],
            )
            session.add(mem)
            print(f"    + 记忆: {mem_data['summary'][:30]}...")

    session.commit()
    print(f"  ✓ 导入智能体记忆: {len(data.get('agent_memories', []))} 条\n")


def _import_stats_analyses(session: Session, seed_dir: Path):
    """导入统计分析"""
    data = _load_json(seed_dir / "stats_analyses.json")
    if not data:
        return

    print("  [统计分析]")

    email_to_uid = {u.email: u.uid for u in session.exec(select(User)).all()}

    for stats_data in data.get("stats_analyses", []):
        user_uid = email_to_uid.get(stats_data["user_email"])
        if not user_uid:
            continue

        stats = StatsAnalysis(
            user_id=user_uid,
            materials_freq=stats_data.get("materials_freq", "{}"),
            risks_freq=stats_data.get("risks_freq", "{}"),
            complexity_distribution=stats_data.get("complexity_distribution", "{}"),
            notice_type_distribution=stats_data.get("notice_type_distribution", "{}"),
            total_time_saved_minutes=stats_data.get("total_time_saved_minutes", 0),
            avg_time_saved_minutes=stats_data.get("avg_time_saved_minutes", 0),
            time_saved_distribution=stats_data.get("time_saved_distribution", "{}"),
            total_parsed_count=stats_data.get("total_parsed_count", 0),
        )
        session.add(stats)
        print(f"    + 统计: 用户 {stats_data['user_email']} - 解析 {stats.total_parsed_count} 条")

    session.commit()
    print(f"  ✓ 导入统计分析: {len(data.get('stats_analyses', []))} 条\n")
