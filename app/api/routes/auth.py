import asyncio
import random
import secrets
from datetime import datetime, timedelta
from html import escape
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select

from app.api.deps import get_current_user, get_optional_current_user
from app.core.config import GlobalConfig
from app.core.database import get_session
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from app.schemas.auth import (
    BindEmailRequest,
    BindPhoneRequest,
    CaptchaResponse,
    CodeDispatchResponse,
    EmailCodeSendRequest,
    PasswordChangeRequest,
    PasswordLoginRequest,
    PasswordResetRequest,
    PasswordSetRequest,
    PhoneCodeSendRequest,
    PhoneLoginRequest,
    PhoneRegisterRequest,
    RecoveryMethod,
    RecoveryOptionsRequest,
    RecoveryOptionsResponse,
    RecoverySendRequest,
)
from app.schemas.token import Token
from app.schemas.user import UserRead
from app.services import email_service
from app.services.auth_challenge_service import (
    create_captcha,
    get_cooldown_remaining,
    issue_code,
    set_cooldown,
    verify_captcha,
    verify_code,
)
from app.services.auth_identity_service import (
    build_placeholder_email,
    detect_identity_kind,
    get_public_email,
    is_valid_login_phone,
    mask_email,
    mask_phone,
    normalize_email,
    normalize_login_phone,
    password_login_allowed,
    resolve_user_for_identifier,
    resolve_user_for_password_identity,
    to_user_read,
    verification_allows_password_login,
)
from app.services.rate_limit_service import allow_request


router = APIRouter()
_CAPTCHA_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
_captcha_rng = random.SystemRandom()


def _client_ip(request: Request) -> str:
    header = request.headers.get("X-Forwarded-For")
    if header:
        return header.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _issue_access_token(user: User) -> Token:
    access_token_expires = timedelta(days=GlobalConfig.ACCESS_TOKEN_EXPIRE_DAYS)
    access_token = create_access_token(subject=user.uid, expires_delta=access_token_expires)
    return Token(access_token=access_token, token_type="bearer")


def _update_login_tracking(user: User, request: Request, method: str) -> None:
    user.last_login = datetime.now()
    user.last_login_method = method
    user.preferred_login_method = method
    client_ip = _client_ip(request)
    if client_ip:
        user.last_ip = client_ip


def _assert_rate_limit(bucket: str, identifier: str, detail: str) -> None:
    if not allow_request(bucket, identifier):
        raise HTTPException(status_code=429, detail=detail)


def _assert_password_strength(password: str) -> None:
    if len((password or "").strip()) < 6:
        raise HTTPException(status_code=400, detail="密码长度至少为 6 位")


def _assert_confirmed_password(new_password: str, confirm_password: str) -> str:
    normalized = (new_password or "").strip()
    if normalized != (confirm_password or "").strip():
        raise HTTPException(status_code=400, detail="两次输入的密码不一致")
    _assert_password_strength(normalized)
    return normalized


def _password_login_method(identity_kind: str) -> str:
    if identity_kind == "email":
        return "email_password"
    if identity_kind == "phone":
        return "phone_password"
    return "username_password"


def _build_default_phone_username(session: Session, phone: str) -> str:
    suffix = normalize_login_phone(phone)[-4:]
    base_name = f"手机用户{suffix}"
    if not session.exec(select(User).where(User.uname == base_name)).first():
        return base_name

    for _ in range(20):
        candidate = f"{base_name}{secrets.randbelow(90) + 10}"
        if not session.exec(select(User).where(User.uname == candidate)).first():
            return candidate

    return f"{base_name}{secrets.token_hex(2)}"


def _render_captcha_svg(text: str) -> str:
    width = 148
    height = 52
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" rx="14" fill="#130d16"/>',
        '<rect x="1" y="1" width="146" height="50" rx="13" fill="none" stroke="rgba(255,255,255,0.12)"/>',
    ]
    for _ in range(4):
        x1 = _captcha_rng.randint(0, width)
        y1 = _captcha_rng.randint(0, height)
        x2 = _captcha_rng.randint(0, width)
        y2 = _captcha_rng.randint(0, height)
        parts.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="rgba(95,209,255,0.18)" stroke-width="1.2" />'
        )
    for index, ch in enumerate(text):
        x = 24 + index * 24 + _captcha_rng.randint(-2, 2)
        y = 33 + _captcha_rng.randint(-4, 4)
        rotate = _captcha_rng.randint(-16, 16)
        fill = ["#ffcf9f", "#5fd1ff", "#ffd966", "#9bf4bc"][index % 4]
        parts.append(
            f'<text x="{x}" y="{y}" font-size="24" font-weight="700" fill="{fill}" '
            f'transform="rotate({rotate} {x} {y})" font-family="Arial, sans-serif">{escape(ch)}</text>'
        )
    parts.append("</svg>")
    return "".join(parts)


