from typing import Optional, Dict, Any
from sqlmodel import SQLModel
from app.models.stats_analysis import StatsAnalysisBase

# 新增 DTO (通常由后端跑批处理生成，前端不需要传入)
class StatsAnalysisCreate(StatsAnalysisBase):
    pass

# 响应 DTO (将 JSON 字符串还原为字典，方便前端直接使用)
class StatsAnalysisRead(SQLModel):
    id: int
    materials_freq: Dict[str, int]
    risks_freq: Dict[str, int]
    complexity_distribution: Dict[str, int]
    notice_type_distribution: Dict[str, int]
    
    # 新增节省时间的数据结构
    total_time_saved_minutes: int
    avg_time_saved_minutes: int
    time_saved_distribution: Dict[str, int]

    total_parsed_count: int
    user_id: Optional[int]
    rag_metrics: Dict[str, Any] = {}
    rag_series: Dict[str, Any] = {}
    vector_scatter: list[Dict[str, Any]] = []
