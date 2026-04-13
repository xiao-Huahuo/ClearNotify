import os
import json
import logging
import secrets
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
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
from app.models.history_event import HistoryEvent
from app.models.search_index_item import SearchIndexItem
from app.models.stats_analysis import StatsAnalysis
from app.core.security import get_password_hash
from app.core.config import GlobalConfig
from app.services import history_service, search_index_service
from app.services.auth_identity_service import (
    build_placeholder_email,
    get_public_email,
    is_valid_login_phone,
    normalize_email,
    normalize_login_phone,
    resolve_user_for_identifier,
)

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
    print("[ok] 数据库表结构创建完成\n")

    # 2. 创建必要的目录
    print(">>> [2/5] 创建必要的目录...")
    _create_directories()
    print("[ok] 目录创建完成\n")

    # 3. 执行数据库迁移（兼容旧版本字段）
    print(">>> [3/5] 执行数据库迁移...")
    _run_migrations()
    print("[ok] 数据库迁移完成\n")

    # 4. 初始化管理员账户
    print(">>> [4/5] 初始化管理员账户...")
    admin_uid = _init_admin_user()
    print("[ok] 管理员账户初始化完成\n")

    # 5. 导入演示数据（如果存在）
    print(">>> [5/5] 导入演示数据...")
    _import_seed_data(admin_uid)
    print("[ok] 演示数据导入完成\n")

    print(">>> [history] 回填统一历史事件...")
    with Session(engine) as session:
        created = history_service.backfill_core_history(session)
    print(f"[ok] 统一历史事件回填完成: {created} 条\n")

    print(">>> [search] 回填统一搜索索引与向量...")
    with Session(engine) as session:
        index_result = search_index_service.backfill_search_index(session)
    print(
        "[ok] 统一搜索索引回填完成: "
        f"{index_result['history_events']} history + "
        f"{index_result['policy_documents']} policy = {index_result['total']}\n"
    )

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
        "ALTER TABLE user ADD COLUMN login_phone VARCHAR",
        "ALTER TABLE user ADD COLUMN phone_verified BOOLEAN NOT NULL DEFAULT 0",
        "ALTER TABLE user ADD COLUMN password_login_enabled BOOLEAN NOT NULL DEFAULT 1",
        "ALTER TABLE user ADD COLUMN preferred_login_method VARCHAR",
        "ALTER TABLE user ADD COLUMN last_login_method VARCHAR",
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
                print(f"  [ok] 执行迁移: {sql[:60]}...")
            except Exception as e:
                # 字段已存在，忽略错误
                pass
        try:
            conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS idx_user_login_phone_unique ON user(login_phone)"))
            conn.commit()
            print("  [ok] 鎵ц杩佺Щ: unique index for user.login_phone")
        except Exception:
            pass

    _backfill_auth_fields()


def _backfill_auth_fields():
    with Session(engine) as session:
        users = session.exec(select(User)).all()
        changed = 0
        for user in users:
            dirty = False
            if getattr(user, "password_login_enabled", None) is None:
                user.password_login_enabled = bool(user.hashed_pwd)
                dirty = True
            if not getattr(user, "login_phone", None) and user.phone:
                normalized_phone = normalize_login_phone(user.phone)
                if is_valid_login_phone(normalized_phone):
                    user.login_phone = normalized_phone
                    user.phone_verified = True
                    dirty = True
            public_email = get_public_email(user.email)
            if getattr(user, "last_login_method", None) == "password":
                user.last_login_method = "email_password" if public_email else ("phone_password" if user.login_phone else "username_password")
                dirty = True
            if not getattr(user, "last_login_method", None):
                if user.login_phone and not user.password_login_enabled:
                    user.last_login_method = "phone_code"
                elif user.hashed_pwd:
                    user.last_login_method = "email_password" if public_email else ("phone_password" if user.login_phone else "username_password")
                dirty = True
            if getattr(user, "preferred_login_method", None) == "password":
                user.preferred_login_method = None
                dirty = True
            if not getattr(user, "preferred_login_method", None):
                if user.login_phone and not user.password_login_enabled:
                    user.preferred_login_method = "phone_code"
                elif user.hashed_pwd:
                    user.preferred_login_method = "email_password" if public_email else ("phone_password" if user.login_phone else "username_password")
                elif getattr(user, "last_login_method", None):
                    user.preferred_login_method = user.last_login_method
                dirty = True
            if dirty:
                session.add(user)
                changed += 1
        if changed:
            session.commit()
            print(f"  [ok] 鍥炲～璁よ瘉瀛楁: {changed} 条")


