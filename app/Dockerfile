# 1. 基础镜像
FROM python:3.12-slim-bullseye

# 2. 设置环境变量
# 防止 python 产生 .pyc 文件，并让输出直接打印在控制台
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# 关键：设置 PYTHONPATH，确保容器能识别 server 为一个包
ENV PYTHONPATH=/server

# 3. 设置工作目录为 /app (这就是代码里的 PROJECT_ROOT)
WORKDIR /server

# 4. 安装系统依赖（如果你的爬虫或加密库需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 5. 安装 Python 依赖
# 先只拷贝 requirements.txt，利用 Docker 缓存层减少构建时间
COPY ./app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. 拷贝代码（虽然开发时会被 volumes 覆盖，但构建镜像仍需此步）
# 明确拷贝 app 文件夹到 /server/app
COPY ./app ./app
# 拷贝其他根目录必要的单个文件（如 database.db 初始文件等）
COPY .env .

# 7. 启动命令
# 必须指定 --host 0.0.0.0，否则外部无法访问
# 必须指定 app.main:app，因为 main.py 现在在 app 文件夹下
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]