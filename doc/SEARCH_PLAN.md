# 全局搜索与 Header 智能搜索改造方案

## 1. 目标

本方案解决三个问题：

1. 让 `Header` 顶部搜索框从“跳转到搜索页的普通输入框”升级为“可即时联想、可下拉选择、可搜一切”的全局搜索入口。
2. 让搜索范围不再局限于“新闻 + 中央文件”，而是覆盖文章、政策、个人历史、智能体对话、收藏、待办、政策发布记录等。
3. 让搜索从纯字符串包含匹配升级为“Trie 前缀召回 + 关键词召回 + RAG 语义模糊召回”的混合搜索。

用户侧最终体验：

- 在 Header 中输入任意关键词，立刻出现下拉栏。
- 下拉栏同时给出前缀联想、最近搜索、热门词、跨类型结果预览。
- 回车或点击“查看更多”进入统一搜索页。
- 搜索结果页按类型聚合展示，并支持筛选“文章 / 政策 / 我的历史 / 对话 / 收藏 / 待办 / 发布记录”。

## 2. 当前现状

### 2.1 前端现状

- `web/src/components/common/Header.vue`
  - 当前只是一个输入框。
  - 行为只有 `handleSearch()`，输入后跳转 `/search?q=...`。
  - 没有 Trie、没有下拉栏、没有即时联想、没有键盘导航。
- `web/src/views/Search.vue`
  - 当前搜索页只调用 `searchNews(q, limit)`。
  - 结果类型只有 `news` 和 `policy`，而且这里的 `policy` 其实是中央文件 RSS，不是站内 `PolicyDocument`。
- `web/src/views/DiscoveryHome.vue`
  - 已有一个“伪前缀搜索”体验。
  - 本质是调 `/news/search` 后，把标题前缀命中的结果排前面，不是真正的 Trie。

### 2.2 后端现状

- `app/api/routes/news.py`
  - `/news/search` 只搜索热点新闻和中央文件。
- `app/services/news_crawler.py`
  - `search_news()` 本质是 `title/description` 的字符串包含匹配。
  - 无向量召回，无站内多源聚合。
- `app/api/routes/policy_document.py`
  - 只有已审核列表、我的发布、推荐等接口。
  - 没有“按关键词全文搜索站内政策文档”的统一入口。
- `app/services/chat_message_service.py`
  - `get_rag_context_for_message()` 目前直接返回空数组，说明解析历史还没有真正接入 RAG 检索能力。
- `app/api/routes/admin.py`
  - `/admin/rag/search` 当前直接返回空结果，是一个 stub。

### 2.3 现有可复用的 RAG 基座

- `app/services/agent_plugin_service.py`
  - 已负责 embedding 准备、Agent Core 预热、全局知识入库。
- `app/agent_plugin/agent/memory.py`
  - 已有 `LongTermMemory`。
  - 已接入 `ChromaDB`。
  - 已有 `rag_ingest()` 和 `rag_query_top_k()`。
- 结论：
  - 当前项目不是“没有 RAG”。
  - 但当前 RAG 主要服务 Agent 插件与全局知识库，不是为统一搜索而设计。

## 3. 统一搜索范围

“搜一切”的第一期范围建议如下。

### 3.1 公共内容

- 热点新闻
- 中央文件
- 站内已审核政策文档 `PolicyDocument(status=approved)`

### 3.2 当前用户私有内容

- 文档可视化解析历史 `ChatMessage`
- 智能体对话历史 `AgentConversation` + 最近消息摘要
- 收藏 `Favorite`
- 待办 `TodoItem`
- 自己发布的政策文档
- 搜索历史

### 3.3 第二期可纳入

- 民意反馈 / 纠错 / 留言 `Opinion`
- 智能体工具调用结果摘要
- 个人偏好与长期记忆片段
- 管理员侧全局搜索入口

## 4. 设计原则

1. 不能只靠 RAG。
   - RAG 适合模糊语义召回。
   - Header 联想必须依赖 Trie 或至少 prefix index。
