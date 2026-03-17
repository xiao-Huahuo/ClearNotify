from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.user import User
from app.models.settings import Settings
from app.schemas.settings import SettingsRead, SettingsUpdate
from app.api.deps import get_current_user

router = APIRouter()

@router.get("/me", response_model=SettingsRead)
def get_my_settings(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户的设置。如果不存在，则创建一个默认设置并返回。
    """
    statement = select(Settings).where(Settings.user_id == current_user.uid)
    settings = session.exec(statement).first()
    
    if not settings:
        # 如果没有找到设置，为其创建默认设置
        settings = Settings(user_id=current_user.uid)
        session.add(settings)
        session.commit()
        session.refresh(settings)
        
    return settings

@router.patch("/me", response_model=SettingsRead)
def update_my_settings(
    settings_in: SettingsUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    更新当前用户的设置。
    """
    statement = select(Settings).where(Settings.user_id == current_user.uid)
    settings = session.exec(statement).first()
    
    if not settings:
        # 如果没有，则先创建
        settings = Settings(user_id=current_user.uid)
        session.add(settings)
        session.commit()
        session.refresh(settings)
        
    # 只更新传入的字段
    update_data = settings_in.model_dump(exclude_unset=True)
    settings.sqlmodel_update(update_data)
    
    session.add(settings)
    session.commit()
    session.refresh(settings)
    
    return settings
