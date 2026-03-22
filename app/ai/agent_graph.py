import os
from typing import Any, Callable, Dict, List, Optional

from langchain_core.messages import SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from app.ai.document_parser import parse_document
from app.core.config import GlobalConfig
from app.services import rag_service
from app.services.agent_memory_service import (
    build_session_summary,
    get_or_create_session_memory,
    update_session_memory,
)


def _build_llm() -> ChatOpenAI:
    api_key = GlobalConfig.MOONSHOT_API_KEY
    if not api_key:
        raise ValueError("MOONSHOT_API_KEY is not set in environment variables (check .env file)")
    timeout = float(GlobalConfig.MOONSHOT_API_TIMEOUT)
    model = os.getenv(GlobalConfig.MOONSHOT_MODEL)
    return ChatOpenAI(
        api_key=api_key,
        base_url="https://api.moonshot.cn/v1",
        model=model,
        temperature=0.3,
        timeout=timeout,
    )


def _shrink_text(text: str, max_chars: int = 8000) -> str:
    if not text:
        return ""
    if len(text) <= max_chars:
        return text
    head = text[: int(max_chars * 0.6)]
    tail = text[-int(max_chars * 0.4) :]
    return f"{head}\n\n[内容过长，已截断]\n\n{tail}"


def _truncate(text: str, max_chars: int = 400) -> str:
    if not text:
        return ""
    if len(text) <= max_chars:
        return text
    return f"{text[:max_chars]}..."


def run_agent_graph(
    user_id: int,
    original_text: str,
    top_k: int = 5,
    history: Optional[List[Dict[str, str]]] = None,
    conversation_id: Optional[int] = None,
    user_audience_label: str = "通用",
    trace_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> Dict[str, Any]:
    tool_state: Dict[str, Any] = {}
    safe_text = _shrink_text(original_text)

    tool_state["tool_calls"] = []

    def _record_tool(name: str, input_text: str, output_hint: str) -> None:
        entry = {
            "tool": name,
            "input": _truncate(input_text, 200),
            "output": _truncate(output_hint, 200),
        }
        tool_state["tool_calls"].append(entry)
        if trace_callback:
            trace_callback(entry)

    @tool("extract_structured")
    def extract_structured(text: str) -> Dict[str, Any]:
        """从通知文本中抽取结构化字段。"""
        parsed_base, parse_mode = parse_document(text, user_id)
        parsed = parsed_base.model_dump()
        tool_state["structured"] = parsed
        tool_state["parse_mode"] = parse_mode
        _record_tool("extract_structured", text, f"字段数: {len(parsed.keys())}")
        return {"structured": parsed, "parse_mode": parse_mode}

    @tool("rag_search")
    def rag_search(query: str) -> Dict[str, Any]:
        """检索与通知相关的知识证据。"""
        items = rag_service.search_related_context(
            query,
            top_k=top_k,
            user_id=user_id,
            source="agent_run_graph",
        )
        evidence = []
        for item in items:
            evidence.append(
                {
                    "title": item.get("title"),
                    "category": item.get("category"),
                    "score": round(float(item.get("score", 0)), 3),
                    "snippet": str(item.get("content", ""))[:160],
                    "tags": item.get("tags", []),
                }
            )
        tool_state["evidence"] = evidence
        _record_tool("rag_search", query, f"命中证据: {len(evidence)}")
        return {"evidence": evidence}

    @tool("summarize_text")
    def summarize_text(text: str) -> Dict[str, Any]:
        """当文本过长时进行压缩提示。"""
        hint = _shrink_text(text, max_chars=3000)
        _record_tool("summarize_text", text, "已生成压缩提示")
        return {"summary_hint": hint}

    memory = None
    if conversation_id:
        memory = get_or_create_session_memory(user_id=user_id, conversation_id=conversation_id)

    memory_text = ""
    if memory:
        memory_text = memory.get("summary", "") or ""

    system = SystemMessage(
        content=(
            "你是通知办理智能体。你必须先调用 extract_structured 获取结构化信息，"
            "必要时调用 rag_search 补充证据，再基于这些信息给出高质量的 Markdown 回复。"
            "禁止输出 JSON 或无意义模板话术。\n\n"
            f"用户偏好视角：{user_audience_label}\n"
            f"会话记忆摘要：{memory_text if memory_text else '暂无'}"
        )
    )

    llm = _build_llm()
    agent = create_react_agent(llm, [extract_structured, rag_search, summarize_text])
    messages: List[Any] = [system]
    if history:
        for item in history[-6:]:
            role = item.get("role")
            content = _shrink_text(item.get("content", ""), max_chars=1200)
            if role in ("user", "assistant") and content:
                messages.append((role, content))
    messages.append(("user", safe_text))

    result = agent.invoke(
        {
            "messages": messages,
        },
        config={"recursion_limit": 6},
    )
    messages = result.get("messages", [])
    assistant_reply = ""
    if messages:
        assistant_reply = messages[-1].content or ""

    # 更新会话记忆
    if conversation_id:
        try:
            summary = build_session_summary(
                user_input=safe_text,
                assistant_reply=assistant_reply,
                previous_summary=memory_text,
            )
            update_session_memory(user_id=user_id, conversation_id=conversation_id, summary=summary)
        except Exception:
            pass

    return {
        "assistant_reply": assistant_reply,
        "tool_state": tool_state,
        "safe_text": safe_text,
    }
