from fastapi import APIRouter, Depends
from sqlmodel import Session
from app.core.database import get_session
from app.models.user import User
from app.api.deps import get_current_user
from app.schemas.stats_analysis import StatsAnalysisRead
from app.services import stats_service

router = APIRouter()

@router.get("/me", response_model=StatsAnalysisRead)
def get_my_stats(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    获取当前登录用户的所有通知解析统计数据。
    该接口底层使用了自研的纯算法（分词）进行高频词统计。
    """
    stats_dict = stats_service.generate_user_stats(session, current_user.uid)
    
    return StatsAnalysisRead(
        id=0, # 动态生成的无ID
        user_id=current_user.uid,
        materials_freq=stats_dict["materials_freq"],
        risks_freq=stats_dict["risks_freq"],
        complexity_distribution=stats_dict["complexity_distribution"],
        notice_type_distribution=stats_dict["notice_type_distribution"],
        total_time_saved_minutes=stats_dict["total_time_saved_minutes"],
        avg_time_saved_minutes=stats_dict["avg_time_saved_minutes"],
        time_saved_distribution=stats_dict["time_saved_distribution"],
        total_parsed_count=stats_dict["total_parsed_count"],
        rag_metrics=stats_dict.get("rag_metrics", {}),
        rag_series=stats_dict.get("rag_series", {}),
        vector_scatter=stats_dict.get("vector_scatter", []),
    )
