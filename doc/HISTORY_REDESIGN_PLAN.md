# 历史体系全面重构蓝图

## 1. 背景

当前项目里“历史”已经不是单一概念，而是多类业务沉淀的总称：

- 文档可视化解析历史
- 文章浏览历史
- 政策浏览历史
- 政策发布历史
- 智能体对话历史
- 搜索历史
- 收藏历史
- 办事待办演进历史

现状问题不是“没有历史”，而是“每种历史散落在不同表、不同页面、不同交互里，没有统一体系”。

## 2. 当前现状

### 2.1 已存在的历史相关数据

1. 文档解析历史
   - 来源：`ChatMessage`
   - 当前是旧式主线历史。
   - 支持导入、导出、恢复、收藏。
2. 智能体对话历史
   - 来源：`AgentConversation` + `AgentMessage`
   - 与文档解析历史并行存在。
3. 收藏
   - 来源：`Favorite`
   - 仅是单独页面，不是统一历史的一部分。
4. 待办
   - 来源：`TodoItem`
   - 与 `source_chat_id` 有弱关联，但没有进入统一历史。
5. 政策发布记录
   - 来源：`PolicyDocument`
   - 当前有“我的发布”和审核状态，但没有统一发布历史时间线。
6. 民意反馈
   - 来源：`Opinion`
   - 当前是反馈业务，不是历史中心的一部分。

### 2.2 当前缺失的历史

- 文章浏览历史
- 政策浏览历史
- 搜索历史
- 历史事件之间的关联关系
- 面向统一时间线的通用历史读模型

### 2.3 当前 UI 现状

- `web/src/views/History.vue`
  - 只有两种模式：`document` 和 `agent`
  - 仍然不是统一历史中心
- `web/src/views/Home.vue`
  - 首页抽屉只展示“最近解析”
- `web/src/views/Profile.vue`
  - 个人中心只读取一小部分最近解析

结论：

- 现在的“历史”是多套局部历史的拼盘。
- 不是一个可扩展、可搜索、可分析、可回放的统一体系。

## 3. 重构目标

历史重构要达成四个结果：

1. 把所有历史统一为同一套“事件体系”。
2. 保留原有业务表作为领域主表，不强行合并业务表。
3. 提供统一历史中心页面与统一查询接口。
4. 让历史天然接入统一搜索体系。

最终历史中心应能回答：

- 我最近看过什么文章和政策。
- 我最近解析过哪些通知。
- 我最近和 Agent 谈过什么。
- 我最近搜过什么。
- 我发布过哪些政策，经历了哪些审核状态变化。
- 哪些历史可以继续办理、恢复对话、重新打开、再次搜索。

## 4. 设计原则

1. 不把 `ChatMessage` 继续硬扛所有历史。
2. 不把历史等同于“原始业务表”。
3. 历史必须是“事件流”，而不是只看最终状态。
4. 历史必须区分“可恢复对象”和“纯浏览事件”。
5. 历史必须可以被统一搜索。
6. 历史必须支持隐私隔离、去重、归档、导出。

## 5. 推荐总体架构

推荐采用“两层模型”：

1. 领域主表层
   - 继续保留 `ChatMessage`、`AgentConversation`、`PolicyDocument`、`Favorite`、`TodoItem`、`Opinion`
2. 统一历史事件层
   - 新增 `history_event`
   - 必要时新增 `history_snapshot`

这样做的好处：

- 业务功能继续由原表负责。
- 历史中心、统一搜索、分析看板都从统一事件层读取。
- 历史扩展新类型时，不需要反复改 `History.vue` 的硬编码结构。

## 6. 核心数据模型

## 6.1 `history_event`

建议新增统一事件表 `history_event`。

建议字段：

- `id`
- `user_id`
  - 事件归属用户
- `actor_user_id`
  - 触发动作的用户
- `domain`
  - `document_parse`
  - `article_browse`
  - `policy_browse`
  - `policy_publish`
  - `agent_chat`
  - `search`
  - `favorite`
  - `todo`
  - `opinion`
- `event_type`
  - `created`
  - `viewed`
  - `opened`
  - `searched`
  - `clicked`
  - `updated`
  - `approved`
  - `rejected`
  - `restored`
  - `continued`
  - `exported`
  - `imported`
  - `deleted`
