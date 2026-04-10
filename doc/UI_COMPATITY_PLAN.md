# 全站 UI 统一开发蓝图

## 1. 目标判断

你在 `TODO.md` 里提出的路线是对的，而且应该作为全站统一 UI 的第一阶段起点：

1. 先停止继续堆单页视觉特效，优先统一全局主题架构。
2. 先解决 Header / Sidebar / 全局容器 / 通用组件的视觉语言一致性。
3. 再把首页已经验证过的“酒红珊瑚色系”抽象成全局可复用的设计 Token。
4. 最后再做页面级精打磨和动效升级。

这条路线的价值在于：

- 先统一底层变量和壳层，后续页面改造不会反复返工。
- 能避免“只有 `/showcase` 像成品，主应用像旧后台”的割裂感。
- 能把“视觉风格”变成真正的主题系统，而不是分散写死在各页面 CSS 里的局部效果。

---

## 2. 当前现状与问题

结合现有代码，当前 UI 体系存在以下结构性问题：

### 2.1 主题系统是半成品

- 前端已有 `theme_mode` 和 `color_scheme` 概念：
  - `web/src/stores/settings.js`
  - `web/src/components/common/Header.vue`
  - `web/src/views/Settings.vue`
- 但后端 `Settings` 模型和 schema 目前没有 `color_scheme` 字段：
  - `app/models/settings.py`
  - `app/schemas/settings.py`
- 这意味着：
  - 未登录用户可本地切色系
  - 登录用户的色系不具备可靠持久化基础
  - 前后端主题能力不对齐

### 2.2 全局变量命名过旧，且语义层级不够

- 目前主变量仍以旧式后台色命名为主：
  - `--header-bg`
  - `--sidebar-bg-gradient`
  - `--color-primary`
  - `--color-primary-light`
  - `--color-primary-dark`
- 问题：
  - 变量粒度偏粗
  - 无法表达“页面背景 / 面板背景 / 浮层 / 品牌强调 / 状态色 / 发光色 / 描边层级”
  - 不利于把首页色系迁移到全站

### 2.3 Header / Sidebar 仍带有旧后台气质

- `web/src/components/common/Header.vue` 里目前使用下拉框切换旧三色方案。
- `web/src/components/common/Sidebar.vue` 里仍直接依赖旧的线性渐变变量。
- 两者虽然能工作，但视觉语气更像“运营后台皮肤切换”，不像统一品牌产品。

### 2.4 页面之间缺乏同一套设计语言

- `/showcase` 已经形成完整叙事型品牌语言。
- 主应用的大部分页面仍以“传统管理后台卡片”方式呈现。
- 结果是：
  - 首页高级
  - 进入功能页后掉档
  - 用户对产品的一致性感知中断

### 2.5 暗色模式大量依赖 `!important` 全局补丁

- `web/src/assets/main.css` 中暗色覆盖非常多，且粒度不统一。
- 这会导致：
  - 可维护性差
  - 组件局部修补越来越多
  - 新页面接入主题时容易遗漏

### 2.6 动效没有统一标准

- `/showcase` 的动效语言已经很清晰。
- 主应用页面的 hover、切换、进场、容器反馈仍不统一。
- 缺少统一的时间曲线、层级反馈和 reduced-motion 降级策略。

---

## 3. 总体设计原则

全站统一 UI 的目标，不是“所有页面都长得像首页”，而是：

### 3.1 同一品牌，不同场景

- 首页：品牌叙事、视觉张力更强。
- 发现页：内容浏览型，允许更媒体化。
- 数据分析页：信息密度高，允许更仪表盘化。
- Agent 页：对话与工作流感更强。
- 其他功能页：应更克制、更稳定，但仍然属于同一品牌语言。

### 3.2 统一的是语言，不是复制首屏

全站应统一这些维度：

- 色彩逻辑
- 字体逻辑
- 卡片与容器层级
- 按钮与表单语法
- 边框、圆角、阴影、发光强度
- 状态反馈
- 动效节奏

### 3.3 从“主题皮肤”升级到“设计系统”

