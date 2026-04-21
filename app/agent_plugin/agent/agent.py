import json
import logging
import re
import sqlite3
from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Annotated, TypedDict, Any, Generator

from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.state import CompiledStateGraph
from langgraph.errors import GraphRecursionError
from sqlmodel import Session

from app.agent_plugin.agent.config import AgentConfig
from app.agent_plugin.agent.memory import LongTermMemory, get_long_term_memory
from app.agent_plugin.agent.safety import StaticSafetyEngine
from app.agent_plugin.agent.tools import tools, tool_node
from app.core.config import GlobalConfig
from app.core.database import engine
from app.models.user import User
from app.services.agent_tool_services.base import normalize_role_value


logger = logging.getLogger(__name__)

_FILE_REF_RE = re.compile(r"(/media/(?:docs|images|avatars)/[^\s\"'<>]+)")
_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff", ".tif"}
_FILE_TOOL_NAMES = {"parse_uploaded_document", "parse_uploaded_image_ocr"}


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    items: list[str] = []
    for value in values:
        normalized = str(value or "").strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        items.append(normalized)
    return items


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    user_id: str
    mode: str
    decision: str
    input_safety_decision: str
    tool_guard_decision: str
    blocked_message: str
    thought_event: str


@dataclass(frozen=True)
class AgentGraphNode:
    id: str
    x: int
    y: int
    width: int = 168
    height: int = 56
    shape: str = "rect"


@dataclass(frozen=True)
class AgentGraphEdge:
    source: str
    target: str
    label: str | None = None


@dataclass(frozen=True)
class AgentGraphSpec:
    title: str
    nodes: tuple[AgentGraphNode, ...]
    edges: tuple[AgentGraphEdge, ...]


AGENT_GRAPH_TITLE = "Agent Workflow"
AGENT_WORKFLOW_NODE_ORDER = (
    "input_safety",
    "decide",
    "agent",
    "tool_safety",
    "action",
    "blocked",
    "answer",
    "summarize",
    "output_safety",
)
AGENT_WORKFLOW_LAYOUT: dict[str, AgentGraphNode] = {
    "START": AgentGraphNode(id="START", x=24, y=160, width=92, height=42, shape="pill"),
    "input_safety": AgentGraphNode(id="input_safety", x=150, y=160),
    "decide": AgentGraphNode(id="decide", x=360, y=80),
    "agent": AgentGraphNode(id="agent", x=360, y=160),
    "tool_safety": AgentGraphNode(id="tool_safety", x=580, y=80),
    "action": AgentGraphNode(id="action", x=790, y=80),
    "blocked": AgentGraphNode(id="blocked", x=360, y=300),
    "answer": AgentGraphNode(id="answer", x=580, y=300),
    "summarize": AgentGraphNode(id="summarize", x=790, y=220),
    "output_safety": AgentGraphNode(id="output_safety", x=1010, y=220),
    "END": AgentGraphNode(id="END", x=1240, y=220, width=92, height=42, shape="pill"),
}
AGENT_WORKFLOW_CONDITIONAL_EDGES = (
    ("input_safety", "blocked", "block"),
    ("input_safety", "decide", "allow"),
    ("decide", "agent", "tools"),
    ("decide", "answer", "answer"),
    ("agent", "tool_safety", "tools"),
    ("agent", "summarize", "summarize"),
    ("tool_safety", "action", "action"),
    ("tool_safety", "summarize", "summarize"),
)
AGENT_WORKFLOW_DIRECT_EDGES = (
    ("START", "input_safety"),
    ("action", "agent"),
    ("blocked", "output_safety"),
    ("answer", "summarize"),
    ("summarize", "output_safety"),
    ("output_safety", "END"),
)


def build_agent_graph_spec() -> AgentGraphSpec:
    nodes = tuple(AGENT_WORKFLOW_LAYOUT[name] for name in ("START", *AGENT_WORKFLOW_NODE_ORDER, "END"))
    edges = tuple(
        [AgentGraphEdge(source, target, label) for source, target, label in AGENT_WORKFLOW_CONDITIONAL_EDGES]
        + [AgentGraphEdge(source, target) for source, target in AGENT_WORKFLOW_DIRECT_EDGES]
    )
    return AgentGraphSpec(title=AGENT_GRAPH_TITLE, nodes=nodes, edges=edges)


def _node_center_x(node: AgentGraphNode) -> float:
    return node.x + node.width / 2


