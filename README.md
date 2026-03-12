# ClearNotify - 民生通知结构化解读和办事助手
> 让每一份复杂通知，都清晰可见.

---

## 软件宗旨
在日常生活中，大众(尤其是老年群众)经常被政务公告、社区通知、学校文件等各种冗长、晦涩的文本包围。由于信息密度大、重点分散，容易导致老年人看不懂、学生容易遗漏关键信息、居民办事往返跑路等问题。

ClearNotify 的宗旨是利用人工智能技术，将这些难读、冗长、零散的文本，自动转化为结构化的办事指南。我们致力于跨越数字鸿沟，让公共信息获取变得零门槛，让办事流程一目了然。

---

## 技术栈
### 项目架构
本项目采用分离式架构,项目技术栈如下：

* **前端 (Client)**:采用**MVVM**(Model-View-ViewModel)设计模式,技术栈包括: Vue3 + Vite + Pinia + ECharts
* **后端 (Server)**: 基于异步分层设计的RESTful**三层架构**(接口层-业务层-DAO层),并添加**智能层**,技术栈包括: FastAPI (Python) + Pydantic + SQLAlchemy
* **数据库 (Database)**: SQLite
* 大语言模型 API (LLM)

### 数据流向
1. 请求流：View (Vue3) 触发事件 -> 调用 Service (Axios) 发起异步请求 -> 后端 Router (FastAPI) 接收并验证参数 (Pydantic)。

2. 处理流：Router 调用业务逻辑层 (Service) -> 业务层异步调用 LLM API -> 获得结果后通过 DAO 层 (SQLAlchemy) 写入数据库 (SQLite)。

3. 反馈流：后端返回标准 JSON 响应 -> 前端 ViewModel 捕获数据并更新 Pinia 仓库 -> View 层利用响应式原理自动重绘界面。

### 项目结构
```shell
.
├── app/                     # 后端应用主目录
│   ├── ai/                  # AI 相关逻辑
│   ├── api/                 # API 接口层
│   │   ├── deps.py          # 依赖注入
│   │   └── routes/          # 路由定义
│   ├── core/                # 核心配置
│   │   ├── config.py        # 全局配置
│   │   ├── database.py      # 数据库连接
│   │   └── security.py      # 安全认证工具
│   ├── models/              # 数据库模型
│   ├── schemas/             # 数据校验模型(Pydantic)
│   ├── services/            # 业务逻辑层
│   └── main.py              # 后台项目入口
├── web/                     # 前端源码目录
│   ├── src/                 # 前端源码
│   │   ├── api/             # API 接口封装
│   │   ├── assets/          # 静态资源
│   │   ├── components/      # 通用组件
│   │   ├── router/          # 路由配置
│   │   │   ├── index.js     # 页面路由
│   │   │   └── api_routes.js # API路由及统一实例
│   │   ├── stores/          # 状态管理 (Pinia)
│   │   ├── utils/           # 工具函数
│   │   ├── views/           # 页面视图
│   │   ├── App.vue          # 根组件
│   │   └── main.js          # 入口文件
│   ├── index.html           # 主HTML文件
│   ├── package.json         # 项目依赖
│   └── vite.config.js       # Vite配置文件
├── doc/
│   └── ClearNotify.openapi.yaml # OpenAPI 文档
├── .env                     # 环境变量配置
├── .gitignore               # Git忽略文件
├── database.db              # SQLite数据库文件
├── README.md                # 项目说明文档
└── requirements.txt         # 后端依赖列表
```
---

## 核心功能
### 主要功能
#### 通知智能解读引擎
输入一段官方通知,输出结构化结果:
* 适用对象
* 办理事项
* 时间/截止时间
* 地点/入口
* 所需材料
* 办理流程
* 注意事项
* 风险提醒
* 官方原文对应位置 (高亮对照)
带有追问功能,基于当前通知上下文的回答.
#### 多版本改写
将同一条通知,自动改写成:
* 学生版
* 老人版
* 家属转述版
* 极简版
* 客服答复版
#### 数据分析可视化
##### 统计与分析模块
* 通知复杂度统计
* 高频材料统计
  - 词云
  - 分类饼图
  - top10柱状图
