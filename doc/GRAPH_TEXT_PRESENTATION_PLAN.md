# 图谱文本化展示扩展实施方案

## 1. 目标

对应 `doc/TODO.md` 中这条未完成项：

- 添加更加直观的方式来进行展示,如树展示,广义表展示等.也应该是直接展示全部节点,且可以收缩和展开.

本方案的目标不是重做一套新的知识图谱数据链路，而是在当前 `KnowledgeGraphPanel` 已有的 `nodes / links / dynamic_payload / visual_config` 基础上，补齐两种更直观的文本化展示方式：

1. 树展示
2. 广义表展示

并满足以下约束：

1. 直接展示全部节点，而不是使用 2D 图谱当前的簇折叠结果。
2. 支持按节点展开和收缩。
3. 与当前“知识图谱式简化版 / 原文结构化版”内容范围切换保持兼容。
4. 与现有节点选中、高亮原文、Agent 小窗复用保持兼容。


## 2. 当前基础

当前前端组件已经具备一半以上的实现基础，主要集中在：

- `web/src/components/Home/KnowledgeGraphPanel.vue`

当前已存在的可复用能力：

1. 图谱原始数据输入
   - `props.nodes`
   - `props.links`
   - `props.dynamicPayload`
   - `props.visualConfig`

2. 根节点与层级推导
   - `rootNodeId`
   - `buildParentDepthMap(nodes, links, rootId)`

3. 文本树基础
   - `buildTextTree(rootIds, options)`
   - `simplifiedTextTree`
   - `sourceStructuredTextTree`
   - `activeTextTree`

4. 文本节点递归组件
   - `GraphTextNode`
   - 当前已经基于 `<details open>` 实现默认展开

5. 与原文映射联动
   - `activeNodeId`
   - `text_mapping`
   - `activeSourceHtml`

因此，这次工作不需要新增后端接口，也不需要改动 `document_parser.py` 的图谱生成逻辑。核心任务是把“已有的树形文本逻辑”从“单一模式”升级为“统一展示树 + 多种文本渲染模式”。


## 3. 当前问题

虽然已有文本树，但它仍然不满足这条 TODO 的完整要求，主要问题如下：

1. 目前“矩形文本”本质上仍是单一树视图，没有“树展示 / 广义表展示”两种独立渲染模式。
2. 当前文本树是按既有 `graph/source` 两种内容树来渲染，但没有一个统一的“全部节点展示树”。
3. 当前 2D 图谱的簇折叠逻辑与文本区是分离的，文本区没有明确声明“永远使用全量节点”。
4. 当前树节点只有基础展开能力，没有统一的“全部展开 / 全部折叠 / 展开到指定层级”等控制。
5. 图谱并不一定是严格树，当前文本化逻辑没有显式定义“主树”和“附加关系”的分离策略。


## 4. 总体方案

### 4.1 核心原则

先把图谱统一转换成一棵“显示树” `displayTree`，再让：

1. 树展示
2. 广义表展示

都基于这同一份 `displayTree` 来渲染。

不要分别从 `nodes / links / dynamic_payload` 各写一套视图推导逻辑，否则后续会出现：

1. 某个模式里有节点，另一个模式里没有。
2. 展开状态无法同步。
3. 原文映射和激活节点无法共享。
4. Agent 小窗与主页容易分叉。


### 4.2 两个维度拆分

文本区需要拆成两个维度，而不是只保留一个 `textMode`：

1. 内容范围 `textScope`
   - `all`：全部节点版
   - `graph`：知识图谱式简化版
   - `source`：原文结构化版

2. 展示形式 `textRenderMode`
   - `tree`：树展示
   - `generalized`：广义表展示

这样才能同时满足：

1. “展示全部节点”
2. “保留原有 graph/source 两档内容语义”
3. “新增树 / 广义表两种直观形式”


## 5. 统一显示树模型

建议在 `KnowledgeGraphPanel.vue` 内新增一层纯前端展示模型：

```js
{
  id: string,
  label: string,
  type: string,
  depth: number,
  sourceRange: [number, number] | null,
  isSourceStructure: boolean,
  children: DisplayTreeNode[],
  extraRelations: Array<{
    targetId: string,
    targetLabel: string,
    relation: string,
    logicType: string,
  }>
}
```

说明：

1. `children`
   - 只保留“主父子关系”
   - 用于树展示与广义表的嵌套

2. `extraRelations`
   - 保存未进入主树的其他关系
   - 防止图谱从“图”被错误压扁成“树”后信息丢失

3. `sourceRange`
   - 来自 `visualConfig.text_mapping`
   - 便于树节点与原文映射联动

4. `isSourceStructure`
   - 便于支持 `graph / source / all` 三种内容范围过滤


