# 云枢观策 - 面向民生政策理解、公共服务提效与基层信息可达性的智能化服务平台  
>  让政策不再停留在纸面，让民生服务真正抵达每个人。  

---

## 项目概述

**云枢观策平台** 是一套围绕“看得懂、找得到、办得成、能反馈、可沉淀”构建的民生政策与公共服务辅助系统。

它不是单一的“政策展示页”，也不是单纯的“AI 对话框”，而是一套已经形成完整闭环的系统：

- 对公众，它降低了政策理解门槛，减少因信息复杂、材料遗漏、入口不清带来的办事成本。
- 对认证主体，它提供了政策发布、展示、触达、反馈和追踪的一体化链路。
- 对管理端，它提供了数据看板、用户治理、意见聚合、日志监控和全局态势展示能力。
- 对系统本身，它已经具备智能体、RAG、OCR、文档解析、可视化分析、邮件验证、Docker 部署和前后端联动的大部分关键能力。

这个项目更关注**民生服务场景**，例如：

- 居民快速理解社区通知、办事须知、政策解读和材料要求
- 学生、职场人、普通居民都能用更适合自己的方式获取公共信息
- 认证主体发布政策后，持续看到阅读、点赞、评议和传播效果
- 管理员用统一后台掌握系统活跃度、内容沉淀、用户角色和反馈分布

---

## 现在这套系统已经具备什么

从当前代码和运行形态看，**云枢观策** 已经不是一个“概念型项目”，而是具备真实产品结构的完整系统。

### 1. 首页不是后台，而是展示型入口

- 根路由默认进入 `/showcase`
- 用户首先看到的是展示首页、政策广场和数据大屏，而不是直接落入系统内部
- 点击“进入系统”后，才进入智能体页 `/agent`
- 这意味着项目同时具备了：
  - 对外展示能力
  - 对内业务承载能力
  - 比赛答辩、项目路演、实际演示三种场景的统一入口

### 2. 智能体不是黑盒问答，而是可追踪的办事辅助

- 系统内置 `CloudCycle / 云小圆` 智能体页
- 支持基于 WebSocket 的流式对话
- 支持实时推送工具调用轨迹
- 支持对解析过程进行分段展示，而不是只在最后一次性给结果
- 支持会话创建、消息持久化、历史对话查看和删除

这使系统具备“**解释过程可见**”的特征，而不只是“最终答案可见”。

### 3. 文档上传不是摆设，而是完整解析链路

- 支持上传 PDF、DOCX、DOC、XLSX、XLS、TXT
- PDF 优先走 `pdfplumber` 文本提取
- 扫描件或纯图片型 PDF 可自动回退到 OCR
- 图片与扫描件支持独立 OCR 接口
- OCR 使用 Kimi 视觉模型进行文本提取
- 解析后可回填至智能解析流程继续处理

这意味着系统能处理的不是“标准文本输入”，而是真实办事场景里常见的：

- 扫描版通知
- 拍照版公告
- 截图版办事说明
- 表格型附件
- 纯文档型通知

### 4. RAG 已经接入，不是口号

- 系统使用本地 embedding 模型
- 使用 `ChromaDB` 作为向量库
- 知识源位于 `app/resources/vector_init/policy_knowledge.json`
- embedding 模型默认位于 `app/resources/embedding/`
- 启动时会进行 embedding 检查和 Agent 插件预热
- Docker 环境下要求先本地下载 embedding，再启动容器

这部分已经形成可运行的知识增强链路，而不是仅停留在文档描述层。

### 5. 色系切换已经是产品级能力，不是临时换肤

项目现在不仅支持明暗主题切换，还支持全局品牌色系切换。

当前已支持：

- `classic`：经典红
- `wine-coral`：酒红珊瑚
- `coral`：珊瑚蓝

色系切换贯穿：

- 展示页头部
- 系统内部 Header
- 设置页
- 用户偏好持久化
- 本地缓存与数据库保存

这意味着项目不仅有“功能可用”，也有较成熟的**品牌化界面控制能力**。

### 6. 系统内部不是单页演示，而是多模块协同

