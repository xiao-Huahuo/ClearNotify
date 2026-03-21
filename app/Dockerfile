# 使用官方 Python 镜像作为基础镜像
FROM python:3.9-slim-buster

# 设置工作目录
WORKDIR /app

# 复制 requirements.txt 并安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制整个 app 目录到容器中
COPY app/ /app/app/

# 暴露 FastAPI 默认端口
EXPOSE 8000

# 启动 FastAPI 应用
# --host 0.0.0.0 允许从外部访问
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
