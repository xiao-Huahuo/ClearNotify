# 云枢观策 - 新质生产力驱动下的基层减负与政务共享平台
> 让每一份政务通知，都清晰可见;让每一个办事流程，都触手可及.

## 软件宗旨 (Project Mission)
云枢观策是一个集政务文件云端共享、人工智能结构化解读与全民参与反馈于一体的综合性办事与调研平台。我们致力于改变传统政务信息单向下发且冗长复杂的现状，通过打造“多方上传-智能提取-公开评议”的完整功能机制，解决不同社会群体在获取和执行公共政策时面临的实际困难。老年群体不再因无法提取关键要素而面临办事阻碍；学生与职场人员不再遗漏繁杂通知中的截止日期和所需材料；普通居民也能彻底避免因政策理解偏差导致的多次往返跑现象。

本平台致力于通过先进的人工智能技术与多边参与机制，构建一个全场景的政务信息流转生态与办事辅助平台。本项目的核心宗旨在于重塑政务信息的产生、传递与消费链路，建立完整的"**共享-解读-反馈-民主**"社会交互流程：

1. **形成云端政策共享广场** 平台彻底打破传统自上而下的单向信息发布壁垒，允许各方主体在完成身份认证后，主动将获取到的政务文件、惠企政策和社区通知上传至云端进行全站共享，建立开放透明的政策数据矩阵。

2. **利用新质生产力智能体解读政策** 面对云端海量的复杂公文，平台调用基于大型语言模型和 RAG 检索增强生成的 Agent 智能体。这些代表新质生产力的技术引擎能够瞬间剥离冗余信息，将长篇大论自动解析为通俗易懂的办理条件、流程清单和风险提示卡片。

3. **构建反馈机制并在广场展示民意调研** 用户在浏览解析后的政策卡片时，不仅可以获取办事指南，还可以直接针对政策的落地情况、解析的准确度进行评价、留言与纠错。这些交互数据会实时汇聚并在全民政策广场中公开展示，形成真实的民意反馈流。

4. **推动全过程人民民主落地** 通过政策的无死角公开、智能技术的赋权以及公众意见的透明化展示，平台让每一位普通用户和企业主体都能平等地参与到政策的讨论与传播中，切实保障公众的知情权、表达权与监督权，利用数字化手段推动全过程人民民主在基层社会治理中的真实落地。

---

## 核心功能详解
#### 认证主体上传与政务文件云端共享广场
这是本平台流转生态的首要环节。系统设计了一套严格的多级身份认证机制，政府职能部门、企事业单位以及经过实名的基层网格员都可以申请成为认证发布者。认证通过后，这些节点可以直接将最新出台的红头文件、行业补贴规范或社区办事指南上传至平台。系统会自动接收这些文件，并将其展示在全站公开的政策广场中。普通用户进入平台后，可以像浏览新闻信息流一样，自由刷取、检索和订阅这些最新政策。这种模式将单向的官方发布转化为多源头的群众共建，确保了政策覆盖的广度和信息下达的时效性。

#### 智能解读引擎与信息结构化处理
系统内置了基于 LangChain 架构的分析智能体，负责对用户或企业上传的长篇复杂公文进行深度逻辑拆解。在处理数千字的文本时，系统会同步启动检索增强生成机制。它会自动连接到后端的 ChromaDB 向量数据库，在海量的法律法规底稿和官方政务百科中进行语义检索，提取最相关的官方原文作为上下文背景，从而防止大语言模型在生成办事流程时出现编造和幻觉。在生成结果的同时，系统会将人工智能的思考过程完全透明化展示，用户可以清楚地看到系统是依据原文的哪一段落推导出了具体的材料清单。此外，系统还会根据不同用户群体的阅读习惯，将解析结果动态重构为关怀模式、极简模式等不同版本，确保信息的精准传达。

#### 通知办理智能体执行闭环
在基础的结构化解析之上，平台提供了一个专属的通知办理智能体作为完整的执行层。该智能体的主要职责是将静态的通知内容转化为可直接执行的动态待办清单。当它接收到解析请求后，会输出一份包含严密逻辑的数据包，其中包括明确的办理事项名称、具体的适用对象范围、必备的材料清单、详细的办理流程步骤、潜在的注意事项以及风险提示。同时，它还会提供每一项要求的证据链片段和置信度评分，并在后台通过对应的接口进行交互展示，帮助用户建立清晰的时间线和办事预期，实现从看懂政策到实际去办的无缝衔接。

