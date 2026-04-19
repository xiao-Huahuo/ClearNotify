# AGENT_TOOLS

## 文档目标

本文件不是“当前已经全部实现的工具清单”，而是基于当前 CloudPolicy 代码现状，对 Agent 下一阶段要补齐的工具体系做统一规划。

这份规划重点解决四件事：

1. 修复 Agent 调用查询类工具时经常返回 0 个结果、但用户看不出原因的问题。
2. 把当前 Agent 从“只能做基础查询 + 轻写入”扩展成“真正能解析文件、图片、历史、搜索、图谱、数据分析”的可执行工作台。
3. 让工具返回的不只是 JSON 文本，还能直接驱动前端小窗可视化，包括知识图谱、表格、图表、地图、时间线、Diff 和证据卡片。
4. 做清晰的权限分层，尤其区分普通用户、认证主体、管理员三种角色的可用工具范围，支持管理员专属数据分析。

---

## 当前现状

### 当前已经落地的 Agent 工具

当前 `app/agent_plugin/agent/tools.py` 已接入的工具有 17 个：

- `query_long_term_memory`
- `parse_local_file`
- `get_my_todos`
- `create_todos_from_chat`
- `confirm_todo`
- `search_policy_documents`
- `recommend_policy_documents`
- `get_user_settings`
- `update_user_settings`
- `search_chat_history`
- `get_chat_message_detail`
- `get_news_digest`
- `search_news_tool`
- `list_favorites`
- `add_favorite`
- `get_my_stats`
- `rewrite_for_audience`

### 当前已经存在但还没有被 Agent 真正接起来的能力

项目当前代码里已经有很多能力可以直接转成 Agent Tool，但还没有接到 `tools.py`：

- 文档上传与解析：`app/api/routes/upload.py`
- Word/Excel 文本提取：`app/services/document_extractor.py`
- PDF 解析与 OCR 回退：`app/ai/document_parser.py`
- 图片/PDF OCR：`app/services/ocr_service.py`
- 全局统一搜索与建议词：`app/api/routes/search.py`、`app/services/search_service.py`
- 历史记录与检索：`app/api/routes/history.py`、`app/services/history_service.py`
- 统计分析：`app/api/routes/stats_analysis.py`、`app/services/stats_service.py`
- 管理员统计、日志、角色、地理分布：`app/api/routes/admin.py`
- 政策文档与审核：`app/api/routes/policy_document.py`
- 民生评论：`app/api/routes/opinion.py`
- 智能体会话历史：`app/api/routes/agent.py`、`app/services/agent_chat_service.py`
- 知识图谱展示组件：`web/src/components/Home/KnowledgeGraphPanel.vue`
- 多种图表组件：`web/src/components/Analysis/*`、`web/src/components/showcase_screen/*`

### 当前明显缺口

从现有代码看，Agent 工具链至少有这些缺口：

- `search_policy_documents` 现在只有分类筛选，没有真正的关键词搜索。
- `search_chat_history` 现在只查 `original_text.contains(query)`，没有把 `handling_matter`、`required_materials`、`risk_warnings`、`chat_analysis`、图谱字段一起纳入检索。
- `parse_local_file` 只支持少量文本后缀，不支持项目真实场景里最重要的 PDF、Word、Excel、图片、扫描件。
- 统一搜索能力已经存在，但还没有作为 Agent Tool 暴露给模型。
- 图谱能力已经存在于解析链路和前端组件里，但还没有“把某条结果以小窗图谱方式弹出”的 Tool 协议。
- 管理员 `rag_search` 当前仍是占位返回空列表，导致管理员视角下的 RAG 检索分析没有真正落地。
- 很多查询工具没有统一返回 `applied_filters`、`total`、`empty_reason`，导致“0 条结果”时无法判断到底是没数据、权限不足、过滤过严，还是工具本身没实现。

---

## 优先修复：查询工具返回 0 个结果

这一条必须先做，不然工具再多，Agent 也会继续给用户“调用了工具但什么都没查到”的错误体验。

### 必须统一的返回规范

所有查询类工具都必须统一返回：

```json
{
  "ok": true,
  "items": [],
  "meta": {
    "query": "高企认定",
    "total": 0,
    "applied_filters": {
      "scope": "current_user",
      "confirmed_only": true,
      "category": null
    },
    "empty_reason": "no_match",
    "fallback_used": false,
    "suggested_tools": ["unified_search_tool", "search_policy_documents_by_query"]
  },
  "display": []
}
```