当前前端路由已经覆盖以下核心页面：

- `/showcase` 展示首页
- `/showcase/discovery` 展示版政策广场
- `/showcase/screen` 展示版数据大屏
- `/agent` 智能体页
- `/home` 核心业务页
- `/public-opinion-hall` 民生反馈大厅
- `/policy-swipe` 政策推荐
- `/policy-publish-center` 政策发布中心
- `/certified-analysis` 发布追踪与统计
- `/todo` 办事进度
- `/favorites` 收藏
- `/history` 历史记录
- `/profile` 个人中心
- `/settings` 设置中心
- `/admin` 管理后台

这不是一页式 AI Demo，而是完整的产品化系统。

---

## 适合的场景

### 公众使用场景

- 看不懂长通知时，用智能体提炼重点
- 面对复杂材料要求时，获得结构化材料清单
- 通过待办页持续跟踪“下一步做什么”
- 收藏重要结果，避免二次查找
- 在民生反馈大厅查看和提交意见

### 认证主体使用场景

- 上传并发布政策文档
- 在政策广场对外展示审核通过的内容
- 统计阅读量、点赞量、评议量、平均评分
- 在发布追踪页看自己内容的传播与反馈情况

### 管理端场景

- 查看用户总量、消息总量、活跃用户
- 管理角色与用户权限
- 查看系统日志
- 实时查看管理统计流
- 在展示大屏汇总用户、内容、评议与地域分布

---

## 产品亮点

## 1. 从“政策文本”到“办事行动”的转换能力

系统核心价值不在于把文本“说得更像人话”，而在于把长文本进一步转成：

- 办理事项
- 适用对象
- 时间节点
- 地点或入口
- 材料清单
- 办理步骤
- 注意事项
- 风险提示

对民生服务场景来说，真正重要的是“下一步怎么做”，而不是“模型回答得多华丽”。

## 2. 可解释的智能体体验

系统不是只给最终回复，而是把推理轨迹通过 WebSocket 实时流式展示给前端。

这带来几个直接优势：

- 用户知道系统在“想什么”
- 工具调用可视化
- 不容易把复杂解析过程变成不可追溯的黑盒
- 展示和答辩时更有说服力

## 3. 以民生为中心的交互设计

当前系统已经具备以下更贴近民生服务的设计方向：

- 支持 OCR 处理现实世界中的截图、扫描件、海报、公告
- 支持 TTS 语音播报，便于用户在移动、浏览或整理材料时快速获取结果
- 支持更通用的默认阅读偏好设置，覆盖大众化浏览与使用场景
- 支持待办沉淀、收藏沉淀、历史沉淀，减少重复理解成本

## 4. 展示页与业务页分离

项目首页默认先进入展示页，而不是直接进入后台系统。

这意味着它兼具：

- 产品展示能力
- 业务系统承载能力
- 赛事答辩和落地使用的双重适配

## 5. 品牌化外观而不是单一皮肤

当前系统已经支持：

- 明亮 / 深色 / 跟随系统
- 经典红 / 酒红珊瑚 / 珊瑚蓝

这使界面不再只是“能用”，而是具备较清晰的视觉品牌方向。

---

## 当前功能全景

### A. 展示层

#### 1. 展示首页 `/showcase`

- 用于对外展示系统定位、亮点和入口
- 作为访客第一视图
- 点击后进入系统内部

#### 2. 展示政策广场 `/showcase/discovery`

- 用于承接公共内容浏览
- 与内部业务页形成展示版分层

#### 3. 展示大屏 `/showcase/screen`

- 汇总用户、消息、政策文档、意见、地域分布等信息
- 适合答辩展示、项目演示和公开汇报

### B. 智能解析层

#### 4. 智能体页 `/agent`

- WebSocket 实时连接
- 会话级消息持久化
- 支持轨迹推送、答案流式输出、结果结构化回传
- 支持基于 RAG 的知识增强解析

#### 5. 核心业务页 `/home`

- 承载上传、解析、结果展示等业务
- 支持 OCR 入口
- 支持 TTS 播报结果