2. 不能只靠 Trie。
   - Trie 适合前缀提示。
   - 语义相近、错字、表达不一致，必须依赖向量召回。
3. 搜索必须做分层。
   - 联想层：毫秒级，服务 Header 下拉栏。
   - 结果层：百毫秒到秒级，服务统一搜索页。
4. 公共内容和私有内容必须隔离。
   - 私有历史、收藏、待办不能被公共搜索读到。
5. 不直接复用 Agent 当前 collection 作为统一搜索主索引。
   - 应新建独立 collection，避免 Agent 记忆和全站搜索互相污染。

## 5. 推荐架构

## 5.1 混合检索架构

统一搜索采用三段式召回：

1. Trie 前缀召回
   - 用于 Header 下拉联想。
   - 返回标题、关键词、最近搜索、最近访问。
2. 关键词召回
   - 用于精确词命中与高亮。
   - 推荐优先使用 SQLite FTS5。
   - 如果目标环境 FTS5 不可用，则降级为 SQL `LIKE`。
3. RAG 语义召回
   - 用于“乡村振兴”搜到“农业现代化”、“就业补贴”搜到“稳岗扩岗”等模糊结果。
   - 使用 ChromaDB + 当前 embedding 模型。

最终结果做统一重排。

## 5.2 索引层

新增统一搜索索引，不直接把现有业务表拿来硬查。

建议新增：

- `search_index_item`
  - 存放统一搜索的结构化元数据。
- `search_query_log`
  - 记录搜索词、来源、点击结果、耗时、用户。

`search_index_item` 建议字段：

- `id`
- `source_type`
  - `news`
  - `central_doc`
  - `policy_document`
  - `chat_history`
  - `agent_conversation`
  - `favorite`
  - `todo`
  - `my_policy_publish`
  - `search_history`
- `source_id`
- `owner_user_id`
  - 公共内容为 `null`
  - 私有内容写用户 id
- `visibility`
  - `public`
  - `private`
- `title`
- `subtitle`
- `summary`
- `body`
- `keywords`
- `route_path`
- `external_url`
- `icon`
- `created_time`
- `updated_time`
- `heat_score`
- `search_text`
  - 用于 FTS / LIKE
- `extra_json`

说明：

- 业务表继续做业务主表。
- `search_index_item` 只做统一检索读模型。

## 5.3 Trie 层

Trie 不建议直接从完整业务表临时现查，而是从轻量 suggestion 文档构建。

建议做法：

1. 从 `search_index_item` 生成 suggestion payload。
2. 按字符构建 Trie。
3. 维护两份缓存：
   - 公共 Trie
   - 当前用户私有增量 Trie
4. 启动时构建，增量事件发生时局部更新。

Trie 节点附带的不是全文，而是轻量候选：

- 展示词
- source_type
- source_id
- subtitle
- route_path / external_url
- score

中文场景下按“字符前缀”构建即可，不需要英文式分词 Trie。

## 5.4 向量索引层

当前实现优先采用“SQLite 检索读模型 + 持久化 embedding”：

- 向量直接落在 `search_index_item.embedding_json`
- 查询时从 `search_index_item` 读候选与已持久化向量
- 只对当前 query 实时做 embedding

后续如果数据规模继续扩大，再演进到独立向量库或专用 collection。

索引内容：

- 标题
- 摘要
- 正文摘要
- 标签
- 最近一条助手回复摘要
- 历史记录摘要

metadata 至少包含：

- `source_type`
- `source_id`
- `owner_user_id`
- `visibility`
- `updated_time`

即使后续升级到独立向量库，也不要和 Agent 的长期记忆 collection 混用，原因如下：

- Agent 长记忆的写入目标是“对话辅助”。
- 统一搜索的写入目标是“全站检索”。
- 两者重排策略、权限边界、更新频率都不同。

## 6. Header 搜索框改造方案

## 6.1 行为目标

`web/src/components/common/Header.vue` 改造为：

- 输入即触发联想
- 支持下拉栏
- 支持键盘上下切换
- 支持回车搜索
- 支持点击建议项直接跳转
- 支持展示分类区块