### 0 结果时必须区分的场景

- `no_match`：确实没有匹配到数据。
- `filter_too_strict`：过滤条件过严，比如 `confirmed_only=true`、时间范围太短、分类太窄。
- `permission_denied`：数据存在，但当前用户角色无权访问。
- `not_implemented`：接口存在但底层仍是占位实现。
- `bad_query`：关键词为空、格式错误、参数类型不合法。
- `data_source_empty`：数据源本身为空，比如当前用户没有历史记录。

### 需要同步加上的诊断能力

- `debug_query_zero_results`
  - 用于返回本次调用的工具名、入参、过滤条件、命中总数、候选数、空结果原因、下一步建议。
- `inspect_agent_runtime`
  - 用于查看当前 `user_id`、角色、模式、会话、可用工具集合，避免工具调用和权限判断错位。
- `get_user_permission_scope`
  - 让 Agent 先知道用户到底有没有管理员权限、认证主体权限，再决定调什么工具。

---

## 总体设计原则

### 1. 工具要分层

后续 Agent Tool 不应只是一层“数据库查询函数”，而要分成三层：

- 数据工具：负责查数据、写数据、解析文档、跑分析。
- 组合工具：把多个底层结果拼成可直接回答用户的问题。
- 展示工具：返回前端可直接消费的小窗展示协议。

### 2. 写操作必须走 Draft + Confirm

所有有副作用的操作都必须支持两段式：

- `draft`
- `confirm`

例如：

- 创建待办
- 审核政策
- 提交评论
- 修改用户角色
- 删除用户

### 3. Tool 返回必须支持前端展示协议

后续所有高价值 Tool 应支持附带 `display` 字段，而不是只返回纯文本。

### 4. 优先复用现有模块，不重新发明业务

优先复用：

- `app/services/*`
- `app/api/routes/*` 对应的业务逻辑
- `app/ai/document_parser.py`
- `app/services/ocr_service.py`
- `app/services/search_service.py`
- `app/services/stats_service.py`
- 现有 Vue 图谱和图表组件

### 5. 不让 Agent 直接依赖路由层

建议继续沿用服务层封装思路，新增：

- `app/services/agent_tool_services/search_tool_service.py`
- `app/services/agent_tool_services/file_tool_service.py`
- `app/services/agent_tool_services/graph_tool_service.py`
- `app/services/agent_tool_services/stats_tool_service.py`
- `app/services/agent_tool_services/admin_tool_service.py`

然后 `tools.py` 只负责 Tool 注册，不直接拼 SQL 和业务。

---

## 统一返回协议

### 查询类工具

```json
{
  "ok": true,
  "items": [],
  "meta": {
    "total": 12,
    "query": "养老补贴",
    "applied_filters": {},
    "empty_reason": null
  },
  "display": []
}
```

### 单对象工具

```json
{
  "ok": true,
  "item": {},
  "meta": {},
  "display": []
}
```

### 变更类工具

```json
{
  "ok": true,
  "item": {},
  "confirm": {
    "required": true,
    "confirmed": false
  },
  "display": []
}
```

### 失败类工具

```json
{
  "ok": false,
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "Admin only"
  }
}
```

### 展示协议

```json
{
  "display": [
    {
      "type": "knowledge_graph",
      "title": "政策结构图谱",
      "placement": "modal",
      "payload": {
        "content": "...",
        "nodes": [],
        "links": [],
        "dynamic_payload": {},
        "visual_config": {}
      }
    }
  ]
}
```

### `display.type` 统一枚举

- `knowledge_graph`
- `original_text`
- `table`
- `metric_board`
- `bar_chart`
- `line_chart`
- `pie_chart`
- `word_cloud`
- `geo_map`
- `timeline`
- `gallery`
- `diff`
- `trace_panel`
- `json_view`

### `display.placement` 统一枚举

- `inline`
- `right_drawer`
- `modal`
- `fullscreen`

---

## 计划增补的 Tool 池

下面这部分是核心。不是一口气全部实现，而是把基于当前软件可落地的 Tool 能力池先定义完整。

## A. 基础诊断与运行时工具

这一组用于先把 Agent 变得“可解释、可诊断”。

- `inspect_agent_runtime`
  - 查看当前 `user_id`、角色、运行模式、会话 ID、可调用工具集合、最近一次工具异常。
- `list_available_tools`
  - 返回当前用户在本轮会话真正可用的工具清单。
- `explain_tool_capability`
  - 根据工具名解释该工具能做什么、需要什么参数、是否有副作用。