后续不再以“换几种颜色”理解主题，而是建立：

- 明暗模式轴
- 品牌色系轴
- 语义 Token 层
- 组件 Token 层
- 页面实现层

---

## 4. 主题系统重构方案

## 4.1 采用双轴主题模型

后续主题系统统一拆成两个维度：

### A. 明暗模式轴

- `light`
- `dark`
- `system`

负责控制：

- 背景亮度
- 面板亮度
- 文本对比
- 边框透明度
- 阴影强度
- 浮层可读性

### B. 品牌色系轴

第一阶段只保留两类对外可见色系：

- `neutral`
  - 作为默认中性方案
  - 负责稳定、克制、业务型页面承载
- `wine-coral`
  - 首页同源品牌方案
  - 负责把“酒红珊瑚色系”扩展到全站

现有旧方案处理建议：

- `classic`
- `morandi`
- `graphite`

处理方式：

- 不再保留为 Header / Sidebar 的公开切换入口
- 作为迁移兼容值短期保留
- 最终逐步收敛为 `neutral` 与 `wine-coral`

这样做的原因：

- 避免主题过多导致品牌识别发散
- 保持评审/答辩场景下的统一印象
- 避免“后台换皮感”

---

## 4.2 主题 Token 分层

建议把全局变量从“旧色值变量”重构为以下层级：

### 第一层：原始品牌色板

示例：

```css
:root {
  --brand-coral-300: #ffb76f;
  --brand-coral-400: #ff8f7a;
  --brand-coral-500: #ff7f6b;
  --brand-gold-400: #ffdb64;
  --brand-cyan-400: #58cbff;
  --brand-cyan-500: #5fd1ff;
  --brand-mint-400: #80fab0;

  --brand-wine-700: #512334;
  --brand-wine-900: #140c12;
  --brand-ink-900: #09131f;
  --brand-blue-900: #15233f;
}
```

### 第二层：语义 Token

示例：

```css
:root {
  --ui-bg-canvas: #f6f7fb;
  --ui-bg-subtle: #eef1f6;
  --ui-bg-surface: rgba(255, 255, 255, 0.82);
  --ui-bg-elevated: rgba(255, 255, 255, 0.94);
  --ui-bg-overlay: rgba(12, 18, 28, 0.55);

  --ui-text-strong: #101521;
  --ui-text-main: #2c3443;
  --ui-text-subtle: #667085;
  --ui-text-faint: #8a93a5;

  --ui-border-soft: rgba(17, 24, 39, 0.08);
  --ui-border-strong: rgba(17, 24, 39, 0.16);

  --ui-accent-primary: var(--brand-coral-500);
  --ui-accent-secondary: var(--brand-cyan-500);
  --ui-accent-tertiary: var(--brand-mint-400);

  --ui-shadow-soft: 0 10px 30px rgba(17, 24, 39, 0.08);
  --ui-shadow-medium: 0 18px 50px rgba(17, 24, 39, 0.12);
  --ui-shadow-strong: 0 28px 80px rgba(17, 24, 39, 0.18);
}
```

### 第三层：组件 Token

示例：

```css
:root {
  --shell-header-bg: linear-gradient(...);
  --shell-sidebar-bg: linear-gradient(...);
  --card-radius-lg: 24px;
  --card-radius-md: 18px;
  --control-radius-pill: 999px;
  --control-height-md: 40px;
  --motion-ease-emphatic: cubic-bezier(0.22, 1, 0.36, 1);
}
```

### 第四层：页面局部 Token

只允许页面在必要时覆盖局部变量，例如：

- `--page-hero-glow`
- `--chart-accent-1`
- `--agent-bubble-user-bg`

禁止页面直接大量写死品牌色。

---

## 4.3 酒红珊瑚色系的全站定义

该色系应成为全站正式品牌方案，而不是首页私有方案。

### 深色场景

- 主背景渐变：
  - `#140c12`
  - `#512334`
  - `#15233f`
  - `#09131f`