下拉栏建议包含四个区块：

1. 前缀联想
2. 最近搜索
3. 我的最近历史
4. 语义相关结果预览

## 6.2 接口建议

新增统一搜索接口：

- `GET /search/suggest?q=&limit=`
  - 主要服务 Header 下拉栏
- `GET /search/unified?q=&types=&page=&page_size=&semantic=1`
  - 服务搜索结果页
- `POST /search/log`
  - 记录查询与点击

`/search/suggest` 返回结构建议：

```json
{
  "query": "医保",
  "items": [
    {
      "group": "prefix",
      "source_type": "policy_document",
      "source_id": 12,
      "title": "医保报销指南",
      "subtitle": "政策文件",
      "route_path": "/policy-swipe?doc_id=12",
      "external_url": null,
      "score": 0.98
    }
  ],
  "groups": {
    "prefix": 5,
    "recent_search": 3,
    "history": 4,
    "semantic": 4
  }
}
```

## 6.3 下拉栏交互细节

- 输入长度 `< 1`
  - 展示最近搜索 + 热门词 + 最近历史
- 输入长度 `>= 1`
  - 优先请求 Trie 联想
- 输入长度 `>= 2`
  - 并发请求语义预览
- 失焦延迟关闭
  - 避免点击建议项时弹层提前消失
- 结果区支持分组标题
  - 文章
  - 政策
  - 我的历史
  - 对话
  - 收藏 / 待办

## 7. 搜索结果页改造方案

`web/src/views/Search.vue` 应从“新闻搜索页”升级为“统一搜索页”。

建议页面能力：

- 顶部保留输入框
- 左侧筛选栏
  - 全部
  - 文章
  - 政策
  - 我的历史
  - 智能体对话
  - 收藏
  - 待办
  - 发布记录
- 结果卡片统一但按类型展示不同动作
  - 新闻：打开原文
  - 政策：打开政策详情
  - 解析历史：恢复解析
  - 对话：继续对话
  - 收藏：进入收藏对象
  - 待办：进入待办详情

## 8. 排序策略

建议统一得分：

`final_score = prefix_score + lexical_score + semantic_score + recency_boost + heat_boost + personal_boost`

## 0. Current Delivery Status (2026-04-11)

- Landed `GET /api/search/unified` for mixed retrieval across history, agent conversations, internal policy documents, central docs, and news.
- Landed `GET /api/search/suggest-index` to provide a lightweight suggestion index for frontend Trie construction.
- Landed Header V1 search dropdown: local Trie prefix matching plus remote semantic suggestion preview.
- Landed Search page V1 mixed result rendering with grouped source types: `history`, `agent`, `policy`, `news`.
- Current semantic retrieval uses the local embedding model plus persisted vectors stored in `search_index_item.embedding_json`.
- DB initialization now runs `history_event` backfill first, then runs unified search index backfill and vectorization automatically.
- Runtime incremental indexing is already wired for committed `history_event` writes and committed `PolicyDocument` writes.
- Query-time only vectorizes the query itself; candidate documents/history are not re-embedded on every search.

排序规则建议：

- Header 下拉联想
  - `prefix_score` 权重最高
- 结果页
  - 关键词精确命中优先
  - 其次语义相关度
  - 私有历史对本人加权
  - 新近结果适度加权

## 9. 数据接入方案

## 9.1 第一批接入

- 新闻与中央文件
  - 来源：`app/services/news_crawler.py`
- 已审核政策
  - 来源：`PolicyDocument`
- 文档解析历史
  - 来源：`ChatMessage`
- Agent 对话
  - 来源：`AgentConversation` + 最近 `AgentMessage`
- 收藏
  - 来源：`Favorite`
- 待办
  - 来源：`TodoItem`

## 9.2 第二批接入

- 自己发布的政策记录
- 搜索历史
- 民意反馈
- 管理端对象

## 9.3 各源索引摘要建议

- `PolicyDocument`
  - `title + category + tags + content`