- `debug_query_zero_results`
  - 专门诊断查询类工具为什么返回 0 条。
- `get_user_permission_scope`
  - 返回普通用户、认证主体、管理员的当前权限范围。
- `inspect_recent_tool_failures`
  - 返回最近 N 次工具失败摘要，便于前端 trace 面板直接展示。

建议复用来源：

- `app/services/agent_plugin_service.py`
- `app/agent_plugin/agent/agent.py`
- `app/models/user.py`

## B. 文件、图片与多模态解析工具

这一组是最重要的增量之一，直接对应 TODO 里“真正解析文件和图片并展示小窗图谱”的需求。

- `list_user_uploaded_files`
  - 列出当前用户最近上传的文档、OCR 文件、图片、导出快照。
- `get_file_metadata`
  - 返回文件名、大小、类型、上传时间、归属用户、可解析方式。
- `parse_uploaded_document`
  - 对已上传文档执行统一解析，支持 PDF、DOCX、DOC、XLSX、XLS、TXT。
- `parse_uploaded_image_ocr`
  - 对图片执行 OCR，返回提取文本和版面信息。
- `parse_uploaded_pdf_ocr`
  - 对扫描型 PDF 直接执行 OCR 回退解析。
- `parse_uploaded_office_document`
  - 专门处理 Word/Excel，返回结构化段落或表格。
- `parse_message_snapshot_json`
  - 解析历史消息导出的 JSON 快照，恢复图谱与分析字段。
- `extract_document_sections`
  - 把文档拆成标题、段落、表格、附件说明等结构块。
- `extract_document_entities`
  - 提取政策对象、材料、流程、时限、地点、机构、限制条件。
- `extract_document_deadlines`
  - 专门提取时间节点、截止日期、周期要求。
- `extract_document_forms`
  - 识别表格、材料清单、字段项，适合后续做 checklist。
- `analyze_image_layout`
  - 识别图片中的标题块、正文块、印章块、表格区域、公告版式。
- `compare_two_documents`
  - 对两份文档做差异比较，输出新增、删除、变更点。
- `build_document_knowledge_graph`
  - 从文档文本生成图谱结果，输出 `nodes`、`links`、`dynamic_payload`、`visual_config`。
- `get_message_knowledge_graph`
  - 从某条历史解析消息中直接拿图谱数据，而不是重新解析。
- `search_graph_nodes`
  - 在图谱节点里按关键词查找实体、流程、条件、风险节点。
- `get_text_mapping_segments`
  - 返回图谱节点与原文映射片段，用于点击节点高亮原文。
- `preview_original_text_segment`
  - 返回原文指定区间的小窗预览，支持定位到某节点对应文本。
- `generate_graph_focus_card`
  - 围绕某个节点生成聚焦图谱卡片，适合小窗展示。
- `generate_document_reader_card`
  - 把结构化原文以小窗阅读器方式返回。

建议复用来源：

- `app/api/routes/upload.py`
- `app/services/document_extractor.py`
- `app/services/ocr_service.py`
- `app/ai/document_parser.py`
- `app/services/chat_message_service.py`
- `web/src/components/Home/KnowledgeGraphPanel.vue`

## C. 搜索与检索工具

这一组用于把当前软件已经存在的全站搜索能力真正接给 Agent。

- `unified_search_tool`
  - 调用现有统一搜索，跨 `history / agent / policy / news` 混合检索。
- `search_suggestions_tool`
  - 返回联想词、最近搜索、快速入口、语义建议。
- `get_suggestion_index_tool`
  - 获取系统的搜索候选索引，用于“你可以搜这些内容”。
- `search_policy_documents_by_query`
  - 真正的政策关键词搜索，而不是只有分类筛选。
- `search_policy_documents_by_category`
  - 分类检索政策文档。
- `get_policy_document_detail`
  - 获取某一篇政策文档详情。
- `recommend_policy_documents_for_me`
  - 按职业/偏好推荐政策文档。
- `search_chat_messages_fulltext`
  - 对历史解析消息做全文搜索，覆盖原文、结构字段、图谱字段。
- `search_agent_conversations`
  - 检索智能体会话标题和消息内容。
- `get_agent_conversation_messages`
  - 获取会话消息明细。
- `search_history_feed`
  - 搜索历史事件流。
- `get_history_facets_tool`
  - 返回历史分类聚合，便于 Agent 推荐下一步范围缩小。
- `search_news_advanced`
  - 按关键词、数量、来源检索新闻。
