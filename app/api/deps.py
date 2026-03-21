from typing import Generator, Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlmodel import Session

from app.core import security
from app.core.config import GlobalConfig
from app.core.database import get_session
from app.models.user import User
from app.schemas.token import TokenPayload

# OAuth2 方案
# tokenUrl 指向登录接口的路径，Swagger UI 会用它来获取 Token
# OAuth2PasswordBearer类对应的请求Header格式:  Authorization: bearer <你的Access Token>
reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl="/"  # 注意：这里要跟 login.py 里的路由一致
)


# 获取当前用户
def get_current_user(
        session: Session = Depends(get_session),
        token: str = Depends(reusable_oauth2)
) -> User:
    """
    解析 Token 并返回当前用户对象,可用于判断登录状态
    """
    try:
        # 解密 Token
        payload = jwt.decode(
            token, GlobalConfig.SECRET_KEY, algorithms=[GlobalConfig.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
        # 解密失败,抛出403
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )

    # 从 Token 中获取 User ID (sub)
    # 注意：TokenPayload 里的 sub 可能是 int 也可能是 str，视生成时的情况而定
    # 我们在 security.py 里生成时用了 str(subject)

    # 用户不存在抛出404
    if token_data.sub is None:
        raise HTTPException(status_code=404, detail="User not found")

    user = session.get(User, int(token_data.sub))

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


def get_current_user_from_token_value(session: Session, token: str) -> User:
    try:
        payload = jwt.decode(
            token, GlobalConfig.SECRET_KEY, algorithms=[GlobalConfig.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )

    if token_data.sub is None:
        raise HTTPException(status_code=404, detail="User not found")

    user = session.get(User, int(token_data.sub))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user
