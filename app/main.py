from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# 使用动态绝对路径加载环境变量
from app.core.config import GlobalConfig
load_dotenv(dotenv_path=GlobalConfig.ENV_PATH)

from app.api.routes import user, login, chat_message, stats_analysis, settings, upload
from app.services.init_db import init_db_and_admin

# 确保上传目录存在 (基于绝对路径)
GlobalConfig.AVATAR_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 定义生命周期管理器
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 应用启动前执行：初始化数据库和管理员
    init_db_and_admin()
    
    yield
    # 应用关闭后执行：这里暂时没有清理工作

# 将 lifespan 传入 FastAPI
app = FastAPI(lifespan=lifespan)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录，使得前端可以通过 /media/... 访问上传的文件 (使用绝对路径)
app.mount("/media", StaticFiles(directory=str(GlobalConfig.UPLOAD_DIR)), name="media")

# 注入路由
app.include_router(user.router, prefix="/user", tags=["user"])
app.include_router(login.router, prefix="/login", tags=["login"])
app.include_router(chat_message.router, prefix="/chat", tags=["chat_message"])
app.include_router(stats_analysis.router, prefix="/analysis", tags=["analysis"])
app.include_router(settings.router, prefix="/settings", tags=["settings"])
app.include_router(upload.router, prefix="/upload", tags=["upload"])

@app.get("/")
async def root():
    return {"message": "Hello World"}

if __name__ == "__main__":
    import uvicorn
    # 传app,且reload=True(热重载),改代码后可以直接改后端,无需重启
    uvicorn.run("app.main:app", host="127.0.0.1", port=8080, reload=True)