### C. 内容与传播层

#### 6. 政策推荐 `/policy-swipe`

- 面向用户的推荐式阅读体验
- 根据职业字段进行一定程度的类别优先推荐
- 已审核通过内容可进入推荐链路

#### 7. 政策发布中心 `/policy-publish-center`

- 认证主体或管理员可发布政策文档
- 管理文档标题、分类、内容与状态

#### 8. 发布追踪 `/certified-analysis`

- 认证主体可查看自己内容的审核状态、阅读、点赞、反馈等
- 对认证主体形成“发布后可量化”的闭环

#### 9. 民生反馈大厅 `/public-opinion-hall`

- 用户可以提交评议、纠错、留言等反馈
- 系统支持意见公开流、意见点赞、类型统计
- 认证主体可查看自己内容收到的反馈

### D. 个人沉淀层

#### 10. 办事进度 `/todo`

- 手动新建待办
- 待办完成状态切换
- 待办确认和删除
- 为“看懂政策”补上“推进办理”的最后一步

#### 11. 收藏 `/favorites`

- 重要内容沉淀
- 提高后续查找效率

#### 12. 历史记录 `/history`

- 保留过往解析结果与会话痕迹
- 支持恢复、导出和继续使用

#### 13. 个人中心 `/profile`

- 汇总个人解析次数
- 汇总待办、收藏等沉淀结果
- 展示 RAG 指标摘要
- 展示个人偏好和近期动态

#### 14. 设置页 `/settings`

- 明暗主题切换
- 色系切换
- 默认受众设置
- 系统通知设置

### E. 管理层

#### 15. 管理后台 `/admin`

- 用户列表
- 用户角色调整
- 实时统计流
- 全局分析
- 地域分布
- 意见统计
- 日志查看

---

## 核心算法与实现亮点

以下部分不是宣传层面的“用了 AI”，而是当前代码中已经落地的关键机制。

### 1. 自由结构化解析引擎

系统的文档解析不是写死字段的简单模板抽取，而是带有“自由结构化”特征的解析链路。

实现思路：

- 先对原文做标准化处理
- 调用 LLM 输出严格 JSON 对象
- 优先使用 `json_schema` 风格约束
- 若模型不支持，则回退到 `json_object`
- 若 JSON 不完整，系统会做本地修补
- 若仍失败，再走一次 JSON 修复逻辑
- 如果最终无法稳定恢复，则返回低质量回退结果，保证系统不崩

这使系统在面对真实、混乱、格式不统一的文档时，具有更强的鲁棒性。

### 2. 动态载荷到图谱的自动生成

当前解析器不仅输出文本结果，还会尝试构建：

- `nodes`
- `links`
- `dynamic_payload`
- `visual_config`

如果模型没有直接给出图结构，系统会根据动态 JSON 自动生成结构图谱。

这意味着系统具备把复杂内容转为“可视图谱”的能力，而不是只能展示纯文本回答。

### 3. 智能体 + 长短期记忆

Agent 插件当前基于 `LangGraph` 封装，具备：

- 短期记忆：按 `thread_id` 持久化对话上下文
- 长期记忆：基于 `ChromaDB` 的向量检索
- SSE 风格流式执行能力
- 工具调用注册与轨迹回传

这比“单轮问答式调用”更接近真实智能体应用形态。

### 4. RAG 预热与本地 embedding 管理

系统使用本地 embedding 文件夹管理模型，而不是每次运行都在线拉取。

当前 embedding 流程特点：

- 启动时检查 embedding 是否存在
- 非 Docker 环境可自动下载
- Docker 环境不在容器内自动下载
- 提供独立脚本 `python -m app.scripts.download_embedding`
- 启动时还会触发全局知识向量化同步

这样做的好处是：

- 部署更稳定
- 避免容器启动时受网络环境影响
- 便于在云服务器 CPU 环境下提前准备资源

### 5. 实时推理轨迹流式编排

智能体页的 WebSocket 不是只把最终答案推给前端，而是采用“结果与轨迹分离”的实时策略。

后端实现关键点：

