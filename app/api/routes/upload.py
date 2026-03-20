import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app.models.user import User
from app.api.deps import get_current_user
from app.core.config import GlobalConfig
from app.services.document_extractor import extract_text_from_docx, extract_text_from_excel
from app.ai.document_parser import extract_pdf_with_ai
import uuid
import mimetypes

router = APIRouter()

# 允许的图片格式
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    用户头像上传接口。
    接收图片文件，保存到本地，并返回可供访问的静态资源 URL。
    """
    # 1. 校验文件类型
    content_type = file.content_type
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="不支持的文件类型。仅允许 JPEG, PNG, WEBP, GIF。")
        
    # 2. 读取文件并校验大小 (Spooling: 小文件在内存，大文件会自动写入临时文件)
    file.file.seek(0, 2)  # 移动指针到末尾
    file_size = file.file.tell()  # 获取大小
    file.file.seek(0)  # 将指针重置回开头
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件过大。最大允许上传 5MB 的图片。")

    # 3. 生成安全唯一的文件名
    # 获取扩展名 (如 .jpg)
    ext = mimetypes.guess_extension(content_type) or ".jpg"
    # 使用 uuid 加上用户 ID 作为文件名，防止覆盖冲突
    new_filename = f"user_{current_user.uid}_{uuid.uuid4().hex[:8]}{ext}"
    
    file_path = GlobalConfig.AVATAR_UPLOAD_DIR / new_filename
    
    # 4. 保存文件到本地磁盘
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存文件失败: {str(e)}")
    finally:
        file.file.close()

    # 5. 返回前端可访问的 URL
    # 这个 URL 是相对于网站根目录的，我们需要在 main.py 中将其挂载为静态目录
    file_url = f"/media/avatars/{new_filename}"
    
    return {"avatar_url": file_url}


# 允许的文档格式
ALLOWED_DOC_TYPES = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/vnd.ms-excel": ".xls",
    "text/plain": ".txt"
}
MAX_DOC_SIZE = 10 * 1024 * 1024  # 10MB

@router.post("/document")
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    通用文档上传与解析接口。
    接收 PDF、Word、Excel、TXT 等文件，保存到本地并提取文本返回。
    """
    # 1. 校验文件类型
    content_type = file.content_type
    
    # 根据文件名做二次兜底校验（有些浏览器的 content-type 可能会丢失）
    filename = file.filename.lower()
    ext = ""
    for mime_type, extension in ALLOWED_DOC_TYPES.items():
        if content_type == mime_type or filename.endswith(extension):
            ext = extension
            break
            
    if not ext:
        raise HTTPException(status_code=400, detail="不支持的文档类型。仅支持 PDF, DOCX, DOC, XLSX, XLS, TXT。")

    # 2. 校验文件大小
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > MAX_DOC_SIZE:
        raise HTTPException(status_code=400, detail="文档过大。最大允许上传 10MB 的文档。")

    # 3. 生成安全唯一的文件名并保存到磁盘
    new_filename = f"doc_{current_user.uid}_{uuid.uuid4().hex[:8]}{ext}"
    file_path = GlobalConfig.DOCS_UPLOAD_DIR / new_filename
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存文件失败: {str(e)}")
    finally:
        file.file.close()

    file_url = f"/media/docs/{new_filename}"

    # 4. 根据文件类型提取纯文本
    extracted_text = ""
    
    try:
        if ext == ".pdf":
            # PDF 包含 AI 处理逻辑，放在 ai 目录下
            extracted_text = extract_pdf_with_ai(file_path)
        elif ext in [".docx", ".doc"]:
            # Word 使用常规 python 库解析
            extracted_text = extract_text_from_docx(file_path)
        elif ext in [".xlsx", ".xls"]:
            # Excel 使用常规 python 库解析
            extracted_text = extract_text_from_excel(file_path)
        elif ext == ".txt":
            # TXT 直接读取
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                extracted_text = f.read()
    except Exception as e:
        # 即使提取失败，文件也已经保存了
        raise HTTPException(status_code=500, detail=f"文件保存成功，但解析文本失败: {str(e)}")

    if not extracted_text or not extracted_text.strip():
        extracted_text = "提示：系统未能从该文件中提取到任何有效文字，这可能是一个扫描件或纯图片。当前版本暂不支持图片 OCR 识别。"

    # 5. 返回提取的文本和文件的静态 URL
    return {
        "file_url": file_url,
        "extracted_text": extracted_text,
        "filename": file.filename
    }


# 允许的 OCR 输入格式（图片 + 扫描 PDF）
ALLOWED_OCR_TYPES = {
    "image/jpeg", "image/png", "image/webp", "image/gif",
    "application/pdf"
}
MAX_OCR_SIZE = 20 * 1024 * 1024  # 20MB

@router.post("/ocr")
async def ocr_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    截图/扫描型PDF的OCR识别接口。
    上传图片或扫描PDF，调用 Kimi 视觉模型提取文字内容。
    """
    content_type = file.content_type
    filename = file.filename.lower()

    # 兜底：根据扩展名判断
    if content_type not in ALLOWED_OCR_TYPES:
        if filename.endswith((".jpg", ".jpeg")):
            content_type = "image/jpeg"
        elif filename.endswith(".png"):
            content_type = "image/png"
        elif filename.endswith(".pdf"):
            content_type = "application/pdf"
        else:
            raise HTTPException(status_code=400, detail="不支持的文件类型，仅支持图片（JPG/PNG/WEBP）和 PDF。")

    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    if file_size > MAX_OCR_SIZE:
        raise HTTPException(status_code=400, detail="文件过大，OCR 最大支持 20MB。")

    # 保存到临时目录
    ext = ".pdf" if content_type == "application/pdf" else (mimetypes.guess_extension(content_type) or ".jpg")
    new_filename = f"ocr_{current_user.uid}_{uuid.uuid4().hex[:8]}{ext}"
    file_path = GlobalConfig.DOCS_UPLOAD_DIR / new_filename

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存文件失败: {str(e)}")
    finally:
        file.file.close()

    # 调用 Kimi 文件上传 OCR
    try:
        from app.ai.request_llm import RequestLLM
        kimi = RequestLLM()

        # 使用 Kimi 文件上传接口
        with open(file_path, "rb") as f:
            upload_resp = kimi.client.files.create(file=(new_filename, f, content_type), purpose="file-extract")

        file_id = upload_resp.id

        # 获取文件内容
        file_content_resp = kimi.client.files.content(file_id)
        extracted_text = file_content_resp.text

        # 清理上传的文件（可选）
        try:
            kimi.client.files.delete(file_id)
        except Exception:
            pass

        if not extracted_text or not extracted_text.strip():
            # 降级：用视觉模型直接识别图片
            import base64
            with open(file_path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode()
            kimi.system_prompt = "你是一个OCR识别助手，请将图片中的所有文字原样提取出来，保持原有格式和段落结构。"
            completion = kimi.client.chat.completions.create(
                model="moonshot-v1-8k",
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

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR 识别失败: {str(e)}")

    return {
        "file_url": f"/media/docs/{new_filename}",
        "extracted_text": extracted_text,
        "filename": file.filename
    }
