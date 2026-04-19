# ShowcaseLanding 全屏滚动首页实施方案

## 当前进度
- ✅ 已创建 `web/src/components/showcase_landing/` 目录
- 🔄 正在拆分组件

## 完整实施步骤

### 第一阶段：拆分现有组件（7个）

#### 1. HeroSection.vue
```vue
<template>
  <div class="hero-section" :class="sectionClasses">
    <div class="hero-bg"></div>
    <div class="hero-content">
      <div class="hero-badge">智能政策分析平台</div>
      <h1 class="hero-title">云上观策</h1>
      <p class="hero-sub">汇聚政策资讯 · 智能解析分析 · 民意实时反馈</p>
      <div class="hero-btns">
        <button class="btn-primary" @click="$router.push('/')">立即体验</button>
        <button class="btn-ghost" @click="$router.push('/showcase/discovery')">浏览政策广场</button>
      </div>
      <div class="hero-stats">
        <div class="hs" v-for="s in heroStats" :key="s.label">
          <span class="hs-num">{{ s.num }}</span>
          <span class="hs-label">{{ s.label }}</span>
        </div>
      </div>
    </div>
    <div class="hero-scroll-hint">
      <div class="scroll-dot"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { apiClient, API_ROUTES } from '@/router/api_routes'

const props = defineProps({
  isActive: Boolean,
  animationDirection: String
})

const heroStats = ref([
  { num: '—', label: '政策文件' },
  { num: '—', label: '认证主体' },
  { num: '—', label: '注册用户' },
  { num: '—', label: '服务可用率' }
])

const sectionClasses = computed(() => ({
  active: props.isActive,
  [`enter-${props.animationDirection}`]: props.isActive
}))

const loadStats = async () => {
  try {
    const res = await apiClient.get(API_ROUTES.ADMIN_STATS)
    heroStats.value[0].num = (res.data.total_policies || 10000).toLocaleString() + '+'
    heroStats.value[1].num = (res.data.certified_users || 500).toLocaleString() + '+'
    heroStats.value[2].num = (res.data.total_users || 50000).toLocaleString() + '+'
    heroStats.value[3].num = (res.data.service_uptime || 99.9) + '%'
  } catch (e) {
    console.warn('统计数据加载失败', e)
    // 使用默认值
    heroStats.value[0].num = '10,000+'
    heroStats.value[1].num = '500+'
    heroStats.value[2].num = '50,000+'
    heroStats.value[3].num = '99.9%'
  }
}

const enter = (direction) => {
  // 进入动画逻辑
}

const leave = (direction) => {
  // 离开动画逻辑
}

defineExpose({ enter, leave })

onMounted(() => {
  if (props.isActive) loadStats()
})
</script>

<style scoped>
.hero-section {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.8s cubic-bezier(0.34, 1.56, 0.64, 1),
              transform 0.8s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.hero-section.active {
  opacity: 1;
  pointer-events: auto;
  z-index: 10;
}

.hero-bg {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, #1a0a09 0%, #c0392b 40%, #2980b9 100%);
}

.hero-bg::after {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse at 60% 40%, rgba(255,255,255,0.08) 0%, transparent 60%);
}

.hero-content {
  position: relative;
  text-align: center;
  color: #fff;
  padding: 80px 20px 40px;
  max-width: 800px;
  animation: fadeInUp 1s ease forwards;
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(40px); }
  to { opacity: 1; transform: translateY(0); }
}

.hero-badge {
  display: inline-block;
  background: rgba(255,255,255,0.15);
  border: 1px solid rgba(255,255,255,0.3);
  padding: 6px 18px;
  border-radius: 20px;
  font-size: 13px;
  margin-bottom: 24px;
  backdrop-filter: blur(8px);
}

.hero-title {
  font-size: clamp(48px, 8vw, 88px);
  font-weight: 900;
  margin: 0 0 16px;
  letter-spacing: -2px;
  text-shadow: 0 4px 24px rgba(0,0,0,0.3);
}

.hero-sub {
  font-size: 18px;
  color: rgba(255,255,255,0.8);
  margin: 0 0 36px;
  line-height: 1.6;
}

.hero-btns {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-bottom: 48px;
  flex-wrap: wrap;
}

.btn-primary {
  background: #fff;
  color: #c0392b;
  border: none;
  padding: 14px 32px;
  border-radius: 30px;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.25s;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.2);
}

.btn-ghost {
  background: rgba(255,255,255,0.12);
  color: #fff;
  border: 1px solid rgba(255,255,255,0.4);
  padding: 14px 32px;
  border-radius: 30px;
  font-size: 15px;
  cursor: pointer;
  transition: all 0.25s;
  backdrop-filter: blur(8px);
}

.btn-ghost:hover {
  background: rgba(255,255,255,0.22);
}

.hero-stats {
  display: flex;
  gap: 40px;
  justify-content: center;
  flex-wrap: wrap;
}

.hs {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.hs-num {
  font-size: 28px;
  font-weight: 900;
}

.hs-label {
  font-size: 12px;
  color: rgba(255,255,255,0.65);
}

.hero-scroll-hint {
  position: absolute;
  bottom: 32px;
  left: 50%;
  transform: translateX(-50%);
}

.scroll-dot {
  width: 6px;
  height: 6px;
  background: rgba(255,255,255,0.6);
  border-radius: 50%;
  animation: bounce 1.6s ease-in-out infinite;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); opacity: 1; }
  50% { transform: translateY(10px); opacity: 0.4; }
}
</style>
```