## 6. 图到树的转换策略

### 6.1 主树选择规则

知识图谱天然可能不是纯树，因此必须先选定每个节点的“主父节点”。建议保持与当前代码一致的优先级：

1. 如果节点有合法 `parent_id`，优先使用它。
2. 否则从 `links` 推导第一条有效父边。
3. 如果仍没有父节点，则挂到根节点。

这个逻辑可复用当前的：

- `buildParentDepthMap(nodes, links, rootId)`

但建议把返回结果继续包装为“主树 + 附加关系”：

1. `parentMap`
2. `childrenMap`
3. `extraRelationsMap`


### 6.2 非树关系处理

下列关系不要强行塞进树层级中：

1. 一个节点的第二父节点
2. 横向关联边
3. 负向约束边
4. 解释性补充边

这些统一进入 `extraRelations`，在树展示和广义表里以“附加关系”形式展示。

示例：

```text
申请条件
  附加关系: 关联 申报流程, 约束 风险提示
```


## 7. 内容范围构建策略

### 7.1 全部节点版 `all`

直接使用原始：

- `safeNodes`
- `safeLinks`

不能使用当前 2D 图谱里已经过簇折叠后的：

- `graphNodes`
- `graphLinks`

原因是 `graphNodes / graphLinks` 会隐藏部分节点，不符合“直接展示全部节点”的要求。


### 7.2 知识图谱式简化版 `graph`

复用当前语义：

1. 从主根节点开始
2. 排除“原文结构节点”
3. 保留语义节点树

等价于当前的 `simplifiedTextTree` 语义，但内部应统一改为基于 `displayTree` 的过滤视图，而不是单独再造一棵树。


### 7.3 原文结构化版 `source`

复用当前语义：

1. 优先从 `sourceStructureRootId` 开始
2. 若图谱里没有原文结构节点，则回退到 `buildContentFallbackTree(props.content)`

等价于当前 `sourceStructuredTextTree` 的逻辑，但也应统一挂到新的显示树体系里。


## 8. 树展示方案

### 8.1 目标

树展示是最直观、最稳定的文本化展示方式，适合替代当前“矩形文本”的默认视图。

### 8.2 渲染形式

每个节点一行，展示：

1. 节点标题
2. 节点类型
3. 子节点数量
4. 附加关系数量

交互行为：

1. 默认全部展开
2. 点击箭头可展开/收缩
3. 点击节点正文可激活节点并联动右侧原文出处

### 8.3 与现有组件的关系

当前 `GraphTextNode` 可以保留，但建议升级为：

- `GraphTreeNode`

升级内容：

1. 不再只接收 `label / children`
2. 接收完整的 `DisplayTreeNode`
3. 展示更多节点元信息
4. 展开状态不再完全依赖浏览器原生 `<details>`，而是优先绑定到统一状态 `collapsedNodeIds`

原因：

原生 `<details>` 适合快速起步，但在需要：

1. 全部展开
2. 全部折叠
3. 展开到指定层级
4. 跨模式保留折叠状态

时，显式状态管理更稳。


## 9. 广义表展示方案

### 9.1 目标

广义表不是为了替代树，而是为了提供一种“更紧凑、更结构化”的阅读方式，让用户快速看到：

1. 节点嵌套关系
2. 结构整体轮廓

### 9.2 展示原则

不要实现成单行、超长、难读的传统括号串。  
建议实现为“多行广义表”：

```text
政策解读(
  申请条件(
    企业注册满一年,
    无重大失信记录
  ),
  申报材料(
    营业执照,
    审计报告
  )
)
```

节点收起后显示为：

```text
申报材料(...)
```

存在附加关系时显示为：

```text
申请条件(...) [关联: 申报流程, 风险提示]
```

### 9.3 渲染方式

建议不要把广义表先拼成单个大字符串再整体 `v-html` 输出，而是：

1. 仍按节点递归渲染
2. 只是每个节点的视觉表现模拟广义表

这样可以保留：

1. 节点点击
2. 高亮当前节点
3. 单节点折叠
4. 与树展示共用状态


## 10. 状态设计

建议在 `KnowledgeGraphPanel.vue` 内新增以下状态：

```js
const textScope = ref('graph');
const textRenderMode = ref('tree');
const collapsedNodeIds = ref(new Set());
```

### 10.1 状态含义

1. `textScope`
   - 控制当前展示“全部节点 / 简化版 / 原文结构版”

2. `textRenderMode`
   - 控制当前展示“树 / 广义表”

3. `collapsedNodeIds`
   - 控制所有文本化节点的折叠状态

### 10.2 状态规则

1. 默认 `textScope = 'graph'`
   - 保持与当前“知识图谱式简化版”默认语义一致