* 高频风险点统计
* 通知类型分布
* 办理时限分布
##### 时间轴模块
将通知中的流程自动转换为时间轴,可视化展示.
##### 用户节省时间估算
* 前后对比卡片
* 节省时间柱状图
#### 清单生成
基于通知,自动生成:
* 任务卡片
* 办理步骤
* 材料清单
* 截止时间提醒
* 可能遗漏项


### 附属功能
#### 通知难度分级
* 语言复杂度：高 / 中 / 低
* 办理复杂度：高 / 中 / 低
* 风险等级：高 / 中 / 低
评分依据：
* 是否有多个时间节点
* 是否有多个办理对象
* 是否需要多项材料
* 是否有特殊限制条件
* 是否存在容易漏掉的风险项



---

## 技术亮点

- Prompt 链式编排 (Prompt Orchestration)：针对复杂通知，项目未采用单次 Prompt，而是设计了“提取-校验-修正”的链式流。首先提取原文要素，再由 AI 进行自我逻辑核查（如：截止日期是否早于发布日期），显著降低了 AI 幻觉带来的信息错误。

- 双向数据对比高亮技术：利用字符串对齐算法（如 Diff 算法思想），将结构化提取后的核心要素反向映射回原文，实现“原文-结果”实时对照高亮，增强了信息的可信度。

- 适老化 UI 动态映射引擎：基于 Vue3 的响应式系统，开发了一套“语义化 UI 映射”逻辑。系统根据 AI 对通知难度的分级，自动调整界面的视觉复杂度与字体层级，实现“千人千面”的阅读体验。

- 采用Vue Router的<router-view>框架,使用全局Modal容器实现切换页面时不刷新,更加适合老年群众的观感.
---

## 快速启动
### 前端(web):
```shell
cd web
npm i --verbose
npm run dev
```

### 后端(app)
```shell
echo MOONSHOT_API_KEY=你的KIMI-API-KEY > .env
pip install -r requirements.txt
uvicorn main:app --reload
```
注:数据库不存在时,后台会初始化管理员账户:
```python
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "111111"
```
或者可以在.env中添加以下两句,自定义初始化管理员账户,然后再进行后台启动:
```
ADMIN_USERNAME = slumpyfufu
ADMIN_PASSWORD = 11235813xx
```
---

## 开发阶段:代码编写规范
### 后端
- 不同的数据结构和业务逻辑即对应api.routes中不同的文件,绝大多数数据结构都应该创建其XXXBase,XXX,XXXCreate,XXXRead,XXXUpdate五大模型.
- models中存储基础数据结构,包括XXXBase(基础模型)和XXX(数据库模型,包括id);schemas中存储DTO,即后端接口层与前端的通信模型,其中XXXCreate(新增DTO)和XXXRead(响应DTO)需继承自XXXBase,XXXUpdate(修改DTO)的所有字段可选,继承自SQLModel.
- 复杂的业务逻辑(多于100行)需提取为业务函数并寄存在services层中,含有人工智能处理的逻辑应存放在ai层中.
- 所有的全局常量都应该放在core.config.GlobalConfig中.

### 前端
- 页面布局是模仿[快手](https://www.kuaishou.com/new-reco)搭建的.
- 所有的API路由都注册在router/api_routes.js中的API代理,禁止在其他地方使用非API代理的路由.
- 所有的页面路由都注册在router/index.js中,以实现Modal对于页面的集中管理.
- 组件分配应该按照**主框架-页面-组件**的逻辑进行编排,主框架(Modal)和所有的页面都放在views中,每个页面XXX含有的组件应该存放于components/XXX/之下,根据页面进行组件的划分,其中components/common存放公共常用组件.不同页面的组件可以相互调用.
- 主色调: 渐变色 #d4ff80-#00e2dc-#002059 ;整体设计以简约大方白色为主色调,#d4ff80为主题色.