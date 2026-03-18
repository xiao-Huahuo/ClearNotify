import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app.models.user import User
from app.api.deps import get_current_user
from app.core.config import GlobalConfig
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