2. 默认 `textRenderMode = 'tree'`
   - 树展示应作为首选主模式

3. 默认 `collapsedNodeIds = 空`
   - 表示全部展开

4. 切换 `tree / generalized` 时，不清空 `collapsedNodeIds`
   - 保证用户当前阅读位置与展开状态不丢失


## 11. 交互设计

建议在当前文本工具栏中新增以下能力：

1. 内容范围切换
   - 全部节点版
   - 知识图谱式简化版
   - 原文结构化版

2. 展示形式切换
   - 树展示
   - 广义表展示

3. 批量操作
   - 全部展开
   - 全部折叠
   - 展开到第 N 层

4. 节点联动
   - 点击文本节点后更新 `activeNodeId`
   - 同步右侧“原文出处”
   - 若当前二维图谱存在对应节点，可同步高亮


## 12. 实施步骤

### 第一步：抽统一显示树

在 `KnowledgeGraphPanel.vue` 内新增几个纯函数：

1. `buildDisplayTreeBase(nodes, links, rootId, textMapping)`
2. `filterDisplayTreeByScope(tree, scope)`
3. `flattenDisplayTreeIds(tree)`

目标：

1. 先从原始图构建统一 `displayTree`
2. 再通过 `scope` 做不同内容范围过滤


### 第二步：替换当前 `activeTextTree`

把当前：

- `simplifiedTextTree`
- `sourceStructuredTextTree`
- `activeTextTree`

重构为：

1. `fullDisplayTree`
2. `graphDisplayTree`
3. `sourceDisplayTree`
4. `activeDisplayTree`

保留当前 `buildContentFallbackTree` 的回退逻辑。


### 第三步：实现树展示组件

将 `GraphTextNode` 升级为状态受控的树节点组件，例如：

- `GraphTreeNode`

需要支持：

1. 节点展开/收缩
2. 元信息显示
3. 关联关系展示
4. 点击节点激活


### 第四步：实现广义表组件

新增：

- `GraphGeneralizedNode`

要求：

1. 吃同一份 `DisplayTreeNode`
2. 吃同一份 `collapsedNodeIds`
3. 与树展示共享点击和激活逻辑


### 第五步：补文本工具栏

在现有文本工具栏上扩展：

1. 范围切换
2. 展示形式切换
3. 全部展开 / 全部折叠 / 按层展开


### 第六步：联动校验

重点验证以下行为：

1. 首页结果页正常工作
2. Agent 小窗中的 `KnowledgeGraphPanel` 同步生效
3. 点击文本节点时原文出处仍能正确定位
4. 切换 `graph/source/all` 时不会出现空树或错误折叠


## 13. 不建议的实现方式

以下方式不建议采用：

1. 直接从 `dynamic_payload` 单独递归生成“广义表”
   - 原因：会绕开现有图谱节点体系，导致和 `activeNodeId`、原文映射、Agent 小窗脱节。

2. 树展示用 `nodes/links`，广义表展示用 `dynamic_payload`
   - 原因：两套数据源最终一定会漂移。

3. 继续完全依赖原生 `<details>` 而不维护统一折叠状态
   - 原因：后续批量展开/折叠和跨模式保留状态会很难维护。

4. 复用 `graphNodes / graphLinks`
   - 原因：这是 2D 图谱视图数据，不是“全部节点”数据。


## 14. 风险点

### 14.1 图不是纯树

风险：

一个节点可能存在多条父边。

处理：

1. 选主父节点构树
2. 其余关系进入 `extraRelations`


### 14.2 节点量过大

风险：

全部展开时，文本区可能非常长。

处理：

1. 默认仍全部展开，满足产品要求
2. 提供“全部折叠”和“展开到指定层级”
3. 若后续确实出现性能问题，再追加虚拟滚动


### 14.3 原文结构节点与语义节点混杂

风险：

`all / graph / source` 的边界可能不稳定。

处理：

沿用当前 `isSourceStructureNode`、`sourceStructureRootId`、`sourceStructureNodeIds` 的判定逻辑，避免重新定义一套规则。


## 15. 推荐实现顺序

推荐严格按以下顺序实施：

1. 统一显示树
2. 全部节点版树展示
3. 简化版 / 原文结构版切换接入统一树
4. 广义表展示
5. 文本工具栏增强
6. Agent 小窗联调

原因：

这样改动最稳，且每一步都可以单独验证，不会把当前已可用的“矩形文本”整体打坏。


## 16. 一句话结论

这项需求最合理的实现方式，不是新增两套独立 UI，而是：

先把当前图谱统一抽象成一棵“全量可展示树”，再让“树展示”和“广义表展示”共享这棵树、共享折叠状态、共享节点选中联动，从而在不改后端协议的前提下完成更直观的文本化图谱展示。