#### 2. FeaturesSection.vue
从 ShowcaseLanding.vue 第28-50行提取，修改：
- 标题保持 "一站式政策智能服务"
- 第5个功能卡片：`ClearFlow 智能体` → `云小圆`，描述中 `AI` → `AI Agent`

#### 3. ComparisonSection.vue
从 ShowcaseLanding.vue 第52-147行提取，调整：
- 右下角胶囊 marginTop 改为 60px（与上方间距相同）

#### 4. FlowSection.vue
从 ShowcaseLanding.vue 第149-171行提取

#### 5. CtaSection.vue
从 ShowcaseLanding.vue 第173-178行提取

#### 6. SponsorsSection.vue
从 ShowcaseLanding.vue 第180-198行提取

#### 7. FooterSection.vue
从 ShowcaseLanding.vue 第200-213行提取

### 第二阶段：创建新增组件（3个）

#### 1. UiShowcaseSection.vue
**位置**：Hero 和 Features 之间

**功能**：
- 左侧 2/3：轮播展示 5 组 UI 组件截图
- 右侧 1/3：标题、副标题、描述文字
- 底部：发光指示器

**UI组件分组**（需要准备截图）：
1. 智能搜索 + 政策卡片
2. 数据大屏 + 图表组件
3. Agent对话 + 消息气泡
4. 政策广场 + 文档阅读
5. 个人中心 + 设置面板

#### 2. DesignPhilosophySection.vue
**位置**：Comparison 和 Flow 之间

**功能**：
- 彩色艺术字大标题："将人们与世界衔接，引领群众响应国家号召"
- 每个字不同颜色，带发光效果
- 字符逐个弹跳进入
- 下方描述文字

#### 3. HighlightsSection.vue
**位置**：DesignPhilosophy 下面

**功能**：
- 顶部圆形+箭头链条（可横向滑动）
- 4个亮点卡片：
  1. Agent智能体 → `/agent`
  2. 超酷炫公共数据大屏 → `/showcase/screen`
  3. 可视化政策扫描图谱 → `/`
  4. 刷剧式无底资讯体验 → `/policy-swipe`
- 打字机效果标题
- 炫酷链接按钮

### 第三阶段：重构 ShowcaseLanding.vue

