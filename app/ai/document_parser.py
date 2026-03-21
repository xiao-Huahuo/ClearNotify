import json
import logging # Import logging
import re
from app.ai.request_llm import RequestLLM
from app.models.chat_message import ChatMessageBase
from pathlib import Path
from app.services.ocr_service import perform_kimi_ocr # Import the new OCR service

logger = logging.getLogger(__name__) # Initialize logger

MAX_PARSE_CHARS = 6000

_KEYWORD_PATTERNS = re.compile(
    r"(通知|公告|办理|报名|申请|材料|提交|附件|时间|日期|截止|地点|地址|入口|方式|流程|步骤|注意|风险|对象|适用|资格|要求|条件)"
)
_DATE_PATTERNS = re.compile(
    r"(\d{4}年\d{1,2}月\d{1,2}日|\d{1,2}月\d{1,2}日|\d{4}-\d{1,2}-\d{1,2}|\d{1,2}:\d{2})"
)


def _normalize_text(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"[ \t]+", " ", text.replace("\r\n", "\n").replace("\r", "\n")).strip()


def _split_lines(text: str) -> list[str]:
    lines = [line.strip() for line in re.split(r"[\n]+", text) if line.strip()]
    if len(lines) <= 1:
        lines = [line.strip() for line in re.split(r"[。；;]+", text) if line.strip()]
    return lines


def _build_condensed_text(text: str) -> tuple[str, bool]:
    normalized = _normalize_text(text)
    if len(normalized) <= MAX_PARSE_CHARS:
        return normalized, False

    lines = _split_lines(normalized)
    key_lines = []
    seen = set()
    for line in lines:
        if _KEYWORD_PATTERNS.search(line) or _DATE_PATTERNS.search(line):
            if line not in seen:
                key_lines.append(line)
                seen.add(line)
        if len(key_lines) >= 30:
            break

    head = normalized[:2000]
    tail = normalized[-1500:]
    key_block = "\n".join(key_lines) if key_lines else "（未匹配到明显关键词，保留原文首尾内容）"
    condensed = f"{head}\n\n【关键信息摘录】\n{key_block}\n\n【原文末段】\n{tail}"
    if len(condensed) > MAX_PARSE_CHARS:
        condensed = condensed[:MAX_PARSE_CHARS]
    return condensed, True


def _extract_title(text: str) -> str:
    lines = _split_lines(text)
    if lines:
        title = lines[0]
        return title if len(title) <= 60 else f"{title[:60]}..."
    return text[:60] + ("..." if len(text) > 60 else "")


def _fallback_parse(original_text: str, user_id: int) -> ChatMessageBase:
    normalized = _normalize_text(original_text)
    title = _extract_title(normalized)

    time_match = _DATE_PATTERNS.search(normalized)
    time_deadline = time_match.group(0) if time_match else None

    location_line = None
    for line in _split_lines(normalized):
        if any(key in line for key in ["地点", "地址", "入口", "办理地点"]):
            location_line = line
            break

    materials_lines = []
    for line in _split_lines(normalized):
        if any(key in line for key in ["材料", "提交", "附件", "携带"]):
            materials_lines.append(line)
        if len(materials_lines) >= 3:
            break
    required_materials = "；".join(materials_lines) if materials_lines else None

    target_line = None
    for line in _split_lines(normalized):
        if any(key in line for key in ["对象", "适用", "资格", "范围"]):
            target_line = line
            break

    return ChatMessageBase(
        original_text=original_text,
        target_audience=target_line,
        handling_matter=title or "未识别到明确事项（已保留原文）",
        time_deadline=time_deadline,
        location_entrance=location_line,
        required_materials=required_materials,
        user_id=user_id,
    )

def _clean_json_response(response_text: str) -> dict:
    """清理并解析 JSON 响应"""
    response_text = response_text.strip()
    if response_text.startswith("```json"):
        response_text = response_text[7:]
    if response_text.startswith("```"):
        response_text = response_text[3:]
    if response_text.endswith("```"):
        response_text = response_text[:-3]
    response_text = response_text.strip()
    return json.loads(response_text)

def _convert_list_to_str(data: dict, key: str) -> None:
    """如果字典中的某个键的值是列表，将其转换为逗号分隔的字符串"""
    if key in data and isinstance(data[key], list):
        data[key] = "，".join([str(item) for item in data[key]])

