# ClearNotify - 民生通知结构化解读和办事助手
> 让每一份政务通知，都清晰可见;让每一个办事流程，都触手可及.

---
## 软件宗旨 (Project Mission)

在数字信息爆炸的时代，政务公告、社区通知、学校文件等公共信息往往以冗长、晦涩的文本形式存在。由于信息密度极大、重点分散，导致了显著的“数字鸿沟”：
- **老年群体**：因无法有效提取关键信息而面临办事难、看不懂的困境。
- **学生与职场人**：在琐碎的通知中极易遗漏截止日期、所需材料等核心要素。
- **普通居民**：因政策解读偏差，常导致办事过程中“往返跑、多次跑”。

**ClearNotify** 致力于通过最前沿的 AI 技术，将这些零散且难读的文本，转化为结构清晰、直观易懂的**全场景办事助手**。我们的核心目标是：

1.  **重塑阅读体验**：利用 LLM 驱动的结构化引擎，将万字长文瞬间浓缩为“谁能办、带什么、去哪办”的极简卡片。
2.  **跨越数字壁垒**：通过**多模态感知系统**（OCR 截图解析、语音交互输入），让不便打字的用户也能无障碍获取信息。
3.  **智能决策辅助**：内置**自主思考智能体 (Agent)**，不仅能解读政策，更能基于 RAG（检索增强生成）技术，针对用户具体情况提供准确的避雷指南与流程建议。
4.  **量化获得感**：通过科学的“节省时间算法”与可视化统计，让每一次信息处理的效率提升都清晰可见。

**让每一份复杂通知，都清晰可见；让每一个办事流程，都触手可及。**

---

## 核心功能详解

### 智能解读：从“阅读”到“获得”的降维打击
这是 **ClearNotify** 的心脏。它不仅仅是做一个摘要，而是通过内置的 **LangChain Agent** 对文本进行手术刀式的拆解。
系统在处理一份数千字的政务公文时，会同步启动 **RAG（检索增强生成）** 机制。它会先在 **ChromaDB** 向量数据库中检索相关的法律法规底稿，确保 AI 不会因为大模型的“幻觉”而编造办事流程。
最关键的一点在于**思考过程（Chain-of-Thought）的透明化**：用户可以看到智能体是如何从一段晦涩的段落中抽取出“需要携带身份证原件”这个结论的。这种逻辑溯源让机器的输出具备了像人类专家一样的可信度。此外，针对不同受众的**多版本改写**（关怀、学生、极简）并非简单的缩减，而是深层语义的重构，确保信息密度与受众的理解力完美匹配。

### 多模态感知：打破数字孤岛
我们不希望用户只能通过“复制粘贴”来使用 AI。
* **视觉侧**：集成 OCR 引擎，无论是路边的布告栏照片，还是手机里的政务 APP 截图，扔进去就能解析。
* **交互侧**：Web Audio API 允许用户直接语音提问，配合 TTS 声学播报，这为视障人士和不便打字的老年人提供了真正的无障碍通道。

### 数据价值量化：让效率提升“肉眼可见”
很多 AI 工具只提供结果，不提供价值证明。我们设计了一套**时间收益算法**。
系统会根据原始文本的字数与逻辑复杂度，对比结构化卡片的阅读成本，计算出用户因使用本平台而省下的具体分钟数。在管理员面板，你可以看到由 **ECharts 5.0** 驱动的红蓝双线对比图：红线是你的个人贡献，蓝线是全站用户的集体效率提升。这种数据上的对比，配合高频材料词云和难度评估雷达图，让“跨越数字鸿沟”不再是一个口号，而是一组实实在在的增长曲线。

### 辅助特性

**社区发现与离线百科**
首页不再是冷冰冰的输入框，而是动态滚动的政务资讯流。所有解析过的通知都可以一键存入个人库。这个库支持离线调用，即便在办事大厅信号不佳的情况下，你依然可以调出那张结构化的“办事小卡片”。

**柔性角色管理系统**
基于 **SMTP** 的真实邮件系统打通了用户与管理员的壁垒。你可以通过邮件申请权限提升，也可以在厌倦管理工作时一键降级为普通用户。