def _send_preview_payload(code: str | None, delivery_channel: str) -> dict[str, Any]:
    return {"preview_code": code if GlobalConfig.AUTH_SANDBOX_SMS else None, "delivery_channel": delivery_channel}


@router.get("/captcha", response_model=CaptchaResponse)
def get_captcha() -> CaptchaResponse:
    text = "".join(secrets.choice(_CAPTCHA_CHARS) for _ in range(4))
    captcha_id = create_captcha(text, GlobalConfig.AUTH_CAPTCHA_EXPIRE_SECONDS)
    return CaptchaResponse(
        captcha_id=captcha_id,
        svg=_render_captcha_svg(text),
        expires_in=GlobalConfig.AUTH_CAPTCHA_EXPIRE_SECONDS,
    )


@router.post("/phone/send-code", response_model=CodeDispatchResponse)
async def send_phone_code(
    payload: PhoneCodeSendRequest,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User | None = Depends(get_optional_current_user),
) -> CodeDispatchResponse:
    phone = normalize_login_phone(payload.phone)
    if not is_valid_login_phone(phone):
        raise HTTPException(status_code=400, detail="请输入有效的中国大陆手机号")
    if payload.purpose != "login" and not verify_captcha(payload.captcha_id or "", payload.captcha_answer or ""):
        raise HTTPException(status_code=400, detail="图形验证码错误或已过期")

    if payload.purpose == "register":
        existing = session.exec(select(User).where(User.login_phone == phone)).first()
        if existing:
            raise HTTPException(status_code=400, detail="该手机号已注册")
    elif payload.purpose == "login":
        existing = session.exec(select(User).where(User.login_phone == phone)).first()
        if not existing:
            raise HTTPException(status_code=404, detail="该手机号尚未注册")
    elif payload.purpose == "reset_password":
        user = session.exec(select(User).where(User.login_phone == phone)).first()
        if not user or not user.phone_verified:
            raise HTTPException(status_code=404, detail="该账号未绑定可用手机号")
    elif payload.purpose == "bind_phone":
        if not current_user:
            raise HTTPException(status_code=401, detail="请先登录后再绑定手机号")
        existing = session.exec(select(User).where(User.login_phone == phone)).first()
        if existing and existing.uid != current_user.uid:
            raise HTTPException(status_code=400, detail="该手机号已被其他账户绑定")

    ip = _client_ip(request)
    _assert_rate_limit("auth_sms_send_ip", ip, "当前请求过于频繁，请稍后再试")
    _assert_rate_limit("auth_sms_send_phone", f"{payload.purpose}:{phone}", "该手机号请求过于频繁，请稍后再试")

    retry_after = get_cooldown_remaining(f"phone:{payload.purpose}", phone)
    if retry_after > 0:
        raise HTTPException(status_code=429, detail=f"请在 {retry_after} 秒后再获取验证码")

    code = email_service.generate_verification_code()
    issue_code(
        "phone",
        payload.purpose,
        phone,
        code,
        GlobalConfig.AUTH_CODE_EXPIRE_MINUTES * 60,
    )
    set_cooldown(f"phone:{payload.purpose}", phone, GlobalConfig.AUTH_SEND_COOLDOWN_SECONDS)
    await asyncio.sleep(0.9)

    extra_payload = _send_preview_payload(code, "sandbox_sms")
    return CodeDispatchResponse(
        message="验证码已发送",
        expires_in=GlobalConfig.AUTH_CODE_EXPIRE_MINUTES * 60,
        retry_after=GlobalConfig.AUTH_SEND_COOLDOWN_SECONDS,
        **extra_payload,
    )


