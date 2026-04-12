from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from threading import Thread
from threading import Lock
from typing import Any, Callable, Dict, Optional
import time

from app.ai.document_parser import parse_document
from app.agent_plugin.agent.agent import AgentCore, write_agent_graph_svg
from app.agent_plugin.agent.config import AgentConfig
from app.agent_plugin.agent.memory import GLOBAL_KNOWLEDGE_USER_ID
from app.agent_plugin.bootstrap import ensure_agent_plugin_configured
from app.core.config import GlobalConfig
from app.scripts.download_embedding import ensure_agent_embedding_ready


logger = logging.getLogger(__name__)
_LOCK = Lock()
_AGENT_CORE: AgentCore | None = None
_INGEST_LOCK = Lock()
_INGEST_STARTED = False
_FILE_REF_RE = re.compile(r"(/media/(?:docs|images|avatars)/[^\s\"'<>]+)")
_FILE_PARSE_LINE_RE = re.compile(r"^【文件解析】.*$", re.MULTILINE)
_FILE_REF_LINE_RE = re.compile(r"^【文件引用】.*$", re.MULTILINE)
_AGENT_PROMPT_SOFT_LIMIT = 2200
_AGENT_PROMPT_HARD_LIMIT = 3200


def _console(text: str) -> None:
    print(text, flush=True)


def warmup_agent_plugin() -> None:
    if not GlobalConfig.AGENT_PLUGIN_ENABLED:
        _console("[AgentPlugin] AGENT_PLUGIN_ENABLED=false，跳过预热")
        return
    started = time.perf_counter()
    _console("\n" + "=" * 80)
    _console("Agent 插件预热开始".center(80))
    _console("=" * 80)
    _console(">>> [1/2] 初始化 Agent Core（包含 embedding 检查）...")
    _get_agent_core()
    _console(">>> [2/2] Agent Core 初始化完成")
    _console(f"✓ Agent 插件预热完成，用时 {time.perf_counter() - started:.2f}s")
    _console("=" * 80 + "\n")


def _console_banner(title: str) -> None:
    _console("=" * 80)
    _console(title)
    _console("=" * 80)


def warmup_agent_plugin() -> None:
    if not GlobalConfig.AGENT_PLUGIN_ENABLED:
        _console("[AgentPlugin] AGENT_PLUGIN_ENABLED=false, skip warmup")
        return

    started = time.perf_counter()
    _console("")
    _console_banner("[Startup] Agent Plugin Warmup Start")
    _console(">>> [1/2] Initializing Agent Core (including embedding check)...")
    _get_agent_core()
    _console(">>> [2/2] Agent Core initialization completed")
    _console_banner(f"[Startup] Agent Plugin Warmup Done ({time.perf_counter() - started:.2f}s)")


def ensure_agent_graph_svg_on_startup(overwrite: bool = True) -> None:
    graph_path = Path(str(GlobalConfig.AGENT_GRAPH_SVG_PATH))
    try:
        wrote = write_agent_graph_svg(graph_path=graph_path, overwrite=overwrite)
        if wrote:
            _console(f"✓ AgentGraph 已生成：{graph_path}")
        else:
            _console(f"✓ AgentGraph 已存在：{graph_path}")
    except Exception as exc:
        _console(f"✗ AgentGraph 生成失败：{exc}")
        logger.exception("AgentGraph 生成失败: %s", exc)


def _ensure_agent_embedding_ready() -> None:
    ensure_agent_embedding_ready(
        skip_if_disabled=True,
        allow_download=not os.getenv("DOCKER_DEPLOYMENT"),
    )
    return

    if not GlobalConfig.AGENT_PLUGIN_ENABLED:
        return

    embedding_path = Path(str(AgentConfig.EMBEDDING_MODEL))
    if embedding_path.exists():
        _console(f"✓ Embedding 已存在：{embedding_path}")
        return

    _console(f">>> Embedding 缺失，开始下载：{embedding_path}")
    logger.warning(
        "Agent plugin enabled but embedding missing, preparing download: %s",
        embedding_path,
    )
    embedding_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        from sentence_transformers import SentenceTransformer

        model_name = str(GlobalConfig.AGENT_PLUGIN_EMBEDDING_MODEL_NAME)
        model = SentenceTransformer(
            model_name,
            cache_folder=str(GlobalConfig.EMBEDDING_MODELS_DIR),
        )
        model.save(str(embedding_path))
        _console(f"✓ Embedding 下载完成并已保存：{embedding_path}")
        logger.info(
            "Agent embedding download completed: model=%s, saved_to=%s",
            model_name,
            embedding_path,
        )
    except Exception as exc:
        _console(f"✗ Embedding 下载失败：{exc}")
        logger.exception("Agent embedding prepare failed: %s", exc)
        raise RuntimeError(
            f"Agent plugin enabled but embedding unavailable: {embedding_path}"
        ) from exc