**极简视觉与系统彩蛋**
全站采用红黑渐变设计，支持像素级的明暗模式切换。至于那个“不要点”的红色按钮，它通往原神的世界，是我们给疲惫办事者的一点幽默感。


---
## 技术与架构
### **核心技术 (Key Technologies)**

本项目采用**前后端分离的异步全栈架构**，通过 AI 智能体与多模态交互技术，构建从信息感知到深度解读的闭环系统。

#### **1. 前端表现层 (Client Side - Vue3 生态)**
* **响应式框架**：基于 **Vue 3 (Composition API)** 与 **Vite** 构建，采用 **MVVM** 设计模式，确保界面在高负载 AI 数据流下的流畅渲染。
* **状态与路由**：使用 **Pinia** 进行全局状态管理（用户信息、鉴权令牌、明暗主题切换），**Vue Router** 实现基于角色的动态权限路由控制。
* **多模态感知 (Perception)**：
    * **语音交互**：集成 **Web Audio API**，实现实时语音录入与指令识别，适配无障碍办事场景。
    * **视觉解析**：通过 **Canvas API** 结合前端 OCR 预处理，支持直接截屏上传政务公告并提取文字。
    * **无障碍播报**：内置 **TTS (Text-to-Speech)** 引擎，为老年用户提供结构化结果的语音朗读功能。
* **数据可视化**：利用 **ECharts 5.0** 绘制动态图表，包含个人/全体用户节省时间趋势的双线图、高频材料词云及通知难度评估雷达图。

#### **2. 后端核心层 (Server Side - FastAPI 异步架构)**
* **异步引擎**：基于 **FastAPI** 的高性能异步特性，采用“接口-业务-数据-智能”四层架构，完美适配长连接的 LLM 请求。
* **智能中枢 (AI Orchestration)**：
    * **智能体 Agent**：基于 **LangChain** 封装，支持 **Chain-of-Thought (CoT)** 思考过程展示，具备逻辑拆解与自主决策能力。
    * **RAG 增强检索**：集成 **ChromaDB** 向量数据库，通过语义搜索政策法规原文，从根本上解决 AI 幻觉问题。
    * **模型路由**：统一适配层对接 Moonshot (Kimi)、GPT-4o 等主流大模型，支持按需动态切换。
* **数据持久化**：使用 **SQLModel (SQLAlchemy)** 进行对象关系映射，配合 **SQLite** 或 **PostgreSQL** 存储结构化通知数据与用户记录。
* **异步任务管理**：集成 **Redis** 作为消息代理，处理 **真实邮件系统 (SMTP)** 的异步发送（如权限申请通知、效率周报）及高频热点资讯缓存。

#### **3. 安全与基础设施 (Security & Infrastructure)**
* **鉴权体系**：采用 **OAuth2 + JWT (JSON Web Token)** 动态令牌机制，配合自定义 Python 装饰器实现严格的管理员与普通用户数据隔离。
* **容器化部署**：支持 **Docker & Docker Compose** 一键环境编排，集成 Nginx 反向代理与 SSL 证书自动化管理。
* **自动化运维**：基于 Git 工作流与 CI/CD 管道，确保后端接口规范化（Pydantic 校验）与前端静态资源的高效构建。



### **数据流向 (Data Flow)**

本项目遵循 **“多模从采集、异步双循环、RAG 增强”** 的闭环逻辑：

1.  **多模态采集 (Ingress)**：前端 **Vue3** 通过 `Axios` 发送请求。数据来源涵盖 **Web Audio API** 实时录音、**OCR** 截图文字提取、手动粘贴及 **.json/.txt** 文件上传。
2.  **安全控制 (Security)**：请求抵达 **FastAPI** 路由后，由 **OAuth2 + JWT** 装饰器校验用户身份，确保管理员（Admin）与普通用户的数据在物理逻辑上完全隔离。
3.  **智能中枢处理 (Core Logic)**：
    * **语义索引**：原始文本经由 Embedding 模型向量化，存入 **ChromaDB**。
    * **RAG 检索**：**LangChain Agent** 自动检索数据库中的政策原文与办事百科，补充上下文以消除 AI 幻觉。
    * **推理生成**：调用 **LLM API**（如 Kimi/GPT-4o），结合 **Chain-of-Thought (CoT)** 导出结构化卡片（适用对象、所需材料、办理流程、风险提示）。