- 强调发光：
  - `#ff8f7a`
  - `#ffb76f`
  - `#ffdb64`
  - `#58cbff`
  - `#5fd1ff`
- 辅助点缀：
  - `#80fab0`

### 浅色场景

不应照搬深色渐变，而应转译为浅底品牌语义：

- 页面基底：
  - 暖白偏粉雾
  - 米白偏冷灰
- 强调按钮：
  - 珊瑚橙主按钮
- 高亮边缘：
  - 冷青蓝描边/微发光
- 局部氛围：
  - 极浅酒红到粉白的柔和径向光晕

结论：

- `wine-coral` 不是“深色专属皮肤”
- 必须同时定义 light / dark 两套映射

---

## 5. Header / Sidebar 改造方案

## 5.1 Header 改造目标

文件：

- `web/src/components/common/Header.vue`

改造方向：

- 删除旧的下拉式三色选择器
- 保留明暗切换
- 在明暗切换按钮右侧增加一个新的“小圆形色系按钮”

### 小圆形色系按钮规范

形态建议：

- 32px 到 36px 圆形按钮
- 使用双层视觉：
  - 外环表示当前色系
  - 内核表示当前主强调色
- `wine-coral` 状态下：
  - 外圈为酒红/蓝黑微渐变
  - 内部为珊瑚橙与青蓝对撞高光

交互建议：

- 单击：在 `neutral` 和 `wine-coral` 之间切换
- Hover：按钮外环出现轻微光晕扩散
- 切换成功：触发 180ms 到 260ms 的缩放回弹

### Header 视觉目标

- 从“后台顶栏”升级为“品牌壳层”
- 背景不再是硬线性渐变条，而是：
  - 浅色下为半透明磨砂悬浮层
  - 深色下为深色玻璃层 + 微弱品牌光晕
- 搜索框、图标按钮、头像胶囊全部接入新的 Token

---

## 5.2 Sidebar 改造目标

文件：

- `web/src/components/common/Sidebar.vue`

改造方向：

- 保留当前图标模式 / 展开模式的交互结构
- 但视觉上从“红灰渐变侧栏”切换为“统一品牌壳层”

### Sidebar 形态规范

#### 展开态

- 背景采用更克制的品牌纵向渐变
- 不再出现明显“旧后台导航条”观感
- Logo 区域与导航区之间增强层级过渡

#### 图标态

- 保留胶囊感
- 增加轻微毛玻璃与浮空阴影
- 当前激活项使用：
  - 内发光
  - 柔和描边
  - 小面积品牌强调色

#### 激活态

- `neutral`：克制灰蓝强调
- `wine-coral`：珊瑚橙 + 青蓝微高光

### Sidebar 动效规范

- 宽窄切换：420ms，`cubic-bezier(0.22, 1, 0.36, 1)`
- 标签显隐：180ms 透明度 + 240ms 最大宽度
- 激活项切换：120ms 背景过渡 + 160ms 外发光

---

## 6. 设置页同步改造

文件：

- `web/src/views/Settings.vue`

设置页应成为主题系统的“完整控制台”，不是旧配置列表。

### 设置项建议

#### 明暗模式

- 保留：
  - 浅色
  - 深色
  - 跟随系统

#### 品牌色系

- 改为：
  - 中性色系 `neutral`
  - 酒红珊瑚 `wine-coral`

#### 展示方式

- 不再使用旧式“传统按钮组”
- 改为带预览卡的小型主题卡片
- 每张卡片展示：
  - 背景样张
  - 主按钮样张
  - 标签样张
  - 说明文字

这样用户一眼能看懂切换后的结果。

---

## 7. 后端兼容与持久化补齐

这是第一阶段必须同步完成的技术债。

### 7.1 需要修改的后端文件

- `app/models/settings.py`
- `app/schemas/settings.py`
- `app/api/routes/settings.py`
- `app/resources/db_init/settings.json`

### 7.2 新增字段

建议补充：

```python
color_scheme: str = Field(default="neutral", description="全局品牌色系")
```

### 7.3 兼容策略

