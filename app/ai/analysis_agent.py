import json
from app.ai.request_llm import RequestLLM
from app.models.chat_message import ChatMessageBase

def analyze_complexity_and_type(original_text: str) -> dict:
    """
    业务函数：仅使用大模型分析单篇通知的【复杂度】和【通知类型】。
    这是方案A中，分词算法无法完成的语义理解部分。
    """
    kimi = RequestLLM()
    
    system_prompt = """
    你是一个通知分析专家。请根据提供的通知原文，分析其“复杂度”和“通知类型”。
    必须返回 JSON 格式，且只能包含以下两个键：
    {
        "complexity": "仅能从 [高, 中, 低] 中选择一个。判断依据：如果有多个时间节点、多个办理对象、多项材料要求、特殊限制条件，则为高；只有单项要求则为低。",
        "notice_type": "提炼出一个简短的通知类型（如：医保缴费、社区活动、入学报名、政策补贴、违章罚款等）。最多不超过6个字。"
    }
    """
    
    kimi.system_prompt = system_prompt
    
    try:
        response_text = kimi.get_response(
            content=original_text, 
            response_format={"type": "json_object"},
            temperature=0.1
        )
        
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
            
        parsed_data = json.loads(response_text)
        
        # 兜底校验
        complexity = parsed_data.get("complexity", "中")
        if complexity not in ["高", "中", "低"]:
            complexity = "中"
            
        notice_type = parsed_data.get("notice_type", "其他通知")
        
        return {
            "complexity": complexity,
            "notice_type": notice_type
        }
        
    except Exception as e:
        print(f"Analysis Agent Error: {e}")
        return {"complexity": "中", "notice_type": "其他通知"}