def _node_center_y(node: AgentGraphNode) -> float:
    return node.y + node.height / 2


def _edge_anchor_points(source: AgentGraphNode, target: AgentGraphNode) -> tuple[tuple[float, float], tuple[float, float]]:
    source_cx = _node_center_x(source)
    source_cy = _node_center_y(source)
    target_cx = _node_center_x(target)
    target_cy = _node_center_y(target)

    dx = target_cx - source_cx
    dy = target_cy - source_cy
    horizontal = abs(dx) >= abs(dy)

    if horizontal:
        start = (source.x + source.width, source_cy) if dx >= 0 else (source.x, source_cy)
        end = (target.x, target_cy) if dx >= 0 else (target.x + target.width, target_cy)
    else:
        start = (source_cx, source.y + source.height) if dy >= 0 else (source_cx, source.y)
        end = (target_cx, target.y) if dy >= 0 else (target_cx, target.y + target.height)
    return start, end


def _edge_path(source: AgentGraphNode, target: AgentGraphNode) -> tuple[str, float, float]:
    start, end = _edge_anchor_points(source, target)
    sx, sy = start
    ex, ey = end
    mid_x = (sx + ex) / 2
    mid_y = (sy + ey) / 2

    if abs(sy - ey) < 1 and ex > sx:
        path = f"M{sx:.1f} {sy:.1f} L{ex:.1f} {ey:.1f}"
    elif abs(sy - ey) < 1 and ex < sx:
        offset = 56.0
        path = (
            f"M{sx:.1f} {sy:.1f} "
            f"C{sx - offset:.1f} {sy - offset:.1f}, {ex + offset:.1f} {ey - offset:.1f}, {ex:.1f} {ey:.1f}"
        )
        mid_y -= offset
    else:
        ctrl_dx = max(abs(ex - sx) * 0.35, 48.0)
        path = f"M{sx:.1f} {sy:.1f} C{sx + ctrl_dx:.1f} {sy:.1f}, {ex - ctrl_dx:.1f} {ey:.1f}, {ex:.1f} {ey:.1f}"
    return path, mid_x, mid_y


def render_agent_graph_svg(spec: AgentGraphSpec | None = None) -> str:
    spec = spec or build_agent_graph_spec()
    width = max(node.x + node.width for node in spec.nodes) + 48
    height = max(node.y + node.height for node in spec.nodes) + 56

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "  <defs>",
        '    <marker id="arrow" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">',
        '      <polygon points="0 0, 10 3.5, 0 7" fill="#475569"/>',
        "    </marker>",
        "    <style>",
        "      .node{fill:#f8fafc;stroke:#334155;stroke-width:2}",
        "      .pill{fill:#e2e8f0;stroke:#334155;stroke-width:2}",
        "      .text{font:14px 'Microsoft YaHei',sans-serif;fill:#0f172a}",
        "      .edge{stroke:#475569;stroke-width:2;marker-end:url(#arrow);fill:none}",
        "      .edge-label{font:12px 'Microsoft YaHei',sans-serif;fill:#334155}",
        "      .title{font:18px 'Microsoft YaHei',sans-serif;fill:#111827;font-weight:700}",
        "    </style>",
        "  </defs>",
        f'  <text x="24" y="34" class="title">{escape(spec.title)}</text>',
    ]

    node_lookup = {node.id: node for node in spec.nodes}
    for edge in spec.edges:
        source = node_lookup[edge.source]
        target = node_lookup[edge.target]
        path, label_x, label_y = _edge_path(source, target)
        parts.append(f'  <path class="edge" d="{path}"/>')
        if edge.label:
            parts.append(
                f'  <text class="edge-label" x="{label_x:.1f}" y="{label_y - 8:.1f}" text-anchor="middle">{escape(edge.label)}</text>'
            )

    for node in spec.nodes:
        cx = _node_center_x(node)
        cy = _node_center_y(node)
        label_y = cy + 5
        if node.shape == "pill":
            rx = node.width / 2
            ry = node.height / 2
            parts.append(f'  <ellipse class="pill" cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}"/>')
        else:
            parts.append(
                f'  <rect class="node" x="{node.x}" y="{node.y}" width="{node.width}" height="{node.height}" rx="12" ry="12"/>'
            )
        parts.append(f'  <text class="text" x="{cx:.1f}" y="{label_y:.1f}" text-anchor="middle">{escape(node.id)}</text>')

    parts.append("</svg>")
    return "\n".join(parts)


