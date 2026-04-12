import json
import logging
import re
import time
from pathlib import Path
from typing import Any

from app.ai.request_llm import RequestLLM
from app.models.chat_message import ChatMessageBase
from app.services.ocr_service import perform_kimi_ocr

logger = logging.getLogger(__name__)

MAX_PARSE_CHARS = 6000
_JSON_SCHEMA_SUPPORTED: bool | None = None
GRAPH_MIN_NODES = 600
GRAPH_MAX_NODES = 5000
GRAPH_MAX_DEPTH = 12
PAYLOAD_DICT_SCAN_LIMIT = 200
PAYLOAD_LIST_SCAN_LIMIT = 200
SOURCE_SENTENCE_CHARS = 96


def _normalize_text(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"[ \t]+", " ", text.replace("\r\n", "\n").replace("\r", "\n")).strip()


def _clean_json_response(response_text: str) -> Any:
    response_text = (response_text or "").strip()
    if response_text.startswith("```json"):
        response_text = response_text[7:]
    if response_text.startswith("```"):
        response_text = response_text[3:]
    if response_text.endswith("```"):
        response_text = response_text[:-3]
    response_text = response_text.strip()
    return json.loads(response_text)


def _extract_first_json_object(text: str) -> str | None:
    s = (text or "").strip()
    if not s:
        return None
    first_obj = s.find("{")
    first_arr = s.find("[")
    if first_obj < 0 and first_arr < 0:
        return None
    if first_obj < 0:
        start = first_arr
    elif first_arr < 0:
        start = first_obj
    else:
        start = min(first_obj, first_arr)

    stack: list[str] = []
    in_str = False
    esc = False
    for i in range(start, len(s)):
        ch = s[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch in "{[":
            stack.append(ch)
        elif ch in "}]":
            if not stack:
                return None
            top = stack.pop()
            if (top == "{" and ch != "}") or (top == "[" and ch != "]"):
                return None
            if not stack:
                return s[start : i + 1]
    return None


def _try_parse_json_loose(text: str) -> Any | None:
    if not text:
        return None
    candidates = []
    try:
        cleaned = _clean_json_response(text)
        if cleaned is not None:
            return cleaned
    except Exception:
        pass

    frag = _extract_first_json_object(text)
    if frag:
        candidates.append(frag)
        repaired = (
            frag.replace("\u201c", '"')
            .replace("\u201d", '"')
            .replace("\u2018", "'")
            .replace("\u2019", "'")
        )
        repaired = re.sub(r",\s*([}\]])", r"\1", repaired)
        candidates.append(repaired)

    for c in candidates:
        try:
            parsed = json.loads(c)
            if parsed is not None:
                return parsed
        except Exception:
            continue
    return None


def _normalize_payload_object(raw: Any) -> dict | None:
    if raw is None:
        return None
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, list):
        return {"items": raw}
    if isinstance(raw, (str, int, float, bool)):
        return {"value": raw}
    return {"value": str(raw)}


def _complete_truncated_json(text: str) -> str | None:
    """
    Best-effort local completion for truncated JSON text:
    - close unterminated string
    - close unmatched braces/brackets
    """
    s = (text or "").strip()
    if not s:
        return None
    frag = _extract_first_json_object(s) or s
    if not frag:
        return None

    stack: list[str] = []
    in_str = False
    esc = False
    for ch in frag:
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch in "{[":
            stack.append(ch)
        elif ch in "}]":
            if stack:
                top = stack[-1]
                if (top == "{" and ch == "}") or (top == "[" and ch == "]"):
                    stack.pop()

    out = frag
    if in_str:
        out += '"'
    while stack:
        top = stack.pop()
        out += "}" if top == "{" else "]"
    out = re.sub(r",\s*([}\]])", r"\1", out)
    return out


def _parse_response_to_object(response_text: str) -> Any | None:
    raw = _try_parse_json_loose(response_text)
    if raw is not None:
        return raw

    completed = _complete_truncated_json(response_text)
    if completed:
        raw = _try_parse_json_loose(completed)
        if raw is not None:
            return raw

    repaired = _repair_json_via_llm(response_text)
    if repaired is not None:
        return repaired

    return None


def _unwrap_stringified_payload(raw: Any) -> Any:
    """
    If LLM returns {"raw_llm_text":"{...}"}-like wrapper, try to recover object payload.
    """
    if not isinstance(raw, dict):
        return raw
    candidate_keys = ("raw_llm_text", "json", "payload", "data", "result")
    for key in candidate_keys:
        value = raw.get(key)
        if not isinstance(value, str):
            continue
        txt = value.strip()
        if not txt.startswith("{") and not txt.startswith("["):
            continue

        parsed = _parse_response_to_object(txt[:12000])
        if parsed is not None:
            return parsed
    return raw


def _freeform_response_format() -> dict:
    # 核心原则（禁止动摇）：仅约束“必须是 JSON 对象”，不限制内容字段与层级。
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "freeform_payload",
            "strict": True,
            "schema": {
                "type": "object",
                "additionalProperties": True,
            },
        },
    }


