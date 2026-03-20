from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.user import User
from app.schemas.user import *
from app.core.security import get_password_hash
from app.api.deps import get_current_user

# 创建路由器
router = APIRouter()  #在main中被登记为"/user"

#用户注册
@router.post("/", response_model=UserRead) #最后返回字段是基于响应DTO(UserRead)过滤后的
def create_user(user: UserCreate, session: Session = Depends(get_session)): #接收注册DTO(UserCreate)
    """
    创建新用户
    :param user:
    :param session:
    :return:
    """
    # 1. 检查邮箱是否已存在 (可选，但推荐)
    # ... (先略过，为了简单，以后再加)

    # 2. 加密密码
    hashed_pwd = get_password_hash(user.pwd)

    # 3. 创建数据库模型实例
    # 用User.model_validate方法(继承SQLModel),接收UserCreate的全部字段并输出给新的User模型,同时更新hashed_pwd字段为加密后的密码
    db_user = User.model_validate(user, update={"hashed_pwd": hashed_pwd})

    # 4. 存入数据库
    session.add(db_user)
    session.commit()
    session.refresh(db_user) # 刷新以获取生成的 uid 和 created_time

    # 5. 返回
    return db_user #最后返回User模型,然后基于"response_model=UserRead"过滤,返回一个UserRead给前端

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
    # TODO: 接入邮件系统后，向每位管理员发送邮件通知
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
    # TODO: 接入邮件系统后，发送降级确认邮件
    return {"message": "已成功降级为普通用户"}