- `subject_type`
  - `chat_message`
  - `news_article`
  - `policy_document`
  - `agent_conversation`
  - `search_query`
  - `favorite`
  - `todo`
  - `opinion`
- `subject_id`
- `title`
- `subtitle`
- `summary`
- `content_excerpt`
- `route_path`
- `external_url`
- `cover`
- `status`
- `is_restorable`
- `visibility`
  - `private`
  - `public`
  - `system`
- `dedupe_key`
- `occurred_time`
- `created_time`
- `search_text`
- `extra_json`

说明：

- 历史中心主要读这张表。
- 统一搜索也会把它当重要数据源。

## 6.2 `history_snapshot`

对“可恢复型历史”建议再做一层快照表。

适用对象：

- 文档解析结果
- 智能体对话摘要或会话快照
- 搜索结果快照

建议字段：

- `id`
- `history_event_id`
- `snapshot_type`
- `storage_path`
- `snapshot_json`
- `version`
- `created_time`

说明：

- 不是所有历史都需要快照。
- 浏览历史、点击历史通常只写事件，不写快照。

## 7. 历史类型映射

## 7.1 文档可视化解析历史

来源：

- `ChatMessage`

映射事件：

- `document_parse.created`
- `document_parse.restored`
- `document_parse.exported`
- `document_parse.imported`
- `document_parse.rewritten`
- `document_parse.deleted`

保留原表原因：

- 解析结果本身就是业务主数据。
- 需要恢复、导出、收藏、二次改写。

## 7.2 智能体对话历史

来源：

- `AgentConversation`
- `AgentMessage`

映射事件：

- `agent_chat.created`
- `agent_chat.continued`
- `agent_chat.replied`
- `agent_chat.deleted`

建议：

- 历史中心展示的是“会话级事件”。
- 消息明细仍从原表读取。

## 7.3 文章浏览历史

来源：

- 搜索页打开新闻
- 发现页打开热点
- 其他文章入口

映射事件：

- `article_browse.viewed`
- `article_browse.opened_external`

建议额外记录：

- 来源页面
- 查询词
- 点击位置
- 外链 URL

## 7.4 政策浏览历史

来源：

- 政策广场
- 推荐流
- 搜索结果页
- 发布追踪页

映射事件：

- `policy_browse.viewed`
- `policy_browse.liked`
- `policy_browse.opened`

说明：

- 当前项目已有 `view_count` 和 `like_count`，但没有“某个用户看过哪些政策”的历史。
- 这块是重构必须补上的。

## 7.5 政策发布历史

来源：

- `PolicyDocument`

映射事件：

- `policy_publish.created`
- `policy_publish.updated`
- `policy_publish.submitted`
- `policy_publish.approved`
- `policy_publish.rejected`

说明：

- 当前只有结果状态。
- 缺少“时间线视角”的发布历史。

## 7.6 搜索历史

来源：

- Header 搜索
- 统一搜索页
- 词云点击搜索
- 发现页搜索

映射事件：

- `search.searched`
- `search.result_clicked`
- `search.refined`

说明：

- 搜索历史不只是存关键词。
- 还要记录来源入口、筛选条件、点击对象。

## 7.7 收藏与待办历史

来源：

- `Favorite`
- `TodoItem`

映射事件：

- `favorite.added`
- `favorite.removed`
- `todo.created`
- `todo.confirmed`
- `todo.completed`
- `todo.reopened`

## 8. 去重与沉淀规则

历史不能无脑全记，否则浏览和搜索会爆炸。

建议规则：

1. 浏览历史去重
   - 同一用户、同一对象、同一页面来源，在 5 分钟窗口内合并。
2. 搜索历史去重
   - 同一用户、同一 query、同一过滤条件，在短时间内只保留一次。
3. 对话历史按会话沉淀
   - 不把每一条消息都塞进历史中心主时间线。
   - 主时间线只展示会话级摘要事件。
4. 可恢复对象保留完整快照
   - 解析结果
   - 会话摘要

## 9. 历史中心 UI 重构方案

`/history` 应改造成统一历史中心。

建议顶部筛选：

- 全部
- 办理解析
- 浏览
- 发布
- 对话
- 搜索
- 收藏
- 待办

建议每条历史卡片统一结构：

- 图标
- 标题
- 类型标签
- 时间
- 摘要
- 来源
- 可执行动作

动作示例：