def _call_freeform_llm(kimi: RequestLLM, content: str, temperature: float = 0.2) -> str:
    global _JSON_SCHEMA_SUPPORTED
    payload = content[:MAX_PARSE_CHARS]

    if _JSON_SCHEMA_SUPPORTED is not False:
        resp = kimi.get_response(
            content=payload,
            model="moonshot-v1-32k",
            response_format=_freeform_response_format(),
            temperature=temperature,
        )
        if resp and not str(resp).strip().startswith("Error:"):
            _JSON_SCHEMA_SUPPORTED = True
            return resp
        _JSON_SCHEMA_SUPPORTED = False
        logger.warning("json_schema response_format unsupported, fallback to json_object")

    return kimi.get_response(
        content=payload,
        model="moonshot-v1-32k",
        response_format={"type": "json_object"},
        temperature=temperature,
    )


def _as_displayable_fallback_payload(response_text: str, source_text: str) -> dict:
    src = str(response_text or source_text or "").strip()
    if not src:
        return {}
    return {
        "parse_warning": "llm_output_not_valid_json_object",
        "raw_excerpt": src[:MAX_PARSE_CHARS],
    }


def _repair_json_via_llm(raw_text: str) -> Any | None:
    """
    DO NOT CHANGE:
    This is a repair-only stage. It must preserve freeform semantics
    and only make the output strict JSON-parseable.
    """
    snippet = (raw_text or "")[:12000]
    if not snippet:
        return None
    try:
        fixer = RequestLLM()
        fixer.system_prompt = (
            "你是JSON修复器。"
            "输入可能是损坏的JSON。"
            "你的任务是仅修复语法并返回严格JSON对象。"
            "禁止增删语义字段，禁止套固定模板，禁止解释。"
        )
        fixed = fixer.get_response(
            content=snippet,
            model="moonshot-v1-32k",
            response_format={"type": "json_object"},
            temperature=0.0,
        )
        return _try_parse_json_loose(fixed)
    except Exception:
        return None


def _safe_nodes(raw: Any) -> list[dict]:
    if not isinstance(raw, list):
        return []
    out: list[dict] = []
    seen = set()
    for idx, item in enumerate(raw):
        if not isinstance(item, dict):
            continue
        nid = str(item.get("id") or f"node_{idx+1}").strip()
        if not nid:
            nid = f"node_{idx+1}"
        if nid in seen:
            nid = f"{nid}_{idx+1}"
        seen.add(nid)
        label = str(item.get("label") or nid).strip()
        try:
            importance = float(item.get("importance", 0.5))
        except (TypeError, ValueError):
            importance = 0.5
        out.append(
            {
                "id": nid,
                "label": label,
                "type": str(item.get("type") or "实体"),
                "importance": max(0.0, min(1.0, importance)),
                "layer": item.get("layer"),
                "group": item.get("group"),
                "parent_id": item.get("parent_id"),
                "properties": item.get("properties") if isinstance(item.get("properties"), dict) else {},
            }
        )
    return out


def _safe_links(raw: Any, node_ids: set[str]) -> list[dict]:
    if not isinstance(raw, list):
        return []
    out: list[dict] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        source = str(item.get("source") or "").strip()
        target = str(item.get("target") or "").strip()
        if source not in node_ids or target not in node_ids:
            continue
        try:
            strength = float(item.get("strength", 0.6))
        except (TypeError, ValueError):
            strength = 0.6
        logic_type = str(item.get("logic_type") or "positive").lower()
        if logic_type not in {"positive", "negative"}:
            logic_type = "positive"
        out.append(
            {
                "source": source,
                "target": target,
                "relation": str(item.get("relation") or "关联"),
                "logic_type": logic_type,
                "strength": max(0.0, min(1.0, strength)),
                "evidence": item.get("evidence"),
            }
        )
    return out


def _basic_visual_config(raw: Any, nodes: list[dict]) -> dict:
    cfg = raw if isinstance(raw, dict) else {}
    focus_node = cfg.get("focus_node")
    node_ids = {n.get("id") for n in nodes}
    if focus_node not in node_ids:
        focus_node = nodes[0]["id"] if nodes else None
    try:
        initial_zoom = float(cfg.get("initial_zoom", 1.0))
    except (TypeError, ValueError):
        initial_zoom = 1.0
    text_mapping = cfg.get("text_mapping") if isinstance(cfg.get("text_mapping"), dict) else {}
    return {
        "focus_node": focus_node,
        "initial_zoom": initial_zoom,
        "text_mapping": text_mapping,
    }


def _normalize_span_value(value: Any, text_length: int) -> list[int] | None:
    if not isinstance(value, (list, tuple)) or len(value) < 2:
        return None
    try:
        start = int(value[0])
        end = int(value[1])
    except (TypeError, ValueError):
        return None
    if start < 0 or end <= start or end > text_length:
        return None
    return [start, end]