#### 多模态感知信息录入中枢
为了最大程度降低平台的使用门槛，系统集成了多模态感知系统，提供了超越传统文本框的交互方式。在视觉信息提取方面，平台内嵌了图像处理和 OCR 识别引擎。用户在路边看到的纸质布告栏，或者在其他政务应用中截取的复杂排版图片，都可以直接上传。系统会自动定位图片中的有效信息区域、消除噪声，并将提取出的文字直接送入智能体进行解析。在语音交互方面，系统利用网页音频接口开发了实时语音录入模块。不方便打字的老年人或视障人士可以直接口述他们想要了解的政策问题，系统处理完毕后，会调用文本转语音引擎，将结构化的办事步骤用清晰的语音直接播报出来，实现了全程无障碍的政务查询体验。

#### 数据价值量化与效能可视化面板
平台不仅提供办事指南，还通过科学的算法对系统带来的效率提升进行严格的量化评估。系统内置了时间收益算法模型，每次解析完成后，系统会对比原始政务公文的字数、逻辑复杂度与系统生成的极简卡片的阅读成本。通过一套包含文本长度、实体密度和逻辑紧密度的计算公式，系统可以精准推算出用户节省的具体分钟数。这些数据会被实时汇总到管理员端的效能看板中。看板采用 ECharts 5.0 引擎渲染，以动态红蓝双线对比图的形式展示个人与全站用户的效率提升总和。同时，系统还会抓取高频出现的申报材料生成词云，并利用雷达图评估各类通知的处理难度，为上级部门优化政务办事流程提供直观的数据支撑。

#### 资讯沉淀与系统辅助特性
用户在政策广场中解析过的所有办事指南和政策卡片，都可以一键收藏并存入个人的离线百科库中。即使在信号覆盖不佳的政务大厅，用户依然可以随时调出所需的材料清单。系统底层接入了真实的邮件传输协议，搭建了完善的用户与管理员通信桥梁，用于处理权限申请审核和系统周报推送。在视觉呈现上，系统采用红灰为主的配色方案，支持界面级别的明暗模式切换，保障用户在不同光线环境下的阅读舒适度。

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
CloudPolicy/
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
│   ├── requirements.txt        # 【环境】后端 Python 核心依赖库清单
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
├── admin_original_data.json    # 【预置数据】系统初始化的政务公告测试数据集
├── docker-compose.yml          # Docker-Compose自动部署配置
└── project_tree.md             # 【结构】当前项目最新的目录树记录
```



---

## 技术亮点 (Technical Highlights)

### 1. 声明式智能体协同架构 (Declarative Agentic Workflow)
项目后端并未采用简单的 API 转发，而是构建了一套基于 **LangChain** 的“逻辑自洽”智能体层，重点在于对非结构化文本的深度理解与策略分发。
* **确定性逻辑拆解**：系统通过预设的 Prompt 链条，强制 LLM 在解析前先进行**意图识别**。无论是政务公告、社区通知还是办事指南，智能体都能根据文本特征自动匹配最佳的提取模板，借用**Function Calling**的json格式化,确保“适用对象、材料清单、办理流程”等核心要素的提取具备高度的确定性。
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

**云枢观策** 的核心价值在于将非结构化的长文本转化为高密度的结构化卡片。为了量化这一过程带来的“获得感”，我们构建了基于人类阅读速率与信息熵损失的效率评估模型。

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

该指数通过 **ECharts 5.0** 渲染为红蓝双线趋势图，直观展现了 **云枢观策** 在跨越数字鸿沟、提升民生办事效率方面的宏观贡献。
### 5. 高内聚、低耦合的工程化实践 (Engineering Excellence)
* **状态与安全中枢**：前端利用 **Pinia** 实现了复杂的跨页面状态同步（如鉴权状态、UI 主题、持久化设置）；后端则通过 **JWT (JSON Web Token)** 与自定义装饰器构建了严密的安全闸口，实现了 SaaS 级别的多租户数据隔离。
* **自动化运维链路**：项目支持 **Docker** 容器化一键编排，集成了 **Redis** 异步任务队列用于处理大规模的邮件通知（SMTP）分发，确保在高频并发场景下系统的极高稳健性。本项目采用 Docker 容器化技术，通过 Docker Compose 实现一键环境部署，确保了在不同操作系统（Windows/macOS/Linux）下运行环境的高度一致性。




---
## 启动与部署

### .env 环境变量（请在项目根目录创建）
以下为**所有可配置字段**的模板，按需填写即可：
```env
# 基础服务配置
HOST=127.0.0.1
PORT=8080
SECRET_KEY=your_random_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_DAYS=30