- `ChatMessage`
  - `original_text + handling_matter + required_materials + risk_warnings + chat_analysis 摘要`
- `AgentConversation`
  - `title + 最近消息摘要 + 最近助手回复摘要`
- `Favorite`
  - `note + 关联消息摘要`
- `TodoItem`
  - `title + detail + deadline`
- `news/central_doc`
  - `title + description`

## 10. RAG 可行性结论

可行，但必须按“独立搜索索引”方式实现。

原因：

1. 当前项目已经具备 embedding + ChromaDB 运行条件。
2. 当前 Agent 插件已经验证过本地 embedding 与 Chroma 的组合链路。
3. 搜索场景不需要生成式回答，只需要向量召回，因此工程难度低于 Agent。
4. 统一搜索的难点不在“能不能用 RAG”，而在“索引怎么组织、权限怎么隔离、结果怎么重排”。

明确判断：

- `Trie`：可立即实现，风险低。
- `站内关键词检索`：可立即实现，建议同步上 FTS5。
- `RAG 语义模糊搜索`：可实现，建议作为统一搜索一期的一部分。
- `直接复用 /admin/rag/search`：不可取，这个接口目前是空实现。

## 11. 索引构建与向量化时机

这里必须明确一个原则：

- 查询词：搜索时实时向量化
- 文档：预先向量化，不在搜索时临时现算

也就是说，统一搜索采用“查询时编码 query，数据侧提前建索引”的模式。

### 11.1 首次初始化时

当数据库不存在、系统开始从 `app/resources/db_init/` 导入初始数据时，应在初始数据导入完成后执行一次统一搜索索引回填。

建议触发点：

- `app/main.py` 启动时执行的 `init_db_and_admin()`
- `app/services/init_db.py` 中 `_import_seed_data(...)` 成功完成后

建议执行逻辑：

1. 创建数据库表
2. 导入 `app/resources/db_init/` 的种子数据
3. 检查统一搜索索引是否存在
4. 如果索引不存在，执行一次全量回填
5. 将所有可搜索对象写入：
   - `history_event`
   - `search_index_item`
   - `search_index_item.embedding_json`

注意：

- 这里的“全量向量化”是首次建索引行为。
- 不是每次服务启动都重跑。

### 11.2 启动时的正确策略

启动时应该做的是“索引存在性检查”和“必要时修复”，而不是无脑全量重建。

建议触发全量回填的条件：

- `search_index_item` 表为空
- `search_index_item` 中缺少 embedding 数据
- 索引版本与代码版本不兼容
- 管理员手动触发重建

不建议的策略：

- 每次 `uvicorn` 启动都全量重建搜索向量
- 每次热重载都重新扫描所有文档

### 11.3 运行期增量向量化

当用户新增或修改可搜索内容时，应做增量索引。

应触发增量向量化的典型场景：

- 用户上传并解析出新的 `ChatMessage`
- 用户导入历史记录，形成新的 `ChatMessage`
- 用户改写解析结果
- 用户创建或更新 `PolicyDocument`
- `PolicyDocument` 审核通过，进入公共搜索域
- 新建 `AgentConversation`
- 会话新增消息并产出新的会话摘要
- 后续新增统一历史事件并生成可搜索摘要

核心原则：

- 必须在数据库事务 `commit` 成功后再提交索引任务
- 不要在事务提交前写搜索索引或 embedding

当前已落地的增量路径：

- `history_service.record_event(..., commit=True)` 在历史事件提交成功后同步 upsert `search_index_item`
- `policy_document` 创建/审核成功后同步 upsert 对应政策搜索索引

否则会出现：

- 向量索引里有数据，但数据库回滚了
- 搜索结果出现脏对象

### 11.4 搜索时绝不现算全量文档 embedding

搜索请求到来时，只做三件事：

1. 对当前 `query` 做 embedding
2. 到关键词索引和向量索引中召回候选
3. 统一重排

不做的事：

- 扫描全表
- 临时对所有政策、历史、对话逐条做 embedding

