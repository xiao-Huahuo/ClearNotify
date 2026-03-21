from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.user import User
from app.schemas.user import *
from app.core.security import get_password_hash
from app.api.deps import get_current_user
from app.core.config import GlobalConfig
from app.services import email_service

# 创建路由器
router = APIRouter()  #在main中被登记为"/user"

#用户注册
@router.post("/", response_model=UserRegisterResponse) #最后返回字段是基于响应DTO(UserRead)过滤后的
def create_user(user: UserCreate, session: Session = Depends(get_session)): #接收注册DTO(UserCreate)
    """
    创建新用户
    :param user:
    :param session:
    :return:
    """
    existing_email = session.exec(select(User).where(User.email == user.email)).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="该邮箱已被注册")

    existing_name = session.exec(select(User).where(User.uname == user.uname)).first()
    if existing_name:
        raise HTTPException(status_code=400, detail="该用户名已存在")

    hashed_pwd = get_password_hash(user.pwd)
    verification_code = email_service.generate_verification_code()

    db_user = User.model_validate(
        user,
        update={
            "hashed_pwd": hashed_pwd,
            "email_verified": False,
            "email_verification_code": verification_code,
            "email_verification_sent_at": datetime.now(),
        },
    )

    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    delivery = email_service.send_verification_email(db_user)
    return UserRegisterResponse(
        user=UserRead(
            uid=db_user.uid,
            uname=db_user.uname,
            email=db_user.email,
            phone=db_user.phone,
            avatar_url=db_user.avatar_url,
            is_admin=db_user.is_admin,
            created_time=db_user.created_time,
            last_login=db_user.last_login,
            email_verified=db_user.email_verified,
        ),
        verification_required=True,
        delivery_channel=delivery["delivery_channel"],
        preview_code=delivery.get("preview_code"),
    )


@router.post("/verify-email")
def verify_email(
    payload: EmailVerificationRequest,
    session: Session = Depends(get_session),
):
    user = session.exec(select(User).where(User.email == payload.email)).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.email_verified:
        return {"message": "邮箱已验证"}
    if not user.email_verification_code or not user.email_verification_sent_at:
        raise HTTPException(status_code=400, detail="验证码不存在，请重新发送")
    if datetime.now() - user.email_verification_sent_at > timedelta(
        minutes=GlobalConfig.EMAIL_VERIFICATION_EXPIRE_MINUTES
    ):
        raise HTTPException(status_code=400, detail="验证码已过期，请重新发送")
    if payload.code != user.email_verification_code:
        raise HTTPException(status_code=400, detail="验证码错误")

    user.email_verified = True
    user.email_verification_code = None
    user.email_verification_sent_at = None
    session.add(user)
    session.commit()
    return {"message": "邮箱验证成功"}


@router.post("/resend-verification")
def resend_verification_email(
    payload: EmailVerificationResendRequest,
    session: Session = Depends(get_session),
):
    user = session.exec(select(User).where(User.email == payload.email)).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.email_verified:
        return {"message": "邮箱已验证", "delivery_channel": "none"}

    user.email_verification_code = email_service.generate_verification_code()
    user.email_verification_sent_at = datetime.now()
    session.add(user)
    session.commit()
    session.refresh(user)

    delivery = email_service.send_verification_email(user)
    return {
        "message": "验证码已重新发送",
        "delivery_channel": delivery["delivery_channel"],
        "preview_code": delivery.get("preview_code"),
    }

#查询个人信息
#Header格式:  Authorization: bearer <你的Access Token>
@router.get("/me",response_model=UserRead)
def get_user(current_user: User = Depends(get_current_user)):
    """
    获取当前登录用户的个人信息
    :param current_user:
    :return:
    """
    return current_user

#修改个人信息(部分更新)
@router.patch("/me",response_model=UserRead)
def update_user(user_in:UserUpdate,session:Session=Depends(get_session),current_user: User = Depends(get_current_user)):
    """
    更新当前登录用户的个人信息
    :param user_in: 更新的用户信息
    :param session:
    :param current_user:
    :return:
    """
    # 1. 提取需要更新的数据的字典 (排除None字段)
    update_data = user_in.model_dump(exclude_unset=True)

    # 2. 如果包含密码，需要特殊处理
    if "pwd" in update_data:
        # 加密新密码
        hashed_password = get_password_hash(update_data["pwd"])
        # 从更新数据中移除明文密码
        del update_data["pwd"]
        # 添加加密后的密码字段
        update_data["hashed_pwd"] = hashed_password

    # 3. 根据字典更新当前用户对象
    current_user.sqlmodel_update(update_data)

    # 4. 保存到数据库
    session.add(current_user)
    session.commit()
    session.refresh(current_user)

    # 5. 返回更新后的用户
    return current_user


@router.post("/request-upgrade")
def request_permission_upgrade(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """普通用户申请提升为管理员权限（向所有管理员发送通知）"""
    if current_user.is_admin:
        raise HTTPException(status_code=400, detail="您已经是管理员")
    # 查找所有管理员
    admins = session.exec(select(User).where(User.is_admin == True)).all()
    if not admins:
        raise HTTPException(status_code=404, detail="暂无管理员可处理申请")
    email_service.send_upgrade_request_email(current_user, admins)
    return {"message": f"申请已提交，已通知 {len(admins)} 位管理员"}


@router.post("/request-downgrade")
def request_permission_downgrade(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """管理员申请降级为普通用户"""
    if not current_user.is_admin:
        raise HTTPException(status_code=400, detail="您不是管理员")
    current_user.is_admin = False
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    email_service.send_role_change_email(current_user, "普通用户")
    return {"message": "已成功降级为普通用户"}