- 继续对话
- 恢复解析
- 打开原文
- 打开政策
- 再次搜索
- 查看审核时间线

## 10. 查询接口建议

建议新增统一历史接口：

- `GET /history/feed`
  - 支持分页、时间筛选、类型筛选、关键字筛选
- `GET /history/{id}`
  - 历史详情
- `GET /history/facets`
  - 返回各类型数量
- `POST /history/backfill`
  - 回填旧数据
- `POST /history/rebuild-index`
  - 重建历史搜索索引

查询参数建议：

- `domain`
- `event_type`
- `subject_type`
- `q`
- `skip`
- `limit`
- `date_from`
- `date_to`

## 11. 写入点位规划

历史写入不能只在页面层做，必须落在后端服务层或路由层。

建议写入点位：

1. 文档解析
   - `app/api/routes/chat_message.py`
   - `app/services/chat_message_service.py`
2. 智能体对话
   - `app/api/routes/agent.py`
   - `app/services/agent_chat_service.py`
3. 政策发布
   - `app/api/routes/policy_document.py`
4. 收藏
   - `app/api/routes/favorite.py`
5. 待办
   - `app/api/routes/todo.py`
6. 搜索
   - 新增统一搜索路由
7. 浏览
   - 前端打开对象时打点到后端

## 12. 与统一搜索的关系

历史重构不能单独做，必须与搜索共用底座。

统一关系：

- `history_event.search_text` 进入统一搜索索引
- Header 搜索可以搜到自己的历史
- 搜索结果点击会反向写入历史

最终形成闭环：

1. 用户搜索
2. 用户点击结果
3. 结果进入浏览历史
4. 历史又可被再次搜索

## 13. 历史事件与向量化时机

历史体系和统一搜索联动时，也必须明确“哪些历史需要向量化、什么时候向量化”。

### 13.1 首次初始化与回填时

当数据库不存在、系统从 `app/resources/db_init/` 导入初始数据时，应同步完成历史事件的初始回填，并对可搜索历史对象建立搜索索引。

建议顺序：

1. 导入种子业务数据
2. 回填 `history_event`
3. 为可搜索历史生成 `search_index_item`
4. 对可搜索历史执行首次向量化

这一步是“首次建库回填”，不是每次启动重跑。

当前已落地：

- `app/services/init_db.py` 在种子数据导入后先执行 `history_service.backfill_core_history(session)`
- 然后执行 `search_index_service.backfill_search_index(session)`
- 因此删库后首启会自动重建历史事件和搜索向量基础层

### 13.2 运行期新增历史时

当用户产生新的历史对象时，应在业务写入成功后同步或异步追加历史事件，并按类型决定是否进入向量索引。

典型场景：

- 新建 `ChatMessage`
  - 生成 `document_parse.created`
  - 同时写入统一搜索索引并向量化
- 导入历史解析
  - 生成 `document_parse.imported`
  - 同时更新搜索索引
- Agent 对话形成新的会话摘要
  - 生成 `agent_chat.continued`
  - 更新该会话的可搜索摘要向量
- 用户搜索
  - 生成 `search.searched`
  - 搜索词进入搜索历史
- 用户点击搜索结果
  - 生成 `search.result_clicked`
- 用户浏览政策
  - 生成 `policy_browse.viewed`
- 用户浏览文章
  - 生成 `article_browse.viewed`

当前已落地的同步增量路径：

- 历史事件通过 `history_service.record_event(..., commit=True)` 写入后，会立即 upsert 到 `search_index_item`
- 新建或审核 `PolicyDocument` 成功后，会立即刷新对应政策索引
- Header 搜索、搜索页点击外链、政策浏览等行为都会继续沉淀为新的历史事件

### 13.3 哪些历史应该向量化

适合向量化的历史：

- 文档解析历史摘要
- 智能体会话摘要
- 搜索历史中的查询词与筛选摘要
- 发布历史中的文档标题、标签、内容摘要
- 有文本内容的收藏备注、待办详情

这些对象有足够文本语义，可以支持模糊搜索。

### 13.4 哪些历史不应逐条向量化

不建议逐条向量化的历史：

- 单纯点击事件
- 单纯打开页面事件
- 高频重复浏览事件
- 没有文本意义的埋点事件

原因：

- 语义弱
- 数量大
- 会污染向量库
- 对搜索质量帮助有限

这类事件应：