这个边界必须严格守住，否则搜索延迟会随着数据量线性恶化。

### 11.5 推荐工程实现

建议在 `search_index_item` 或等价索引表里增加以下状态字段：

- `is_indexed`
- `is_dirty`
- `indexed_at`
- `source_updated_at`
- `index_version`

推荐状态流：

1. 业务对象创建/更新
2. 标记对应搜索索引记录 `is_dirty = true`
3. 后台 worker 拉取 dirty 记录
4. 重新生成搜索文本
5. 重算 embedding
6. 更新 Chroma 中该条文档
7. 写回 `indexed_at`，清理 `is_dirty`

### 11.6 批量回填与异步队列

项目当前已经有 worker 启动链路，因此统一搜索索引也应尽量走异步任务，而不是在请求线程里做重向量化。

推荐：

- 首次回填：后台批量任务
- 用户新增/修改：异步增量任务
- 管理员重建索引：后台任务 + 进度接口

不建议：

- 在上传文档的主请求里同步完成 embedding 与 Chroma 写入
- 在 Agent 回复主链路里同步重建整个会话索引

### 11.7 对当前项目的具体落点

建议在以下位置挂接搜索索引更新：

- `app/services/init_db.py`
  - 种子数据导入完成后触发“首次全量回填”
- `app/services/chat_message_service.py`
  - `create_message_from_payload()`
  - `update_message_audience_via_ai()`
  - `import_message_from_file()`
- `app/api/routes/policy_document.py` 或对应 service
  - 创建、更新、审核时触发
- `app/services/agent_chat_service.py`
  - 在会话级摘要变更后触发，而不是每条消息都重建

### 11.8 一句话实现原则

统一搜索的向量化时机应当是：

- 首次初始化种子数据时：做一次全量回填
- 平时业务新增或修改时：做增量向量化
- 用户真正搜索时：只向量化查询词

## 12. 推荐实施顺序

### Phase 0

- 完成本文档
- 明确搜索源与权限边界

### Phase 1

- 新增统一搜索服务与接口
- 建立 `search_index_item`
- 接入新闻、中央文件、已审核政策
- 接入 Header 下拉栏基础版

### Phase 2

- 接入 `ChatMessage`
- 接入 `AgentConversation`
- 接入 `Favorite`、`TodoItem`
- 建立私有搜索权限过滤

### Phase 3

- 接入向量索引
- 完成 RAG 语义召回
- 完成混合重排

### Phase 4

- 搜索日志与最近搜索
- 点击埋点
- 搜索质量评估

## 13. 关键风险

1. 如果只做 Trie，不做统一索引，后续类型扩展会越来越乱。
2. 如果直接把 Agent 记忆库当搜索库，会出现权限和语义污染。
3. 如果只做语义检索，不做前缀联想，Header 下拉体验会发虚。
4. 如果只做 `LIKE`，中文长文本结果质量会明显不足。
5. 如果不先定义统一结果卡片协议，前后端会持续分裂出多套搜索逻辑。
6. 如果把“首次全量回填”和“每次启动全量重建”混为一谈，启动成本会迅速失控。
7. 如果不在 `commit` 后再写索引，会出现数据库与向量库不一致。

## 14. 建议落地文件

建议新增或改造：

- `app/services/unified_search_service.py`
- `app/api/routes/search.py`
- `app/models/search_index_item.py`
- `app/models/search_query_log.py`
- `web/src/api/search.js`
- `web/src/components/common/Header.vue`
- `web/src/views/Search.vue`

## 15. 最终结论

这项改造完全可做，而且应当优先做。

最合理的路线不是“把 Header 做个更漂亮的输入框”，而是：

1. 先建立统一搜索索引与统一搜索接口。
2. 再让 Header 使用 Trie + 下拉栏作为统一搜索的即时入口。
3. 再接入 RAG 语义召回，把“搜一切”真正做完整。

如果后续按本方案实施，Header 搜索、搜索页、历史页、发现页搜索、词云点击搜索，最终都应收敛到同一套统一搜索底座。