- 单独维护 `trace_queue`
- 将工具调用、思考事件逐条放入队列
- 先流式发送轨迹
- 再发送 `trace_done`
- 再发送结构化结果
- 最后分块发送自然语言答案

这种设计的价值在于：

- 前端看到的是真正逐步发生的过程
- 轨迹不会被答案正文冲掉
- 系统体验更稳定，也更适合展示“智能体正在工作”

### 6. 民生场景下的时间节省建模

统计服务中，系统不是只做“调用次数统计”，而是尝试量化“节省了多少阅读理解时间”。

当前实现逻辑为：

```text
原文阅读耗时 ≈ max(字符数 / 150, 3)
单次节省时间 ≈ min(max(int(原文阅读耗时 - 1), 2), 30)
```

也就是说，系统把复杂通知压缩成可理解结果之后，会估算：

- 总节省时间
- 平均节省时间
- 每次解析节省的分钟数分布

这类指标非常适合用于说明系统对民生办事效率的实际价值。

### 7. 关键词统计与风险频次分析

系统使用 `jieba` 对历史解析结果中的材料和风险字段做词频分析，生成：

- 材料高频项
- 风险高频项
- 通知类型分布
- 复杂度分布

同时还构造：

- `rag_metrics`
- `rag_series`
- `vector_scatter`

这使统计页和个人中心不只是展示“次数”，而是能展示“内容结构”和“检索表现”。

### 8. 文档解析链路中的多级回退

当前上传解析链路具备真实工程化特征：

- PDF 文本优先走 `pdfplumber`
- 扫描版 PDF 自动回退 OCR
- Word 走 `python-docx`
- Excel 支持 `openpyxl` 和 `xlrd`
- TXT 直接读取
- OCR 走 Kimi 文件提取或视觉识别回退

这使系统能更稳地覆盖真实办事场景中的材料形态。

### 9. 新闻与热点模块的缓存与限流

系统新闻模块不是简单写死数据，而是具备：

- RSS 抓取
- Redis 缓存
- 内存级兜底缓存
- 请求频率限制
- 抓取任务入队
- mock 数据兜底

因此即使外部源短时不稳定，页面仍可回退到可展示状态。

### 10. 邮件系统的“真实发送 + 本地预览”双轨机制

用户注册后需要完成邮箱验证。

但系统没有把流程绑死在 SMTP 成功上，而是设计了双轨机制：

- SMTP 配置齐全时，真实发信
- SMTP 未配置或失败时，写入 `mail_outbox/`
- 同时前端可以拿到 `preview_code`

这对于开发、测试、演示和比赛环境都非常友好。

### 11. 主题与色系切换的持久化实现

界面外观不是局部 CSS 切换，而是完整设置能力。

当前已实现：

- `theme_mode`：浅色、深色、跟随系统
- `color_scheme`：经典红、酒红珊瑚、珊瑚蓝
- `localStorage` 本地持久化
- 登录用户数据库持久化
- Header 和展示页即时切换

对一个比赛项目来说，这已经超过“做个主题按钮”的水平，而是产品化程度较高的品牌外观控制。

---

## 技术栈

### 前端

- Vue 3
- Vite
- Vue Router
- Pinia
- Axios
- ECharts 5
- Web Speech API（语音播报）

### 后端

- FastAPI
- SQLModel / SQLAlchemy
- SQLite
- Redis
- WebSocket
- LangGraph
- ChromaDB
- sentence-transformers
- jieba
- pdfplumber
- python-docx
- openpyxl / xlrd

### 部署与运维

- Docker
- Docker Compose
- Nginx

---

## 系统架构概览

```text
用户访问展示首页 (/showcase)
        ↓
点击进入系统 (/agent)
        ↓
上传文本 / 图片 / PDF / Word / Excel / OCR
        ↓
FastAPI 接收请求并解析文件
        ↓
Agent 插件 + LLM + RAG 执行理解与增强检索
        ↓
生成结构化结果 / 图谱 / 轨迹 / 会话记录
        ↓
前端流式展示轨迹、答案与统计
        ↓
用户收藏、反馈、加入待办、进入个人沉淀
        ↓
认证主体和管理员在发布追踪、后台和大屏中查看效果
```