def _init_admin_user() -> int:
    """
    初始化管理员账户
    返回管理员的 uid
    """
    admin_email = normalize_email(os.getenv("ADMIN_EMAIL", GlobalConfig.DEFAULT_ADMIN_EMAIL) or "")
    admin_username = os.getenv("ADMIN_USERNAME", GlobalConfig.DEFAULT_ADMIN_USERNAME)
    admin_password = os.getenv("ADMIN_PASSWORD", GlobalConfig.DEFAULT_ADMIN_PASSWORD)
    admin_phone = normalize_login_phone(os.getenv("ADMIN_PHONE", GlobalConfig.DEFAULT_ADMIN_PHONE) or "")
    if not is_valid_login_phone(admin_phone):
        admin_phone = None

    if not admin_email and not admin_phone:
        print("  [warn] 未配置管理员邮箱或手机号，跳过管理员初始化")
        return None

    with Session(engine) as session:
        existing = None
        if admin_email:
            existing = session.exec(select(User).where(User.email == admin_email)).first()
        if not existing and admin_phone:
            existing = session.exec(select(User).where(User.login_phone == admin_phone)).first()
        if not existing:
            existing = session.exec(select(User).where(User.uname == admin_username)).first()

        if existing:
            # 管理员已存在，确保认证字段和权限一致
            existing.uname = admin_username
            if admin_email:
                existing.email = admin_email
                existing.email_verified = True
            elif not existing.email and admin_phone:
                existing.email = build_placeholder_email(admin_phone)
                existing.email_verified = False
            if admin_phone:
                existing.phone = admin_phone
                existing.login_phone = admin_phone
                existing.phone_verified = True
            existing.hashed_pwd = get_password_hash(admin_password)
            existing.role = UserRole.admin
            existing.password_login_enabled = True
            existing.preferred_login_method = "email_password" if admin_email else ("phone_password" if admin_phone else "username_password")
            if not existing.last_login_method:
                existing.last_login_method = existing.preferred_login_method
            session.add(existing)
            session.commit()
            print(f"  [ok] 更新管理员账户: {existing.uname} ({existing.email})")
            return existing.uid

        # 创建新管理员
        stored_email = admin_email or build_placeholder_email(admin_phone)
        preferred_login_method = "email_password" if admin_email else ("phone_password" if admin_phone else "username_password")
        admin = User(
            uname=admin_username,
            email=stored_email,
            phone=admin_phone,
            login_phone=admin_phone,
            hashed_pwd=get_password_hash(admin_password),
            role=UserRole.admin,
            email_verified=bool(admin_email),
            phone_verified=bool(admin_phone),
            password_login_enabled=True,
            preferred_login_method=preferred_login_method,
            last_login_method=preferred_login_method,
        )
        session.add(admin)
        session.commit()
        session.refresh(admin)
        print(f"  [ok] 创建管理员账户: {admin_username} ({stored_email})")
        if admin_phone:
            print(f"  [ok] 管理员绑定手机号: {admin_phone}")
        print(f"  [ok] 管理员密码: {admin_password}")
        return admin.uid


def _import_seed_data(admin_uid: int):
    """
    导入演示数据
    从 app/resources/db_init/ 目录读取各个 JSON 文件
    """
    if not admin_uid:
        print("  [warn] 管理员账户未初始化，跳过演示数据导入")
        return

    seed_dir = GlobalConfig.DB_INIT_DIR
    if not seed_dir.exists():
        print(f"  [warn] 演示数据目录不存在: {seed_dir}")
        return

    with Session(engine) as session:
        # 检查是否已有数据（除了管理员）
        user_count = session.exec(select(User)).all()
        if len(user_count) > 1:
            print("  [warn] 数据库已有数据，跳过演示数据导入")
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
        _ensure_settings_for_all_users(session)

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


