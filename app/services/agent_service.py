import json
import re
from typing import Any, Callable, Dict, List, Optional

from sqlmodel import Session, select

from app.ai.document_parser import parse_document
from app.ai.agent_graph import run_agent_graph
from app.models.chat_message import ChatMessage
from app.models.settings import Settings
from app.services import chat_message_service, rag_service, agent_chat_service

AGENT_NAME = "通知办理智能体"

_SPLIT_PATTERN = re.compile(r"[，,；;。\n、]+")
_DATE_PATTERN = re.compile(r"(\d{4}年\d{1,2}月\d{1,2}日|\d{4}-\d{1,2}-\d{1,2}|\d{1,2}月\d{1,2}日)")


def _split_items(text: Optional[str]) -> List[str]:
    if not text:
        return []
    items = [item.strip() for item in _SPLIT_PATTERN.split(text) if item.strip()]
    return items[:12]


def _build_steps(process_text: Optional[str]) -> List[str]:
    steps = _split_items(process_text)
    if steps:
        return steps
    return ["准备材料", "提交申请或办理", "等待审核或处理", "领取结果或完成办理"]


def _build_materials(materials_text: Optional[str]) -> List[str]:
    materials = _split_items(materials_text)
    return materials if materials else ["身份证明材料", "申请表或登记材料", "相关证明材料"]


def _build_notices(precautions: Optional[str], risk_warnings: Optional[str]) -> List[str]:
    notices = _split_items(precautions) + _split_items(risk_warnings)
    if notices:
        return notices
    return ["注意核对材料完整性", "关注时间节点与截止日期", "避免信息填写错误"]


def _build_risks(risk_warnings: Optional[str]) -> List[str]:
    risks = _split_items(risk_warnings)
    if risks:
        return risks
    return ["材料缺失可能导致退回", "超过截止时间可能失效"]


def _build_timeline(time_deadline: Optional[str], original_text: str) -> List[Dict[str, Any]]:
    timeline: List[Dict[str, Any]] = []
    if time_deadline:
        timeline.append({"time": time_deadline, "event": "截止时间或办理节点"})
    matches = _DATE_PATTERN.findall(original_text or "")
    for date_text in matches[:3]:
        if time_deadline and date_text in time_deadline:
            continue
        timeline.append({"time": date_text, "event": "原文提及的时间点"})
    if not timeline:
        timeline.append({"time": "待确认", "event": "请结合原文确认时间节点"})
    return timeline


