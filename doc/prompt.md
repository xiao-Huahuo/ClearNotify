CloudPolicy 作品运行说明

本作品提供两个 Docker 镜像包：

1. `cloudpolicy-app-latest.tar`
   后端服务镜像
2. `cloudpolicy-web-latest.tar`
   前端服务镜像

说明：

- 后端镜像包不包含 `.env` 文件。
- 镜像中未打包作者本地的私有环境变量、API Key、邮箱口令等敏感配置。
- 使用者需要在本地自行准备环境变量后再启动容器。

一、导入镜像

在两个镜像包所在目录下执行：

```powershell
docker load -i cloudpolicy-app-latest.tar
docker load -i cloudpolicy-web-latest.tar
```

导入完成后，可通过以下命令查看镜像：

```powershell
docker images
```

二、准备环境变量

请在本地新建一个 `.env` 文件，补充项目运行所需的关键环境变量，
字段如下:
```env
# 基础服务配置
# HOST: 后端监听地址，本地开发用 127.0.0.1，Docker 部署改为 0.0.0.0
# PORT: 后端监听端口
# SECRET_KEY: JWT 签名密钥，建议用 openssl rand -hex 32 生成，勿泄露
# ALGORITHM: JWT 签名算法，保持默认即可
# ACCESS_TOKEN_EXPIRE_DAYS: 登录 Token 有效天数
HOST=127.0.0.1
PORT=8080
SECRET_KEY=your_random_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_DAYS=30

# 默认管理员初始化（可选）
# ADMIN_USERNAME: 首次启动自动创建的管理员用户名
# ADMIN_PASSWORD: 管理员初始密码，生产环境请改为强密码
# ADMIN_EMAIL: 管理员邮箱
# ADMIN_PHONE: 管理员手机号，格式：11位数字
ADMIN_USERNAME=admin
ADMIN_PASSWORD=111111
ADMIN_EMAIL=admin@example.com
ADMIN_PHONE=your_phone

# SMTP 邮件系统（真实发信需配置，不配置则邮件落盘至 mail_outbox/）
# SMTP_HOST: SMTP 服务器地址，如 smtp.qq.com、smtp.163.com
# SMTP_PORT: 端口，SSL 通常为 465，TLS 通常为 587
# SMTP_USERNAME: SMTP 登录账号（通常为邮箱地址）
# SMTP_PASSWORD: SMTP 授权码（非邮箱登录密码，需在邮箱设置中生成）
# SMTP_SENDER: 发件人邮箱地址
# SMTP_SENDER_NAME: 发件人显示名称
# SMTP_USE_SSL: 是否使用 SSL，端口 465 时设为 true
# SMTP_USE_TLS: 是否使用 STARTTLS，端口 587 时设为 true，与 SSL 互斥
SMTP_HOST=smtp.example.com
SMTP_PORT=465
SMTP_USERNAME=your_smtp_user
SMTP_PASSWORD=your_smtp_password
SMTP_SENDER=your_sender@example.com
SMTP_SENDER_NAME=CloudPolicy
SMTP_USE_SSL=true
SMTP_USE_TLS=false

# 邮箱验证与前后端回跳
# EMAIL_VERIFICATION_CODE_LENGTH: 验证码位数，默认 6 位
# EMAIL_VERIFICATION_EXPIRE_MINUTES: 验证码有效期（分钟）
# PUBLIC_BASE_URL: 后端公开访问地址，用于邮件中的链接跳转
# FRONTEND_BASE_URL: 前端访问地址，用于邮件验证后的页面回跳
EMAIL_VERIFICATION_CODE_LENGTH=6
EMAIL_VERIFICATION_EXPIRE_MINUTES=15
PUBLIC_BASE_URL=http://127.0.0.1:8080
FRONTEND_BASE_URL=http://127.0.0.1:5173

# Redis/任务队列
# REDIS_HOST: Redis 服务地址，Docker 部署时改为服务名 redis
# REDIS_PORT: Redis 端口，默认 6379
# REDIS_DB_CACHE: 用于缓存（热点资讯等）的 Redis 数据库编号
# REDIS_DB_QUEUE: 用于任务队列（邮件发送等）的 Redis 数据库编号
# REDIS_QUEUE_NAME: 任务队列名称，保持默认即可
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB_CACHE=0
REDIS_DB_QUEUE=1
REDIS_QUEUE_NAME=crawler_tasks

# 爬虫限流
# CRAWLER_RATE_LIMIT: 每个时间窗口内最大请求次数
# CRAWLER_RATE_WINDOW_SECONDS: 限流时间窗口（秒）
CRAWLER_RATE_LIMIT=30
CRAWLER_RATE_WINDOW_SECONDS=60

# 模型密钥（如需）
# LLM_API_KEY: Kimi/OpenAI 等 LLM 的 API Key
# LLM_BASE_URL: LLM API 地址，使用 Kimi 保持默认，换其他模型按需修改
# LLM_TIMEOUT: 请求超时时间（秒），长文档解析建议不低于 120
# LLM_MODEL: 使用的模型名称，可选 moonshot-v1-32k、moonshot-v1-128k 等
# LLM_TEMPERATURE: 模型温度，0 表示输出最稳定，政策解析场景建议保持 0
LLM_API_KEY=sk-xxxxx
LLM_BASE_URL=https://api.moonshot.cn/v1
LLM_TIMEOUT=240
LLM_MODEL=moonshot-v1-8k
LLM_TEMPERATURE=0

# Agent Plugin（通用插件配置，统一由 GlobalConfig 控制）
# AGENT_PLUGIN_ENABLED: 是否启用 Agent 插件，false 时智能体页仅支持普通对话
# AGENT_PLUGIN_EMBEDDING_MODEL: 向量化模型名称，首次启动自动下载
# AGENT_PLUGIN_COLLECTION_NAME: ChromaDB 向量集合名称，保持默认即可
# AGENT_PLUGIN_RAG_CHUNK_SIZE: 知识库文本分片大小（字符数）
# AGENT_PLUGIN_RAG_METADATA_EXTRAS: 向量存储时附加的元数据字段
# AGENT_PLUGIN_RAG_FORCE_UPDATE: 是否强制重建向量库，true 时每次启动都重新向量化
# AGENT_PLUGIN_RAG_TOP_K: 语义检索返回的最大候选片段数
# AGENT_PLUGIN_RAG_SCORE_THRESHOLD: 相似度过滤阈值，低于此值的检索结果将被丢弃
# AGENT_PLUGIN_SYSTEM_PROMPT: 智能体系统提示词
AGENT_PLUGIN_ENABLED=true
AGENT_PLUGIN_EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2
AGENT_PLUGIN_COLLECTION_NAME=agent_plugin_memory
AGENT_PLUGIN_RAG_CHUNK_SIZE=500
AGENT_PLUGIN_RAG_METADATA_EXTRAS=category,source
AGENT_PLUGIN_RAG_FORCE_UPDATE=false
AGENT_PLUGIN_RAG_TOP_K=5
AGENT_PLUGIN_RAG_SCORE_THRESHOLD=0.7
AGENT_PLUGIN_SYSTEM_PROMPT=You are an autonomous AI assistant called 云小圆. Call tools when necessary and answer accurately and concisely.

# PaddleOCR（本地图片 OCR / PDF 图片 OCR / DOCX 图片 OCR，可选）
# PADDLEOCR_ENABLED: 是否启用本地 PaddleOCR，false 时图片识别自动回退至 LLM OCR
# PADDLEOCR_MODELS_DIR: PaddleOCR 模型存放目录，对应 app/resources/paddleocr
# PADDLE_PDX_CACHE_HOME: PaddleX 缓存目录，对应 app/resources/paddlex
# PADDLEOCR_LANG: 识别语言，ch 为中英文混合，en 为纯英文
# PADDLEOCR_USE_ANGLE_CLS: 是否启用方向分类，处理旋转图片时建议开启
# PADDLEOCR_ENABLE_STRUCTURE: 是否启用版面分析，处理表格、多栏排版时建议开启
PADDLEOCR_ENABLED=false
PADDLEOCR_MODELS_DIR=paddleocr
PADDLE_PDX_CACHE_HOME=paddlex
PADDLEOCR_LANG=ch
PADDLEOCR_USE_ANGLE_CLS=true
PADDLEOCR_ENABLE_STRUCTURE=true
```
具体可详见源代码中的README.md.

三、启动后端镜像

将本地 `.env` 文件注入后端容器：

```powershell
docker run -d ^
  --name CloudPolicy_Service ^
  --env-file .env ^
  -p 8080:8080 ^
  cloudpolicy-app:latest
```

如镜像标签不是 `cloudpolicy-app:latest`，请以 `docker images` 查询结果为准。

五、启动前端镜像

前端镜像启动：

```powershell
docker run -d ^
  --name CloudPolicy_Web ^
  -p 80:80 ^
  cloudpolicy-web:latest
```

如镜像标签不是 `cloudpolicy-web:latest`，请以 `docker images` 查询结果为准。

六、访问方式
两个镜像运行后,可访问`http://localhost`访问页面服务.
- 前端页面默认访问地址：`http://127.0.0.1`
- 后端接口默认访问地址：`http://127.0.0.1:8080`

七、补充说明

- 若需正常使用大模型能力，请确保 `.env` 中已填写正确的 LLM 相关配置。
- 若需正常使用 OCR，请确保 `.env` 中填写的 PaddleOCR 模型目录在本机可用。
- 若端口被占用，可自行修改 `docker run` 中的端口映射。
- 本说明用于作品演示与部署参考，源码、Dockerfile 和完整工程文件见素材与源码文件夹。