def _node_mapping_candidates(node: dict[str, Any]) -> list[str]:
    props = node.get("properties") if isinstance(node.get("properties"), dict) else {}
    candidates: list[str] = []
    seen: set[str] = set()

    def push(value: Any) -> None:
        text = _normalize_text(str(value or ""))
        if not text:
            return
        if len(text) < 4 and not re.search(r"[\u4e00-\u9fa5]{2,}", text):
            return
        if text in seen:
            return
        seen.add(text)
        candidates.append(text)

    push(node.get("label"))
    for key in (
        "source_text",
        "source_quote",
        "text",
        "snippet",
        "excerpt",
        "quote",
        "evidence",
        "summary",
        "content",
        "raw",
    ):
        push(props.get(key))
    return candidates


def _find_text_span(source_text: str, candidate: str) -> list[int] | None:
    text = _normalize_text(source_text)
    query = _normalize_text(candidate)
    if not text or not query:
        return None

    idx = text.find(query)
    if idx >= 0:
        return [idx, idx + len(query)]

    fragments = [
        piece.strip()
        for piece in re.split(r"[，,；;：:\n/|]", query)
        if piece and piece.strip()
    ]
    fragments.sort(key=len, reverse=True)
    for fragment in fragments[:6]:
        if len(fragment) < 6 and not re.search(r"[\u4e00-\u9fa5]{3,}", fragment):
            continue
        idx = text.find(fragment)
        if idx >= 0:
            return [idx, idx + len(fragment)]
    return None


def _build_parent_children_index(nodes: list[dict], links: list[dict]) -> tuple[dict[str, str | None], dict[str, list[str]]]:
    node_ids = {str(node.get("id") or "") for node in nodes}
    parent_map: dict[str, str | None] = {}
    root_id = _pick_graph_root_id(nodes, links)
    if root_id:
        parent_map[root_id] = None

    for node in nodes:
        node_id = str(node.get("id") or "")
        parent_id = str(node.get("parent_id") or "").strip()
        if node_id and parent_id and parent_id in node_ids and parent_id != node_id and node_id not in parent_map:
            parent_map[node_id] = parent_id

    for link in links:
        source = str(link.get("source") or "").strip()
        target = str(link.get("target") or "").strip()
        if not source or not target or source == target:
            continue
        if source not in node_ids or target not in node_ids:
            continue
        parent_map.setdefault(target, source)

    if root_id:
        for node in nodes:
            node_id = str(node.get("id") or "")
            if node_id and node_id != root_id:
                parent_map.setdefault(node_id, root_id)

    children_map: dict[str, list[str]] = {}
    for child_id, parent_id in parent_map.items():
        if not parent_id:
            continue
        children_map.setdefault(parent_id, []).append(child_id)
    return parent_map, children_map


def build_text_mapping_for_graph(
    nodes: list[dict],
    *,
    source_text: str,
    links: list[dict] | None = None,
    base_mapping: dict[str, Any] | None = None,
) -> dict[str, list[int]]:
    text = _normalize_text(source_text)
    if not text or not nodes:
        return {}

    links = links or []
    text_length = len(text)
    mapping: dict[str, list[int]] = {}

    if isinstance(base_mapping, dict):
        for node_id, span in base_mapping.items():
            normalized = _normalize_span_value(span, text_length)
            if normalized:
                mapping[str(node_id)] = normalized

    for node in nodes:
        node_id = str(node.get("id") or "").strip()
        if not node_id or node_id in mapping:
            continue
        props = node.get("properties") if isinstance(node.get("properties"), dict) else {}
        direct_span = (
            _normalize_span_value(props.get("span"), text_length)
            or _normalize_span_value(props.get("source_span"), text_length)
            or _normalize_span_value(props.get("text_span"), text_length)
        )
        if direct_span:
            mapping[node_id] = direct_span
            continue
        for candidate in _node_mapping_candidates(node):
            hit = _find_text_span(text, candidate)
            if hit:
                mapping[node_id] = hit
                break

    parent_map, children_map = _build_parent_children_index(nodes, links)
    resolved: dict[str, list[int]] = dict(mapping)

    def resolve_from_descendants(node_id: str, visiting: set[str] | None = None) -> list[int] | None:
        if node_id in resolved:
            return resolved[node_id]
        visiting = visiting or set()
        if node_id in visiting:
            return None
        visiting.add(node_id)
        spans: list[list[int]] = []
        for child_id in children_map.get(node_id, []):
            child_span = resolve_from_descendants(child_id, visiting)
            if child_span:
                spans.append(child_span)
        visiting.remove(node_id)
        if not spans:
            return None
        merged = [min(span[0] for span in spans), max(span[1] for span in spans)]
        resolved[node_id] = merged
        return merged

    for node in nodes:
        node_id = str(node.get("id") or "").strip()
        if not node_id or node_id in resolved:
            continue
        resolve_from_descendants(node_id)

    root_id = _pick_graph_root_id(nodes, links)
    if root_id and text_length:
        resolved[root_id] = [0, text_length]

    return resolved