def _build_checklist(steps: List[str], materials: List[str]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for step in steps[:4]:
        items.append({"label": step, "status": "pending", "type": "step"})
    for material in materials[:4]:
        items.append({"label": material, "status": "pending", "type": "material"})
    return items


def _build_summary(parsed: Dict[str, Any]) -> str:
    matter = parsed.get("handling_matter") or "办理事项"
    audience = parsed.get("target_audience") or "适用人群"
    time_deadline = parsed.get("time_deadline") or "待确认"
    return f"本次为 {matter}，面向 {audience}，关键时间节点：{time_deadline}。"


def _build_rag_query(parsed: Dict[str, Any], original_text: str) -> str:
    return "\n".join(
        filter(
            None,
            [
                parsed.get("handling_matter"),
                parsed.get("required_materials"),
                parsed.get("risk_warnings"),
                (original_text or "")[:500],
            ],
        )
    )


def run_agent(
    session: Session,
    user_id: int,
    original_text: str,
    file_url: Optional[str],
    goal: Optional[str],
    scene: Optional[str],
    use_rag: bool = True,
    top_k: int = 5,
    save_to_history: bool = True,
    conversation_id: Optional[int] = None,
    trace_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> Dict[str, Any]:
    graph_reply = ""
    tool_state: Dict[str, Any] = {}
    safe_text = original_text
    history_payload: List[Dict[str, str]] = []
    if conversation_id:
        try:
            items = agent_chat_service.get_messages(session, user_id, conversation_id)
            history_payload = [
                {"role": item.role, "content": item.content}
                for item in items[-8:]
                if item.role in ("user", "assistant") and item.content
            ]
            if history_payload and history_payload[-1]["role"] == "user" and history_payload[-1]["content"] == original_text:
                history_payload = history_payload[:-1]
        except Exception:
            history_payload = []
    try:
        graph_result = run_agent_graph(
            user_id=user_id,
            original_text=original_text,
            top_k=top_k,
            history=history_payload,
            conversation_id=conversation_id,
            user_audience_label=user_audience_label,
            trace_callback=trace_callback,
        )
        graph_reply = graph_result.get("assistant_reply", "") or ""
        tool_state = graph_result.get("tool_state", {}) or {}
        safe_text = graph_result.get("safe_text", original_text) or original_text
    except Exception:
        graph_reply = ""
        tool_state = {}
        safe_text = original_text

    parsed = tool_state.get("structured")
    parse_mode = tool_state.get("parse_mode")
    if not parsed or not parse_mode:
        parsed_base, parse_mode = parse_document(safe_text, user_id)
        parsed = parsed_base.model_dump()
    parsed["file_url"] = file_url or parsed.get("file_url")

    steps = _build_steps(parsed.get("handling_process"))
    materials = _build_materials(parsed.get("required_materials"))
    notices = _build_notices(parsed.get("precautions"), parsed.get("risk_warnings"))
    risks = _build_risks(parsed.get("risk_warnings"))
    timeline = _build_timeline(parsed.get("time_deadline"), original_text)
    checklist = _build_checklist(steps, materials)
    summary = _build_summary(parsed)

    evidence: List[Dict[str, Any]] = []
    avg_score = 0.0
    result_count = 0
    if use_rag:
        if tool_state.get("evidence"):
            evidence = tool_state.get("evidence", [])
            result_count = len(evidence)
            avg_score = sum(item.get("score", 0) for item in evidence) / result_count if result_count else 0.0
        else:
            query = _build_rag_query(parsed, safe_text)
            items = rag_service.search_related_context(
                query,
                top_k=top_k,
                user_id=user_id,
                source="agent_run",
            )
            result_count = len(items)
            avg_score = sum(item.get("score", 0) for item in items) / result_count if result_count else 0.0
            for item in items:
                content = str(item.get("content", ""))[:160]
                evidence.append(
                    {
                        "title": item.get("title"),
                        "category": item.get("category"),
                        "score": round(float(item.get("score", 0)), 3),
                        "snippet": content,
                        "tags": item.get("tags", []),
                    }
                )

    confidence = 0.35
    if parse_mode == "ai":
        confidence += 0.2
    if use_rag:
        confidence += min(avg_score, 1.0) * 0.45
    confidence = round(min(confidence, 0.95), 3)

    chat_message_id = None
    user_audience_label = "通用"
    try:
        settings = session.exec(select(Settings).where(Settings.user_id == user_id)).first()
        if settings:
            mapping = {
                "elderly": "老年版",
                "student": "学生版",
                "worker": "职场版",
                "none": "通用",
            }
            user_audience_label = mapping.get(settings.default_audience, "通用")
    except Exception:
        pass

    if save_to_history:
        analysis_payload = {
            "parse_mode": parse_mode,
            "agent_name": AGENT_NAME,
            "confidence": confidence,
            "goal": goal,
            "scene": scene,
        }
        parsed["chat_analysis"] = json.dumps(analysis_payload, ensure_ascii=False)
        message: ChatMessage = chat_message_service.create_message_from_payload(
            session=session,
            message_payload=parsed,
            user_id=user_id,
        )
        chat_message_id = message.id

    return {
        "agent_name": AGENT_NAME,
        "parse_mode": parse_mode,
        "confidence": confidence,
        "summary": summary,
        "structured": parsed,
        "assistant_reply": graph_reply,
        "tool_calls": tool_state.get("tool_calls", []),
        "checklist": checklist,
        "timeline": timeline,
        "process_steps": steps,
        "materials": materials,
        "notices": notices,
        "risks": risks,
        "rag_metrics": {
            "result_count": result_count,
            "avg_score": round(avg_score, 3),
            "hit_rate": 1.0 if result_count > 0 else 0.0,
        },
        "evidence": evidence,
        "chat_message_id": chat_message_id,
        "user_audience": user_audience_label,
    }


def _is_json_like(text: str) -> bool:
    if not text:
        return False
    t = text.strip()
    if (t.startswith("{") and t.endswith("}")) or (t.startswith("[") and t.endswith("]")):
        return True
    if re.search(r"\"[^\"]+\"\\s*:", t):
        return True
    return False


_NOISE_PHRASES = [
    "本次为咨询使用的LLM",
    "关键时间节点",
    "办理流程：",
    "材料清单：",
    "注意事项：",
    "风险提示：",
]


def _strip_noise(text: Optional[str]) -> str:
    if not text:
        return ""
    t = text.strip()
    if not t or _is_json_like(t):
        return ""
    for phrase in _NOISE_PHRASES:
        if phrase in t:
            return ""
    return t


def _clean_items(items: List[str]) -> List[str]:
    cleaned: List[str] = []
    seen = set()
    for item in items:
        t = _strip_noise(str(item))
        if not t or len(t) < 2:
            continue
        if t in seen:
            continue
        cleaned.append(t)
        seen.add(t)
    return cleaned


def _format_list(items: List[str], fallback: str) -> List[str]:
    if not items:
        return [f"- {fallback}"]
    return [f"- {item}" for item in items]


def build_agent_reply(result: Dict[str, Any], user_text: str | None = None) -> str:
    audience_label = "通用"
    if result.get("user_audience"):
        audience_label = str(result.get("user_audience"))

    structured = result.get("structured", {}) or {}
    has_core = any(
        structured.get(key)
        for key in [
            "handling_matter",
            "required_materials",
            "handling_process",
            "time_deadline",
            "precautions",
            "risk_warnings",
        ]
    )
    if not has_core:
        return (
            "目前没有识别到明确的通知要点。\n\n"
            "请补充更完整的通知内容或上传原文件，我可以继续拆解办理步骤、材料清单与时间节点。"
        )

    handling_matter = _strip_noise(structured.get("handling_matter")) or "办理事项"
    target = _strip_noise(structured.get("target_audience")) or "适用对象"
    time_deadline = _strip_noise(structured.get("time_deadline")) or "待确认"
    location = _strip_noise(structured.get("location_entrance")) or "待确认"
    summary = _strip_noise(result.get("summary")) or f"事项：{handling_matter}；对象：{target}；时间：{time_deadline}。"

    steps = _clean_items(list(result.get("process_steps", []) or []))[:6]
    materials = _clean_items(list(result.get("materials", []) or []))[:6]
    notices = _clean_items(list(result.get("notices", []) or []))[:5]
    risks = _clean_items(list(result.get("risks", []) or []))[:4]

    lines: List[str] = []
    lines.append("## 结论概览")
    lines.append(f"- 办理事项：{handling_matter}")
    lines.append(f"- 适用对象：{target}")
    lines.append(f"- 关键时间：{time_deadline}")
    lines.append(f"- 地点/入口：{location}")
    lines.append(f"- 简要判断：{summary}")
    lines.append("")

    lines.append("## 你需要做什么")
    lines.extend(_format_list(steps, "先确认办理渠道与提交方式（线上/线下）"))
    lines.append("说明：以上步骤会结合通知原文持续细化。")
    lines.append("")

    lines.append("## 材料与准备")
    lines.extend(_format_list(materials, "准备身份与申请相关的基础材料"))
    lines.append("建议：如材料不齐，先补齐关键材料再提交，以避免退回。")
    lines.append("")

    lines.append("## 时间节点")
    lines.append(f"- 主要截止或关键节点：{time_deadline}")
    lines.append("- 如原文存在多个时间点，我会在结构化区给出时间线。")
    lines.append("")

    lines.append("## 注意事项与风险")
    lines.extend(_format_list(notices, "核对信息完整性，避免填写错误"))
    lines.extend(_format_list(risks, "材料缺失或超期可能导致退回/失效"))
    lines.append("")

    lines.append("## 我需要你确认的内容")
    lines.append("- 是否必须本人办理？是否允许代办或线上办理？")
    lines.append("- 是否有明确的提交窗口、网址或线下地点？")
    lines.append("- 是否存在特殊人群或豁免条件（如年龄、户籍、行业）？")
    lines.append("")

    lines.append("如果你希望我继续完善，请补充通知原文或截图，我会把结构化结果和清单细化到可直接执行。")
    return "\n".join(lines)
