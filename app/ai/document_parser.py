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


def _build_graph_from_payload(payload: dict, max_nodes: int = 220) -> tuple[list[dict], list[dict]]:
    """
    核心原则（禁止动摇）：
    仅按 JSON 结构生成图谱，不做任何固定业务字段推断。
    """
    if not isinstance(payload, dict) or not payload:
        return [], []

    nodes: list[dict] = []
    links: list[dict] = []
    seen_nodes: set[str] = set()
    seen_edges: set[tuple[str, str, str]] = set()

    def add_node(node_id: str, label: str, layer: int, importance: float) -> bool:
        if node_id in seen_nodes or len(nodes) >= max_nodes:
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
                "parent_id": None,
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
        if len(nodes) >= max_nodes or depth > 6:
            return

        if isinstance(value, dict):
            for k, v in list(value.items())[:40]:
                child_id = f"{parent_id}_{_slug(k)}_{depth}"
                if add_node(child_id, str(k), depth, 0.82 - depth * 0.08):
                    add_edge(parent_id, child_id, "", 0.7 - depth * 0.06)
                walk(v, child_id, str(k), depth + 1)
            return

        if isinstance(value, list):
            for idx, item in enumerate(value[:24], start=1):
                title = f"{key_hint}#{idx}" if key_hint else f"item_{idx}"
                child_id = f"{parent_id}_item_{idx}_{depth}"
                if add_node(child_id, title, depth, 0.78 - depth * 0.08):
                    add_edge(parent_id, child_id, "", 0.66 - depth * 0.06)
                walk(item, child_id, key_hint, depth + 1)
            return

        text = str(value).strip()
        if not text:
            return
        leaf_id = f"{parent_id}_{_slug(text[:36])}_{depth}"
        if add_node(leaf_id, text[:120], depth, 0.72 - depth * 0.08):
            add_edge(parent_id, leaf_id, "", 0.6 - depth * 0.05)

    walk(payload, root_id, "payload", 1)
    for item in nodes:
        if item["id"] != root_id:
            item["parent_id"] = item["id"].rsplit("_", 2)[0] if "_" in item["id"] else root_id
    return nodes, links


def build_graph_from_dynamic_payload(payload: dict) -> tuple[list[dict], list[dict]]:
    """
    Public helper for callers that need structural graph generation
    from freeform dynamic payload.
    """
    return _build_graph_from_payload(payload)


def _freeform_prompt() -> str:
    # 核心原则（禁止动摇）：禁止预设任何内容结构字段，必须允许 LLM 自由生成字段与层级。
    return (
        "你是自由结构化引擎。"
        "输入可能是任意类型文本。"
        "请只返回一个JSON对象（禁止markdown）。"
        "字段名、层级、分块方式完全由你根据内容自由决定。"
        "不要套固定模板，不要强制出现任何预设业务字段。"
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
            response = kimi.get_response(
                content=text[:MAX_PARSE_CHARS],
                model="moonshot-v1-32k",
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            if not response or str(response).strip().startswith("Error:"):
                continue
            raw = _try_parse_json_loose(response)
            if raw is None:
                raw = _repair_json_via_llm(response)
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
        response = kimi.get_response(
            content=text[:MAX_PARSE_CHARS],
            model="moonshot-v1-32k",
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        if not response or str(response).strip().startswith("Error:"):
            raise ValueError(str(response))

        raw = _try_parse_json_loose(response)
        if raw is None:
            if callable(progress_cb):
                try:
                    progress_cb(45, "JSON 修复中")
                except Exception:
                    pass
            raw = _repair_json_via_llm(response)
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
            nodes, links = _build_graph_from_payload(dynamic_payload)
        visual_config = _basic_visual_config(raw_dict.get("visual_config"), nodes)
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
            dynamic_payload = {"text": text[:MAX_PARSE_CHARS]} if text else {}
        nodes, links = _build_graph_from_payload(dynamic_payload) if dynamic_payload else ([], [])
        parse_mode = "fallback_recovered" if dynamic_payload and "text" not in dynamic_payload else "fallback_fast"
        return {
            "original_text": original_text,
            "user_id": user_id,
            "content": text,
            "nodes": nodes,
            "links": links,
            "dynamic_payload": dynamic_payload,
            "visual_config": {"focus_node": (nodes[0]["id"] if nodes else None), "initial_zoom": 1.0, "text_mapping": {}},
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
