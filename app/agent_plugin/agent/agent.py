import json
import sqlite3
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


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    user_id: str
    mode: str
    decision: str
    input_safety_decision: str
    tool_guard_decision: str
    blocked_message: str
    thought_event: str


AGENT_GRAPH_SVG_TEMPLATE = """<svg xmlns="http://www.w3.org/2000/svg" width="980" height="420" viewBox="0 0 980 420">
  <defs>
    <marker id="arrow" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
      <polygon points="0 0, 10 3.5, 0 7" fill="#445"/>
    </marker>
    <style>
      .n{fill:#f8fafc;stroke:#334155;stroke-width:2;rx:12;ry:12}
      .t{font:14px 'Microsoft YaHei',sans-serif;fill:#0f172a}
      .l{stroke:#475569;stroke-width:2;marker-end:url(#arrow);fill:none}
      .h{font:12px 'Microsoft YaHei',sans-serif;fill:#334155}
      .ttl{font:18px 'Microsoft YaHei',sans-serif;fill:#111827;font-weight:700}
    </style>
  </defs>
  <text x="24" y="34" class="ttl">AgentGraph ?????</text>

  <rect class="n" x="40"  y="90"  width="150" height="56"/><text class="t" x="89"  y="124">decide</text>
  <rect class="n" x="250" y="90"  width="150" height="56"/><text class="t" x="307" y="124">agent</text>
  <rect class="n" x="460" y="90"  width="150" height="56"/><text class="t" x="515" y="124">action</text>
  <rect class="n" x="250" y="230" width="150" height="56"/><text class="t" x="304" y="264">answer</text>
  <rect class="n" x="670" y="160" width="170" height="56"/><text class="t" x="719" y="194">summarize</text>
  <rect class="n" x="880" y="160" width="70"  height="56"/><text class="t" x="904" y="194">END</text>

  <path class="l" d="M190 118 L250 118"/><text class="h" x="202" y="108">tools</text>
  <path class="l" d="M190 130 C220 190, 220 250, 250 258"/><text class="h" x="194" y="208">answer</text>
  <path class="l" d="M400 118 L460 118"/><text class="h" x="414" y="108">has tool_calls</text>
  <path class="l" d="M610 118 L400 118"/><text class="h" x="488" y="106">loop</text>
  <path class="l" d="M400 130 C500 150, 580 170, 670 188"/><text class="h" x="486" y="160">no tool_calls</text>
  <path class="l" d="M400 258 C510 240, 580 210, 670 188"/>
  <path class="l" d="M840 188 L880 188"/>
</svg>
"""


def write_agent_graph_svg(graph_path: Path, overwrite: bool = False) -> bool:
    if graph_path.exists() and not overwrite:
        return False
    graph_path.parent.mkdir(parents=True, exist_ok=True)
    graph_path.write_text(AGENT_GRAPH_SVG_TEMPLATE, encoding="utf-8")
    return True


class AgentCore:
    MAX_RECURSION_STEPS = 24

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
        self.workflow.add_node("input_safety", self._input_safety_check)
        self.workflow.add_node("decide", self._decide_need_tools)
        self.workflow.add_node("agent", self._call_model)
        self.workflow.add_node("tool_safety", self._tool_safety_check)
        self.workflow.add_node("action", tool_node)
        self.workflow.add_node("blocked", self._blocked_reply)
        self.workflow.add_node("answer", self._direct_answer)
        self.workflow.add_node("summarize", self._summarize_and_store)
        self.workflow.add_node("output_safety", self._output_safety_check)
        self.workflow.set_entry_point("input_safety")
        self.workflow.add_conditional_edges(
            "input_safety",
            self._route_after_input_safety,
            path_map={"block": "blocked", "allow": "decide"},
        )
        self.workflow.add_conditional_edges(
            "decide",
            self._route_after_decide,
            path_map={"tools": "agent", "answer": "answer"},
        )
        self.workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            path_map={"tools": "tool_safety", "summarize": "summarize"},
        )
        self.workflow.add_conditional_edges(
            "tool_safety",
            self._route_after_tool_safety,
            path_map={"action": "action", "summarize": "summarize"},
        )
        self.workflow.add_edge("action", "agent")
        self.workflow.add_edge("blocked", "output_safety")
        self.workflow.add_edge("answer", "summarize")
        self.workflow.add_edge("summarize", "output_safety")
        self.workflow.add_edge("output_safety", END)

        self.conn = sqlite3.connect(AgentConfig.RELATIONAL_DB_PATH, check_same_thread=False)
        self.saver = SqliteSaver(self.conn)
        self.app = self.workflow.compile(checkpointer=self.saver)

    def _ensure_graph_image(self):
        graph_path = Path(GlobalConfig.AGENT_GRAPH_SVG_PATH)
        try:
            write_agent_graph_svg(graph_path=graph_path, overwrite=False)
        except Exception:
            # ??????????????????
            pass

    def _inject_runtime_args(self, state: AgentState, response: Any) -> Any:
        tool_calls = getattr(response, "tool_calls", []) or []
        for tc in tool_calls:
            args = tc.get("args")
            if not isinstance(args, dict):
                args = {}
                tc["args"] = args
            args.setdefault("user_id", state["user_id"])
        return response

    def _call_model(self, state: AgentState):
        system_msg = SystemMessage(content=AgentConfig.SYSTEM_PROMPT)
        response = self.model.invoke([system_msg] + state["messages"])
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

    def _get_user_role(self, user_id: str) -> str:
        try:
            with Session(engine) as session:
                user = session.get(User, int(user_id))
                if user and user.role:
                    return str(user.role)
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
        response = self.plain_model.invoke([system_msg] + state["messages"])
        return {"messages": [response], "thought_event": "已直接生成答复（未调用工具）"}

    def _should_continue(self, state: AgentState):
        last_message = state["messages"][-1]
        return "tools" if getattr(last_message, "tool_calls", None) else "summarize"

    def _summarize_and_store(self, state: AgentState):
        summary_prompt = SystemMessage(
            content="分析对话，提取 1-2 条关于用户的新信息（偏好/习惯/背景）。若无新增信息，仅回复 NONE。"
        )

        response = self.model.invoke([summary_prompt] + state["messages"])
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
                        if last_msg is not None and getattr(last_msg, "tool_calls", None):
                            for tc in last_msg.tool_calls:
                                print(f"--- [内核决策] 调用工具 [{tc['name']}]")
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
                        payload["tool_results"] = [
                            {
                                "name": getattr(last_msg, "name", "tool") if last_msg is not None else "tool",
                                "tool_call_id": getattr(last_msg, "tool_call_id", None) if last_msg is not None else None,
                                "output": output[:6000],
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