- 进入 `history_event`
- 用于时间线、统计与行为分析
- 必要时只生成聚合摘要参与搜索

### 13.5 提交顺序要求

历史事件写入和搜索索引写入都必须以数据库主事务成功为前提。

推荐顺序：

1. 业务对象写库并 `commit`
2. 追加 `history_event`
3. 标记对应搜索索引 dirty 或直接投递增量索引任务
4. 后台 worker 完成向量化

不推荐：

1. 先写向量库
2. 再尝试写业务表

否则会出现历史中心与搜索中心读到不存在对象的问题。

## 14. 迁移与回填策略

## 13.1 可回填的数据

- `ChatMessage`
- `AgentConversation`
- `Favorite`
- `TodoItem`
- `PolicyDocument`
- `Opinion`

## 13.2 不可回填或只能部分回填的数据

- 文章浏览历史
- 政策浏览历史
- 搜索历史

原因：

- 当前没有对应行为日志。
- 只能从新版本开始记录。

## 14.3 回填映射建议

- `ChatMessage.created_time` -> `document_parse.created`
- `AgentConversation.created_time` -> `agent_chat.created`
- `PolicyDocument.created_time` -> `policy_publish.created`
- `PolicyDocument.reviewed_time + status` -> `policy_publish.approved/rejected`
- `Favorite.created_time` -> `favorite.added`
- `TodoItem.created_time` -> `todo.created`

## 15. 分阶段实施建议

### Phase 0

- 完成本文档
- 明确事件模型

### Phase 1

- 新增 `history_event`
- 新增 `history_snapshot`
- 接入 `ChatMessage`
- 接入 `AgentConversation`
- 改造 `/history` 后端查询接口

### Phase 2

- 接入搜索历史
- 接入文章浏览历史
- 接入政策浏览历史
- 接入收藏与待办事件

### Phase 3

- 接入政策发布历史
- 接入审核状态时间线
- 改造 `/history` 前端页面为统一历史中心

### Phase 4

- 统一首页、个人中心、分析页的“最近历史”读取逻辑
- 历史接入统一搜索
- 历史导出与归档

## 16. 风险与注意事项

1. 不要试图删除现有 `ChatMessage` / `AgentConversation` 表来“统一历史”。
   - 那会把业务数据和时间线数据混成一团。
2. 不要把浏览历史全量明细直接塞入主页面。
   - 必须有去重与摘要规则。
3. 不要把历史中心继续写成固定 tab 的前端硬编码。
   - 应由统一事件类型驱动。
4. 不要让搜索历史和浏览历史无权限隔离。
   - 它们天然是强隐私数据。
5. 不要把所有行为事件都丢进向量库。
   - 历史事件表和语义搜索索引不是一回事。
6. 不要在历史对象尚未提交成功前写入搜索索引。
   - 必须保证历史主数据、事件流、搜索索引的一致性。

## 17. 建议新增文件

建议新增：

- `app/models/history_event.py`
- `app/models/history_snapshot.py`
- `app/services/history_service.py`
- `app/api/routes/history.py`

建议重点改造：

- `web/src/views/History.vue`
- `web/src/views/Home.vue`
- `web/src/views/Profile.vue`

## 18. 最终结论

这次历史重构的重点，不是“把历史页面做得更大”，而是把系统中原本分散的行为沉淀统一成事件体系。

正确路线应当是：

1. 保留现有业务表。
2. 新建统一历史事件层。
3. 让所有历史通过统一接口查询。
4. 让统一搜索可以直接搜索历史。

这样做完以后，项目里的“历史”才会从旧式解析记录列表，真正升级为覆盖浏览、搜索、发布、对话、办理沉淀的完整历史系统。

## 0. Current Delivery Status (2026-04-11)

- Landed unified backend history event model and API routes: `/api/history/feed`, `/api/history/facets`, `/api/history/track`.
- Landed unified History page V1 that reads the event stream instead of the old dual-mode page.
- Landed deep-link restore/open flows for chat restore, agent conversation jump, policy document jump, search replay, and external browse jump.
- Landed history tracking for document parsing, agent conversation actions, favorites, todo, policy publish/review/view, explicit search, and several external browse flows.
- Search-facing integration is now using the unified history stream as one of the primary retrieval sources.
- DB initialization and runtime commits now both drive unified search index updates from the history layer, so history and search no longer drift apart after rebuild.