def _resolve_seed_user(
    session: Session,
    record: Dict[str, Any],
    *,
    email_key: str = "user_email",
    identifier_key: str = "user_identifier",
) -> Optional[User]:
    identifier = (record.get(identifier_key) or record.get(email_key) or "").strip()
    if not identifier:
        return None
    return resolve_user_for_identifier(session, identifier)


def _build_seed_user(user_data: Dict[str, Any], *, default_role: UserRole, default_password: str) -> User:
    uname = (user_data.get("uname") or "").strip()
    if not uname:
        raise ValueError("seed user is missing uname")

    public_email = normalize_email(user_data.get("email") or "") or None

    login_phone = normalize_login_phone(user_data.get("login_phone") or user_data.get("phone") or "")
    if not is_valid_login_phone(login_phone):
        login_phone = None

    stored_email = public_email or (build_placeholder_email(login_phone) if login_phone else None)
    if not stored_email:
        raise ValueError(f"seed user '{uname}' must provide email or a valid login_phone")

    password_login_enabled = bool(user_data.get("password_login_enabled", True))
    seed_password = (user_data.get("seed_password") or "").strip()
    effective_password = (seed_password or default_password) if password_login_enabled else secrets.token_urlsafe(24)

    email_verified = bool(user_data.get("email_verified", bool(public_email)))
    phone_verified = bool(user_data.get("phone_verified", bool(login_phone)))

    if "preferred_login_method" in user_data:
        preferred_login_method = user_data.get("preferred_login_method")
    elif login_phone and not password_login_enabled:
        preferred_login_method = "phone_code"
    elif password_login_enabled and public_email:
        preferred_login_method = "email_password"
    elif password_login_enabled and login_phone:
        preferred_login_method = "phone_password"
    elif password_login_enabled:
        preferred_login_method = "username_password"
    else:
        preferred_login_method = None

    if "last_login_method" in user_data:
        last_login_method = user_data.get("last_login_method")
    else:
        last_login_method = preferred_login_method

    raw_role = user_data.get("role")
    role = UserRole(raw_role) if raw_role else default_role

    contact_phone = user_data.get("phone")
    if not contact_phone and login_phone:
        contact_phone = login_phone

    return User(
        uname=uname,
        email=stored_email,
        phone=contact_phone,
        login_phone=login_phone,
        profession=user_data.get("profession"),
        avatar_url=user_data.get("avatar_url"),
        hashed_pwd=get_password_hash(effective_password),
        role=role,
        email_verified=email_verified,
        phone_verified=phone_verified,
        password_login_enabled=password_login_enabled,
        preferred_login_method=preferred_login_method,
        last_login_method=last_login_method,
    )


def _ensure_settings_for_all_users(session: Session):
    existing_user_ids = {setting.user_id for setting in session.exec(select(Settings)).all()}
    created = 0

    for user in session.exec(select(User)).all():
        if user.uid in existing_user_ids:
            continue
        session.add(Settings(user_id=user.uid))
        created += 1

    if created:
        session.commit()
        print(f"  [ok] 为缺少设置的用户补全默认设置: {created} 条")
    else:
        print("  [ok] 所有用户均已有设置")


