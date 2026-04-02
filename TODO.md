# TODO
### 客户端UI
### 人力完成(UI)
- [ ] 美化智能体页面Agent回答的markdown,让它看起来不那么诡异:
```md
引入 GitHub 风格样式（最快）
在你的 HTML 中引入 github-markdown-css。

安装：npm install github-markdown-css

包裹：给你的 Markdown 容器加上 markdown-body 这个类名。

HTML
<div class="markdown-body">
  </div>
```

- [ ] 莫兰迪色系数据统计的引入.
- [ ] 响应式布局的实现,争取在移动端适配.
---

### 功能完善
- [ ] 全面调整chat_message的结构化字段,完全放弃无用的结构化通知提取(因为普通AI也能做到),而是转向全面的知识图谱可视化显示,动态标签,动态json,返回的内容完全由LLM决定,并设计 三维知识图谱球+二维知识图谱+矩形文本 这三种可视化方法.
    具体实现思路如下(可以对字段进行必要的补充或者修改):
``` 
1. 模型结构定义 (Pydantic / SQLModel)我们需要将返回内容解构为三层：元数据层、知识图谱层（点边数据）、展示配置层（控制 3D/2D 渲染）。Pythonfrom typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class KGNode(BaseModel):
    """知识图谱节点：支持动态标签"""
    id: str = Field(..., description="唯一标识符")
    label: str = Field(..., description="节点显示名称")
    type: str = Field(..., description="节点类型，如：主体、权益、时间、限制条件")
    importance: float = Field(0.5, description="重要程度 0-1，决定 3D 球体中的节点大小")
    properties: Dict[str, Any] = Field(default_factory=dict, description="LLM 决定的动态属性/标签")

class KGLink(BaseModel):
    """知识图谱边：定义逻辑关系"""
    source: str = Field(..., description="源节点 ID")
    target: str = Field(..., description="目标节点 ID")
    relation: str = Field(..., description="关系描述，如：属于、前置条件、排他关系")
    logic_type: str = Field("positive", description="逻辑性质：positive(正向), negative(约束/冲突)")

class VisualConfig(BaseModel):
    """可视化参数：指导前端渲染引擎"""
    focus_node: Optional[str] = None
    initial_zoom: float = 1.0
    # 文本锚点映射：点击图谱节点后，矩形文本框自动高亮并滚动的索引
    text_mapping: Dict[str, List[int]] = Field(default_factory=dict, description="节点ID对应原文的[start, end]索引")

class ChatMessageBase(BaseModel):
    """重构后的核心响应模型"""
    content: str = Field(..., description="LLM 生成的自然语言简述或经过标记的原文")
    
    # 核心：动态图谱数据
    nodes: List[KGNode] = Field(default_factory=list)
    links: List[KGLink] = Field(default_factory=list)
    
    # 扩展：完全由 LLM 决定的动态 JSON 负载
    # 比如：LLM 认为这个政策有特殊的计算公式，可以直接放在这里
    dynamic_payload: Dict[str, Any] = Field(default_factory=dict)
    
    # 指导前端三维/二维切换的配置
    visual_config: Optional[VisualConfig] = None
2. 后端核心实现思路A. 提示词工程 (Prompt) 的重塑在 analysis_agent.py 中，你需要强制 LLM 输出上述格式。不再问“政策是什么”，而是命令它“构建拓扑”：“请将该政策解析为非线性的知识网络。识别所有权利实体与义务边界，并评估其关联强度。输出必须严格符合 JSON Graph 格式，为重要节点标注 importance。若存在因果逻辑，请在 links 中标记 logic_type。”B. 矩形文本 (Rect-Text) 的关联实现为了实现点击图谱节点、原文高亮的“穿透效果”，后端在生成 text_mapping 时，需要计算节点在 content 字符串中的偏移量。实现技巧：在 content 中使用特定的 HTML 标签或 ID 包裹实体，例如 <span id="node_1">专精特新企业</span>，前端解析 VisualConfig 时直接定位 DOM。3. 前端可视化对接方案在 Vue3 中，你可以根据 ChatMessageBase 返回的数据，同时初始化三个视图：可视化组件技术实现核心逻辑三维图谱球3d-force-graph (Three.js)遍历 nodes，将 importance 映射为 nodeVal。使用球状力导向布局，展示政策的全局复杂度。二维逻辑图antv/g6 或 D3.js渲染 links 中的 logic_type。如果是 negative（约束条件），线段渲染为红色破折号；如果是 positive，渲染为带箭头的实线。矩形文本框Markdown-it + Custom Highlight监听图谱组件的 onNodeClick 事件，获取 text_mapping 中的索引，调用 window.scrollTo 实现联动。 
```
- [ ] 发现页面改编为"全景政策广场",作为系统默认首页，集中展示各方认证主体上传的最新政务文件和惠企政策。将静态国家政策数据改变为真实的认证主体上传的政务文件,结合爬虫获取的时事热点资讯,联合展示.
- [ ] 民意评议大厅页面: 集中展现全过程人民民主的互动版块。将全站用户对各项政策的落地评价、智能解析纠错和办事留言进行公开展示，形成真实透明的社会反馈信息流。认证主体可查询自己提交的所有政策以及用户的民主反馈.
- [ ] 添加更多权限:
    - 管理员: 可以管理普通用户，审核上传的政务文件，回复用户留言等。
    - 认证主体: 可以上传政务文件，查看相关数据分析，但不能管理其他用户。
    - 普通用户: 可以浏览政务文件，参与民意评议，但不能上传文件或管理其他用户。
- [ ] 认证主体专属的数据分析页面: 认证主体可以查看自己上传的政务文件的解析数据分析,如解析数量,用户反馈等.并且可以和所有用户的总体数据进行对比分析.
- [ ] 认证主体专属的政策发布中心页面: 可以上传标准化的政务文件,上传后需要管理员审核通过才能在全景政策广场展示.审核通过后这个文件就会出现在全景政策广场的最新政务文件中,并且会被智能解析和纳入数据分析的统计中.
- [ ] 管理员专属的数据分析页面增加内容:
  - 发布数据追踪:供上传者查看其发布政策的触达效果。展示各项文件的浏览量、被调用解析的频次以及群众的具体反馈评价，帮助发布者了解政策下达的实际穿透率。
  - 民意评议分析:供管理员查看民意评议大厅的整体反馈情况。展示用户对各项政策的评价分布、智能解析纠错的反馈情况以及办事留言的内容分析，帮助管理员把握群众对政策的真实态度和需求。
  - 用户IP地理分布:供管理员查看用户的地理分布情况。展示用户IP地址的可视化分布的可交互可缩放中国地图，帮助管理员了解政策触达的地域覆盖情况。(需要增加用户IP字段)
注: AI在实现上述功能时,不仅可以按照上述功能描述来实现,还可以根据自己的理解和创意进行适当的调整和优化,让界面包含更多内容,只要不违背上述功能的核心需求即可.
### 人力完成(后端)
- [ ] 删除后端遗留的agent逻辑,加入单独的自制的agent插件.
--- 
### 部署问题
- [ ] 解决docker部署条件下无法显示头像的问题.
- [ ] 解决docker不是条件下环境变量未被正确加载的问题(如413解析错误,智能体连接失败等)




