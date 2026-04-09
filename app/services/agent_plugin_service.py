from __future__ import annotations

import json
import logging
from threading import Thread
from threading import Lock
from typing import Any, Callable, Dict, Optional

from app.ai.document_parser import parse_document
from app.agent_plugin.agent.agent import AgentCore
from app.agent_plugin.agent.memory import GLOBAL_KNOWLEDGE_USER_ID
from app.agent_plugin.bootstrap import ensure_agent_plugin_configured
from app.core.config import GlobalConfig


logger = logging.getLogger(__name__)
_LOCK = Lock()
_AGENT_CORE: AgentCore | None = None
_INGEST_LOCK = Lock()
_INGEST_STARTED = False


def _get_agent_core() -> AgentCore:
    global _AGENT_CORE
    with _LOCK:
        if _AGENT_CORE is None:
            ensure_agent_plugin_configured()
            _AGENT_CORE = AgentCore()
            _ensure_global_rag_ingest_once(_AGENT_CORE)
    return _AGENT_CORE


def close_agent_core() -> None:
    global _AGENT_CORE, _INGEST_STARTED
    with _LOCK:
        if _AGENT_CORE is not None:
            _AGENT_CORE.close()
            _AGENT_CORE = None
    with _INGEST_LOCK:
        _INGEST_STARTED = False


def _run_global_rag_ingest(core: AgentCore) -> None:
    try:
        core.memory_engine.rag_ingest(user_id=GLOBAL_KNOWLEDGE_USER_ID)
        logger.info(
            "Agent plugin 全局知识已同步: source=%s, owner=%s",
            GlobalConfig.AGENT_PLUGIN_RAG_RAW_FILE_PATH,
            GLOBAL_KNOWLEDGE_USER_ID,
        )
    except Exception:
        logger.exception("Agent plugin 全局知识同步失败")


def _ensure_global_rag_ingest_once(core: AgentCore) -> None:
    global _INGEST_STARTED
    with _INGEST_LOCK:
        if _INGEST_STARTED:
            return
        _INGEST_STARTED = True
    Thread(target=_run_global_rag_ingest, args=(core,), daemon=True).start()


def _parse_sse_chunk(raw_chunk: str) -> Dict[str, Any] | None:
    if not raw_chunk or not raw_chunk.startswith("data: "):
        return None
    body = raw_chunk[len("data: ") :].strip()
    if not body or body == "[DONE]":
        return None
    try:
        return json.loads(body)
    except Exception:
        return None


def _try_parse_json_object(text: str) -> dict[str, Any] | None:
    raw = (text or "").strip()
    if not raw:
        return None
    if raw.startswith("```json"):
        raw = raw[7:].strip()
    if raw.startswith("```"):
        raw = raw[3:].strip()
    if raw.endswith("```"):
        raw = raw[:-3].strip()
    try:
        obj = json.loads(raw)
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


def _extract_evidence_from_tool_output(tool_name: str, output: str) -> list[dict[str, Any]]:
    if not output:
        return []
    try:
        payload = json.loads(output)
    except Exception:
        return []

    if not isinstance(payload, dict) or not payload.get("ok"):
        return []
    items = payload.get("items")
    if not isinstance(items, list):
        return []

    evidence: list[dict[str, Any]] = []
    for item in items[:10]:
        if isinstance(item, str):
            content = item.strip()
        elif isinstance(item, dict):
            content = json.dumps(item, ensure_ascii=False)
        else:
            content = str(item).strip()
        if not content:
            continue
        evidence.append(
            {
                "source": tool_name,
                "content": content[:1200],
                "score": 1.0,
            }
        )
    return evidence


def run_agent_plugin(
    user_id: int,
    prompt: str,
    conversation_id: Optional[int] = None,
    trace_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> Dict[str, Any]:
    base_result = {
        "enabled": bool(GlobalConfig.AGENT_PLUGIN_ENABLED),
        "assistant_reply": "",
        "tool_calls": [],
        "structured": None,
        "parse_mode": None,
        "evidence": [],
    }

    if not GlobalConfig.AGENT_PLUGIN_ENABLED:
        return base_result

    thread_id = f"conversation_{conversation_id}" if conversation_id else f"user_{user_id}_adhoc"
    assistant_reply = ""
    tool_calls: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    seen = set()

    try:
        core = _get_agent_core()
        for raw_chunk in core.stream_run(prompt=prompt, user_id=str(user_id), thread_id=thread_id):
            payload = _parse_sse_chunk(raw_chunk)
            if not payload:
                continue

            if payload.get("node") in {"agent", "answer", "blocked", "output_safety"} and payload.get("content"):
                assistant_reply = str(payload["content"])
            thought_event = str(payload.get("thought_event", "")).strip()
            if thought_event and trace_callback:
                trace_callback(
                    {
                        "tool": "agent_thought",
                        "input": thought_event,
                        "output": "",
                    }
                )

            for tc in payload.get("tool_calls", []) or []:
                normalized = {
                    "tool": tc.get("name", "tool"),
                    "input": json.dumps(tc.get("args", {}), ensure_ascii=False),
                    "output": "",
                }
                key = json.dumps(normalized, ensure_ascii=False, sort_keys=True)
                if key in seen:
                    continue
                seen.add(key)
                tool_calls.append(normalized)
                if trace_callback:
                    trace_callback(normalized)

            for tr in payload.get("tool_results", []) or []:
                output = str(tr.get("output", "")).strip()
                if not output:
                    continue
                tool_name = tr.get("name", "tool")
                matched = False
                for item in reversed(tool_calls):
                    if item.get("tool") == tool_name and not item.get("output"):
                        item["output"] = output
                        evidence.extend(_extract_evidence_from_tool_output(str(tool_name), output))
                        matched = True
                        if trace_callback:
                            trace_callback(item)
                        break
                if not matched:
                    fallback = {"tool": tool_name, "input": "{}", "output": output}
                    tool_calls.append(fallback)
                    evidence.extend(_extract_evidence_from_tool_output(str(tool_name), output))
                    if trace_callback:
                        trace_callback(fallback)

    except Exception as exc:
        logger.exception("Agent plugin 执行失败: %s", exc)
        base_result["error"] = str(exc)
        return base_result

    structured = _try_parse_json_object(assistant_reply)
    parse_mode: str | None = "plugin_json" if structured else None
    if structured is None:
        try:
            structured, parse_mode = parse_document(prompt, user_id)
        except Exception:
            structured, parse_mode = None, None

    base_result["assistant_reply"] = assistant_reply
    base_result["tool_calls"] = tool_calls
    base_result["structured"] = structured
    base_result["parse_mode"] = parse_mode
    base_result["evidence"] = evidence
    return base_result
