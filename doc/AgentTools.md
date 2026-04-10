# AgentPlugin Tools 实施清单

目标：优先接入“查询型 + 低副作用执行型”工具，先把智能体从“能回答”提升到“能办事”。

## P0（首批实现）

### 1) Todo 办理清单工具组
- `get_my_todos(confirmed_only: bool = true) -> {"items":[...]}`
- `create_todos_from_chat(items: [{"title":str,"detail"?:str,"deadline"?:str}], source_chat_id?: int, confirm: bool = false) -> {"items":[...],"pending_confirm":bool}`
- `confirm_todo(todo_id: int, confirm: bool = false) -> {"todo": {...}}`

调用链路：
`tool -> app/services/todo_tool_service.py(新增) -> app/models/todo.py(TodoItem)`

现有能力来源：
`app/api/routes/todo.py`

价值：
将通知解析结果直接落成待办事项，形成闭环。

### 2) 政策文档检索工具组
- `search_policy_documents(category?: str, skip: int = 0, limit: int = 20) -> {"items":[...]}`
- `recommend_policy_documents(for_me: bool = false, skip: int = 0, limit: int = 10) -> {"items":[...]}`

调用链路：
`tool -> app/services/policy_tool_service.py(新增) -> app/models/policy_document.py`

现有能力来源：
`app/api/routes/policy_document.py`

价值：
给智能体回答补“政策依据”和“可追溯出处”。

### 3) 用户偏好设置工具组
- `get_user_settings() -> {"settings": {...}}`
- `update_user_settings(default_audience?: str, theme_mode?: str, system_notifications?: bool, confirm: bool = false) -> {"settings": {...},"pending_confirm":bool}`

调用链路：
`tool -> app/services/settings_tool_service.py(新增) -> app/models/settings.py`

现有能力来源：
`app/api/routes/settings.py`

价值：
使智能体能按用户偏好输出（通用/学生/老年/职场等）。

### 4) 历史消息检索工具组
- `search_chat_history(query?: str, skip: int = 0, limit: int = 20, sort_by: str = "created_time", sort_order: str = "desc") -> {"items":[...]}`
- `get_chat_message_detail(message_id: int) -> {"item": {...}}`

调用链路：
`tool -> app/services/chat_message_service.py -> app/models/chat_message.py`

现有能力来源：
`app/services/chat_message_service.py`

价值：
支持“基于历史记录继续办理”，减少重复输入。

### 5) 新闻/政务资讯工具组
- `get_news_digest() -> {"summary": {...}}`
- `search_news(query: str, limit: int = 10) -> {"items":[...]}`

调用链路：
`tool -> app/services/news_crawler.py`

现有能力来源：
`app/api/routes/news.py`

价值：
补时效背景信息，增强解释能力。

## P1（第二批）

### 6) 收藏工具组
- `list_favorites() -> {"items":[...]}`
- `add_favorite(chat_message_id: int, note?: str, confirm: bool = false) -> {"item": {...},"pending_confirm":bool}`

来源：
`app/api/routes/favorite.py`

### 7) 统计分析工具
- `get_my_stats() -> {"stats": {...}}`

来源：
`app/services/stats_service.py`

### 8) 人群改写工具
- `rewrite_for_audience(message_id: int, target_audience: str, confirm: bool = false) -> {"item": {...},"pending_confirm":bool}`

来源：
`app/services/chat_message_service.py::update_message_audience_via_ai`

## 不建议直接接入（P2/P3）

- 权限升级/降级类：`request-upgrade` / `request-downgrade`
- 管理员接口：`/admin/*`
- 强发布副作用：`create_opinion`、上传政策文件（至少需要“草稿 + 人工确认”后再执行）

## 工具统一约束

### 返回格式
- 查询类工具统一返回 JSON 对象：`{"ok": true, "items": [...], "meta": {...}}`
- 变更类工具统一返回 JSON 对象：`{"ok": true, "item": {...}, "pending_confirm": bool}`
- 失败统一：`{"ok": false, "error": {"code": "...", "message": "..."}}`

### 安全与执行策略
- 所有工具必须显式携带并校验 `user_id`（由 Agent 运行时注入）。
- 所有有副作用工具都加 `confirm: bool = false`，默认不执行写操作。
- 优先在 `app/services/*_tool_service.py` 新增服务层封装，避免工具直接依赖路由层。

### Tool 命名建议
- `todo_*`, `policy_*`, `settings_*`, `chat_*`, `news_*`
- 名称采用“动词 + 领域对象”风格，避免歧义。

## 实施顺序建议

1. 先落地 P0 的 1/2/4（Todo + 政策检索 + 历史消息），最快形成可见价值。  
2. 再补 P0 的 3/5（用户设置 + 新闻）。  
3. 最后做 P1，并在前端 trace 面板显示工具入参与输出摘要。  