@router.post("/phone/register", response_model=Token)
def phone_register(
    payload: PhoneRegisterRequest,
    request: Request,
    session: Session = Depends(get_session),
) -> Token:
    phone = normalize_login_phone(payload.phone)
    if not is_valid_login_phone(phone):
        raise HTTPException(status_code=400, detail="请输入有效的中国大陆手机号")
    if session.exec(select(User).where(User.login_phone == phone)).first():
        raise HTTPException(status_code=400, detail="该手机号已注册")
    uname = (payload.uname or "").strip()
    if uname:
        if session.exec(select(User).where(User.uname == uname)).first():
            raise HTTPException(status_code=400, detail="该用户名已存在")
    else:
        uname = _build_default_phone_username(session, phone)

    password = (payload.pwd or "").strip()
    if password:
        _assert_password_strength(password)

    ok, reason, _ = verify_code(
        "phone",
        "register",
        phone,
        payload.code,
        max_attempts=GlobalConfig.AUTH_MAX_VERIFY_ATTEMPTS,
    )
    if not ok:
        raise HTTPException(status_code=400, detail="验证码错误或已过期" if reason != "too_many_attempts" else "验证码错误次数过多，请重新获取")

    if password:
        hashed_pwd = get_password_hash(password)
        password_login_enabled = True
        preferred_login_method = "phone_password"
    else:
        hashed_pwd = get_password_hash(secrets.token_urlsafe(24))
        password_login_enabled = False
        preferred_login_method = "phone_code"

    user = User(
        uname=uname,
        email=build_placeholder_email(phone),
        phone=None,
        login_phone=phone,
        hashed_pwd=hashed_pwd,
        email_verified=False,
        phone_verified=True,
        password_login_enabled=password_login_enabled,
        preferred_login_method=preferred_login_method,
        last_login_method="phone_code",
    )
    _update_login_tracking(user, request, "phone_code")
    user.preferred_login_method = preferred_login_method
    session.add(user)
    session.commit()
    session.refresh(user)
    return _issue_access_token(user)


@router.post("/phone/login", response_model=Token)
def phone_login(
    payload: PhoneLoginRequest,
    request: Request,
    session: Session = Depends(get_session),
) -> Token:
    phone = normalize_login_phone(payload.phone)
    if not is_valid_login_phone(phone):
        raise HTTPException(status_code=400, detail="请输入有效的中国大陆手机号")
    user = session.exec(select(User).where(User.login_phone == phone)).first()
    if not user:
        raise HTTPException(status_code=404, detail="该手机号尚未注册")

    ok, reason, _ = verify_code(
        "phone",
        "login",
        phone,
        payload.code,
        max_attempts=GlobalConfig.AUTH_MAX_VERIFY_ATTEMPTS,
    )
    if not ok:
        raise HTTPException(status_code=400, detail="验证码错误或已过期" if reason != "too_many_attempts" else "验证码错误次数过多，请重新获取")

    user.phone_verified = True
    _update_login_tracking(user, request, "phone_code")
    session.add(user)
    session.commit()
    return _issue_access_token(user)


@router.post("/login/password", response_model=Token)
def password_login(
    payload: PasswordLoginRequest,
    request: Request,
    session: Session = Depends(get_session),
) -> Token:
    identity = (payload.identity or "").strip()
    user = resolve_user_for_password_identity(session, identity)
    if not user or not password_login_allowed(user) or not verify_password(payload.password, user.hashed_pwd):
        raise HTTPException(status_code=400, detail="账号或密码错误")
    if not verification_allows_password_login(user):
        raise HTTPException(status_code=403, detail="邮箱尚未验证，请先完成邮箱验证")

    identity_kind = detect_identity_kind(identity)
    _update_login_tracking(user, request, _password_login_method(identity_kind))
    session.add(user)
    session.commit()
    return _issue_access_token(user)


@router.post("/password/recovery/options", response_model=RecoveryOptionsResponse)
def recovery_options(
    payload: RecoveryOptionsRequest,
    session: Session = Depends(get_session),
) -> RecoveryOptionsResponse:
    user = resolve_user_for_identifier(session, payload.identifier)
    methods: list[RecoveryMethod] = []
    if user and user.login_phone and user.phone_verified:
        methods.append(RecoveryMethod(channel="phone", masked_target=mask_phone(user.login_phone), label="手机号验证码"))
    if user:
        public_email = get_public_email(user.email)
        if public_email and user.email_verified:
            methods.append(RecoveryMethod(channel="email", masked_target=mask_email(public_email), label="邮箱验证码"))
    return RecoveryOptionsResponse(identifier=payload.identifier.strip(), methods=methods)