4.  **异步任务链 (Async Tasks)**：后端利用 **Redis** 队列触发非阻塞任务，包括通过 **SMTP** 发送真实邮件（通知权限申请、周报推送）以及数据缓存更新。
5.  **价值量化与呈现 (Egress)**：系统对比文本处理前后的字数与逻辑密度，计算“节省时间”数据并入库。前端 **ECharts** 实时轮询接口，动态渲染红蓝双线趋势图及高频材料词云。
6.  **反馈闭环 (Feedback)**：用户对解析结果的收藏与纠错行为将反馈至数据库，持续优化智能体的政策解读精度。

### 项目结构与文件职责
```shell
ClearNotify/
├── app/                        # 后端核心 (FastAPI)
│   ├── main.py                 # 【入口】程序主入口，FastAPI 初始化与路由挂载
│   ├── ai/                     # 智能中枢层
│   │   ├── analysis_agent.py   # 【核心】Agent 智能体：含 CoT 思考过程与结构化逻辑
│   │   ├── document_parser.py  # 【多模态】文档解析器：支持 OCR 与多格式预处理
│   │   └── request_llm.py      # 【接口】LLM 适配层：统一封装 Kimi/GPT 请求
│   ├── api/                    
│   │   ├── deps.py             # 【鉴权】全局依赖：JWT 校验、权限控制与 DB Session
│   │   └── routes/             # 【业务路由】admin, user, stats, news, todo 等
│   ├── core/                   
│   │   └── config.py           # 【配置中心】全局变量管理、安全算法及 SMTP 配置
│   ├── models/                 # 【模型】基于 SQLModel 的数据库实体与 Pydantic 模式
│   ├── services/               # 【业务层】核心逻辑实现、复杂统计计算与邮件发送服务
│   ├── db/                     # 【数据库】存储引擎初始化、连接池与 Session 管理
│   └── Dockerfile              # 后台Dockerfile配置
├── web/                        # 前端核心 (Vue3)
│   ├── src/
│   │   ├── main.js             # 【入口】前端初始化、全局插件与样式挂载
│   │   ├── api/                
│   │   │   └── index.js        # 【通信控制】Axios 拦截器封装与后端接口统一管理
│   │   ├── router/             
│   │   │   └── index.js        # 【路由守卫】全站页面路由配置与权限导航拦截
│   │   ├── stores/             
│   │   │   ├── auth.js         # 【鉴权状态】用户登录态、Token 持久化与权限信息
│   │   │   └── settings.js     # 【系统状态】主题切换、响应式布局参数管理
│   │   ├── utils/              
│   │   │   └── tts.js          # 【工具】Web Speech API 语音播报封装
│   │   ├── components/         # 模块化组件（含 Analysis 图表、Home 登录、common 公共件）
│   │   └── views/              # 页面视图（智能解析、发现页、数据中心、管理后台）
│   ├── vite.config.js          # 【构建】Vite 配置：开发代理设置与打包性能优化
│   ├── nginx.conf              # 【网关】Nginx配置
│   └── Dockerfile              # 网页端Dockerfile配置
├── .env                        # 【变量】环境变量：存储 API Keys、数据库路径及邮件服务器私密信息
├── .gitignore                  # 【版本控制】Git 忽略清单，排除敏感配置与临时文件
├── README.md                   # 【文档】项目说明书、技术架构与启动指南
├── TODO.md                     # 【路线图】开发进度跟踪与全功能设想清单
├── database.db                 # 【存储】本地 SQLite 数据库文件
├── requirements.txt            # 【环境】后端 Python 核心依赖库清单
├── admin_original_data.json    # 【预置数据】系统初始化的政务公告测试数据集
├── docker-compose.yml          # Docker-Compose自动部署配置
└── project_tree.md             # 【结构】当前项目最新的目录树记录
```



---

## 技术亮点 (Technical Highlights)