def _get_agent_core() -> AgentCore:
    global _AGENT_CORE
    with _LOCK:
        if _AGENT_CORE is None:
            ensure_agent_plugin_configured()
            _ensure_agent_embedding_ready()
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
        _console(">>> [RAG] 开始初始化全局向量知识库...")
        result = core.memory_engine.rag_ingest(user_id=GLOBAL_KNOWLEDGE_USER_ID) or {}
        status = str(result.get("status", "")).strip().lower()
        source = result.get("source_path") or GlobalConfig.AGENT_PLUGIN_RAG_RAW_FILE_PATH
        input_count = int(result.get("input_count", 0) or 0)
        synced_count = int(result.get("synced_count", 0) or 0)

        if status == "synced":
            _console(f"✓ [RAG] 全局知识同步完成：{synced_count} 条（来源 {source}）")
            logger.info(
                "Agent plugin 全局知识已同步: source=%s, owner=%s, input_count=%s, synced_count=%s",
                source,
                GLOBAL_KNOWLEDGE_USER_ID,
                input_count,
                synced_count,
            )
            return
        if status == "skipped":
            _console(f"✓ [RAG] 全局知识未变化，跳过同步（来源 {source}）")
            logger.info(
                "Agent plugin 全局知识跳过同步: source=%s, owner=%s, input_count=%s",
                source,
                GLOBAL_KNOWLEDGE_USER_ID,
                input_count,
            )
            return
        if status == "empty":
            _console(f"✓ [RAG] 无可同步知识，已跳过（来源 {source}）")
            logger.info(
                "Agent plugin 全局知识为空，跳过同步: source=%s, owner=%s",
                source,
                GLOBAL_KNOWLEDGE_USER_ID,
            )
            return

        _console("✓ [RAG] 全局知识初始化完成")
        logger.info(
            "Agent plugin 全局知识初始化完成: source=%s, owner=%s, status=%s",
            source,
            GLOBAL_KNOWLEDGE_USER_ID,
            status or "unknown",
        )
    except Exception:
        _console("✗ [RAG] 全局向量知识库初始化失败")
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


def _extract_display_from_tool_output(tool_name: str, output: str) -> list[dict[str, Any]]:
    if not output:
        return []
    payload = _try_parse_json_object(output)
    if not isinstance(payload, dict) or not payload.get("ok"):
        return []
    raw_cards = payload.get("display")
    if not isinstance(raw_cards, list):
        return []

    cards: list[dict[str, Any]] = []
    for card in raw_cards:
        if not isinstance(card, dict):
            continue
        normalized = dict(card)
        normalized.setdefault("source_tool", tool_name)
        cards.append(normalized)
    return cards


def _compact_text(text: str, limit: int = 240) -> str:
    normalized = " ".join(str(text or "").split()).strip()
    if not normalized:
        return ""
    return normalized if len(normalized) <= limit else f"{normalized[: limit - 3]}..."


def _extract_file_refs(prompt: str) -> list[str]:
    refs: list[str] = []
    seen: set[str] = set()
    for match in _FILE_REF_RE.findall(str(prompt or "")):
        item = match.rstrip(".,;:)]}>")
        if not item or item in seen:
            continue
        seen.add(item)
        refs.append(item)
    return refs


