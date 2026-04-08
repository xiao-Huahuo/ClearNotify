# TODO
### 客户端UI
- [ ] 实现极其酷炫的数据分析大屏.
可能的实现代码:
### 人力完成(UI)
- [ ] 首页内容和动效极致的美化.
- [ ] 莫兰迪色系数据统计的引入.
- [ ] 响应式布局的实现,争取在移动端适配.
- [x] 美化智能体页面Agent回答的markdown,让它看起来不那么诡异:
    ```md
    引入 GitHub 风格样式（最快）
    在你的 HTML 中引入 github-markdown-css。

    安装：npm install github-markdown-css

    包裹：给你的 Markdown 容器加上 markdown-body 这个类名。

    HTML
    <div class="markdown-body">
      </div>
    ```
---

### 功能完善
- [ ] header上添加一个返回按钮,点击后触发浏览器的回退.
注: AI在实现上述功能时,不仅可以按照上述功能描述来实现,还可以根据自己的理解和创意进行适当的调整和优化,让界面包含更多内容,只要不违背上述功能的核心需求即可.且页面和组件必须要接入全局的明暗切换状态管理。
### 数据/资源补充
- [ ] 通过初始json的方法大量补充初始化数据库的数据.每种数据至少要几十条,最好要上百条.而且数据量级要加大,含有的内容要增多.
- [ ] 补充好各个地方所需的真实图片,将需要的图片列举在下面:
    主页-示例的占位图片*3,后续扩展成*9
    发现页面的轮播图*3
    发现页面-资讯列表的占位图片
    民意大厅的轮播图*5
    首页-为什么选择我们区域的六个图片
    首页-各个合作伙伴的图标
- [ ] 图片填充清单(位置/命名/大小)：

1) 主页-示例占位图（现 3 张，后续扩到 9 张）
   放置位置：
   - 页面/组件：web/src/views/Home.vue -> .examples-grid -> .example-card -> .breakout-image img
   - 资源目录：web/src/assets/photos/main-examples/
   命名：
   - example1.png ~ example9.png
   大小：
   - 前端显示：约 140px 宽（高度自适应），卡片图片区高度 120px
   - 建议源图：840x600（4:3），最小不低于 560x400
**事实操作**:在main-examples/中全部改为了png文件.命名方式自由化.应该将逻辑进行修改,读取所有的png格式图片然后显示.
2) 发现页面轮播图（3 张）
   放置位置：
   - 页面/组件：web/src/views/DiscoveryHome.vue -> .panorama-hero -> .hero-slide（background-image）
   - 资源目录：web/src/assets/photos/discover/
   命名：
   - slide1.jpg, slide2.jpg, slide3.jpg
   大小：
   - 前端显示：容器高度 clamp(260px, 33vh, 420px)，宽度自适应
   - 建议源图：1920x1080（16:9），最小不低于 1280x720
**事实操作**:填充了五个jpg.应该在逻辑里面加上后两个jpg.
3) 发现页面-资讯列表占位图
   放置位置（按当前页面结构预留）：
   - 页面/组件：web/src/views/DiscoveryHome.vue -> 资讯区 news-list-view / news-card-view（建议在卡片头部区域补图）
   - 资源目录建议：web/src/assets/photos/discover/news/
   命名建议：
   - discover-news-01.jpg ~ discover-news-20.jpg
   大小：
   - 卡片头图建议显示区域：约 100% x 60px（可按 .nc-header 扩展）
   - 建议源图：640x360（16:9），最小不低于 480x270
**还没填充**.
4) 民意大厅轮播图（5 张）
   放置位置：
   - 页面/组件：web/src/views/PublicOpinionHall.vue -> .carousel-area -> .carousel-slide（顶部轮播）
   - 资源目录建议：web/src/assets/photos/opinion-carousel/
   命名建议：
   - opinion-slide-1.jpg ~ opinion-slide-5.jpg
   大小：
   - 前端显示：轮播区高度 280px，宽度为 top-section 左侧 2/3
   - 建议源图：1600x700（约 16:7），最小不低于 1200x525
**事实操作**:已填充.应该替换掉占位符.
5) 首页“为什么选择我们”区域 6 张图
   放置位置：
   - 页面/组件：web/src/views/showcase/ShowcaseLanding.vue -> advantageCards/disadvantageCards -> .comp-card-image img
   - 资源目录建议：web/src/assets/photos/landing/why-us/
   命名建议：
   - advantage-1.jpg ~ advantage-3.jpg
   - disadvantage-1.jpg ~ disadvantage-3.jpg
   大小：
   - 前端显示：100x100（圆形裁切）；平板 80x80；移动端 70x70
   - 建议源图：600x600（1:1），最小不低于 300x300
**事实操作**:已填充.应该替换掉占位符.
6) 首页-合作伙伴图标（6 个）
   放置位置：
   - 页面/组件：web/src/views/showcase/ShowcaseLanding.vue -> sponsors -> .sponsor-logo img
   - 资源目录建议：web/src/assets/photos/partners/
   命名建议：
   - tencent-cloud.svg
   - bytedance.svg
   - aliyun.svg
   - huawei-cloud.svg
   - baidu-cloud.svg
   - jd-cloud.svg
   大小：
   - 前端显示容器：70x70，图标最大显示 55x55；移动端容器 55x55，图标最大 40x40
   - 建议源图：SVG 优先；若 PNG 建议 220x220（透明背景）
**还没填充**.

【seed_data.json 数据补充清单】
每类至少30-50条，最好100条：

1. certified_users: 现有8条→扩充至30+，各类政府部门/街道办/事业单位
2. normal_users: 现有10条→扩充至50+，普通市民姓名
3. policy_documents: 现有5条→扩充至50+，content字段200字以上，涵盖医疗/教育/住房/就业/环保/市场监管等category
4. opinions: 现有9条→扩充至100+，每篇文件至少5-10条，review类型需有rating(1-5)
5. todos: 现有3条→扩充至30+，detail字段详细说明办理步骤
6. chat_messages: 现有3条→扩充至50+，所有字段填充真实内容，original_text_mapping和chat_analysis都要有值



### 人力完成(后端)
- [ ] 删除后端遗留的agent逻辑,加入单独的自制的agent插件.
- [ ] 公共数据大屏的中国地图和超酷炫UI的实现.
---
### 部署问题
- [ ] 解决docker部署条件下无法显示头像的问题.
- [ ] 解决docker不是条件下环境变量未被正确加载的问题(如413解析错误,智能体连接失败等)
