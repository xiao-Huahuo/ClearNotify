from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AgentRunRequest(BaseModel):
    original_text: str = Field(..., description="原始通知文本")
    file_url: Optional[str] = Field(default=None, description="原文件 URL")
    goal: Optional[str] = Field(default=None, description="任务目标")
    scene: Optional[str] = Field(default=None, description="场景描述")
    use_rag: bool = Field(default=True, description="是否启用 RAG")
    top_k: int = Field(default=5, ge=1, le=10, description="RAG 检索条数")
    save_to_history: bool = Field(default=True, description="是否保存到历史")


class AgentEvidence(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    score: float = 0.0
    snippet: str = ""
    tags: List[str] = []


class AgentRunResponse(BaseModel):
    agent_name: str
    parse_mode: str
    confidence: float
    summary: str
    structured: Dict[str, Any]
    checklist: List[Dict[str, Any]]
    timeline: List[Dict[str, Any]]
    process_steps: List[str]
    materials: List[str]
    notices: List[str]
    risks: List[str]
    rag_metrics: Dict[str, Any]
    evidence: List[AgentEvidence]
    chat_message_id: Optional[int] = None