### 1. 声明式智能体协同架构 (Declarative Agentic Workflow)
项目后端并未采用简单的 API 转发，而是构建了一套基于 **LangChain** 的“逻辑自洽”智能体层，重点在于对非结构化文本的深度理解与策略分发。
* **确定性逻辑拆解**：系统通过预设的 Prompt 链条，强制 LLM 在解析前先进行**意图识别**。无论是政务公告、社区通知还是办事指南，智能体都能根据文本特征自动匹配最佳的提取模板，确保“适用对象、材料清单、办理流程”等核心要素的提取具备高度的确定性。
* **思考过程可视化 (CoT Transparency)**：利用大模型的思维链（Chain-of-Thought）技术，系统将 AI 的解析逻辑从“黑盒”转变为“白屏”。用户可以直观查看到智能体是如何从一段长达数千字的原文中，逐步推导出具体办事步骤的。这种**可解释性 AI** 的设计，显著提升了政务解读场景下的用户信任度。

### 2. RAG 增强检索与知识校准 (Retrieval-Augmented Generation)
针对大语言模型在政务领域易产生“幻觉”的痛点，我们引入了工业级的 RAG 生产链路。
* **语义向量化存储**：利用 **ChromaDB** 向量数据库，将官方政务百科、法律法规底稿进行分片并向量化存储。
* **闭环校准算法**：在生成解析卡片前，系统会首先进行**语义相似度检索 (Vector Search)**，提取最相关的官方原文作为 Context。通过将生成结果与原文进行二次交叉验证（Cross-Check），确保每一个办事地点、每一项所需材料都有据可查，从根本上保证了信息的权威性。

### 3. 多模态感知与无障碍交互引擎 (Multimodal & VUI Integration)
我们重新定义了信息的入口，让数字化服务真正触达边缘群体。
* **视觉语义解析 (Visual-to-Semantic)**：不仅是简单的 **OCR** 识字。系统集成了一套图像预处理流水线，能够对复杂的线下公示牌、不规则排版的 APP 截图进行区域定位与噪声消除，随后将提取出的非结构化文本直接喂入 AI 解析引擎，实现了从“像素”到“结构化数据”的一站式转化。
* **全链路语音中枢 (Voice-First Design)**：基于 **Web Audio API** 封装了高灵敏度的语音录入模块，配合后端的语音转文字（ASR）与文本转语音（TTS）技术，构建了完整的声学反馈闭环，为视障用户及习惯口语交互的老年群体提供了尊严感十足的无障碍体验。

### 4. 科学量化的效率评估模型 (Quantitative Efficiency Model)
我们将民生服务的“获得感”进行了数学建模，让提效不再是虚名。
* **基于信息熵的增益计算**：引入了上文提到的 $T_{saved}$ 算法模型。系统不仅统计字符缩减率，更通过加权计算**实体密度 (Entity Density)** 来评估信息获取效率。
* **数据可视化体系**：前端深度定制 **ECharts 5.0** 渲染引擎。通过复杂的 Canvas 绘图实现了红蓝双线动态趋势图、多维度通知难度雷达图。管理员可实时洞察社会化办公效率的波动，通过数据看板辅助决策，锁定政务服务的阻塞点。
#### 核心算法：效率增益模型 (Efficiency Gain Model)

**ClearNotify** 的核心价值在于将非结构化的长文本转化为高密度的结构化卡片。为了量化这一过程带来的“获得感”，我们构建了基于人类阅读速率与信息熵损失的效率评估模型。

##### 1. 节省时间估算算法 (Time-Saving Estimation)
系统通过对比原始文本阅读成本与 AI 结构化卡片阅读成本，实时计算用户的效率增益：

$$
T_{saved} = \max \left( 0, \frac{W_{original}}{V_{human}} - T_{card} \right)
$$

其中：
* $W_{original}$：原始通知的总字符数。
* $V_{human}$：人类常态化阅读与理解政务公文的平均速率（本项目取基准值 $150 \text{ chars/min}$）。
* $T_{card}$：阅读结构化卡片（含适用对象、材料、流程）的平均耗时（经实测收敛于 $1.0 \text{ min}$）。

##### 2. 综合难度评估权重 (Difficulty Assessment Score)
除了单纯的时间维度，我们还引入了**通知复杂度因子 $D$**，用于绘制管理员端的难度雷达图：

$$
D = \alpha \cdot \ln(W_{original}) + \beta \cdot N_{entities} + \gamma \cdot \sigma_{logic}
$$