@router.post("/password/recovery/send", response_model=CodeDispatchResponse)
async def send_recovery_code(
    payload: RecoverySendRequest,
    request: Request,
    session: Session = Depends(get_session),
) -> CodeDispatchResponse:
    if not verify_captcha(payload.captcha_id, payload.captcha_answer):
        raise HTTPException(status_code=400, detail="图形验证码错误或已过期")

    user = resolve_user_for_identifier(session, payload.identifier)
    if not user:
        raise HTTPException(status_code=404, detail="未找到可恢复的账户")

    ip = _client_ip(request)
    _assert_rate_limit("auth_recovery_send_ip", ip, "找回请求过于频繁，请稍后再试")

    if payload.channel == "phone":
        if not user.login_phone or not user.phone_verified:
            raise HTTPException(status_code=400, detail="该账户未绑定可用手机号")
        target = normalize_login_phone(user.login_phone)
        retry_after = get_cooldown_remaining("phone:reset_password", target)
        if retry_after > 0:
            raise HTTPException(status_code=429, detail=f"请在 {retry_after} 秒后再获取验证码")
        code = email_service.generate_verification_code()
        issue_code("phone", "reset_password", target, code, GlobalConfig.AUTH_CODE_EXPIRE_MINUTES * 60)
        set_cooldown("phone:reset_password", target, GlobalConfig.AUTH_SEND_COOLDOWN_SECONDS)
        await asyncio.sleep(0.9)
        extra_payload = _send_preview_payload(code, "sandbox_sms")
        return CodeDispatchResponse(
            message="验证码已发送到绑定手机号",
            expires_in=GlobalConfig.AUTH_CODE_EXPIRE_MINUTES * 60,
            retry_after=GlobalConfig.AUTH_SEND_COOLDOWN_SECONDS,
            **extra_payload,
        )

    public_email = get_public_email(user.email)
    if not public_email or not user.email_verified:
        raise HTTPException(status_code=400, detail="该账户未绑定可用邮箱")
    retry_after = get_cooldown_remaining("email:reset_password", public_email)
    if retry_after > 0:
        raise HTTPException(status_code=429, detail=f"请在 {retry_after} 秒后再获取验证码")
    code = email_service.generate_verification_code()
    issue_code("email", "reset_password", public_email, code, GlobalConfig.AUTH_CODE_EXPIRE_MINUTES * 60)
    delivery = email_service.send_code_email(public_email, code, "reset_password")
    set_cooldown("email:reset_password", public_email, GlobalConfig.AUTH_SEND_COOLDOWN_SECONDS)
    await asyncio.sleep(0.6)
    return CodeDispatchResponse(
        message="验证码已发送到绑定邮箱",
        expires_in=GlobalConfig.AUTH_CODE_EXPIRE_MINUTES * 60,
        retry_after=GlobalConfig.AUTH_SEND_COOLDOWN_SECONDS,
        delivery_channel=delivery["delivery_channel"],
        preview_code=delivery.get("preview_code"),
    )


@router.post("/password/reset")
def reset_password(
    payload: PasswordResetRequest,
    session: Session = Depends(get_session),
) -> dict[str, str]:
    user = resolve_user_for_identifier(session, payload.identifier)
    if not user:
        raise HTTPException(status_code=404, detail="账户不存在")

    new_password = _assert_confirmed_password(payload.new_password, payload.confirm_password)
    if payload.channel == "phone":
        if not user.login_phone or not user.phone_verified:
            raise HTTPException(status_code=400, detail="该账户未绑定可用手机号")
        ok, reason, _ = verify_code(
            "phone",
            "reset_password",
            normalize_login_phone(user.login_phone),
            payload.code,
            max_attempts=GlobalConfig.AUTH_MAX_VERIFY_ATTEMPTS,
        )
    else:
        public_email = get_public_email(user.email)
        if not public_email or not user.email_verified:
            raise HTTPException(status_code=400, detail="该账户未绑定可用邮箱")
        ok, reason, _ = verify_code(
            "email",
            "reset_password",
            public_email,
            payload.code,
            max_attempts=GlobalConfig.AUTH_MAX_VERIFY_ATTEMPTS,
        )
    if not ok:
        raise HTTPException(status_code=400, detail="验证码错误或已过期" if reason != "too_many_attempts" else "验证码错误次数过多，请重新获取")

    user.hashed_pwd = get_password_hash(new_password)
    user.password_login_enabled = True
    session.add(user)
    session.commit()
    return {"message": "密码已重置，请使用新密码登录"}