def parse_document(original_text: str, user_id: int) -> tuple[ChatMessageBase, str]:
    """
    通用文档解析，传入文本或提取出的文件文本，调用大模型进行归纳和解析
    """
    kimi = RequestLLM()
    
    # 构造系统提示词，要求返回 JSON 格式
    system_prompt = """
    你是一个专业的文档解析助手。你的任务是从用户提供的官方通知或长文本中，精确提取出关键的业务信息。
    请务必返回一个标准的 JSON 对象，且仅包含以下键名（如果文中未提及，请填入null）。
    注意：所有键对应的值都必须是字符串（String）或 null，绝对不能是数组（Array）或列表（List）！如果是多个项目，请用逗号连接成一个长字符串。
    - target_audience (适用对象)
    - handling_matter (办理事项)
    - time_deadline (时间/截止时间)
    - location_entrance (地点/入口)
    - required_materials (所需材料)
    - handling_process (办理流程)
    - precautions (注意事项)
    - risk_warnings (风险提醒)
    """
    
    system_prompt += f"\n\n原文长度提示：{len(original_text)}字。"
    system_prompt += "\n要求：当原文较长时，\"办理时间、所需材料、办理流程、注意事项\"四项必须给出更完整、更细致的内容，避免过短。"
    system_prompt += "\n可做概括性扩展，但不要编造具体日期、地点或特定材料名称。"
    system_prompt += f"\n\n原文长度提示：{len(original_text)}字。"
    system_prompt += "\n要求：当原文较长时，\"办理时间、所需材料、办理流程、注意事项\"四项必须给出更完整、更细致的内容，避免过短。"
    system_prompt += "\n可做概括性扩展，但不要编造具体日期、地点或特定材料名称。"
    kimi.system_prompt = system_prompt
    
    # 调用 Kimi 接口，开启 json_object 格式返回
    response_text = kimi.get_response(
        content=original_text,
        model="moonshot-v1-32k",
        response_format={"type": "json_object"},
        temperature=0.3
    )
    
    # 尝试解析返回的 JSON
    try:
        if response_text.strip().startswith("Error:"):
            logger.error(f"Kimi parsing error: {response_text}")
            return _fallback_parse(original_text, user_id), "fallback"

        parsed_data = _clean_json_response(response_text)
        
        # 强制类型转换，防止大模型抽风返回了列表
        _convert_list_to_str(parsed_data, "required_materials")
        _convert_list_to_str(parsed_data, "handling_process")
        _convert_list_to_str(parsed_data, "precautions")
        _convert_list_to_str(parsed_data, "risk_warnings")
        _convert_list_to_str(parsed_data, "target_audience")
        _convert_list_to_str(parsed_data, "handling_matter")
        _convert_list_to_str(parsed_data, "time_deadline")
        _convert_list_to_str(parsed_data, "location_entrance")

        if not (parsed_data.get("handling_matter") or "").strip():
            parsed_data["handling_matter"] = _extract_title(original_text)

        if not any(
            (parsed_data.get(key) or "").strip()
            for key in [
                "target_audience",
                "handling_matter",
                "time_deadline",
                "location_entrance",
                "required_materials",
                "handling_process",
                "precautions",
                "risk_warnings",
            ]
        ):
            logger.warning("Parsed data empty, fallback to heuristic parsing.")
            return _fallback_parse(original_text, user_id), "fallback"

        if not (parsed_data.get("handling_matter") or "").strip():
            parsed_data["handling_matter"] = _extract_title(original_text)

        # 构建返回的模型
        return ChatMessageBase(
            original_text=original_text,
            target_audience=parsed_data.get("target_audience"),
            handling_matter=parsed_data.get("handling_matter"),
            time_deadline=parsed_data.get("time_deadline"),
            location_entrance=parsed_data.get("location_entrance"),
            required_materials=parsed_data.get("required_materials"),
            handling_process=parsed_data.get("handling_process"),
            precautions=parsed_data.get("precautions"),
            risk_warnings=parsed_data.get("risk_warnings"),
            user_id=user_id
        ), "ai"
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from Kimi response: {e}")
        logger.error(f"Raw response: {response_text}")
        return _fallback_parse(original_text, user_id), "fallback"
        # 如果解析失败，进行基础的回退处理
        return ChatMessageBase(
            original_text=original_text,
            handling_matter="解析失败，请检查输入或稍后重试",
            user_id=user_id
        )