若线上或已有本地数据库没有该字段，需要提供迁移方案：

- 开发期 SQLite 可做兼容初始化或迁移脚本
- 旧值映射建议：
  - `classic` -> `neutral`
  - `morandi` -> `neutral`
  - `graphite` -> `neutral`

原因：

- 避免历史用户进入后出现未知主题值
- 保证统一视觉收敛

---

## 8. 页面分层改造策略

后续页面不应一次性全改，应按壳层、通用件、核心业务页、次要页分批推进。

## 8.1 A 类：保留独特 UI，但接入统一主题底层

这些页面允许维持独特视觉身份：

- `/showcase`
- `/showcase/discovery`
- `/showcase/screen`
- `/agent`
- `/data-analysis-and-visualization`

改造原则：

- 保留页面个性
- 统一基础变量
- 统一按钮、弹窗、标题、输入框、标签的主题映射
- 统一明暗模式和色系切换行为

### 对这类页面的要求

- 不要求长得一样
- 但必须共享：
  - 颜色 Token
  - 字体 Token
  - 阴影和边框 Token
  - 通用交互动效

## 8.2 B 类：必须重点统一到首页同源语言

这些页面应最优先统一：

- `/`
- `/profile`
- `/settings`
- `/favorites`
- `/history`
- `/todo`
- `/search`
- `/rewrite`
- `/public-opinion-hall`
- `/policy-publish-center`
- `/certified-analysis`

目标：

- 看起来属于同一产品
- 不再是多个“独立小项目拼接”

## 8.3 C 类：后台管理页允许更克制，但不能脱轨

- `/admin`

改造目标：

- 保持高可读、高效率
- 但仍使用统一卡片、按钮、表格、标签和弹层语法

---

## 9. 通用组件设计系统规范

## 9.1 卡片系统

建议建立三类卡片：

### Surface Card

- 用于普通信息容器
- 背景柔和
- 边框极浅
- 阴影轻

### Elevated Card

- 用于重点区块
- 更强阴影
- 更明显的玻璃感或亮度差

### Accent Card

- 用于关键指标、CTA、空状态、重要入口
- 使用品牌渐变或高亮描边
- 但面积不能过多

## 9.2 按钮系统

统一为以下级别：

- `primary`
- `secondary`
- `ghost`
- `danger`
- `icon`

要求：

- 高度统一
- 圆角统一
- 文案字重统一
- hover / active / disabled / loading 全状态齐全

`wine-coral` 下的主按钮建议：

- 浅色：珊瑚橙实底 + 微暖阴影
- 深色：暖橙到浅金渐变 + 深色文本或高对比文本

## 9.3 输入与搜索框

输入类控件应统一：

- 背景层级
- 描边强度
- focus ring
- 占位文字颜色
- 错误态 / 成功态 / 禁用态

首页风格迁移建议：

- 输入框 focus 时加入青蓝或珊瑚微光边缘
- 不要使用传统蓝色浏览器式发光

## 9.4 标签 / Badge / Chip

统一成三类：

- 信息标签
- 状态标签
- 操作标签

目标：

- 替代大量临时样式
- 在全站形成统一识别

## 9.5 弹窗 / 抽屉 / 菜单

统一规范：

- 浮层背景
- 背景模糊
- 遮罩透明度
- 关闭动效
- 出场位移

推荐：

- Modal：Y 轴上浮 20px -> 0，240ms
- Drawer：X 轴滑入，280ms
- Dropdown：缩放 0.96 -> 1，160ms

## 9.6 表格与列表

尤其是后台类页面，需要统一：

- 表头背景
- 行 hover
- 行选中
- 分隔线
- 工具栏
- 批量操作栏

目标：

- 即使是“管理页”，也保持高级感
- 不回退成普通管理系统模板

---

## 10. 动效系统蓝图

## 10.1 动效原则

动效的目标不是“炫”，而是：

- 建立层级
- 传达状态变化
- 增强产品完成度
- 保持与首页同一节奏

## 10.2 时间体系

建议统一为：