```vue
<template>
  <div class="landing-container" @wheel.prevent="handleWheel" @touchstart="handleTouchStart" @touchend="handleTouchEnd">
    <ShowcaseHeader top-text="light" />
    
    <!-- 导航指示器 -->
    <div class="section-indicators">
      <span 
        v-for="(_, idx) in sections" 
        :key="idx"
        class="indicator"
        :class="{ active: idx === currentSectionIndex }"
        @click="navigateToSection(idx, idx > currentSectionIndex ? 'down' : 'up')"
      ></span>
    </div>
    
    <!-- 所有 Section 组件 -->
    <HeroSection 
      ref="heroRef"
      :is-active="currentSectionIndex === 0"
      :animation-direction="animationDirection"
    />
    <UiShowcaseSection 
      ref="uiShowcaseRef"
      :is-active="currentSectionIndex === 1"
      :animation-direction="animationDirection"
    />
    <FeaturesSection 
      ref="featuresRef"
      :is-active="currentSectionIndex === 2"
      :animation-direction="animationDirection"
    />
    <ComparisonSection 
      ref="comparisonRef"
      :is-active="currentSectionIndex === 3"
      :animation-direction="animationDirection"
    />
    <DesignPhilosophySection 
      ref="philosophyRef"
      :is-active="currentSectionIndex === 4"
      :animation-direction="animationDirection"
    />
    <HighlightsSection 
      ref="highlightsRef"
      :is-active="currentSectionIndex === 5"
      :animation-direction="animationDirection"
    />
    <FlowSection 
      ref="flowRef"
      :is-active="currentSectionIndex === 6"
      :animation-direction="animationDirection"
    />
    <CtaSection 
      ref="ctaRef"
      :is-active="currentSectionIndex === 7"
      :animation-direction="animationDirection"
    />
    <SponsorsSection 
      ref="sponsorsRef"
      :is-active="currentSectionIndex === 8"
      :animation-direction="animationDirection"
    />
    <FooterSection 
      ref="footerRef"
      :is-active="currentSectionIndex === 9"
      :animation-direction="animationDirection"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import ShowcaseHeader from '@/components/showcase/ShowcaseHeader.vue'
import HeroSection from '@/components/showcase_landing/HeroSection.vue'
import UiShowcaseSection from '@/components/showcase_landing/UiShowcaseSection.vue'
import FeaturesSection from '@/components/showcase_landing/FeaturesSection.vue'
import ComparisonSection from '@/components/showcase_landing/ComparisonSection.vue'
import DesignPhilosophySection from '@/components/showcase_landing/DesignPhilosophySection.vue'
import HighlightsSection from '@/components/showcase_landing/HighlightsSection.vue'
import FlowSection from '@/components/showcase_landing/FlowSection.vue'
import CtaSection from '@/components/showcase_landing/CtaSection.vue'
import SponsorsSection from '@/components/showcase_landing/SponsorsSection.vue'
import FooterSection from '@/components/showcase_landing/FooterSection.vue'

const currentSectionIndex = ref(0)
const isAnimating = ref(false)
const animationDirection = ref('from-bottom')

const heroRef = ref(null)
const uiShowcaseRef = ref(null)
const featuresRef = ref(null)
const comparisonRef = ref(null)
const philosophyRef = ref(null)
const highlightsRef = ref(null)
const flowRef = ref(null)
const ctaRef = ref(null)
const sponsorsRef = ref(null)
const footerRef = ref(null)

const sections = ref([])

onMounted(() => {
  sections.value = [
    heroRef.value,
    uiShowcaseRef.value,
    featuresRef.value,
    comparisonRef.value,
    philosophyRef.value,
    highlightsRef.value,
    flowRef.value,
    ctaRef.value,
    sponsorsRef.value,
    footerRef.value
  ]
})

const handleWheel = (event) => {
  if (isAnimating.value) return
  
  const delta = event.deltaY
  if (Math.abs(delta) < 10) return
  
  if (delta > 0 && currentSectionIndex.value < sections.value.length - 1) {
    navigateToSection(currentSectionIndex.value + 1, 'down')
  } else if (delta < 0 && currentSectionIndex.value > 0) {
    navigateToSection(currentSectionIndex.value - 1, 'up')
  }
}

let touchStartY = 0
const handleTouchStart = (e) => {
  touchStartY = e.touches[0].clientY
}

const handleTouchEnd = (e) => {
  const touchEndY = e.changedTouches[0].clientY
  const diff = touchStartY - touchEndY
  
  if (Math.abs(diff) > 50) {
    if (diff > 0 && currentSectionIndex.value < sections.value.length - 1) {
      navigateToSection(currentSectionIndex.value + 1, 'down')
    } else if (diff < 0 && currentSectionIndex.value > 0) {
      navigateToSection(currentSectionIndex.value - 1, 'up')
    }
  }
}

const navigateToSection = async (targetIndex, direction) => {
  if (isAnimating.value || !sections.value[targetIndex]) return
  
  isAnimating.value = true
  animationDirection.value = direction === 'down' ? 'from-bottom' : 'from-top'
  
  const currentSection = sections.value[currentSectionIndex.value]
  const targetSection = sections.value[targetIndex]
  
  if (currentSection?.leave) currentSection.leave(direction)
  
  await new Promise(resolve => setTimeout(resolve, 100))
  
  currentSectionIndex.value = targetIndex
  
  if (targetSection?.enter) targetSection.enter(animationDirection.value)
  
  setTimeout(() => {
    isAnimating.value = false
  }, 1000)
}

// 键盘导航
const handleKeydown = (e) => {
  if (e.key === 'ArrowDown') {
    e.preventDefault()
    if (currentSectionIndex.value < sections.value.length - 1) {
      navigateToSection(currentSectionIndex.value + 1, 'down')
    }
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    if (currentSectionIndex.value > 0) {
      navigateToSection(currentSectionIndex.value - 1, 'up')
    }
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.landing-container {
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  position: relative;
}

.section-indicators {
  position: fixed;
  right: 24px;
  top: 50%;
  transform: translateY(-50%);
  z-index: 100;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.indicator.active {
  background: var(--color-primary);
  box-shadow: 0 0 12px var(--color-primary);
  transform: scale(1.3);
}

.indicator:hover {
  background: rgba(255, 255, 255, 0.6);
  transform: scale(1.2);
}
</style>
```

## 实施顺序

1. ✅ 创建 `showcase_landing/` 目录
2. 拆分 HeroSection.vue（对接统计API）
3. 拆分 FeaturesSection.vue（修改文案）
4. 拆分 ComparisonSection.vue（调整布局）
5. 拆分 FlowSection.vue
6. 拆分 CtaSection.vue
7. 拆分 SponsorsSection.vue
8. 拆分 FooterSection.vue
9. 创建 UiShowcaseSection.vue（新增）
10. 创建 DesignPhilosophySection.vue（新增）
11. 创建 HighlightsSection.vue（新增）
12. 重构 ShowcaseLanding.vue 为全屏滚动容器
13. 测试所有动画和交互
14. 响应式适配

## 注意事项

- 所有组件必须支持明暗主题切换
- 使用 `cubic-bezier(0.34, 1.56, 0.64, 1)` 作为主要缓动函数
- 图片使用懒加载
- 防抖滚轮事件（isAnimating 锁）
- 提供键盘导航（上下箭头）