# 默认管理员初始化（可选）
ADMIN_USERNAME=admin
ADMIN_PASSWORD=111111
ADMIN_EMAIL=admin@example.com
ADMIN_PHONE=your_phone

# SMTP 邮件系统（真实发信需配置）
SMTP_HOST=smtp.example.com
SMTP_PORT=465
SMTP_USERNAME=your_smtp_user
SMTP_PASSWORD=your_smtp_password
SMTP_SENDER=your_sender@example.com
SMTP_SENDER_NAME=CloudPolicy
SMTP_USE_SSL=true
SMTP_USE_TLS=false

# 邮箱验证与前后端回跳
EMAIL_VERIFICATION_CODE_LENGTH=6
EMAIL_VERIFICATION_EXPIRE_MINUTES=15
PUBLIC_BASE_URL=http://127.0.0.1:8080
FRONTEND_BASE_URL=http://127.0.0.1:5173

# Redis/任务队列
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB_CACHE=0
REDIS_DB_QUEUE=1
REDIS_QUEUE_NAME=crawler_tasks

# 爬虫限流
CRAWLER_RATE_LIMIT=30
CRAWLER_RATE_WINDOW_SECONDS=60

# 模型密钥（如需）
LLM_API_KEY=sk-xxxxx
LLM_BASE_URL=https://api.moonshot.cn/v1
LLM_TIMEOUT=60
LLM_MODEL=moonshot-v1-8k
LLM_TEMPERATURE=0
```
说明：未配置 SMTP 时系统会自动将邮件写入 `mail_outbox` 目录供本地预览。


### 运行

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
1. 配置环境变量:在根目录创建`.env`,写入上面所要求的环境变量字段.
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
### 构建
1. 安装打包工具:
```
pip install pyinstaller
```
2. 执行打包指令:
Windows:     ```pyinstaller --onefile --noconsole --name CloudPolicyServer --add-data "app/core;app/core" app/main.py```
macOS/Linux: ```pyinstaller --onefile --name CloudPolicyServer --add-data "app/core:app/core" app/main.py```
构建完成后,在`CloudPolicy/dist/`生成可执行文件`CloudPolicyServer.exe`（Windows 系统）或`CloudPolicyServer`（Linux/macOS 系统）.
3. 前端生产环境构建：
```shell 
cd web
npm install --verbose
npm run build
```
构建完成后，将在 `web/dist` 目录下生成静态文件 , 可以直接将其部署至 Nginx 的`html/`目录.
**若集成到后端**: 将 `dist` 内的所有内容拷贝至后端项目的静态文件目录，并在 FastAPI 中挂载：
app.mount("/", StaticFiles(directory="dist", html=True), name="static")

---

### Docker 部署 

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
    "https://dockerproxy.com",
    "https://docker.nju.edu.cn",
    "https://docker.mirrors.sjtug.sjtu.edu.cn",
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com",
    "https://docker.xuanyuan.me",
    "https://xuanyuan.cloud",
    "https://mirror.ccs.tencentyun.com",
    "https://docker.1panel.live",
    "https://docker.nju.edu.cn"
  ]
}
```
必要时可以手动安装所需镜像:
![Docker-Images](doc/assets/Docker-Images.png)
拉取指令:
```shell
docker pull redis:latest
docker pull node:16-alpine
docker pull nginx:stable-alpine
docker pull python:3.12-slim-bullseye
```
1.  **启动服务**:
    在项目根目录执行以下命令：
    ```bash
    docker-compose up --build -d
    ```
    *   `--build`: 首次运行时或当 Dockerfile 有更新时，用于重新构建镜像。
    *   `-d`: 在后台运行服务。

2. **访问应用**:
    *   前端应用将通过 Nginx 运行在 `http://localhost:80`。
    *   后端 API 将在 Docker 内部运行于 `http://app:8080`，并通过前端 Nginx 代理访问。
    *   也可以打开Docker Desktop找到CloudPolicy容器,即可运行,点击web的链接即可打开网页.
3. **停止服务**:
    在项目根目录执行：
    ```bash
    docker-compose down
    ```
    **再次启动服务**:
   在项目根目录执行:
    ```bash
    docker-compose up
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