def _build_agent_prompt(prompt: str) -> tuple[str, dict[str, Any]]:
    raw = str(prompt or "").strip()
    meta = {
        "original_length": len(raw),
        "final_length": len(raw),
        "prompt_compacted": False,
        "file_ref_count": len(_extract_file_refs(raw)),
    }
    if not raw:
        return raw, meta

    file_refs = _extract_file_refs(raw)
    if len(raw) <= _AGENT_PROMPT_SOFT_LIMIT:
        return raw, meta

    leading_text = raw
    marker_positions = [idx for idx in (raw.find("【文件解析】"), raw.find("【文件引用】")) if idx >= 0]
    if marker_positions:
        leading_text = raw[: min(marker_positions)].strip()
    leading_text = _compact_text(leading_text, limit=360)

    file_parse_lines = _FILE_PARSE_LINE_RE.findall(raw)[:6]
    file_ref_lines = _FILE_REF_LINE_RE.findall(raw)[:6]

    parts: list[str] = []
    if leading_text:
        parts.append(leading_text)
    parts.extend(file_parse_lines)
    parts.extend(file_ref_lines)

    if file_refs:
        parts.append("文档正文过长，已在入口处省略。请优先根据上述文件引用调用上传文件解析工具，再基于文件内容回答。")
    else:
        parts.append("输入正文过长，已在入口处截断。请基于保留内容先完成回答。")
        remaining = raw[len(leading_text) :] if leading_text and raw.startswith(leading_text) else raw
        remaining = remaining.strip()
        if remaining:
            parts.append(_compact_text(remaining, limit=1400))

    compacted = "\n\n".join(part for part in parts if part).strip()
    if len(compacted) > _AGENT_PROMPT_HARD_LIMIT:
        compacted = compacted[:_AGENT_PROMPT_HARD_LIMIT].rstrip()

    meta["final_length"] = len(compacted)
    meta["prompt_compacted"] = compacted != raw
    return compacted, meta


def run_agent_plugin(
    user_id: int,
    prompt: str,
    mode: str = "agent",
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
        "display_cards": [],
    }

    if not GlobalConfig.AGENT_PLUGIN_ENABLED:
        return base_result

    thread_id = f"conversation_{conversation_id}" if conversation_id else f"user_{user_id}_adhoc"
    assistant_reply = ""
    tool_calls: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    display_cards: list[dict[str, Any]] = []
    seen = set()
    display_seen = set()
    agent_prompt, prompt_meta = _build_agent_prompt(prompt)
    if prompt_meta.get("prompt_compacted"):
        logger.info(
            "Agent prompt compacted user_id=%s thread_id=%s original_length=%s final_length=%s file_ref_count=%s",
            user_id,
            thread_id,
            prompt_meta.get("original_length"),
            prompt_meta.get("final_length"),
            prompt_meta.get("file_ref_count"),
        )
        if trace_callback:
            trace_callback(
                {
                    "tool": "agent_prompt_compactor",
                    "input": json.dumps(
                        {
                            "original_length": prompt_meta.get("original_length"),
                            "final_length": prompt_meta.get("final_length"),
                            "file_ref_count": prompt_meta.get("file_ref_count"),
                        },
                        ensure_ascii=False,
                    ),
                    "output": "已压缩超长输入，保留文件引用，优先走文件工具解析。",
                }
            )

    try:
        core = _get_agent_core()
        for raw_chunk in core.stream_run(
            prompt=agent_prompt,
            user_id=str(user_id),
            thread_id=thread_id,
            mode=mode,
        ):
            payload = _parse_sse_chunk(raw_chunk)
            if not payload:
                continue

            node_name = str(payload.get("node", "") or "")
            has_tool_calls = bool(payload.get("tool_calls"))
            if payload.get("content") and (
                node_name in {"answer", "blocked", "output_safety"}
                or (node_name == "agent" and not has_tool_calls)
            ):
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
                preview_output = str(tr.get("output", "")).strip()
                full_output = str(tr.get("full_output") or preview_output).strip()
                if not full_output and not preview_output:
                    continue
                tool_name = tr.get("name", "tool")
                output = preview_output or full_output
                for card in _extract_display_from_tool_output(str(tool_name), full_output):
                    key = json.dumps(card, ensure_ascii=False, sort_keys=True, default=str)
                    if key in display_seen:
                        continue
                    display_seen.add(key)
                    display_cards.append(card)
                matched = False
                for item in reversed(tool_calls):
                    if item.get("tool") == tool_name and not item.get("output"):
                        item["output"] = output
                        evidence.extend(_extract_evidence_from_tool_output(str(tool_name), full_output))
                        matched = True
                        if trace_callback:
                            trace_callback(item)
                        break
                if not matched:
                    fallback = {"tool": tool_name, "input": "{}", "output": output}
                    tool_calls.append(fallback)
                    evidence.extend(_extract_evidence_from_tool_output(str(tool_name), full_output))
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
    base_result["display_cards"] = display_cards
    return base_result