- `get_news_digest_tool`
  - 获取政务热点日报。
- `get_hot_news_tool`
  - 获取热点新闻列表。
- `get_central_docs_tool`
  - 获取中央文件列表。
- `get_hot_keywords_tool`
  - 获取热词，用于趋势回答。
- `search_long_term_memory_tool`
  - 查询当前用户长时记忆。
- `search_global_knowledge_tool`
  - 查询全局知识库，不只查用户私有记忆。

建议复用来源：

- `app/api/routes/search.py`
- `app/services/search_service.py`
- `app/services/search_index_service.py`
- `app/services/history_service.py`
- `app/services/news_crawler.py`
- `app/agent_plugin/agent/memory.py`

## D. 个人工作台工具

这一组是普通用户最常用的执行型 Tool。

- `get_my_todos`
  - 当前已有，保留。
- `create_todos_from_chat`
  - 当前已有，保留。
- `confirm_todo`
  - 当前已有，保留。
- `complete_todo`
  - 把待办标记为已完成。
- `reopen_todo`
  - 重新打开待办。
- `delete_todo`
  - 删除待办，需确认。
- `batch_confirm_todos`
  - 批量确认 AI 草稿待办。
- `get_user_settings`
  - 当前已有，保留。
- `update_user_settings`
  - 当前已有，保留。
- `list_favorites`
  - 当前已有，保留。
- `add_favorite`
  - 当前已有，保留。
- `remove_favorite`
  - 删除收藏。
- `rewrite_for_audience`
  - 当前已有，保留。
- `get_recent_history`
  - 返回最近历史行为，便于“继续上次工作”。
- `get_history_facets`
  - 返回个人历史的分类聚合。
- `save_chat_snapshot`
  - 将当前解析/会话结果保存为快照。
- `get_chat_snapshot_path`
  - 返回快照文件路径与导出信息。
- `restore_message_from_snapshot`
  - 从快照恢复消息内容。

建议复用来源：

- `app/models/todo.py`
- `app/models/settings.py`
- `app/models/favorite.py`
- `app/services/chat_message_service.py`
- `app/api/routes/history.py`
- `app/services/history_service.py`

## E. 政策文档与民意评论工具

这一组面向认证主体和管理员，也支持普通用户查询公共信息。

- `create_policy_document_draft`
  - 生成政策文档发布草稿，不直接提交。
- `submit_policy_document`
  - 正式提交政策文档，需认证主体或管理员权限。
- `list_my_policy_documents`
  - 查询我上传的政策文档。
- `list_pending_policy_documents`
  - 查询待审核政策文档，管理员专用。
- `review_policy_document`
  - 审核通过/驳回政策文档，管理员专用，必须二次确认。
- `increment_policy_view`
  - 记录浏览动作。
- `like_policy_document`
  - 点赞政策文档。
- `get_my_policy_document_stats`
  - 获取我上传文档的浏览、点赞、评分、评论统计。
- `list_document_opinions`
  - 查询某篇政策的评论列表。
- `get_public_opinion_feed`
  - 获取全站评论流。
- `list_my_document_opinions`
  - 查询我名下政策收到的评论。
- `create_opinion_draft`
  - 先生成评论草稿。
- `submit_opinion`
  - 正式提交评论。
- `like_opinion`
  - 点赞评论。

建议复用来源：

- `app/api/routes/policy_document.py`
- `app/api/routes/opinion.py`
- `app/models/policy_document.py`
- `app/models/opinion.py`

## F. 数据分析与结果可视化工具

这一组直接对应 TODO 里“数据分析结果”的要求，而且要支持 Agent 不只答文本，而是弹图表。

- `get_my_stats`
  - 当前已有，保留。
- `get_my_rag_metrics`
  - 只返回 RAG 命中、均分、空结果率。
- `get_my_rag_series`
  - 返回时序 RAG 曲线。
- `get_my_materials_freq`
  - 返回高频材料词统计。
- `get_my_risks_freq`
  - 返回高频风险词统计。
- `get_my_complexity_distribution`
  - 返回复杂度分布。
- `get_my_notice_type_distribution`
  - 返回通知类型分布。
- `get_my_time_saved_report`
  - 返回累计节省时间、平均节省时间、分布图数据。
- `get_my_vector_scatter`
  - 返回散点数据，用于显示文本长度、难度、材料复杂度。
- `compare_my_analysis_periods`
  - 比较两个时间窗口内的解析量、风险、材料变化。
- `get_showcase_landing_stats`
  - 获取展示首页摘要统计。
