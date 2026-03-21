import logging
import os
import base64
from pathlib import Path
import mimetypes

from fastapi import HTTPException

from app.ai.request_llm import RequestLLM

logger = logging.getLogger(__name__)

async def perform_kimi_ocr(file_path: Path, content_type: str, original_filename: str) -> str:
    """
    使用 Kimi 视觉模型执行 OCR 识别。
    :param file_path: 本地文件路径
    :param content_type: 文件的 MIME 类型
    :param original_filename: 原始文件名
    :return: 提取的文本
    """
    extracted_text = ""
    file_id = None
    kimi = RequestLLM() # Initialize Kimi client

    try:
        # 1. 尝试使用 Kimi 文件上传接口进行 OCR
        logger.info(f"Attempting to upload file {original_filename} ({file_path}) to Kimi for OCR (purpose=file-extract).")
        with open(file_path, "rb") as f:
            upload_resp = kimi.client.files.create(file=(original_filename, f, content_type), purpose="file-extract")
        file_id = upload_resp.id
        logger.info(f"File uploaded to Kimi successfully. File ID: {file_id}")

        logger.info(f"Attempting to get content for Kimi File ID: {file_id}")
        file_content_resp = kimi.client.files.content(file_id)
        extracted_text = file_content_resp.text
        logger.info(f"Content extracted from Kimi File ID {file_id}. Text length: {len(extracted_text)}")

        # 2. 如果文件提取返回空，降级到 Kimi 视觉模型
        if not extracted_text or not extracted_text.strip():
            logger.warning(f"Kimi file-extract returned empty text for file ID {file_id}. Attempting visual OCR fallback.")
            with open(file_path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode()
            
            # Reset system prompt for visual OCR
            kimi.system_prompt = "你是一个OCR识别助手，请将图片中的所有文字原样提取出来，保持原有格式和段落结构。"
            completion = kimi.client.chat.completions.create(
                model="moonshot-v1-8k", # Assuming moonshot-v1-8k supports vision
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:{content_type};base64,{img_b64}"}},
                        {"type": "text", "text": "请提取图片中的所有文字内容。"}
                    ]
                }],
                temperature=0.1
            )
            extracted_text = completion.choices[0].message.content
            logger.info(f"Visual OCR fallback completed. Extracted text length: {len(extracted_text)}")

    except Exception as e:
        logger.error(f"OCR processing failed for file {original_filename} ({file_path}): {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"OCR 识别失败: {str(e)}")
    finally:
        # 确保 Kimi 上传的文件被清理
        if file_id:
            try:
                kimi.client.files.delete(file_id)
                logger.info(f"Kimi File ID {file_id} deleted successfully.")
            except Exception as e:
                logger.error(f"Failed to delete Kimi File ID {file_id}: {e}")
        
        # 清理本地临时文件 (如果需要，这里假设调用者会处理本地文件清理)
        # if file_path.exists():
        #     os.remove(file_path)
        #     logger.info(f"Local temporary file {file_path} deleted.")

    return extracted_text
