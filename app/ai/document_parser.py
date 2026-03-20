import json
from app.ai.request_llm import RequestLLM
from app.models.chat_message import ChatMessageBase
from pathlib import Path

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

def parse_document(original_text: str, user_id: int) -> ChatMessageBase:
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
    
    kimi.system_prompt = system_prompt
    
    # 调用 Kimi 接口，开启 json_object 格式返回
    response_text = kimi.get_response(
        content=original_text, 
        response_format={"type": "json_object"},
        temperature=0.3
    )
    
    # 尝试解析返回的 JSON
    try:
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
        )
        
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON: {e}")
        print(f"Raw response: {response_text}")
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
        response_format={"type": "json_object"},
        temperature=0.4
    )
    
    try:
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
        print(f"Failed to rewrite: {e}")
        return ChatMessageBase(original_text=original_text, user_id=user_id)


def extract_pdf_with_ai(file_path: Path) -> str:
    """
    使用 Kimi大模型(或其他支持文档上传的模型) 直接解析 PDF，包括扫描版。
    注意：这里需要依赖官方 SDK 的文件上传接口 (kimi/moonshot 提供了 file-upload 和基于 file_id 的对话能力)
    由于本项目中你的 request_kimi 封装暂时只支持纯文本对话，
    这里提供一种降级的通用方案：先尝试本地提取，如果没有，则提示用户。
    或者如果你想调用真实的大模型文件接口，可以在这里重写逻辑。
    """
    import pdfplumber
    
    # 尝试使用本地 pdfplumber 提取
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
            return "\n".join(full_text)
            
        # 2. 如果全空，极大可能是扫描版 (全是图片)，触发 OCR 或多模态 AI
        return "提示：系统检测到这是一个扫描版 PDF 或纯图片构成的文件，当前的文本提取引擎未能识别出有效文字。在未来的版本中，此部分将自动切换至 AI 多模态视觉模型进行深度文字识别（OCR）。"
        
    except Exception as e:
        return f"PDF 解析失败: {str(e)}"