- `get_showcase_screen_data`
  - 获取大屏数据。
- `build_metric_cards`
  - 把统计结果转成指标卡显示。
- `build_wordcloud_card`
  - 把词频结果转成词云显示。
- `build_bar_chart_card`
  - 生成柱状图展示协议。
- `build_line_chart_card`
  - 生成折线图展示协议。
- `build_pie_chart_card`
  - 生成饼图展示协议。
- `build_map_chart_card`
  - 生成地理分布地图展示协议。
- `build_timeline_card`
  - 生成时间线卡片。
- `build_table_card`
  - 生成表格展示卡片。

建议复用来源：

- `app/api/routes/stats_analysis.py`
- `app/api/routes/showcase.py`
- `app/services/stats_service.py`
- `web/src/components/Analysis/*`
- `web/src/components/showcase_screen/*`

## G. 管理员专属分析与治理工具

这一组是必须单独做权限隔离的重点。

- `list_users_admin`
  - 列用户清单。
- `get_user_detail_admin`
  - 查看单用户详情、角色、最近活跃、头像、最近统计。
- `get_admin_stats`
  - 获取后台总量统计。
- `get_all_users_analysis`
  - 获取全站分析数据。
- `get_user_analysis_admin`
  - 获取某个指定用户的解析分析结果。
- `compare_users_admin`
  - 对两个或多个用户做对比分析。
- `get_admin_user_geo`
  - 获取用户地理分布。
- `get_admin_opinion_stats`
  - 获取评论统计、评分分布、热词。
- `get_admin_user_role_distribution`
  - 获取用户角色分布。
- `get_admin_logs`
  - 获取日志摘要。
- `get_rag_status_admin`
  - 查看 RAG 状态。
- `rag_search_admin`
  - 真正实现管理员 RAG 搜索，而不是占位空结果。
- `set_user_role_draft`
  - 生成角色调整草稿。
- `set_user_role_apply`
  - 正式修改角色，必须确认。
- `toggle_admin_draft`
  - 生成管理员开关操作草稿。
- `toggle_admin_apply`
  - 正式执行管理员开关。
- `delete_user_draft`
  - 生成删用户草稿。
- `delete_user_apply`
  - 正式删除用户，必须确认。
- `get_user_avatar_admin`
  - 查询指定用户头像。
- `get_recent_tool_failures_admin`
  - 返回近期工具失败统计，便于管理员排障。

建议复用来源：

- `app/api/routes/admin.py`
- `app/models/user.py`
- `app/services/stats_service.py`

## H. 展示型 Tool / UI Slot Tool

这一组不是去查数据，而是把已有数据包装成前端可直接显示的小窗。

- `show_knowledge_graph_modal`
  - 弹出知识图谱小窗。
- `show_original_text_mapping_modal`
  - 弹出原文高亮映射小窗。
- `show_chart_modal`
  - 弹出通用图表小窗。
- `show_table_modal`
  - 弹出表格小窗。
- `show_metric_board_modal`
  - 弹出指标卡小窗。
- `show_map_modal`
  - 弹出地图小窗。
- `show_gallery_modal`
  - 弹出图片/新闻图集小窗。
- `show_diff_modal`
  - 弹出文档差异小窗。
- `show_trace_panel_card`
  - 在侧边面板显示本轮工具链路、过滤条件、命中数、空结果原因。

注意：

- 这组 Tool 不直接操作 DOM。
- 它们只返回 `display` 协议。
- 前端据此决定在 `modal`、`right_drawer`、`fullscreen` 中如何渲染。

---

## 前端展示协议建议

### 1. 知识图谱展示协议

应尽量直接兼容 `web/src/components/Home/KnowledgeGraphPanel.vue` 的现有入参：

```json
{
  "type": "knowledge_graph",
  "title": "高企认定政策图谱",
  "placement": "modal",
  "payload": {
    "content": "......",
    "nodes": [],
    "links": [],
    "dynamic_payload": {},
    "visual_config": {
      "focus_node": "node_1",
      "initial_zoom": 1.0,
      "text_mapping": {}
    }
  }
}
```

### 2. 图表展示协议

建议统一成：

```json
{
  "type": "bar_chart",
  "title": "我的高频材料",
  "placement": "right_drawer",
  "payload": {
    "chart_lib": "echarts",
    "option": {}
  }
}
```

### 3. 表格展示协议

```json
{
  "type": "table",
  "title": "命中文档列表",
  "placement": "modal",
  "payload": {
    "columns": [],
    "rows": []
  }
}
```