@router.post("/password/set")
def set_password(
    payload: PasswordSetRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    if current_user.password_login_enabled:
        raise HTTPException(status_code=400, detail="当前账户已设置登录密码")
    new_password = _assert_confirmed_password(payload.new_password, payload.confirm_password)
    current_user.hashed_pwd = get_password_hash(new_password)
    current_user.password_login_enabled = True
    session.add(current_user)
    session.commit()
    return {"message": "密码设置成功"}


@router.post("/password/change")
def change_password(
    payload: PasswordChangeRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    if not current_user.password_login_enabled:
        raise HTTPException(status_code=400, detail="当前账户尚未设置登录密码")
    if not verify_password(payload.current_password, current_user.hashed_pwd):
        raise HTTPException(status_code=400, detail="当前密码错误")
    new_password = _assert_confirmed_password(payload.new_password, payload.confirm_password)
    current_user.hashed_pwd = get_password_hash(new_password)
    session.add(current_user)
    session.commit()
    return {"message": "密码修改成功"}


@router.post("/email/send-code", response_model=CodeDispatchResponse)
async def send_bind_email_code(
    payload: EmailCodeSendRequest,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> CodeDispatchResponse:
    if not verify_captcha(payload.captcha_id, payload.captcha_answer):
        raise HTTPException(status_code=400, detail="图形验证码错误或已过期")
    email = normalize_email(payload.email)
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="请输入有效邮箱地址")

    existing = session.exec(select(User).where(User.email == email)).first()
    if existing and existing.uid != current_user.uid:
        raise HTTPException(status_code=400, detail="该邮箱已被其他账户绑定")

    ip = _client_ip(request)
    _assert_rate_limit("auth_email_send_ip", ip, "邮箱验证码请求过于频繁，请稍后再试")
    _assert_rate_limit("auth_email_send_target", f"bind_email:{email}", "该邮箱请求过于频繁，请稍后再试")

    retry_after = get_cooldown_remaining("email:bind_email", email)
    if retry_after > 0:
        raise HTTPException(status_code=429, detail=f"请在 {retry_after} 秒后再获取验证码")

    code = email_service.generate_verification_code()
    issue_code("email", "bind_email", email, code, GlobalConfig.AUTH_CODE_EXPIRE_MINUTES * 60)
    delivery = email_service.send_code_email(email, code, "bind_email")
    set_cooldown("email:bind_email", email, GlobalConfig.AUTH_SEND_COOLDOWN_SECONDS)
    await asyncio.sleep(0.6)

    return CodeDispatchResponse(
        message="验证码已发送到邮箱",
        expires_in=GlobalConfig.AUTH_CODE_EXPIRE_MINUTES * 60,
        retry_after=GlobalConfig.AUTH_SEND_COOLDOWN_SECONDS,
        delivery_channel=delivery["delivery_channel"],
        preview_code=delivery.get("preview_code"),
    )


@router.post("/email/bind", response_model=UserRead)
def bind_email(
    payload: BindEmailRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> UserRead:
    email = normalize_email(payload.email)
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="请输入有效邮箱地址")
    existing = session.exec(select(User).where(User.email == email)).first()
    if existing and existing.uid != current_user.uid:
        raise HTTPException(status_code=400, detail="该邮箱已被其他账户绑定")

    ok, reason, _ = verify_code(
        "email",
        "bind_email",
        email,
        payload.code,
        max_attempts=GlobalConfig.AUTH_MAX_VERIFY_ATTEMPTS,
    )
    if not ok:
        raise HTTPException(status_code=400, detail="验证码错误或已过期" if reason != "too_many_attempts" else "验证码错误次数过多，请重新获取")

    current_user.email = email
    current_user.email_verified = True
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return to_user_read(current_user)


@router.post("/phone/bind", response_model=UserRead)
def bind_phone(
    payload: BindPhoneRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> UserRead:
    phone = normalize_login_phone(payload.phone)
    if not is_valid_login_phone(phone):
        raise HTTPException(status_code=400, detail="请输入有效的中国大陆手机号")
    existing = session.exec(select(User).where(User.login_phone == phone)).first()
    if existing and existing.uid != current_user.uid:
        raise HTTPException(status_code=400, detail="该手机号已被其他账户绑定")

    ok, reason, _ = verify_code(
        "phone",
        "bind_phone",
        phone,
        payload.code,
        max_attempts=GlobalConfig.AUTH_MAX_VERIFY_ATTEMPTS,
    )
    if not ok:
        raise HTTPException(status_code=400, detail="验证码错误或已过期" if reason != "too_many_attempts" else "验证码错误次数过多，请重新获取")

    current_user.login_phone = phone
    current_user.phone_verified = True
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return to_user_read(current_user)