def build_visual_config_for_graph(
    raw: Any,
    nodes: list[dict],
    *,
    links: list[dict] | None = None,
    source_text: str = "",
) -> dict:
    cfg = _basic_visual_config(raw, nodes)
    cfg["text_mapping"] = build_text_mapping_for_graph(
        nodes,
        source_text=source_text,
        links=links or [],
        base_mapping=cfg.get("text_mapping"),
    )
    return cfg


def _slug(text: str) -> str:
    return re.sub(r"[^0-9a-zA-Z\u4e00-\u9fa5]+", "_", str(text or "").strip()).strip("_") or "node"


def _pick_payload_title(payload: Any) -> str:
    seen: set[int] = set()

    def walk(value: Any, depth: int = 0) -> str:
        if depth > 4:
            return ""
        if isinstance(value, str):
            t = value.strip()
            if t and len(t) >= 2:
                return t[:80]
            return ""
        if isinstance(value, list):
            for item in value[:20]:
                hit = walk(item, depth + 1)
                if hit:
                    return hit
            return ""
        if isinstance(value, dict):
            oid = id(value)
            if oid in seen:
                return ""
            seen.add(oid)
            for k, v in list(value.items())[:40]:
                key_text = str(k).strip()
                if key_text and len(key_text) >= 2:
                    return key_text[:80]
                hit = walk(v, depth + 1)
                if hit:
                    return hit
        return ""

    title = walk(payload)
    return title or "文档"


