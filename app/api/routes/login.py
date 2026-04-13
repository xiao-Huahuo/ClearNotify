from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from app.core.config import GlobalConfig
from app.core.database import get_session
from app.core.security import create_access_token, verify_password
from app.schemas.token import Token
from app.services.auth_identity_service import (
    detect_identity_kind,
    password_login_allowed,
    resolve_user_for_password_identity,
    verification_allows_password_login,
)


router = APIRouter()


@router.post("/", response_model=Token)
def login_access_token(
    request: Request,
    session: Session = Depends(get_session),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    identity = (form_data.username or "").strip()
    user = resolve_user_for_password_identity(session, identity)

    if not user or not password_login_allowed(user) or not verify_password(form_data.password, user.hashed_pwd):
        raise HTTPException(status_code=400, detail="Incorrect identity or password")
    if not verification_allows_password_login(user):
        raise HTTPException(status_code=403, detail="邮箱尚未验证，请先完成邮箱验证")

    user.last_login = datetime.now()
    identity_kind = detect_identity_kind(identity)
    if identity_kind == "email":
        user.last_login_method = "email_password"
    elif identity_kind == "phone":
        user.last_login_method = "phone_password"
    else:
        user.last_login_method = "username_password"
    user.preferred_login_method = user.last_login_method
    client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else None)
    if client_ip:
        user.last_ip = client_ip.split(",")[0].strip()
    session.add(user)
    session.commit()

    access_token_expires = timedelta(days=GlobalConfig.ACCESS_TOKEN_EXPIRE_DAYS)
    access_token = create_access_token(subject=user.uid, expires_delta=access_token_expires)
    return Token(access_token=access_token, token_type="bearer")