* **$\alpha, \beta, \gamma$**：权重系数，分别对应文本长度、政务实体数量（如单位、地点）及逻辑复杂嵌套度。
* **$N_{entities}$**：通过智能体提取出的办事材料与步骤的总和。
* **$\sigma_{logic}$**：逻辑紧密度，衡量通知中前置条件与限制条件的关联数量。

##### 3. 全站协同效率指数 (Collective Efficiency Index)
对于管理员而言，我们通过全站数据的积分累加，定义了社会化提效指数 $\mathcal{E}$：

$$
\mathcal{E} = \sum_{i=1}^{n} T_{saved, i} \cdot \omega_{user}
$$

该指数通过 **ECharts 5.0** 渲染为红蓝双线趋势图，直观展现了 **ClearNotify** 在跨越数字鸿沟、提升民生办事效率方面的宏观贡献。
### 5. 高内聚、低耦合的工程化实践 (Engineering Excellence)
* **状态与安全中枢**：前端利用 **Pinia** 实现了复杂的跨页面状态同步（如鉴权状态、UI 主题、持久化设置）；后端则通过 **JWT (JSON Web Token)** 与自定义装饰器构建了严密的安全闸口，实现了 SaaS 级别的多租户数据隔离。
* **自动化运维链路**：项目支持 **Docker** 容器化一键编排，集成了 **Redis** 异步任务队列用于处理大规模的邮件通知（SMTP）分发，确保在高频并发场景下系统的极高稳健性。本项目采用 Docker 容器化技术，通过 Docker Compose 实现一键环境部署，确保了在不同操作系统（Windows/macOS/Linux）下运行环境的高度一致性。




---
## 启动与部署 

### Docker 部署 (推荐)

使用 Docker 可以极大地简化环境配置和项目启动过程。请确保您的系统已安装 Docker 和 Docker Compose。
并在Docker Desktop - Settings - Docker Engine中配置镜像源:
``` json
{
  "builder": {
    "gc": {
      "defaultKeepStorage": "20GB",
      "enabled": true
    }
  },
  "experimental": false,
  "registry-mirrors": [
    "https://docker.xuanyuan.me",
    "https://xuanyuan.cloud",
    "https://mirror.ccs.tencentyun.com",
    "https://docker.1panel.live",
    "https://docker.nju.edu.cn"
  ]
}
```
1.  **配置环境变量**:
    在项目根目录创建 `.env` 文件（如果尚未创建），并根据您的实际情况填写以下环境变量：
    ```
    # 生产环境建议关闭调试模式
    DEBUG=False

    # 必须更换为强随机字符串
    JWT_SECRET_KEY=your_random_secret_string_here

    # 确保 SMTP 授权码正确以维持邮件系统运转
    MAIL_PASSWORD=your_smtp_auth_code

    # 你的KIMI-API_KEY 
    MOONSHOT_API_KEY=your_kimi_api_key

    # 自定义管理员账户 (可选，如果数据库不存在，后台会优先使用这些信息初始化管理员)
    # ADMIN_USERNAME=your_admin_username
    # ADMIN_PASSWORD=your_admin_password
    ```
    **重要提示**: 请务必替换 `JWT_SECRET_KEY`, `MAIL_PASSWORD` 和 `MOONSHOT_API_KEY` 为您自己的值。

2.  **启动服务**:
    在项目根目录执行以下命令：
    ```bash
    docker-compose up --build -d
    ```
    *   `--build`: 首次运行时或当 Dockerfile 有更新时，用于重新构建镜像。
    *   `-d`: 在后台运行服务。

3.  **访问应用**:
    *   前端应用将通过 Nginx 运行在 `http://localhost:80`。
    *   后端 API 将在 Docker 内部运行于 `http://app:8000`，并通过前端 Nginx 代理访问。

4.  **停止服务**:
    在项目根目录执行：
    ```bash
    docker-compose down
    ```

5.  **查看日志**:
    ```bash
    docker-compose logs -f
    ```

### 手动部署 (传统方式)

#### 前端(web):
```shell
cd web
npm install --verbose
npm run dev
```

#### 后端(app)
0. 启动之前:部署好Redis,可采用docker进行部署.
    1. 未安装Redis时: 开启Docker Desktop后,在终端输入: `docker run --name redis -p 6379:6379 -d redis`
    2. 安装后:
    - 停止 Redis： `docker stop redis`
    - 启动 Redis： `docker start redis`