- `120ms`：点击反馈、图标反馈
- `180ms`：hover、标签变化、小弹层
- `240ms`：输入框 focus、下拉菜单、按钮状态变化
- `320ms`：卡片浮起、面板切换
- `420ms`：Sidebar 宽窄、页面小范围布局变化
- `820ms`：仅限首页或展示型页面的大场景切换

## 10.3 曲线体系

建议统一：

```css
--motion-ease-standard: cubic-bezier(0.2, 0, 0, 1);
--motion-ease-emphatic: cubic-bezier(0.22, 1, 0.36, 1);
--motion-ease-exit: cubic-bezier(0.4, 0, 1, 1);
```

## 10.4 全站应落地的动效

### Hover

- 卡片轻微上浮 `translateY(-2px ~ -6px)`
- 阴影增强
- 描边更清晰

### Focus

- 输入框外环品牌色微发光
- 不使用突兀蓝光

### Route 切换

- 主应用功能页：轻量淡入上浮
- 不做首页那种整屏切场

### Skeleton / Loading

- 使用低对比 shimmer
- `wine-coral` 模式下 shimmer 可带极弱暖冷渐变

### 状态切换

- 按钮 loading
- tab 切换
- badge 更新
- 数据刷新

都要有最小反馈，而不是静态跳变。

## 10.5 Reduced Motion

必须补齐：