---

## 项目结构

```shell
.
├── app/                            # 后端核心 (FastAPI)
│   ├── main.py                     # 应用入口、生命周期、路由挂载、静态资源挂载
│   ├── api/                        # API 路由层
│   │   ├── routes/
│   │   │   ├── agent.py            # 智能体、会话、WebSocket
│   │   │   ├── upload.py           # 头像、文档、OCR 上传
│   │   │   ├── policy_document.py  # 政策文档发布、审核、推荐、统计
│   │   │   ├── opinion.py          # 民生反馈、纠错、留言、点赞
│   │   │   ├── settings.py         # 用户设置
│   │   │   ├── stats_analysis.py   # 统计分析
│   │   │   ├── news.py             # 新闻与热点
│   │   │   ├── todo.py             # 待办事项
│   │   │   ├── user.py             # 注册、邮箱验证、个人信息、权限申请
│   │   │   ├── login.py            # 登录鉴权
│   │   │   ├── admin.py            # 管理员后台能力
│   │   │   └── showcase.py         # 展示首页与大屏聚合数据
│   ├── ai/                         # LLM 与解析逻辑
│   │   ├── document_parser.py      # 自由结构化解析、图谱生成、PDF AI 解析
│   │   └── request_llm.py          # 模型请求封装
│   ├── agent_plugin/               # Agent 插件系统
│   │   ├── agent/                  # AgentCore、记忆、工具、配置
│   │   ├── bootstrap.py            # 插件配置注入
│   │   └── README.md               # 插件说明
│   ├── core/                       # 全局配置、安全、数据库、日志
│   ├── models/                     # SQLModel 数据模型
│   ├── schemas/                    # Pydantic/SQLModel DTO
│   ├── services/                   # 业务服务
│   │   ├── agent_service.py        # 智能解析业务封装
│   │   ├── agent_plugin_service.py # Agent 预热、embedding 检查、RAG 同步
│   │   ├── agent_chat_service.py   # 智能体会话与消息持久化
│   │   ├── stats_service.py        # 统计建模、词频与时间节省分析
│   │   ├── ocr_service.py          # OCR 服务
│   │   ├── news_crawler.py         # RSS 抓取、缓存、热点生成
│   │   ├── email_service.py        # 邮件与本地预览回退
│   │   ├── redis_queue.py          # Redis 队列
│   │   └── worker.py               # 后台 worker
│   ├── resources/                  # 初始化数据与知识资源
│   │   ├── db_init/                # 数据库初始化数据
│   │   ├── vector_init/            # RAG 初始知识源
│   │   └── embedding/              # 本地 embedding 模型目录
│   ├── scripts/                    # 独立执行脚本
│   │   └── download_embedding.py   # 单独下载 embedding 模型
│   ├── requirements.txt            # 后端依赖
│   └── Dockerfile                  # 后端镜像构建
├── web/                            # 前端核心 (Vue 3)
│   ├── src/
│   │   ├── views/                  # 页面
│   │   ├── components/             # 组件
│   │   ├── stores/                 # Pinia 状态管理
│   │   ├── router/                 # 前端路由与 API 路由封装
│   │   ├── utils/                  # 工具函数，如 TTS 等
│   │   ├── composables/            # 可复用逻辑
│   │   └── assets/                 # 静态资源
│   ├── nginx.conf                  # Web 容器 Nginx 配置
│   ├── package.json                # 前端依赖与脚本
│   └── Dockerfile                  # 前端镜像构建
├── doc/                            # 文档与素材
├── uploads/                        # 运行时上传目录
│   ├── avatars/                    # 用户头像
│   ├── docs/                       # 上传文档
│   ├── images/                     # 上传图片
│   ├── chat_exports/               # 对话导出
│   └── agent_plugin/               # Agent 数据与向量目录
├── logs/                           # 运行时日志目录
├── mail_outbox/                    # SMTP 不可用时的本地邮件预览目录
├── docker-compose.yml              # Docker 编排
├── README.md                       # 旧版说明
├── README-NOW.md                   # 当前版本说明
└── TODO.md                         # 待办与部署问题记录
```

