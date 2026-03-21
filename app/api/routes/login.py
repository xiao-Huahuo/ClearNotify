from datetime import timedelta, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select

from app.core.config import GlobalConfig
from app.core.database import get_session
from app.core.security import create_access_token, verify_password
from app.models.user import User
from app.schemas.token import Token

router = APIRouter()


# 用户登录
@router.post("/", response_model=Token)
def login_access_token(
        session: Session = Depends(get_session),
        form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """
    OAuth2兼容的access-token验证登录接口
    """
    statement = select(User).where(User.uname == form_data.username)
    user = session.exec(statement).first()

    if not user or not verify_password(form_data.password, user.hashed_pwd):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    if not user.email_verified:
        raise HTTPException(status_code=403, detail="邮箱未验证，请先完成邮箱验证")

    user.last_login = datetime.now()
    session.add(user)
    session.commit()

    access_token_expires = timedelta(days=GlobalConfig.ACCESS_TOKEN_EXPIRE_DAYS)
    access_token = create_access_token(
        subject=user.uid, expires_delta=access_token_expires
    )

    return Token(access_token=access_token, token_type="bearer")