1. 配置环境变量:在根目录创建`.env`,写入:
```
MOONSHOT_API_KEY=你的KIMI-API-KEY
```
2. 创建虚拟环境:
Windows:     ```python -m venv .venv```
macOS/Linux: ```python3 -m venv .venv```

3. 激活虚拟环境:
Windows:     `.venv\Scripts\activate`
macOS/Linux: `source .venv/bin/activate`

4. 安装依赖:
```
pip install -r requirements.txt
```
5. 启动后台服务:
```
uvicorn app.main:app --reload
```
### 打包与部署
1. 安装打包工具:
```
pip install pyinstaller
```
2. 执行打包指令:
Windows:     ```pyinstaller --onefile --noconsole --name ClearNotifyServer --add-data "app/core;app/core" app/main.py```
macOS/Linux: ```pyinstaller --onefile --name ClearNotifyServer --add-data "app/core:app/core" app/main.py```
构建完成后,在`ClearNotify/dist/`生成可执行文件`ClearNotifyServer.exe`（Windows 系统）或`ClearNotifyServer`（Linux/macOS 系统）.
2. 前端生产环境构建：
```shell 
cd web
npm install --verbose
npm run build
```
构建完成后，将在 `web/dist` 目录下生成静态文件 , 可以直接将其部署至 Nginx 的`html/`目录.
**若集成到后端**: 将 `dist` 内的所有内容拷贝至后端项目的静态文件目录，并在 FastAPI 中挂载：
app.mount("/", StaticFiles(directory="dist", html=True), name="static")
3. Docker 一键部署：
```shell
`docker-compose up -d --build`
```
4. 环境与安全:
- 务必检查 .env 文件中的配置，确保生产环境的安全性.
- 打包后的可执行文件需与 .env 文件放在同一目录下运行.
- 生产环境下的跨域由 Nginx 处理，请确保 vite.config.js 中的代理路径与 Nginx 配置一致.
- 使用 Docker 部署时，请确保 `docker-compose.yml` 中已配置 volumes 挂载，以持久化存储数据库文件.
```toml
# 生产环境建议关闭调试模式
DEBUG=False

# 必须更换为强随机字符串
JWT_SECRET_KEY=your_random_secret_string_here

# 确保 SMTP 授权码正确以维持邮件系统运转
MAIL_PASSWORD=your_smtp_auth_code 
```
---

## 开发阶段:代码编写规范
### 后端
- 不同的数据结构和业务逻辑即对应api.routes中不同的文件,绝大多数数据结构都应该创建其XXXBase,XXX,XXXCreate,XXXRead,XXXUpdate五大模型.
- models中存储基础数据结构,包括XXXBase(基础模型)和XXX(数据库模型,包括id);schemas中存储DTO,即后端接口层与前端的通信模型,其中XXXCreate(新增DTO)和XXXRead(响应DTO)需继承自XXXBase,XXXUpdate(修改DTO)的所有字段可选,继承自SQLModel.
- 复杂的业务逻辑(多于100行)需提取为业务函数并寄存在services层中,含有人工智能处理的逻辑应存放在ai层中.
- 所有的全局常量都应该放在core.config.GlobalConfig中.
- 注:数据库不存在时,后台会初始化管理员账户:
```python
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "111111"
```
或者可以在.env中添加以下两句,自定义初始化管理员账户,然后再进行后台启动:
```
ADMIN_USERNAME = slumpyfufu
ADMIN_PASSWORD = 11235813xx
```
### 前端
- 页面布局是模仿[快手](https://www.kuaishou.com/new-reco)搭建的.
- 所有的API路由都注册在router/api_routes.js中的API代理,禁止在其他地方使用非API代理的路由.
- 所有的页面路由都注册在router/index.js中,以实现Modal对于页面的集中管理.
- 组件分配应该按照**主框架-页面-组件**的逻辑进行编排,主框架(Modal)和所有的页面都放在views中,每个页面XXX含有的组件应该存放于components/XXX/之下,根据页面进行组件的划分,其中components/common存放公共常用组件.不同页面的组件可以相互调用.
- 主色调: 红灰配色;整体设计以简约大方红色为主色调,灰色作为点缀和辅助色.