def rewrite_document(original_text: str, target_audience: str, user_id: int) -> ChatMessageBase:
    """
    根据目标群体，重新改写文档并提取对应信息
    """
    kimi = RequestLLM()
    
    system_prompt = f"""
    你是一个专业的公文翻译和改写专家。现在有一篇官方通知，你需要根据目标受众【{target_audience}】，重新审视并改写这份通知，以便于他们理解。
    
    改写原则：
    1. 如果目标受众是“老人版”，请使用大白话，极其精简，强调防骗和核心步骤。
    2. 如果目标受众是“学生版”，请条理清晰，突出他们需要交的材料和截止日期。
    3. 其他受众同理，确保用词符合他们的阅读习惯。
    
    你必须先在脑海中完成全文改写，然后将你改写后的内容，重新按照下面的 JSON 结构输出。
    注意：所有键对应的值都必须是字符串（String）或 null，绝对不能是数组（Array）或列表（List）！如果是多个项目，请用换行或逗号连接成一个长字符串。
    - target_audience (适用对象：写上这次的目标群体名称)
    - handling_matter (办理事项：用最简单的话概括)
    - time_deadline (时间节点)
    - location_entrance (地点/入口)
    - required_materials (所需材料：精简描述)
    - handling_process (办理流程：步骤化，不要废话)
    - precautions (注意事项：针对该人群的特别提醒)
    - risk_warnings (风险提醒)
    
    必须且只能返回纯 JSON。
    """
    
    kimi.system_prompt = system_prompt
    
    response_text = kimi.get_response(
        content=original_text,
        model="moonshot-v1-32k",
        response_format={"type": "json_object"},
        temperature=0.4
    )
    
    try:
        if response_text.strip().startswith("Error:"):
            logger.error(f"Kimi rewrite error: {response_text}")
            return _fallback_parse(original_text, user_id)

        parsed_data = _clean_json_response(response_text)
        
        # 强制类型转换，防止大模型抽风返回了列表
        _convert_list_to_str(parsed_data, "required_materials")
        _convert_list_to_str(parsed_data, "handling_process")
        _convert_list_to_str(parsed_data, "precautions")
        _convert_list_to_str(parsed_data, "risk_warnings")
        _convert_list_to_str(parsed_data, "target_audience")
        _convert_list_to_str(parsed_data, "handling_matter")
        _convert_list_to_str(parsed_data, "time_deadline")
        _convert_list_to_str(parsed_data, "location_entrance")
        
        return ChatMessageBase(
            original_text=original_text, # 确保原文不丢失
            target_audience=parsed_data.get("target_audience", target_audience),
            handling_matter=parsed_data.get("handling_matter"),
            time_deadline=parsed_data.get("time_deadline"),
            location_entrance=parsed_data.get("location_entrance"),
            required_materials=parsed_data.get("required_materials"),
            handling_process=parsed_data.get("handling_process"),
            precautions=parsed_data.get("precautions"),
            risk_warnings=parsed_data.get("risk_warnings"),
            user_id=user_id
        )
    except Exception as e:
        logger.error(f"Failed to rewrite document: {e}")
        return _fallback_parse(original_text, user_id)


async def extract_pdf_with_ai(file_path: Path) -> str: # Make function async
    """
    使用 Kimi大模型(或其他支持文档上传的模型) 直接解析 PDF，包括扫描版。
    首先尝试本地提取，如果失败，则调用 AI 多模态视觉模型进行深度文字识别（OCR）。
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
                    
        # 1. 正常PDF，成功提取文本
        if has_text:
            logger.info(f"Successfully extracted text from PDF {file_path} using pdfplumber.")
            return "\n".join(full_text)
            
        # 2. 如果全空，极大可能是扫描版 (全是图片)，触发 OCR 或多模态 AI
        logger.info(f"pdfplumber found no text in {file_path}. Attempting OCR via Kimi.")
        
        # Call perform_kimi_ocr for scanned PDFs
        extracted_text_from_ocr = await perform_kimi_ocr(
            file_path=file_path,
            content_type="application/pdf", # For PDFs, content type is fixed
            original_filename=file_path.name
        )
        
        if extracted_text_from_ocr and extracted_text_from_ocr.strip():
            logger.info(f"Successfully extracted text from {file_path} using Kimi OCR.")
            return extracted_text_from_ocr
        else:
            logger.warning(f"Kimi OCR also failed to extract text from {file_path}.")
            return "提示：系统未能从该文件中提取到任何有效文字，这可能是一个扫描件或纯图片，且 AI OCR 识别也未能成功。请尝试上传清晰度更高的文件。"
        
    except Exception as e:
        logger.error(f"PDF parsing or OCR failed for {file_path}: {e}", exc_info=True)
        return f"PDF 解析失败: {str(e)}"