---

## 运行时目录说明

以下目录是运行后生成或持续写入的：

- `uploads/`
- `logs/`
- `mail_outbox/`

其中：

- `uploads/avatars/` 存放用户头像
- `uploads/docs/` 存放用户上传的文档与 OCR 中转文件
- `uploads/chat_exports/` 存放对话导出结果
- `uploads/agent_plugin/` 存放 Agent 插件相关数据
- `logs/app.log` 存放应用日志
- `mail_outbox/` 存放本地邮件预览文件

---

## 启动前准备

### 1. 创建 `.env`

请在项目根目录创建 `.env`，可以参考如下模板：

```env
# 基础服务
HOST=127.0.0.1
PORT=8080
SECRET_KEY=your_random_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_DAYS=30
REALTIME_STREAM_INTERVAL_SECONDS=2
SQLALCHEMY_ECHO=false

# 默认管理员（可选）
ADMIN_USERNAME=admin
ADMIN_PASSWORD=111111
ADMIN_EMAIL=admin@example.com
ADMIN_PHONE=

# 邮件系统
SMTP_HOST=
SMTP_PORT=465
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_SENDER=
SMTP_SENDER_NAME=CloudPolicy
SMTP_USE_SSL=true
SMTP_USE_TLS=false
EMAIL_VERIFICATION_CODE_LENGTH=6
EMAIL_VERIFICATION_EXPIRE_MINUTES=15

# 前后端地址
PUBLIC_BASE_URL=http://127.0.0.1:8080
FRONTEND_BASE_URL=http://127.0.0.1:5173
PUBLIC_BASE_URL_DOCKER=http://127.0.0.1:8080
FRONTEND_BASE_URL_DOCKER=http://127.0.0.1

# Redis
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_DB_CACHE=0
REDIS_DB_QUEUE=1
REDIS_QUEUE_NAME=crawler_tasks

# 限流
CRAWLER_RATE_LIMIT=30
CRAWLER_RATE_WINDOW_SECONDS=60

# LLM
LLM_API_KEY=sk-xxxxx
LLM_BASE_URL=https://api.moonshot.cn/v1
LLM_TIMEOUT=60
LLM_MODEL=moonshot-v1-8k
LLM_TEMPERATURE=0

# Agent Plugin / RAG
AGENT_PLUGIN_ENABLED=true
AGENT_PLUGIN_EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2
AGENT_PLUGIN_COLLECTION_NAME=agent_plugin_memory
AGENT_PLUGIN_RAG_CHUNK_SIZE=500
AGENT_PLUGIN_RAG_METADATA_EXTRAS=category,source
AGENT_PLUGIN_RAG_FORCE_UPDATE=false
AGENT_PLUGIN_RAG_TOP_K=5
AGENT_PLUGIN_RAG_SCORE_THRESHOLD=0.7
AGENT_PLUGIN_SYSTEM_PROMPT=你是一个具备自主能力的 AI 助手。请在必要时调用工具，并给出准确、简洁、可执行的答案。
```

### 2. 准备 Redis

本项目新闻抓取队列与缓存依赖 Redis。

如果本机未安装 Redis，可以直接使用 Docker：

```bash
docker run --name redis -p 6379:6379 -d redis
```

常用命令：

```bash
docker stop redis
docker start redis
```

### 3. 先下载 embedding

在 Docker 部署前，**必须先准备本地 embedding 模型**。

执行：

```bash
python -m app.scripts.download_embedding
```

如果缺少这一步，Docker 容器内不会自动下载 embedding，而是直接报错退出。

---

## 本地运行

### 后端

```bash
cd app
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS / Linux:

```bash
source .venv/bin/activate
```

安装依赖：

```bash
pip install -r requirements.txt
```

启动后端：

```bash
uvicorn app.main:app --reload
```

首次启动时，系统会执行：

- 数据库初始化
- 默认管理员初始化
- Agent 图谱生成
- embedding 检查
- Agent 预热
- 全局知识向量同步
- Redis worker 启动

### 前端

```bash
cd web
npm install --verbose
npm run dev
```

前端开发环境默认地址一般为：

- `http://127.0.0.1:5173`