def _estimate_graph_node_budget(payload: Any, source_text: str = "") -> int:
    try:
        payload_size = len(json.dumps(payload, ensure_ascii=False))
    except Exception:
        payload_size = 0
    text_size = len(source_text or "")
    budget = 600 + min(3400, text_size // 28) + min(1000, payload_size // 18)
    return max(GRAPH_MIN_NODES, min(GRAPH_MAX_NODES, budget))


def _pick_graph_root_id(nodes: list[dict], links: list[dict]) -> str | None:
    if not nodes:
        return None
    node_ids = {str(node.get("id") or "") for node in nodes}
    parentless = [
        node
        for node in nodes
        if not node.get("parent_id") or str(node.get("parent_id")) not in node_ids
    ]
    if parentless:
        ranked = sorted(parentless, key=lambda item: float(item.get("importance") or 0.0), reverse=True)
        return str(ranked[0].get("id") or "") or None
    targets = {str(link.get("target") or "") for link in links}
    roots = [node for node in nodes if str(node.get("id") or "") not in targets]
    if roots:
        ranked = sorted(roots, key=lambda item: float(item.get("importance") or 0.0), reverse=True)
        return str(ranked[0].get("id") or "") or None
    ranked = sorted(nodes, key=lambda item: float(item.get("importance") or 0.0), reverse=True)
    return str(ranked[0].get("id") or "") or None


def _outline_level(text: str) -> int | None:
    value = str(text or "").strip()
    if not value:
        return None
    patterns = (
        (r"^\d+(?:\.\d+){2,}[、.．]?", 4),
        (r"^\d+\.\d+[、.．]?", 3),
        (r"^[一二三四五六七八九十百千]+[、.．]", 1),
        (r"^[（(][一二三四五六七八九十百千]+[）)]", 2),
        (r"^\d+[、.．]", 2),
        (r"^[（(]?\d+[）)]", 3),
        (r"^[A-Za-z][、.)]", 4),
    )
    for pattern, level in patterns:
        if re.match(pattern, value):
            return level
    return None


def _iter_source_blocks(source_text: str) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    lines: list[dict[str, Any]] = []
    cursor = 0

    def flush() -> None:
        nonlocal lines
        if not lines:
            return
        blocks.append(
            {
                "start": lines[0]["start"],
                "end": lines[-1]["end"],
                "text": "\n".join(item["text"] for item in lines).strip(),
                "lines": list(lines),
            }
        )
        lines = []

    for raw_line in source_text.splitlines(True):
        line = raw_line[:-1] if raw_line.endswith("\n") else raw_line
        stripped = line.strip()
        line_end = cursor + len(line)
        if stripped:
            line_start = cursor + (len(line) - len(line.lstrip()))
            lines.append({"start": line_start, "end": line_end, "text": stripped})
        else:
            flush()
        cursor += len(raw_line)
    flush()
    return blocks


def _split_block_sentences(text: str, base_start: int) -> list[dict[str, Any]]:
    parts: list[dict[str, Any]] = []
    for match in re.finditer(r"[^。！？!?；;\n]+[。！？!?；;]?|[^\n]+", text):
        segment = match.group(0).strip()
        if not segment:
            continue
        parts.append(
            {
                "start": base_start + match.start(),
                "end": base_start + match.end(),
                "text": segment,
            }
        )
    if len(parts) <= 1:
        return []

    merged: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for part in parts:
        if current is None:
            current = dict(part)
            continue
        candidate = f'{current["text"]}{part["text"]}'
        if len(candidate) > SOURCE_SENTENCE_CHARS:
            merged.append(current)
            current = dict(part)
            continue
        current["end"] = part["end"]
        current["text"] = candidate
    if current:
        merged.append(current)
    return [item for item in merged if item["text"].strip()]


def _append_source_text_structure(
    nodes: list[dict],
    links: list[dict],
    *,
    source_text: str,
    attach_to: str | None,
    max_nodes: int,
) -> None:
    text = _normalize_text(source_text)
    if not text or len(nodes) >= max_nodes:
        return

    blocks = _iter_source_blocks(text)
    if not blocks:
        return

    seen_nodes = {str(node.get("id") or "") for node in nodes}
    seen_edges = {
        (str(link.get("source") or ""), str(link.get("target") or ""), str(link.get("relation") or ""))
        for link in links
    }

    def unique_id(base: str) -> str:
        candidate = base
        suffix = 2
        while candidate in seen_nodes:
            candidate = f"{base}_{suffix}"
            suffix += 1
        return candidate

    def add_node(
        node_id: str,
        label: str,
        node_type: str,
        importance: float,
        parent_id: str | None,
        properties: dict[str, Any],
    ) -> bool:
        if node_id in seen_nodes or len(nodes) >= max_nodes:
            return False
        seen_nodes.add(node_id)
        nodes.append(
            {
                "id": node_id,
                "label": str(label)[:120],
                "type": node_type,
                "importance": max(0.2, min(1.0, importance)),
                "layer": "L3",
                "group": "source_text",
                "parent_id": parent_id,
                "properties": properties,
            }
        )
        return True

    def add_edge(source: str, target: str, relation: str, strength: float) -> None:
        if source not in seen_nodes or target not in seen_nodes:
            return
        key = (source, target, relation)
        if key in seen_edges:
            return
        seen_edges.add(key)
        links.append(
            {
                "source": source,
                "target": target,
                "relation": relation,
                "logic_type": "positive",
                "strength": max(0.2, min(1.0, strength)),
                "evidence": None,
            }
        )

    source_root_id = unique_id("source_text_root")
    if add_node(
        source_root_id,
        "原文结构",
        "结构",
        0.86,
        attach_to,
        {"source": "original_text", "span": [0, len(text)]},
    ) and attach_to:
        add_edge(attach_to, source_root_id, "展开", 0.56)

    heading_stack: dict[int, str] = {0: source_root_id}
    current_parent_id = source_root_id

    def nearest_heading_parent(level: int) -> str:
        for idx in range(level - 1, -1, -1):
            if idx in heading_stack:
                return heading_stack[idx]
        return source_root_id

    def add_paragraph(block: dict[str, Any], parent_id: str, block_index: int) -> None:
        if len(nodes) >= max_nodes:
            return
        paragraph_id = unique_id(f"source_paragraph_{block_index}")
        paragraph_text = block["text"].replace("\n", " / ").strip()
        if not add_node(
            paragraph_id,
            paragraph_text,
            "段落",
            0.56,
            parent_id,
            {"source": "original_text", "span": [block["start"], block["end"]]},
        ):
            return
        add_edge(parent_id, paragraph_id, "展开", 0.46)

        short_lines = [item for item in block["lines"] if len(item["text"]) <= 48]
        if len(block["lines"]) > 1 and len(short_lines) >= min(len(block["lines"]), 2):
            for line_index, line in enumerate(block["lines"], start=1):
                if len(nodes) >= max_nodes:
                    break
                line_id = unique_id(f"source_line_{block_index}_{line_index}")
                if add_node(
                    line_id,
                    line["text"],
                    "条目",
                    0.48,
                    paragraph_id,
                    {"source": "original_text", "span": [line["start"], line["end"]]},
                ):
                    add_edge(paragraph_id, line_id, "细分", 0.42)
            return

        for sentence_index, sentence in enumerate(_split_block_sentences(block["text"], block["start"]), start=1):
            if len(nodes) >= max_nodes:
                break
            if sentence["text"].strip() == block["text"].strip():
                continue
            sentence_id = unique_id(f"source_sentence_{block_index}_{sentence_index}")
            if add_node(
                sentence_id,
                sentence["text"],
                "句子",
                0.42,
                paragraph_id,
                {"source": "original_text", "span": [sentence["start"], sentence["end"]]},
            ):
                add_edge(paragraph_id, sentence_id, "细分", 0.38)

    for block_index, block in enumerate(blocks, start=1):
        if len(nodes) >= max_nodes:
            break
        first_line = block["lines"][0]["text"] if block["lines"] else ""
        level = _outline_level(first_line)
        is_heading = level is not None and (len(block["lines"]) == 1 or len(first_line) <= 48)
        if is_heading:
            parent_id = nearest_heading_parent(level)
            section_id = unique_id(f"source_section_{block_index}")
            if add_node(
                section_id,
                block["text"].replace("\n", " / "),
                "章节",
                max(0.46, 0.74 - level * 0.06),
                parent_id,
                {"source": "original_text", "span": [block["start"], block["end"]]},
            ):
                add_edge(parent_id, section_id, "条目", 0.5)
                heading_stack = {k: v for k, v in heading_stack.items() if k < level}
                heading_stack[level] = section_id
                current_parent_id = section_id
            if len(block["lines"]) > 1:
                add_paragraph(
                    {
                        "start": block["lines"][1]["start"],
                        "end": block["lines"][-1]["end"],
                        "text": "\n".join(item["text"] for item in block["lines"][1:]).strip(),
                        "lines": block["lines"][1:],
                    },
                    current_parent_id,
                    block_index,
                )
            continue

        add_paragraph(block, current_parent_id, block_index)


def _supplement_existing_graph_with_source_text(
    nodes: list[dict],
    links: list[dict],
    *,
    source_text: str,
    max_nodes: int | None = None,
) -> tuple[list[dict], list[dict]]:
    if not nodes or not source_text:
        return nodes, links
    budget = max_nodes or _estimate_graph_node_budget({}, source_text)
    budget = max(budget, len(nodes))
    merged_nodes = [
        {
            **node,
            "properties": dict(node.get("properties") or {}),
        }
        for node in nodes
    ]
    merged_links = [dict(link) for link in links]
    root_id = _pick_graph_root_id(merged_nodes, merged_links)
    _append_source_text_structure(
        merged_nodes,
        merged_links,
        source_text=source_text,
        attach_to=root_id,
        max_nodes=budget,
    )
    return merged_nodes, merged_links


def _build_graph_from_payload(payload: dict, max_nodes: int | None = None, source_text: str = "") -> tuple[list[dict], list[dict]]:
    """
    核心原则（禁止动摇）：
    仅按 JSON 结构生成图谱，不做任何固定业务字段推断。
    """
    if not isinstance(payload, dict) or not payload:
        return [], []

    limit = max_nodes or _estimate_graph_node_budget(payload, source_text)
    nodes: list[dict] = []
    links: list[dict] = []
    seen_nodes: set[str] = set()
    seen_edges: set[tuple[str, str, str]] = set()
    seen_containers: set[int] = set()

    def add_node(node_id: str, label: str, layer: int, importance: float, parent_id: str | None = None) -> bool:
        if node_id in seen_nodes or len(nodes) >= limit:
            return False
        seen_nodes.add(node_id)
        nodes.append(
            {
                "id": node_id,
                "label": str(label)[:120],
                "type": "实体",
                "importance": max(0.2, min(1.0, importance)),
                "layer": f"L{min(layer, 3)}",
                "group": "payload",
                "parent_id": parent_id,
                "properties": {},
            }
        )
        return True

    def add_edge(source: str, target: str, relation: str = "关联", strength: float = 0.6) -> None:
        if source not in seen_nodes or target not in seen_nodes:
            return
        key = (source, target, relation)
        if key in seen_edges:
            return
        seen_edges.add(key)
        links.append(
            {
                "source": source,
                "target": target,
                "relation": relation,
                "logic_type": "positive",
                "strength": max(0.2, min(1.0, strength)),
                "evidence": None,
            }
        )

    root_id = "payload_root"
    root_label = _pick_payload_title(payload)
    add_node(root_id, root_label, 0, 0.98)

    def walk(value: Any, parent_id: str, key_hint: str, depth: int) -> None:
        if len(nodes) >= limit or depth > GRAPH_MAX_DEPTH:
            return

        if isinstance(value, dict):
            oid = id(value)
            if oid in seen_containers:
                return
            seen_containers.add(oid)
            for index, (k, v) in enumerate(value.items(), start=1):
                if index > PAYLOAD_DICT_SCAN_LIMIT or len(nodes) >= limit:
                    break
                if str(k) in {"text_blocks", "raw_text_preview"}:
                    continue
                child_id = f"{parent_id}_{_slug(k)}_{depth}"
                if add_node(child_id, str(k), depth, 0.82 - depth * 0.08, parent_id):
                    add_edge(parent_id, child_id, "", 0.7 - depth * 0.06)
                walk(v, child_id, str(k), depth + 1)
            return

        if isinstance(value, list):
            oid = id(value)
            if oid in seen_containers:
                return
            seen_containers.add(oid)
            for idx, item in enumerate(value, start=1):
                if idx > PAYLOAD_LIST_SCAN_LIMIT or len(nodes) >= limit:
                    break
                title = f"{key_hint}#{idx}" if key_hint else f"item_{idx}"
                child_id = f"{parent_id}_item_{idx}_{depth}"
                if add_node(child_id, title, depth, 0.78 - depth * 0.08, parent_id):
                    add_edge(parent_id, child_id, "", 0.66 - depth * 0.06)
                walk(item, child_id, key_hint, depth + 1)
            return

        text = str(value).strip()
        if not text:
            return
        leaf_id = f"{parent_id}_{_slug(text[:36])}_{depth}"
        if add_node(leaf_id, text[:120], depth, 0.72 - depth * 0.08, parent_id):
            add_edge(parent_id, leaf_id, "", 0.6 - depth * 0.05)

    walk(payload, root_id, "payload", 1)
    _append_source_text_structure(
        nodes,
        links,
        source_text=source_text,
        attach_to=root_id,
        max_nodes=limit,
    )
    return nodes, links


def build_graph_from_dynamic_payload(payload: dict, source_text: str = "") -> tuple[list[dict], list[dict]]:
    """
    Public helper for callers that need structural graph generation
    from freeform dynamic payload.
    """
    return _build_graph_from_payload(payload, source_text=source_text)


def _freeform_prompt() -> str:
    # 核心原则（禁止动摇）：禁止预设任何内容结构字段，必须允许 LLM 自由生成字段与层级。
    return (
        "你是自由结构化引擎。"
        "输入可能是任意类型文本。"
        "请只返回一个JSON对象（禁止markdown）。"
        "字段名、层级、分块方式完全由你根据内容自由决定。"
        "不要套固定模板，不要强制出现任何预设业务字段。"
        "请保持精炼：禁止大段复制原文。"
        "总字段数建议不超过 40；数组项建议不超过 12；单个字符串建议不超过 160 字。"
        "必须保证输出是闭合的合法 JSON 对象。"
        "如果你提供图谱，请放在 nodes/links；若没有也可仅输出 dynamic_payload。"
    )


def generate_dynamic_payload_freeform(original_text: str) -> dict:
    """
    核心原则（禁止动摇）：
    必须保持 LLM 对 dynamic_payload 的自由生成能力；
    严禁在此函数中预设任何与内容语义相关的固定字段或模板结构。
    """
    text = _normalize_text(original_text)
    if not text:
        return {}
    kimi = RequestLLM()
    kimi.system_prompt = _freeform_prompt()
    for _ in range(1):
        try:
            response = _call_freeform_llm(kimi, text, temperature=0.2)
            if not response or str(response).strip().startswith("Error:"):
                continue
            raw = _parse_response_to_object(response)
            raw = _unwrap_stringified_payload(raw)
            if raw is None:
                raw = _as_displayable_fallback_payload(str(response), text)
            payload = _normalize_payload_object(raw)
            if isinstance(payload, dict) and payload:
                return payload
        except Exception:
            continue
    return {"text": text[:MAX_PARSE_CHARS]}


def parse_document(original_text: str, user_id: int, progress_cb=None) -> tuple[dict, str]:
    """
    核心原则（禁止动摇）：
    - 不做任何固定业务字段筛选/抽取。
    - 所有内容结构由 LLM 自由生成。
    """
    text = _normalize_text(original_text)
    kimi = RequestLLM()
    kimi.system_prompt = _freeform_prompt()
    started = time.perf_counter()
    if callable(progress_cb):
        try:
            progress_cb(25, "LLM 自由解析中")
        except Exception:
            pass

    try:
        response = _call_freeform_llm(kimi, text, temperature=0.2)
        if not response or str(response).strip().startswith("Error:"):
            raise ValueError(str(response))

        raw = _parse_response_to_object(response)
        if raw is None:
            if callable(progress_cb):
                try:
                    progress_cb(45, "JSON 修复中")
                except Exception:
                    pass
        raw = _unwrap_stringified_payload(raw)
        if raw is None:
            raw = _as_displayable_fallback_payload(str(response), text)
        normalized = _normalize_payload_object(raw)
        if not isinstance(normalized, dict):
            raise ValueError("LLM payload cannot be normalized")

        raw_dict = normalized if isinstance(raw, dict) else {}
        content = _normalize_text(str(raw_dict.get("content") or text))
        nodes = _safe_nodes(raw_dict.get("nodes"))
        node_ids = {item["id"] for item in nodes}
        links = _safe_links(raw_dict.get("links"), node_ids)
        top_level_keys = {"content", "nodes", "links", "dynamic_payload", "visual_config"}
        dynamic_payload = (
            raw_dict.get("dynamic_payload")
            if isinstance(raw_dict.get("dynamic_payload"), dict)
            else {k: v for k, v in raw_dict.items() if k not in top_level_keys}
        )
        if not dynamic_payload and not raw_dict:
            dynamic_payload = normalized
        if not isinstance(dynamic_payload, dict):
            dynamic_payload = {}

        if callable(progress_cb):
            try:
                progress_cb(65, "图谱构建中")
            except Exception:
                pass

        if not nodes and dynamic_payload:
            nodes, links = _build_graph_from_payload(dynamic_payload, source_text=content or text)
        elif nodes:
            nodes, links = _supplement_existing_graph_with_source_text(
                nodes,
                links,
                source_text=content or text,
            )
        visual_config = build_visual_config_for_graph(
            raw_dict.get("visual_config"),
            nodes,
            links=links,
            source_text=text,
        )
        if callable(progress_cb):
            try:
                progress_cb(80, "结果整理中")
            except Exception:
                pass
        elapsed = time.perf_counter() - started
        logger.info(
            "Freeform parse completed in %.2fs (nodes=%d, links=%d, mode=ai)",
            elapsed,
            len(nodes),
            len(links),
        )

        return {
            "original_text": original_text,
            "user_id": user_id,
            "content": content,
            "nodes": nodes,
            "links": links,
            "dynamic_payload": dynamic_payload,
            "visual_config": visual_config,
        }, "ai"
    except Exception as e:
        elapsed = time.perf_counter() - started
        logger.error("Freeform parse failed in %.2fs: %s", elapsed, e)
        if callable(progress_cb):
            try:
                progress_cb(82, "主解析失败，自由重试中")
            except Exception:
                pass
        dynamic_payload = generate_dynamic_payload_freeform(text) if text else {}
        if not isinstance(dynamic_payload, dict) or not dynamic_payload:
            dynamic_payload = _as_displayable_fallback_payload("", text) if text else {}
        nodes, links = _build_graph_from_payload(dynamic_payload, source_text=text) if dynamic_payload else ([], [])
        low_quality_keys = {"parse_warning", "raw_excerpt", "text"}
        recovered = bool(dynamic_payload) and not set(dynamic_payload.keys()).issubset(low_quality_keys)
        parse_mode = "fallback_recovered" if recovered else "fallback_fast"
        return {
            "original_text": original_text,
            "user_id": user_id,
            "content": text,
            "nodes": nodes,
            "links": links,
            "dynamic_payload": dynamic_payload,
            "visual_config": build_visual_config_for_graph(
                {"focus_node": (nodes[0]["id"] if nodes else None), "initial_zoom": 1.0, "text_mapping": {}},
                nodes,
                links=links,
                source_text=text,
            ),
        }, parse_mode


def rewrite_document(original_text: str, target_audience: str, user_id: int) -> ChatMessageBase:
    """保留兼容接口：按目标受众改写传统字段。"""
    kimi = RequestLLM()

    system_prompt = f"""
你是专业改写助手。请面向目标受众：{target_audience}，把输入文本改写为更易读版本。
只返回 JSON，禁止 Markdown，字段如下：
- target_audience
- handling_matter
- time_deadline
- location_entrance
- required_materials
- handling_process
- precautions
- risk_warnings
所有字段必须是字符串或 null；如果有多个要点，请用“；”拼接为单个字符串。
    """

    kimi.system_prompt = system_prompt

    response_text = kimi.get_response(
        content=original_text,
        model="moonshot-v1-32k",
        response_format={"type": "json_object"},
        temperature=0.4,
    )

    try:
        if response_text.strip().startswith("Error:"):
            logger.error(f"Kimi rewrite error: {response_text}")
            return ChatMessageBase(original_text=original_text, handling_matter=original_text[:60], user_id=user_id)

        parsed_data = _clean_json_response(response_text)
        for key in [
            "required_materials",
            "handling_process",
            "precautions",
            "risk_warnings",
            "target_audience",
            "handling_matter",
            "time_deadline",
            "location_entrance",
        ]:
            if key in parsed_data and isinstance(parsed_data[key], list):
                parsed_data[key] = "；".join([str(item) for item in parsed_data[key]])

        return ChatMessageBase(
            original_text=original_text,
            target_audience=parsed_data.get("target_audience", target_audience),
            handling_matter=parsed_data.get("handling_matter"),
            time_deadline=parsed_data.get("time_deadline"),
            location_entrance=parsed_data.get("location_entrance"),
            required_materials=parsed_data.get("required_materials"),
            handling_process=parsed_data.get("handling_process"),
            precautions=parsed_data.get("precautions"),
            risk_warnings=parsed_data.get("risk_warnings"),
            user_id=user_id,
        )
    except Exception as e:
        logger.error(f"Failed to rewrite document: {e}")
        return ChatMessageBase(original_text=original_text, handling_matter=original_text[:60], user_id=user_id)


async def extract_pdf_with_ai(file_path: Path) -> str:
    from app.services.pdf_extractor import extract_pdf_with_ai as extract_pdf_with_service

    return await extract_pdf_with_service(file_path)


async def _legacy_extract_pdf_with_ai(file_path: Path) -> str:
    """
    使用 Kimi 或 OCR 解析 PDF（含扫描件）。
    """
    import pdfplumber

    full_text = []
    has_text = False

    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text and text.strip():
                    full_text.append(text)
                    has_text = True

        if has_text:
            logger.info(f"Successfully extracted text from PDF {file_path} using pdfplumber.")
            return "\n".join(full_text)

        logger.info(f"pdfplumber found no text in {file_path}. Attempting OCR via Kimi.")

        extracted_text_from_ocr = await perform_kimi_ocr(
            file_path=file_path,
            content_type="application/pdf",
            original_filename=file_path.name,
        )

        if extracted_text_from_ocr and extracted_text_from_ocr.strip():
            logger.info(f"Successfully extracted text from {file_path} using Kimi OCR.")
            return extracted_text_from_ocr

        logger.warning(f"Kimi OCR also failed to extract text from {file_path}.")
        return "提示：系统未能从该文件中提取到有效文字，可能是扫描件或纯图片，且 OCR 识别也未成功。请尝试上传更清晰的文件。"

    except Exception as e:
        logger.error(f"PDF parsing or OCR failed for {file_path}: {e}", exc_info=True)
        return f"PDF 解析失败: {str(e)}"