def _import_users(session: Session, seed_dir: Path):
    """导入用户数据"""
    data = _load_json(seed_dir / "users.json")
    if not data:
        return

    print("  [用户数据]")

    group_specs = [
        ("certified_users", UserRole.certified, "GovService#2026", "认证主体"),
        ("normal_users", UserRole.normal, "Citizen#2026", "普通用户"),
        ("auth_demo_users", UserRole.normal, "AuthDemo#2026", "认证演示"),
    ]
    imported_counts: Dict[str, int] = {}

    for group_name, default_role, default_password, label in group_specs:
        group_count = 0
        for user_data in data.get(group_name, []):
            user = _build_seed_user(
                user_data,
                default_role=default_role,
                default_password=default_password,
            )
            session.add(user)
            group_count += 1
            identifier = user.login_phone or user.email
            print(f"    + {label}: {user.uname} ({identifier})")
        imported_counts[group_name] = group_count

    session.commit()
    print(
        "  [ok] 导入用户: "
        f"{imported_counts.get('certified_users', 0)} 个认证主体, "
        f"{imported_counts.get('normal_users', 0)} 个普通用户, "
        f"{imported_counts.get('auth_demo_users', 0)} 个认证演示账号\n"
    )


def _import_policy_documents(session: Session, seed_dir: Path):
    """导入政策文档"""
    data = _load_json(seed_dir / "policy_documents.json")
    if not data:
        return

    print("  [政策文档]")

    for doc_data in data.get("documents", []):
        uploader = _resolve_seed_user(
            session,
            doc_data,
            email_key="uploader_email",
            identifier_key="uploader_identifier",
        )
        if not uploader:
            continue

        doc = PolicyDocument(
            title=doc_data["title"],
            content=doc_data["content"],
            category=doc_data.get("category"),
            tags=doc_data.get("tags"),
            uploader_id=uploader.uid,
            status=DocStatus[doc_data.get("status", "approved")],
            view_count=doc_data.get("view_count", 0),
            like_count=doc_data.get("like_count", 0),
            reviewed_time=datetime.now(),
        )
        session.add(doc)
        print(f"    + 文档: {doc.title[:30]}...")

    session.commit()
    print(f"  [ok] 导入政策文档: {len(data.get('documents', []))} 篇\n")


def _import_opinions(session: Session, seed_dir: Path):
    """导入民意评议"""
    data = _load_json(seed_dir / "opinions.json")
    if not data:
        return

    print("  [民意评议]")

    title_to_doc_id = {d.title: d.id for d in session.exec(select(PolicyDocument)).all()}

    type_map = {
        "review": OpinionType.review,
        "correction": OpinionType.correction,
        "message": OpinionType.message
    }

    for opinion_data in data.get("opinions", []):
        doc_id = title_to_doc_id.get(opinion_data["doc_title"])
        user = _resolve_seed_user(session, opinion_data)

        if not doc_id or not user:
            continue

        opinion = Opinion(
            doc_id=doc_id,
            user_id=user.uid,
            opinion_type=type_map.get(opinion_data["opinion_type"], OpinionType.review),
            content=opinion_data["content"],
            rating=opinion_data.get("rating"),
            like_count=opinion_data.get("like_count", 0),
        )
        session.add(opinion)
        print(f"    + 评议: {opinion_data['opinion_type']} - {opinion_data['content'][:20]}...")

    session.commit()
    print(f"  [ok] 导入民意评议: {len(data.get('opinions', []))} 条\n")


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
    print(f"  [ok] 导入解析记录: {len(data.get('chat_messages', []))} 条\n")


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
    print(f"  [ok] 导入待办事项: {len(data.get('todos', []))} 条\n")


def _import_favorites(session: Session, seed_dir: Path):
    """导入收藏"""
    data = _load_json(seed_dir / "favorites.json")
    if not data:
        return

    print("  [收藏记录]")

    chat_messages = session.exec(select(ChatMessage)).all()

    for fav_data in data.get("favorites", []):
        user = _resolve_seed_user(session, fav_data)
        if not user:
            continue

        # 根据索引获取 chat_message_id
        chat_msg_index = fav_data.get("chat_message_index", 0)
        if chat_msg_index < len(chat_messages):
            chat_msg_id = chat_messages[chat_msg_index].id

            fav = Favorite(
                user_id=user.uid,
                chat_message_id=chat_msg_id,
                note=fav_data.get("note"),
            )
            session.add(fav)
            print(f"    + 收藏: {fav_data.get('note', '无备注')[:30]}...")

    session.commit()
    print(f"  [ok] 导入收藏记录: {len(data.get('favorites', []))} 条\n")


