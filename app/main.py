from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import threading
import logging

from app.core.config import GlobalConfig
from app.api.routes import user, login, chat_message, stats_analysis, settings, upload, news, todo, favorite, admin, agent
from app.services.init_db import init_db_and_admin
from app.services.worker import start_worker, stop_worker # 导入 worker 的启动和停止函数
from app.core.cors import CorsMiddleWare
from app.core.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    # 确保同时有控制台和文件输出
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(GlobalConfig.APP_LOG_PATH, encoding="utf-8")
    ]
)
# 确保上传目录存在 (基于绝对路径)
GlobalConfig.AVATAR_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
GlobalConfig.DOCS_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
GlobalConfig.IMAGES_UPLOAD_DIR.mkdir(parents=True, exist_ok=True) # 确保图片上传目录也存在
GlobalConfig.CHAT_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
GlobalConfig.LOG_DIR.mkdir(parents=True, exist_ok=True)
GlobalConfig.MAIL_OUTBOX_DIR.mkdir(parents=True, exist_ok=True)

# 用于存储 worker 线程
worker_thread: threading.Thread = None

# 定义生命周期管理器
@asynccontextmanager
async def lifespan(app: FastAPI):
    global worker_thread
    # 应用启动前执行：初始化数据库和管理员
    init_db_and_admin()
    
    # 启动 Redis Worker 线程
    logger.info("Starting Redis worker thread...")
    worker_thread = threading.Thread(target=start_worker, daemon=True) # daemon=True 确保主程序退出时线程也会退出
    worker_thread.start()
    logger.info("Redis worker thread started.")
    
    yield
    
    # 应用关闭后执行：停止 Redis Worker 线程
    logger.info("Stopping Redis worker thread...")
    stop_worker()
    if worker_thread.is_alive():
        worker_thread.join(timeout=5) # 等待 worker 线程结束，最多等待5秒
        if worker_thread.is_alive():
            logger.warning("Worker thread did not terminate gracefully.")
    logger.info("Redis worker thread stopped.")

# 将 lifespan 传入 FastAPI
app = FastAPI(lifespan=lifespan)

# 配置 CORS
app=CorsMiddleWare(app).add_cors_middleware(
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.middleware("http")
async def log_request_middleware(request: Request, call_next):
    logger.info("HTTP %s %s", request.method, request.url.path)
    response = await call_next(request)
    logger.info("HTTP %s %s -> %s", request.method, request.url.path, response.status_code)
    return response
# 挂载静态文件目录，使得前端可以通过 /media/... 访问上传的文件 (使用绝对路径)
app.mount("/media", StaticFiles(directory=str(GlobalConfig.UPLOAD_DIR)), name="media")

# 注入路由
app.include_router(user.router, prefix="/user", tags=["user"])
app.include_router(login.router, prefix="/login", tags=["login"])
app.include_router(chat_message.router, prefix="/chat", tags=["chat_message"])
app.include_router(stats_analysis.router, prefix="/analysis", tags=["analysis"])
app.include_router(settings.router, prefix="/settings", tags=["settings"])
app.include_router(upload.router, prefix="/upload", tags=["upload"])
app.include_router(news.router, prefix="/news", tags=["news"])
app.include_router(todo.router, prefix="/todo", tags=["todo"])
app.include_router(favorite.router, prefix="/favorite", tags=["favorite"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(agent.router, prefix="/agent", tags=["agent"])

@app.get("/")
async def root():
    return {"message": "Hello World"}

if __name__ == "__main__":
    import uvicorn
    # 传app,且reload=True(热重载),改代码后可以直接改后端,无需重启
    uvicorn.run("app.main:app", host=GlobalConfig.HOST, port=GlobalConfig.PORT, reload=True, timeout_keep_alive=60)