### 4. 地图展示协议

地图数据建议直接复用现有 `geo_dist` 结构：

```json
{
  "type": "geo_map",
  "title": "用户地域分布",
  "placement": "modal",
  "payload": {
    "geo_dist": [
      { "name": "广东", "value": 12 }
    ]
  }
}
```

---

## 权限矩阵

### 普通用户

可用：

- 文件解析
- OCR
- 统一搜索
- 我的历史
- 我的待办
- 我的收藏
- 我的统计
- 公共政策查询
- 公共评论查询

不可用：

- 审核政策
- 用户管理
- 日志读取
- 全站统计
- 角色变更

### 认证主体

在普通用户基础上新增：

- 提交政策文档
- 查看我的政策文档
- 查看我的政策反馈与统计
- 查看我名下政策评论

### 管理员

在前两者基础上新增：

- 待审核政策列表
- 审核政策
- 全站统计
- 全站用户分析
- 用户地理分布
- 用户角色分布
- 评论统计
- 日志查看
- RAG 状态与真实检索
- 用户角色修改
- 用户删除

---

## 命名建议

建议统一按前缀分组：

- `agent_*`
- `file_*`
- `ocr_*`
- `graph_*`
- `search_*`
- `history_*`
- `todo_*`
- `favorite_*`
- `settings_*`
- `policy_*`
- `opinion_*`
- `stats_*`
- `admin_*`
- `ui_*`

不要再继续使用模糊命名。工具名必须一眼能看懂是“查什么 / 做什么 / 给谁用”。

---

## 建议落地顺序

## P0

先解决体验断层，优先落这些：

- `debug_query_zero_results`
- `inspect_agent_runtime`
- `get_user_permission_scope`
- `unified_search_tool`
- `search_chat_messages_fulltext`
- `search_policy_documents_by_query`
- `parse_uploaded_document`
- `parse_uploaded_image_ocr`
- `build_document_knowledge_graph`
- `get_message_knowledge_graph`
- `show_knowledge_graph_modal`
- `show_trace_panel_card`
- `get_my_stats`
- `build_metric_cards`

## P1

补齐高频业务闭环：

- `list_user_uploaded_files`
- `compare_two_documents`
- `search_agent_conversations`
- `get_agent_conversation_messages`
- `complete_todo`
- `remove_favorite`
- `get_my_policy_document_stats`
- `list_document_opinions`
- `build_wordcloud_card`
- `build_map_chart_card`

## P2

补齐管理员与治理能力：

- `get_all_users_analysis`
- `get_user_analysis_admin`
- `compare_users_admin`
- `get_admin_logs`
- `rag_search_admin`
- `set_user_role_*`
- `toggle_admin_*`
- `delete_user_*`

---

## 实施注意事项

- 现有 `tools.py` 已经偏长，后续不要继续把所有 Tool 直接堆在一个文件里。
- 查询工具必须统一带上 `meta.total`、`meta.applied_filters`、`meta.empty_reason`。
- 任何工具如果返回 0 个结果，前端 trace 面板必须能看出“为什么是 0”。
- 图谱类 Tool 的返回应尽量复用现有 `KnowledgeGraphPanel.vue` 数据结构。
- 图表类 Tool 应尽量复用现有 ECharts 组件，不要新造一套渲染协议。
- 管理员写操作必须走 `draft + confirm`，不能让 Agent 一步到位直接改角色或删用户。
- `rag_search_admin` 不能再返回占位空数组，必须真实实现，否则管理员分析链路会持续失真。

---

## 本文档结论

基于当前代码现状，CloudPolicy 并不缺“可转成 Agent Tool 的底层能力”，真正缺的是三件事：

1. 缺一个统一的 Tool 体系设计，把现有上传、搜索、图谱、统计、管理能力接起来。
2. 缺查询结果的可诊断协议，导致 0 结果时 Agent 和用户都不知道问题出在哪里。
3. 缺展示型 Tool 协议，导致 Agent 即便拿到了图谱和分析结果，也只能把它们压成一段文本，而不能以小窗图谱、图表、地图、表格的方式展示出来。

所以下一步不是继续零散加几个函数，而是按本文件把 Tool 体系拆成：

- 基础诊断
- 文件/图片解析
- 搜索检索
- 个人工作台
- 政策与评论
- 数据分析
- 管理员治理
- 展示型 Tool

这样后续增补才是“基于现在整个软件的能力扩展”，而不是给 Agent 再塞几条孤立函数。