def _import_settings(session: Session, seed_dir: Path):
    """导入用户设置"""
    data = _load_json(seed_dir / "settings.json")
    if not data:
        return

    print("  [用户设置]")

    for setting_data in data.get("settings", []):
        user = _resolve_seed_user(session, setting_data)
        if not user:
            continue

        setting = Settings(
            user_id=user.uid,
            default_audience=setting_data.get("default_audience", "none"),
            theme_mode=setting_data.get("theme_mode", "light"),
            color_scheme=setting_data.get("color_scheme", "classic"),
            system_notifications=setting_data.get("system_notifications", True),
        )
        session.add(setting)
        setting_identifier = setting_data.get("user_identifier") or setting_data.get("user_email")
        print(f"    + 设置: 用户 {setting_identifier}")

    session.commit()
    print(f"  [ok] 导入用户设置: {len(data.get('settings', []))} 条\n")


def _import_agent_conversations(session: Session, seed_dir: Path):
    """导入智能体对话"""
    data = _load_json(seed_dir / "agent_conversations.json")
    if not data:
        return

    print("  [智能体对话]")

    for conv_data in data.get("agent_conversations", []):
        user = _resolve_seed_user(session, conv_data)
        if not user:
            continue

        conv = AgentConversation(
            user_id=user.uid,
            title=conv_data["title"],
        )
        session.add(conv)
        print(f"    + 对话: {conv.title}")

    session.commit()
    print(f"  [ok] 导入智能体对话: {len(data.get('agent_conversations', []))} 条\n")


def _import_agent_messages(session: Session, seed_dir: Path):
    """导入智能体消息"""
    data = _load_json(seed_dir / "agent_messages.json")
    if not data:
        return

    print("  [智能体消息]")

    conversations = session.exec(select(AgentConversation)).all()

    for msg_data in data.get("agent_messages", []):
        user = _resolve_seed_user(session, msg_data)
        if not user:
            continue

        conv_index = msg_data.get("conversation_index", 0)
        if conv_index < len(conversations):
            conv_id = conversations[conv_index].id

            msg = AgentMessage(
                conversation_id=conv_id,
                user_id=user.uid,
                role=msg_data["role"],
                content=msg_data["content"],
            )
            session.add(msg)
            print(f"    + 消息: {msg_data['role']} - {msg_data['content'][:20]}...")

    session.commit()
    print(f"  [ok] 导入智能体消息: {len(data.get('agent_messages', []))} 条\n")


def _import_agent_memories(session: Session, seed_dir: Path):
    """导入智能体记忆"""
    data = _load_json(seed_dir / "agent_memories.json")
    if not data:
        return

    print("  [智能体记忆]")

    conversations = session.exec(select(AgentConversation)).all()

    for mem_data in data.get("agent_memories", []):
        user = _resolve_seed_user(session, mem_data)
        if not user:
            continue

        conv_index = mem_data.get("conversation_index", 0)
        if conv_index < len(conversations):
            conv_id = conversations[conv_index].id

            mem = AgentMemory(
                user_id=user.uid,
                conversation_id=conv_id,
                summary=mem_data["summary"],
            )
            session.add(mem)
            print(f"    + 记忆: {mem_data['summary'][:30]}...")

    session.commit()
    print(f"  [ok] 导入智能体记忆: {len(data.get('agent_memories', []))} 条\n")


def _import_stats_analyses(session: Session, seed_dir: Path):
    """导入统计分析"""
    data = _load_json(seed_dir / "stats_analyses.json")
    if not data:
        return

    print("  [统计分析]")

    for stats_data in data.get("stats_analyses", []):
        user = _resolve_seed_user(session, stats_data)
        if not user:
            continue

        stats = StatsAnalysis(
            user_id=user.uid,
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
        stats_identifier = stats_data.get("user_identifier") or stats_data.get("user_email")
        print(f"    + 统计: 用户 {stats_identifier} - 解析 {stats.total_parsed_count} 条")

    session.commit()
    print(f"  [ok] 导入统计分析: {len(data.get('stats_analyses', []))} 条\n")