def write_agent_graph_svg(graph_path: Path, overwrite: bool = False) -> bool:
    if graph_path.exists() and not overwrite:
        return False
    graph_path.parent.mkdir(parents=True, exist_ok=True)
    graph_path.write_text(render_agent_graph_svg(), encoding="utf-8")
    return True


class AgentCore:
    MAX_RECURSION_STEPS = 24
    MAX_MODEL_MESSAGES = 12
    MAX_MODEL_CHARS = 6000

    model: Any
    plain_model: Any
    safety_engine: StaticSafetyEngine
    memory_engine: LongTermMemory
    workflow: StateGraph
    conn: sqlite3.Connection
    saver: SqliteSaver
    app: CompiledStateGraph

    def __init__(self):
        self._ensure_graph_image()
        self.safety_engine = StaticSafetyEngine(
            Path.cwd() / "app" / "resources" / "sensitive"
        )
        self.memory_engine = get_long_term_memory()

        self.model = ChatOpenAI(
            model=AgentConfig.LLM_MODEL,
            api_key=AgentConfig.LLM_API_KEY,
            base_url=AgentConfig.LLM_URL_BASE,
            temperature=AgentConfig.LLM_TEMPERATURE,
            timeout=AgentConfig.LLM_TIMEOUT,
        ).bind_tools(tools)
        self.plain_model = ChatOpenAI(
            model=AgentConfig.LLM_MODEL,
            api_key=AgentConfig.LLM_API_KEY,
            base_url=AgentConfig.LLM_URL_BASE,
            temperature=AgentConfig.LLM_TEMPERATURE,
            timeout=AgentConfig.LLM_TIMEOUT,
        )

        self.workflow = StateGraph(AgentState)
        self._configure_workflow()

        self.conn = sqlite3.connect(AgentConfig.RELATIONAL_DB_PATH, check_same_thread=False)
        self.saver = SqliteSaver(self.conn)
        self.app = self.workflow.compile(checkpointer=self.saver)

    def _ensure_graph_image(self):
        graph_path = Path(GlobalConfig.AGENT_GRAPH_SVG_PATH)
        try:
            write_agent_graph_svg(graph_path=graph_path, overwrite=True)
        except Exception:
            # ??????????????????
            pass

    def _configure_workflow(self) -> None:
        node_handlers = {
            "input_safety": self._input_safety_check,
            "decide": self._decide_need_tools,
            "agent": self._call_model,
            "tool_safety": self._tool_safety_check,
            "action": tool_node,
            "blocked": self._blocked_reply,
            "answer": self._direct_answer,
            "summarize": self._summarize_and_store,
            "output_safety": self._output_safety_check,
        }
        for node_name in AGENT_WORKFLOW_NODE_ORDER:
            self.workflow.add_node(node_name, node_handlers[node_name])

        self.workflow.set_entry_point("input_safety")
        self.workflow.add_conditional_edges(
            "input_safety",
            self._route_after_input_safety,
            path_map={label: target for source, target, label in AGENT_WORKFLOW_CONDITIONAL_EDGES if source == "input_safety"},
        )
        self.workflow.add_conditional_edges(
            "decide",
            self._route_after_decide,
            path_map={label: target for source, target, label in AGENT_WORKFLOW_CONDITIONAL_EDGES if source == "decide"},
        )
        self.workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            path_map={label: target for source, target, label in AGENT_WORKFLOW_CONDITIONAL_EDGES if source == "agent"},
        )
        self.workflow.add_conditional_edges(
            "tool_safety",
            self._route_after_tool_safety,
            path_map={label: target for source, target, label in AGENT_WORKFLOW_CONDITIONAL_EDGES if source == "tool_safety"},
        )
        for source, target in AGENT_WORKFLOW_DIRECT_EDGES:
            if source == "START":
                continue
            self.workflow.add_edge(source, END if target == "END" else target)

    def _extract_file_refs_from_text(self, text: str) -> list[str]:
        refs: list[str] = []
        for match in _FILE_REF_RE.findall(str(text or "")):
            refs.append(match.rstrip(".,;:)]}>"))
        return _dedupe_preserve_order(refs)

    def _tool_name_for_file_ref(self, file_ref: str) -> str:
        suffix = Path(str(file_ref or "")).suffix.lower()
        return "parse_uploaded_image_ocr" if suffix in _IMAGE_SUFFIXES else "parse_uploaded_document"

    def _select_context_file_ref(
        self,
        tool_name: str,
        provided_ref: str,
        file_refs: list[str],
    ) -> tuple[str | None, str | None]:
        raw_value = str(provided_ref or "").strip()
        if not file_refs:
            return None, None

        if raw_value in file_refs:
            return raw_value, None

        preferred_refs = [
            ref for ref in file_refs if self._tool_name_for_file_ref(ref) == self._tool_name_for_file_ref(tool_name)
        ]
        candidate_refs = preferred_refs or file_refs

        if not raw_value and len(candidate_refs) == 1:
            return candidate_refs[0], "fill_from_message_context"

        if raw_value and len(candidate_refs) == 1 and not raw_value.startswith("/media/"):
            return candidate_refs[0], "replace_filename_with_message_ref"

        if raw_value:
            raw_name = Path(raw_value).name.lower()
            if raw_name:
                name_matches = [ref for ref in candidate_refs if Path(ref).name.lower() == raw_name]
                if len(name_matches) == 1:
                    return name_matches[0], "match_by_uploaded_name"

            raw_suffix = Path(raw_value).suffix.lower()
            if raw_suffix:
                suffix_matches = [ref for ref in candidate_refs if Path(ref).suffix.lower() == raw_suffix]
                if len(suffix_matches) == 1:
                    return suffix_matches[0], "match_by_uploaded_suffix"

        return None, None

    def _normalize_tool_call(
        self,
        state: AgentState,
        tool_name: str,
        args: dict[str, Any],
        file_refs: list[str],
    ) -> tuple[str, dict[str, Any], list[str]]:
        normalized_args = dict(args)
        rewrite_reasons: list[str] = []
        runtime_user_id = str(state["user_id"])
        model_user_id = str(normalized_args.get("user_id", "") or "").strip()
        if model_user_id != runtime_user_id:
            if model_user_id:
                rewrite_reasons.append(f"user_id_override:{model_user_id}->{runtime_user_id}")
            else:
                rewrite_reasons.append(f"user_id_injected:{runtime_user_id}")
        normalized_args["user_id"] = runtime_user_id

        rewritten_tool_name = tool_name

        if tool_name == "parse_local_file" and file_refs:
            file_name = str(normalized_args.get("file_name", "") or "").strip()
            selected_ref, select_reason = self._select_context_file_ref("parse_uploaded_document", file_name, file_refs)
            if selected_ref:
                rewritten_tool_name = self._tool_name_for_file_ref(selected_ref)
                normalized_args = {"user_id": runtime_user_id, "file_ref": selected_ref}
                rewrite_reasons.append(f"tool_redirect:{tool_name}->{rewritten_tool_name}")
                rewrite_reasons.append(f"file_ref:{select_reason}")
                return rewritten_tool_name, normalized_args, rewrite_reasons

        if rewritten_tool_name in _FILE_TOOL_NAMES:
            selected_ref, select_reason = self._select_context_file_ref(
                rewritten_tool_name,
                str(normalized_args.get("file_ref", "") or ""),
                file_refs,
            )
            if selected_ref:
                if str(normalized_args.get("file_ref", "") or "") != selected_ref:
                    rewrite_reasons.append(f"file_ref:{select_reason}")
                normalized_args["file_ref"] = selected_ref
                expected_tool_name = self._tool_name_for_file_ref(selected_ref)
                if expected_tool_name != rewritten_tool_name:
                    rewrite_reasons.append(f"tool_redirect:{rewritten_tool_name}->{expected_tool_name}")
                    rewritten_tool_name = expected_tool_name

        return rewritten_tool_name, normalized_args, rewrite_reasons

    def _preview_json(self, value: Any, limit: int = 800) -> str:
        try:
            text = json.dumps(value, ensure_ascii=False, default=str)
        except Exception:
            text = str(value)
        if len(text) <= limit:
            return text
        return f"{text[:limit]}...(truncated)"

    def _summarize_tool_output(self, output: str) -> dict[str, Any]:
        text = str(output or "").strip()
        if not text:
            return {}
        try:
            payload = json.loads(text)
        except Exception:
            return {"preview": text[:300]}

        if not isinstance(payload, dict):
            return {"preview": self._preview_json(payload, limit=300)}

        error = payload.get("error") if isinstance(payload.get("error"), dict) else {}
        meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
        summary: dict[str, Any] = {
            "ok": payload.get("ok"),
            "error_code": error.get("code"),
            "error_message": error.get("message"),
        }
        if meta:
            summary["meta"] = meta
        if "item" in payload:
            summary["has_item"] = True
        if isinstance(payload.get("items"), list):
            summary["items_count"] = len(payload.get("items") or [])
        return summary

    def _inject_runtime_args(self, state: AgentState, response: Any) -> Any:
        tool_calls = getattr(response, "tool_calls", []) or []
        user_text = self._extract_user_text(state)
        file_refs = self._extract_file_refs_from_text(user_text)
        runtime_normalizations: list[dict[str, Any]] = []
        for tc in tool_calls:
            original_tool_name = str(tc.get("name", "") or "tool")
            args = tc.get("args")
            if not isinstance(args, dict):
                args = {}
            original_args = dict(args)
            normalized_tool_name, normalized_args, rewrite_reasons = self._normalize_tool_call(
                state,
                original_tool_name,
                original_args,
                file_refs,
            )
            tc["name"] = normalized_tool_name
            tc["args"] = normalized_args
            if rewrite_reasons:
                event = {
                    "tool": normalized_tool_name,
                    "original_tool": original_tool_name,
                    "original_args": original_args,
                    "normalized_args": normalized_args,
                    "reasons": rewrite_reasons,
                }
                runtime_normalizations.append(event)
                logger.info(
                    "Agent tool normalized user_id=%s thread_mode=%s event=%s",
                    state["user_id"],
                    state.get("mode", "agent"),
                    self._preview_json(event),
                )

        if runtime_normalizations or file_refs:
            extra = getattr(response, "additional_kwargs", None)
            if not isinstance(extra, dict):
                extra = {}
                try:
                    response.additional_kwargs = extra
                except Exception:
                    extra = {}
            extra["_runtime_context"] = {
                "user_id": state["user_id"],
                "mode": state.get("mode", "agent"),
                "file_refs": file_refs,
            }
            if runtime_normalizations:
                extra["_runtime_normalizations"] = runtime_normalizations
        return response

    def _call_model(self, state: AgentState):
        system_msg = SystemMessage(content=AgentConfig.SYSTEM_PROMPT)
        response = self.model.invoke([system_msg] + self._select_model_messages(state))
        response = self._inject_runtime_args(state, response)
        return {"messages": [response]}

    def _extract_user_text(self, state: AgentState) -> str:
        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage):
                return str(msg.content or "").strip()
            if getattr(msg, "type", "") == "human":
                return str(getattr(msg, "content", "") or "").strip()
        return ""

    def _extract_last_ai_text(self, state: AgentState) -> str:
        for msg in reversed(state["messages"]):
            if isinstance(msg, AIMessage):
                return str(msg.content or "").strip()
            if getattr(msg, "type", "") == "ai":
                return str(getattr(msg, "content", "") or "").strip()
        return ""

    def _message_length(self, msg: Any) -> int:
        content = getattr(msg, "content", "")
        if isinstance(content, str):
            return len(content)
        return len(str(content or ""))

    def _message_has_tool_calls(self, msg: Any) -> bool:
        return bool(getattr(msg, "tool_calls", []) or [])

    def _is_tool_message(self, msg: Any) -> bool:
        msg_type = str(getattr(msg, "type", "") or "").strip().lower()
        return msg_type == "tool" or msg.__class__.__name__ == "ToolMessage"

    def _group_messages_for_model(self, messages: list[Any]) -> list[list[Any]]:
        grouped: list[list[Any]] = []
        idx = 0
        while idx < len(messages):
            msg = messages[idx]
            if self._message_has_tool_calls(msg):
                group = [msg]
                tool_call_ids = {
                    str(tc.get("id", "") or "").strip()
                    for tc in list(getattr(msg, "tool_calls", []) or [])
                    if isinstance(tc, dict)
                }
                idx += 1
                while idx < len(messages):
                    next_msg = messages[idx]
                    if not self._is_tool_message(next_msg):
                        break
                    next_tool_call_id = str(getattr(next_msg, "tool_call_id", "") or "").strip()
                    if tool_call_ids and next_tool_call_id and next_tool_call_id not in tool_call_ids:
                        break
                    group.append(next_msg)
                    idx += 1
                grouped.append(group)
                continue

            grouped.append([msg])
            idx += 1
        return grouped

    def _select_model_messages(self, state: AgentState) -> list[Any]:
        messages = list(state.get("messages") or [])
        if not messages:
            return []

        grouped_messages = self._group_messages_for_model(messages)
        selected_groups: list[list[Any]] = []
        selected_count = 0
        total_chars = 0
        for group in reversed(grouped_messages):
            group_count = len(group)
            group_chars = sum(self._message_length(msg) for msg in group)
            if selected_groups and (
                selected_count + group_count > self.MAX_MODEL_MESSAGES
                or total_chars + group_chars > self.MAX_MODEL_CHARS
            ):
                continue
            selected_groups.append(group)
            selected_count += group_count
            total_chars += group_chars
            if selected_count >= self.MAX_MODEL_MESSAGES or total_chars >= self.MAX_MODEL_CHARS:
                break

        if not selected_groups and grouped_messages:
            latest_group = grouped_messages[-1]
            selected_groups = [latest_group]
            selected_count = len(latest_group)
            total_chars = sum(self._message_length(msg) for msg in latest_group)

        selected = [msg for group in reversed(selected_groups) for msg in group]
        if len(selected) != len(messages):
            logger.info(
                (
                    "Agent message window trimmed user_id=%s original_messages=%s "
                    "original_groups=%s selected_messages=%s selected_groups=%s selected_chars=%s"
                ),
                state.get("user_id"),
                len(messages),
                len(grouped_messages),
                len(selected),
                len(selected_groups),
                total_chars,
            )
        return selected

    def _get_user_role(self, user_id: str) -> str:
        try:
            with Session(engine) as session:
                user = session.get(User, int(user_id))
                if user and user.role:
                    return normalize_role_value(user.role)
        except Exception:
            pass
        return "normal"

    def _input_safety_check(self, state: AgentState):
        user_text = self._extract_user_text(state)
        role = self._get_user_role(state["user_id"])
        result = self.safety_engine.audit_input(user_text, user_role=role)
        decision = result.get("decision", "allow")
        thought = f"输入审核：{decision}（{result.get('reason', '')}）"
        if decision == "block":
            return {
                "input_safety_decision": "block",
                "blocked_message": "请求内容存在安全风险，已被拦截。请调整后重试。",
                "thought_event": thought,
            }
        if decision == "sanitize" and result.get("sanitized_text") and result.get("sanitized_text") != user_text:
            return {
                "messages": [HumanMessage(content=result["sanitized_text"])],
                "input_safety_decision": "allow",
                "thought_event": thought,
            }
        return {"input_safety_decision": "allow", "thought_event": thought}

    def _route_after_input_safety(self, state: AgentState):
        return "block" if state.get("input_safety_decision") == "block" else "allow"

    def _parse_decision(self, text: str) -> str:
        raw = (text or "").strip()
        if not raw:
            return "answer"
        if raw.startswith("```json"):
            raw = raw[7:].strip()
        if raw.startswith("```"):
            raw = raw[3:].strip()
        if raw.endswith("```"):
            raw = raw[:-3].strip()
        try:
            data = json.loads(raw)
            need_tools = bool(data.get("need_tools", False))
            return "tools" if need_tools else "answer"
        except Exception:
            low = raw.lower()
            if "true" in low or "tools" in low:
                return "tools"
            return "answer"

    def _decide_need_tools(self, state: AgentState):
        mode = str(state.get("mode", "agent") or "agent").strip().lower()
        if mode == "chat":
            return {"decision": "answer", "thought_event": "模式切换：Chat 模式，直接回答"}
        if mode == "agent":
            return {"decision": "tools", "thought_event": "模式切换：Agent 模式，进入工具循环"}
        user_text = self._extract_user_text(state)
        decide_prompt = SystemMessage(
            content=(
                "你是调度决策器。只判断当前问题是否需要调用外部工具。"
                "若用户问题涉及：查询用户历史/待办/设置、检索政策文档、新闻检索、文件读取、或执行写操作（新增/修改/确认），"
                "则 need_tools=true。"
                "若仅是常识问答、解释、润色、泛化建议，不依赖项目内数据，则 need_tools=false。"
                "只返回JSON：{\"need_tools\": true|false, \"reason\": \"...\"}"
            )
        )
        try:
            decision_resp = self.plain_model.invoke([decide_prompt, HumanMessage(content=user_text)])
            decision = self._parse_decision(str(getattr(decision_resp, "content", "") or ""))
        except Exception:
            decision = "answer"
        thought = "决策完成：将调用工具进行检索/执行" if decision == "tools" else "决策完成：无需工具，直接回答"
        return {"decision": decision, "thought_event": thought}

    def _route_after_decide(self, state: AgentState):
        return "tools" if state.get("decision") == "tools" else "answer"

    def _tool_safety_check(self, state: AgentState):
        if not state.get("messages"):
            return {"tool_guard_decision": "summarize", "thought_event": "静态安全层：无消息"}
        last_msg = state["messages"][-1]
        calls = list(getattr(last_msg, "tool_calls", []) or [])
        if not calls:
            return {"tool_guard_decision": "summarize", "thought_event": "静态安全层：无工具调用"}
        allowed = {tool.name for tool in tools}
        role = self._get_user_role(state["user_id"])
        result = self.safety_engine.audit_tool_calls(calls, allowed_tools=allowed, user_role=role)
        decision = result.get("decision", "deny")
        if decision == "deny":
            try:
                last_msg.tool_calls = []
            except Exception:
                pass
            return {
                "tool_guard_decision": "summarize",
                "thought_event": f"静态安全层拦截工具调用：{result.get('reason', '')}",
            }
        if decision == "rewrite":
            try:
                last_msg.tool_calls = result.get("tool_calls", calls)
            except Exception:
                pass
            return {
                "tool_guard_decision": "action",
                "thought_event": "静态安全层已重写工具参数并允许执行",
            }
        return {
            "tool_guard_decision": "action",
            "thought_event": "静态安全层通过，允许执行工具",
        }

    def _route_after_tool_safety(self, state: AgentState):
        return "action" if state.get("tool_guard_decision") == "action" else "summarize"

    def _blocked_reply(self, state: AgentState):
        msg = state.get("blocked_message") or "请求已被安全策略拦截。"
        return {"messages": [AIMessage(content=msg)], "thought_event": "安全层已拦截并返回固定回复"}

    def _direct_answer(self, state: AgentState):
        system_msg = SystemMessage(content=AgentConfig.SYSTEM_PROMPT + "\n本轮无需调用工具，请直接回答。")
        response = self.plain_model.invoke([system_msg] + self._select_model_messages(state))
        return {"messages": [response], "thought_event": "已直接生成答复（未调用工具）"}

    def _should_continue(self, state: AgentState):
        last_message = state["messages"][-1]
        return "tools" if getattr(last_message, "tool_calls", None) else "summarize"

    def _summarize_and_store(self, state: AgentState):
        summary_prompt = SystemMessage(
            content="分析对话，提取 1-2 条关于用户的新信息（偏好/习惯/背景）。若无新增信息，仅回复 NONE。"
        )

        response = self.model.invoke([summary_prompt] + self._select_model_messages(state))
        content = (response.content or "").strip()

        self.memory_engine.summarize_and_store_knowledge(
            user_id=state["user_id"],
            content=content,
        )

        return {}

    def _output_safety_check(self, state: AgentState):
        ai_text = self._extract_last_ai_text(state)
        if not ai_text:
            return {"thought_event": "输出审核：无可审查输出"}
        result = self.safety_engine.audit_output(ai_text)
        decision = result.get("decision", "allow")
        thought = f"输出审核：{decision}（{result.get('reason', '')}）"
        safe_text = result.get("safe_text", ai_text)
        if decision in {"block", "sanitize"} and safe_text != ai_text:
            return {"messages": [AIMessage(content=safe_text)], "thought_event": thought}
        return {"thought_event": thought}

    def stream_run(self, prompt: str, user_id: str, thread_id: str, mode: str = "agent") -> Generator[str, None, None]:
        """
        同步生成器：驱动图运行并输出 SSE 数据流。
        """
        inputs = {
            "messages": [HumanMessage(content=prompt)],
            "user_id": user_id,
            "mode": mode,
        }
        config = {
            "configurable": {"thread_id": thread_id},
            "recursion_limit": self.MAX_RECURSION_STEPS,
        }
        runtime_context = {
            "thread_id": thread_id,
            "user_id": user_id,
            "mode": mode,
            "file_refs": self._extract_file_refs_from_text(prompt),
        }
        print(f"[runtime_context] {self._preview_json(runtime_context)}")
        logger.info("Agent task start %s", self._preview_json(runtime_context))

        print(f"\n{'=' * 20} 任务开始 (Thread: {thread_id}) {'=' * 20}")
        print(f"[用户输入]: {prompt}")

        try:
            for event in self.app.stream(inputs, config=config, stream_mode="updates"):
                for node_name, state_update in event.items():
                    if state_update is None:
                        continue

                    print(f"\n>>> [动作追踪] 进入节点 <{node_name}>")

                    has_messages = "messages" in state_update and bool(state_update.get("messages"))
                    last_msg = state_update["messages"][-1] if has_messages else None

                    if node_name == "agent":
                        runtime_meta = {}
                        if last_msg is not None:
                            runtime_meta = getattr(last_msg, "additional_kwargs", {}) or {}
                        for item in runtime_meta.get("_runtime_normalizations", []) or []:
                            print(f"--- [runtime_normalized] {self._preview_json(item)}")
                        if runtime_meta.get("_runtime_context"):
                            print(f"--- [runtime_context] {self._preview_json(runtime_meta['_runtime_context'])}")
                        if last_msg is not None and getattr(last_msg, "tool_calls", None):
                            for idx, tc in enumerate(last_msg.tool_calls, start=1):
                                print(
                                    f"--- [tool_plan:{idx}] name={tc['name']} args={self._preview_json(tc.get('args', {}))}"
                                )
                        if last_msg is not None and last_msg.content:
                            print(f"[内核回复]: {last_msg.content}")
                    elif node_name == "action":
                        print("--- [系统执行] 工具执行完毕，结果已写回上下文")
                    elif node_name == "input_safety":
                        print(f"--- [输入审核] {state_update.get('thought_event', '已完成')}")
                    elif node_name == "decide":
                        print(f"--- [调度决策] {state_update.get('thought_event', '已完成决策')}")
                    elif node_name == "tool_safety":
                        print(f"--- [静态安全层] {state_update.get('thought_event', '已完成')}")
                    elif node_name == "blocked":
                        print("--- [安全拦截] 请求已被拦截")
                    elif node_name == "answer":
                        print("--- [直接作答] 无需工具，直接输出答案")
                    elif node_name == "summarize":
                        print("--- [知识复盘] 正在提炼并归档新记忆")
                    elif node_name == "output_safety":
                        print(f"--- [输出审核] {state_update.get('thought_event', '已完成')}")

                    payload = {
                        "node": node_name,
                        "user_id": user_id,
                        "content": (last_msg.content if (last_msg is not None and last_msg.content) else ""),
                        "tool_calls": [
                            {"name": tc["name"], "args": tc["args"]}
                            for tc in getattr(last_msg, "tool_calls", [])
                        ]
                        if (last_msg is not None and hasattr(last_msg, "tool_calls"))
                        else [],
                        "tool_results": [],
                        "thought_event": str(state_update.get("thought_event", "") or ""),
                    }
                    if node_name == "agent":
                        if last_msg is not None and getattr(last_msg, "tool_calls", None):
                            tool_names = [tc.get("name", "tool") for tc in getattr(last_msg, "tool_calls", [])]
                            payload["thought_event"] = f"正在决策：准备调用工具 {', '.join(tool_names)}"
                        else:
                            payload["thought_event"] = "正在整合信息并生成最终答复"
                    if node_name == "action":
                        output = last_msg.content if last_msg is not None else ""
                        if not isinstance(output, str):
                            output = json.dumps(output, ensure_ascii=False)
                        preview_output = output[:2000]
                        if len(output) > 2000:
                            preview_output = f"{preview_output}...(truncated)"
                        summary = self._summarize_tool_output(output)
                        if summary:
                            print(f"--- [tool_result] {self._preview_json(summary)}")
                        payload["tool_results"] = [
                            {
                                "name": getattr(last_msg, "name", "tool") if last_msg is not None else "tool",
                                "tool_call_id": getattr(last_msg, "tool_call_id", None) if last_msg is not None else None,
                                "output": preview_output,
                                "full_output": output,
                            }
                        ]
                        payload["thought_event"] = "工具执行完成，正在吸收结果并继续推理"
                    if node_name == "summarize":
                        payload["thought_event"] = "正在提炼并归档长期记忆"
                    yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
        except GraphRecursionError:
            guard_payload = {
                "node": "guard",
                "user_id": user_id,
                "content": "",
                "tool_calls": [],
                "tool_results": [],
                "thought_event": f"已触发循环保护：超过最大步骤 {self.MAX_RECURSION_STEPS}，停止继续调用工具。",
            }
            yield f"data: {json.dumps(guard_payload, ensure_ascii=False)}\n\n"

        print(f"\n{'=' * 20} 任务结束 {'=' * 20}")
        yield "data: [DONE]\n\n"

    def close(self):
        if self.conn:
            self.conn.close()