```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

这是全站动效正式化的重要组成部分。

---

## 11. 分阶段实施计划

## Phase 0：主题底座重构

目标：

- 让主题切换真正成为系统能力

任务：

- 补后端 `color_scheme`
- 统一 `settingsStore`
- 清理旧 `classic / morandi / graphite` 入口
- 建立新的主题枚举和值映射
- 重写 `web/src/assets/main.css` 的 Token 结构

交付物：

- 全局主题可稳定持久化
- light / dark / system 正常
- `neutral / wine-coral` 正常

## Phase 1：壳层统一

目标：

- 让用户一进入应用就能感知“同一个产品”

任务：

- 改造 `Header.vue`
- 改造 `Sidebar.vue`
- 改造 `App.vue` 主容器
- 新增色系按钮
- 统一顶栏搜索框、图标按钮、头像胶囊、浮层菜单

交付物：

- 壳层全面接入新主题
- Header / Sidebar 与首页品牌语气对齐

## Phase 2：通用组件统一

目标：

- 让页面改造不再重复造样式

任务：

- 按钮
- 输入框
- 卡片
- 标签
- 弹窗
- 下拉菜单
- 表格容器
- 空状态
- Skeleton

交付物：

- 一套真正可复用的 UI 基础件

## Phase 3：核心业务页统一

优先级建议：

1. `Home.vue`
2. `Settings.vue`
3. `Profile.vue`
4. `Favorites.vue`
5. `History.vue`
6. `TodoList.vue`
7. `PolicyPublishCenter.vue`
8. `CertifiedAnalysis.vue`
9. `PublicOpinionHall.vue`
10. `Search.vue`
11. `Rewrite.vue`

目标：

- 形成全站主体验的一致感

## Phase 4：特色页接轨

页面：

- `Agent.vue`
- `DataAnalysisAndVisualization.vue`
- `showcase/*`

目标：

- 保留个性
- 统一底层 Token、控件语法、浮层语法、状态反馈

## Phase 5：细节打磨与验收

任务：

- 调整字号体系
- 打磨留白与栅格
- 压缩硬编码颜色
- 补动效降级
- 补移动端适配
- 做一次系统级对照巡检

---

## 12. 页面级改造要求

## 12.1 首页 / 主工作台

目标：

- 接近 `/showcase` 的品牌完成度
- 但不复制展示页的整屏切换结构

重点：

- 卡片层级
- 顶部信息条
- 结果区块
- 历史与推荐模块
- 搜索与上传入口

## 12.2 收藏 / 历史 / 待办

目标：

- 从“功能页”升级为“产品资产页”

重点：

- 列表行 hover
- 过滤器标签
- 时间与状态展示
- 空状态插图与动作引导

## 12.3 发布中心 / 发布追踪 / 民意大厅

目标：

- 业务页仍有品牌感
- 表单、统计、列表之间形成统一节奏

重点：

- 头部总览区
- 表单卡片层级
- 切换 tab 的风格
- 状态 badge 的品牌化

## 12.4 设置 / 个人中心

目标：

- 作为“个人资产中枢”
- 必须足够精致

原因：

- 这是用户最容易感知全站统一程度的页面之一

## 12.5 Agent / 大屏 / 发现页

目标：

- 保持独特性
- 不破坏统一品牌母体

约束：

- 共用字体与基础色系
- 共用按钮与浮层逻辑
- 共用明暗模式与色系切换

---

## 13. 技术实现建议

## 13.1 建议新增主题配置文件

建议在前端新增类似文件：

- `web/src/theme/palettes.js`
- `web/src/theme/tokens.css`
- `web/src/theme/motion.css`

目的：

- 不再把所有变量堆在 `main.css`
- 让色系与动效配置独立可维护

## 13.2 `settingsStore` 升级建议

需要支持：

- 主题枚举白名单
- 旧值兼容映射
- 本地存储与服务端回写分离
- 切换时的立即生效
- 登录后与服务端配置同步

## 13.3 颜色使用约束

后续开发过程中：

- 禁止新增页面大量写死十六进制品牌色
- 必须优先使用语义 Token
- Showcase 组件如确需特殊色值，也应逐步迁回 Token

## 13.4 组件视觉测试

建议后续每完成一阶段，至少人工检查：

- light + neutral
- dark + neutral
- light + wine-coral
- dark + wine-coral

否则很容易出现只在某一种模式下好看的问题。

---

## 14. 验收标准

满足以下条件，才算全站统一 UI 初步完成：

### 主题能力

- 明暗模式切换稳定
- 色系切换稳定
- 登录后刷新不丢失
- 未登录也能正确本地记忆

### 壳层一致性

- Header / Sidebar / 主内容区高度统一
- 所有页面的壳层看起来属于同一产品

### 页面一致性

- 除特色页外，所有主要页面都与首页同源
- 不再出现明显旧后台残留风格

### 动效一致性

- hover / focus / 弹层 / 切换节奏统一
- 不再出现有的地方无反馈、有的地方过度夸张

### 技术一致性

- 全局硬编码品牌色大幅下降
- 新页面只需消费 Token，不需重造样式系统

---

## 15. 风险与注意事项

### 15.1 最大风险

不是改不动，而是改成“首页风复制版”。

需要明确：

- 全站统一不等于所有页面都做成展示页
- 功能页必须保持效率、可读性、信息密度

### 15.2 第二个风险

只改颜色，不改结构。

如果只做色系切换而不处理：

- 卡片层级
- 容器节奏
- 表单语法
- 按钮样式
- 列表样式

那么最终效果仍然只是“旧后台换新配色”。

### 15.3 第三个风险

动效失控。

必须避免：

- 所有控件都发光
- 所有卡片都浮起很多
- 所有切换都延迟很长

品牌高级感来自节制，不来自堆叠。

---

## 16. 本蓝图对应的第一步落地结论

第一步开发顺序建议固定为：

1. 补 `color_scheme` 后端持久化
2. 重构全局 Token 体系
3. 改造 `Header.vue` 与 `Sidebar.vue`
4. 用新小圆按钮接入 `wine-coral`
5. 改造 `Settings.vue` 为正式主题控制台
6. 再开始全站页面精打磨

这一步完成后，项目会从“首页有气质”进入“整个应用开始像同一个产品”的阶段。

---

## 17. 结论

这个方案不是“可行而已”，而是目前最合理的起手式。

如果目标是让整个项目具备计设级别的完整产品感，那么正确顺序一定是：

- 先主题底座
- 再壳层统一
- 再通用件
- 再页面精修
- 最后做特色页融合和动效校准

后续实施时，应始终以“同一品牌、同一语法、不同场景”作为最高原则。