后端默认地址一般为：

- `http://127.0.0.1:8080`

---

## Docker 部署

### 1. 一键启动

在项目根目录执行：

```bash
docker compose up --build -d
```

这会启动三个服务：

- `redis`
- `app`
- `web`

### 2. 访问方式

- 前端页面：`http://localhost`
- 后端 API：容器内部为 `http://app:8080`
- 前端通过 Nginx 代理访问后端

### 3. 停止服务

```bash
docker compose down
```

### 4. 再次启动

```bash
docker compose up
```

---

## 当前 Docker 部署特性

当前 Docker 方案已经适配了几个关键问题：

### 1. CPU 友好

后端镜像在构建时预装的是 **CPU 版 PyTorch**，避免在无 GPU 的云服务器上拉取体积巨大的 CUDA 依赖。

### 2. 头像与上传资源可访问

Nginx 已将 `/media/` 代理到后端静态目录，因此 Docker 条件下头像、上传文档和相关静态资源能够被正常访问。

### 3. WebSocket 已适配智能体连接

Nginx 已对：

- `/agent/ws`
- `/api/agent/ws`

配置 WebSocket 代理、升级头和超时，保证智能体页在 Docker 条件下正常连接。

### 4. 上传体积已放宽

Nginx 配置了：

```nginx
client_max_body_size 25m;
```

可有效避免常见的 413 请求体过大问题。

---

## 入口说明

当前系统的入口逻辑如下：

- 访问根路径 `/` 时，默认进入展示首页 `/showcase`
- 在展示页点击“进入系统”后，进入智能体页 `/agent`
- 登录成功后也会进入 `/agent`
- 退出登录后回到 `/showcase`

这套逻辑符合“先展示，再进入系统”的当前产品定位。

---

## 为什么说它已经超出普通 README 能覆盖的范围

因为它现在已经同时具备以下层次：

- 有对外展示层
- 有对内业务层
- 有多角色权限体系
- 有真实上传与解析链路
- 有 OCR 与文档回退机制
- 有 RAG 与本地 embedding 管理
- 有 WebSocket 智能体实时交互
- 有统计建模与可视化
- 有政策发布、推荐、反馈与追踪
- 有主题和品牌色系切换
- 有邮件验证与本地邮件预览回退
- 有 Docker 编排、Nginx 代理、Redis 队列与缓存

这已经是一套较完整的智能化民生服务平台，而不是单功能原型。

---

## 适合在比赛中强调的价值

如果用于展示或答辩，建议重点强调：

- 它解决的是**民生政策理解与公共服务信息可达性**问题
- 它不是单点 AI，而是“展示 + 智能体 + 内容发布 + 反馈闭环 + 管理分析”的完整系统
- 它把复杂政策文本转化为可执行办事信息
- 它兼顾公众使用、认证主体发布和管理端治理三类角色
- 它已经具备工程化部署能力，而不仅是页面效果
- 它将色系切换、主题切换和展示入口纳入产品设计，说明系统已经开始考虑品牌和体验的一致性

在表达上，更适合强调：

- 民生服务效率
- 政策可理解性
- 基层信息触达
- 多角色协同
- 公共服务体验改善
- 数字化助办与信息减负

而不是停留在“用了大模型”这一层。

---

## 当前版本总结

**云枢观策** 当前已经形成以下闭环：

**展示首页引流 → 进入系统 → 上传与解析 → RAG 增强 → 结构化理解 → 待办沉淀 / 收藏沉淀 / 历史沉淀 → 发布传播 → 民生反馈 → 管理端统计与大屏展示**

对于一个面向比赛与落地双场景的项目来说，这套系统现在最有价值的地方，不只是功能多，而是已经开始形成：

- 产品结构
- 工程结构
- 数据结构
- 部署结构
- 视觉结构

这也是为什么需要一份新的 README，而不是继续沿用最初的版本说明。
