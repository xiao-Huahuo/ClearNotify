<template>
  <div class="showcase-screen" :class="{ immersive: isImmersive }">
    <ShowcaseHeader :transparent-top="true" top-text="light" />

    <div class="screen-noise"></div>
    <div class="screen-orb orb-left"></div>
    <div class="screen-orb orb-right"></div>
    <div class="screen-gridlines"></div>

    <main class="screen-shell">
      <ScreenTopBar :current-time="currentTime" :active-users="formatCompactNumber(summary.active_users)" />

      <section class="screen-grid">
        <div class="screen-column side-column side-column-left">
          <DataTowerGroup class="widget-span-2" :towers="towers" :accent-start="screenPalette.coral" :accent-end="screenPalette.sky" />
          <DistributionPanel
            class="screen-widget"
            title="公众参与结构"
            eyebrow="Role Distribution"
            subtitle="普通用户、认证主体与管理员构成的参与层级"
            :accent-start="screenPalette.sky"
            :accent-end="screenPalette.coral"
            :items="roleItems"
          />
          <TrendMatrix
            class="screen-widget"
            title="解析活跃度矩阵"
            eyebrow="Parsing Pulse"
            subtitle="最近 24 小时智能解析流量与脉冲起伏"
            :headline-value="analysisPeakValue"
            :headline-label="analysisPeakLabel"
            :accent-start="screenPalette.coral"
            :accent-end="screenPalette.sky"
            :items="screenData.hourly_trend"
          />
        </div>

        <div class="screen-column center-column">
          <ChinaMapDeck :geo-data="screenData.geo_dist" :summary="summary" />
        </div>

        <div class="screen-column side-column side-column-right">
          <DistributionPanel
            class="screen-widget"
            title="公众反馈类型"
            eyebrow="Opinion Distribution"
            subtitle="落地评价、解析纠错与办事留言的当前占比"
            :accent-start="screenPalette.coral"
            :accent-end="screenPalette.amber"
            :items="opinionItems"
          />
          <DistributionPanel
            class="screen-widget"
            title="评分能级分布"
            eyebrow="Rating Spectrum"
            subtitle="从一星到五星的满意度梯度与结构密度"
            :accent-start="screenPalette.gold"
            :accent-end="screenPalette.cyan"
            :items="ratingItems"
            mode="bar"
          />
          <SignalFeed class="screen-widget" :feed="screenData.feed" :accent-start="screenPalette.coral" :accent-end="screenPalette.sky" />
          <StatusDigest
            class="screen-widget"
            :metrics="digestMetrics"
            :approval-rate="approvalRate"
            :notes="digestNotes"
            :accent-start="screenPalette.mint"
            :accent-end="screenPalette.cyan"
          />
        </div>
      </section>

      <SummaryRibbon :items="ribbonItems" />
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import ShowcaseHeader from '@/components/showcase/ShowcaseHeader.vue'
import ChinaMapDeck from '@/components/showcase_screen/ChinaMapDeck.vue'
import DataTowerGroup from '@/components/showcase_screen/DataTowerGroup.vue'
import DistributionPanel from '@/components/showcase_screen/DistributionPanel.vue'
import ScreenTopBar from '@/components/showcase_screen/ScreenTopBar.vue'
import SignalFeed from '@/components/showcase_screen/SignalFeed.vue'
import StatusDigest from '@/components/showcase_screen/StatusDigest.vue'
import SummaryRibbon from '@/components/showcase_screen/SummaryRibbon.vue'
import TrendMatrix from '@/components/showcase_screen/TrendMatrix.vue'
import { formatCompactNumber, screenPalette } from '@/components/showcase_screen/screenTheme'
import { apiClient, API_ROUTES } from '@/router/api_routes'

defineOptions({ name: 'ShowcaseScreen' })

const roleOrder = ['normal', 'certified', 'admin']
const opinionOrder = ['review', 'correction', 'message']
const ratingColors = ['#ff6b6b', '#ff9b5a', '#ffd166', '#80fab0', '#58cbff']

const createEmptyTrend = () => {
  const now = new Date()
  return Array.from({ length: 24 }, (_, index) => {
    const date = new Date(now)
    date.setHours(now.getHours() - (23 - index), 0, 0, 0)
    return {
      label: `${String(date.getHours()).padStart(2, '0')}:00`,
      value: 0,
    }
  })
}

const createEmptyScreenData = () => ({
  summary: {
    total_users: 0,
    certified_users: 0,
    total_messages: 0,
    active_users: 0,
    total_opinions: 0,
    total_docs: 0,
    approved_docs: 0,
    pending_docs: 0,
  },
  role_dist: {},
  role_labels: {
    normal: '普通用户',
    certified: '认证主体',
    admin: '管理员',
  },
  geo_dist: [],
  opinion_type_dist: {},
  opinion_labels: {
    review: '落地评价',
    correction: '解析纠错',
    message: '办事留言',
  },
  rating_dist: {
    1: 0,
    2: 0,
    3: 0,
    4: 0,
    5: 0,
  },
  hourly_trend: createEmptyTrend(),
  hourly_opinion_trend: createEmptyTrend(),
  feed: [],
})

const screenData = ref(createEmptyScreenData())
const currentTime = ref('')
const isImmersive = ref(false)
let clockTimer = null
let refreshTimer = null
let immersiveMedia = null

const overflowSnapshot = {
  htmlOverflow: '',
  bodyOverflow: '',
  bodyOverscroll: '',
}

const updateCurrentTime = () => {
  currentTime.value = new Date().toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  })
}

const syncImmersiveMode = () => {
  const nextState = Boolean(immersiveMedia?.matches)
  isImmersive.value = nextState

  document.documentElement.style.overflow = nextState ? 'hidden' : overflowSnapshot.htmlOverflow
  document.body.style.overflow = nextState ? 'hidden' : overflowSnapshot.bodyOverflow
  document.body.style.overscrollBehavior = nextState ? 'none' : overflowSnapshot.bodyOverscroll
}

const mergeScreenData = (payload = {}) => ({
  ...createEmptyScreenData(),
  ...payload,
  summary: {
    ...createEmptyScreenData().summary,
    ...(payload.summary || {}),
  },
  role_labels: {
    ...createEmptyScreenData().role_labels,
    ...(payload.role_labels || {}),
  },
  opinion_labels: {
    ...createEmptyScreenData().opinion_labels,
    ...(payload.opinion_labels || {}),
  },
  rating_dist: {
    ...createEmptyScreenData().rating_dist,
    ...(payload.rating_dist || {}),
  },
  hourly_trend: payload.hourly_trend?.length ? payload.hourly_trend : createEmptyTrend(),
  hourly_opinion_trend: payload.hourly_opinion_trend?.length ? payload.hourly_opinion_trend : createEmptyTrend(),
  geo_dist: payload.geo_dist || [],
  feed: payload.feed || [],
})

const loadScreenData = async () => {
  try {
    const { data } = await apiClient.get(API_ROUTES.SHOWCASE_SCREEN_DATA)
    screenData.value = mergeScreenData(data)
  } catch (error) {
    console.warn('公共数据分析大屏数据加载失败', error)
  }
}

const summary = computed(() => screenData.value.summary)

const roleItems = computed(() => {
  const labels = screenData.value.role_labels
  const dist = screenData.value.role_dist || {}
  const colors = [screenPalette.sky, screenPalette.coral, screenPalette.gold]

  return roleOrder.map((key, index) => ({
    label: labels[key] || key,
    value: dist[key] || 0,
    color: colors[index],
  }))
})

const opinionItems = computed(() => {
  const labels = screenData.value.opinion_labels
  const dist = screenData.value.opinion_type_dist || {}
  const colors = [screenPalette.coral, screenPalette.cyan, screenPalette.mint]

  return opinionOrder.map((key, index) => ({
    label: labels[key] || key,
    value: dist[key] || 0,
    color: colors[index],
  }))
})

const ratingItems = computed(() =>
  [1, 2, 3, 4, 5].map((level, index) => ({
    label: `${level} 星`,
    value: screenData.value.rating_dist[String(level)] || 0,
    color: ratingColors[index],
  })),
)

const towers = computed(() => [
  {
    value: formatCompactNumber(summary.value.total_users),
    label: '参与主体',
    note: '沉淀的总用户与可触达主体规模',
    suffix: 'USR',
    colorA: screenPalette.coral,
    colorB: screenPalette.amber,
  },
  {
    value: formatCompactNumber(summary.value.total_messages),
    label: '智能解析',
    note: '政策文本进入分析链路的累计次数',
    suffix: 'MSG',
    colorA: screenPalette.cyan,
    colorB: screenPalette.sky,
  },
  {
    value: formatCompactNumber(summary.value.total_opinions),
    label: '公众评议',
    note: '评价、纠错与留言形成的反馈总量',
    suffix: 'OPN',
    colorA: screenPalette.mint,
    colorB: screenPalette.cyan,
  },
])

const getPeakPoint = (items = []) =>
  items.reduce(
    (peak, item) => (item.value > peak.value ? item : peak),
    { label: '00:00', value: 0 },
  )

const analysisPeak = computed(() => getPeakPoint(screenData.value.hourly_trend))
const opinionPeak = computed(() => getPeakPoint(screenData.value.hourly_opinion_trend))

const analysisPeakValue = computed(() => formatCompactNumber(analysisPeak.value.value))
const analysisPeakLabel = computed(() => `单小时峰值 · ${analysisPeak.value.label}`)

const approvalRate = computed(() => {
  if (!summary.value.total_docs) return 0
  return Math.round((summary.value.approved_docs / summary.value.total_docs) * 100)
})

const certifiedRate = computed(() => {
  if (!summary.value.total_users) return 0
  return Math.round((summary.value.certified_users / summary.value.total_users) * 100)
})

const opinionPerDoc = computed(() => {
  if (!summary.value.total_docs) return '0.0'
  return (summary.value.total_opinions / summary.value.total_docs).toFixed(1)
})

const messagePerActiveUser = computed(() => {
  if (!summary.value.active_users) return '0.0'
  return (summary.value.total_messages / summary.value.active_users).toFixed(1)
})

const digestMetrics = computed(() => [
  {
    label: '文件公开率',
    value: `${approvalRate.value}%`,
    note: '已审核文件进入公开展示链路的占比',
  },
  {
    label: '主体渗透率',
    value: `${certifiedRate.value}%`,
    note: '认证主体与管理员在全体用户中的覆盖',
  },
  {
    label: '反馈密度',
    value: `${opinionPerDoc.value} /份`,
    note: '平均每份文件承接的公众反馈强度',
  },
  {
    label: '解析频度',
    value: `${messagePerActiveUser.value} /人`,
    note: '活跃用户平均触发的解析次数',
  },
])

const digestNotes = computed(() => [
  `解析峰值出现在 ${analysisPeak.value.label}，单小时达到 ${formatCompactNumber(analysisPeak.value.value)} 次。`,
  `评议峰值出现在 ${opinionPeak.value.label}，单小时达到 ${formatCompactNumber(opinionPeak.value.value)} 条。`,
])

const ribbonItems = computed(() => [
  { label: '总用户', value: formatCompactNumber(summary.value.total_users) },
  { label: '活跃用户', value: formatCompactNumber(summary.value.active_users) },
  { label: '认证主体', value: formatCompactNumber(summary.value.certified_users) },
  { label: '总解析量', value: formatCompactNumber(summary.value.total_messages) },
  { label: '总评议量', value: formatCompactNumber(summary.value.total_opinions) },
  { label: '总文件量', value: formatCompactNumber(summary.value.total_docs) },
  { label: '已审核文件', value: formatCompactNumber(summary.value.approved_docs) },
  { label: '待审核文件', value: formatCompactNumber(summary.value.pending_docs) },
  { label: '覆盖省份', value: formatCompactNumber(screenData.value.geo_dist.length) },
  { label: '解析小时峰值', value: `${formatCompactNumber(analysisPeak.value.value)} @ ${analysisPeak.value.label}` },
  { label: '评议小时峰值', value: `${formatCompactNumber(opinionPeak.value.value)} @ ${opinionPeak.value.label}` },
])

onMounted(async () => {
  overflowSnapshot.htmlOverflow = document.documentElement.style.overflow
  overflowSnapshot.bodyOverflow = document.body.style.overflow
  overflowSnapshot.bodyOverscroll = document.body.style.overscrollBehavior
  immersiveMedia = window.matchMedia('(min-width: 1680px) and (min-height: 860px)')
  syncImmersiveMode()
  if (immersiveMedia.addEventListener) {
    immersiveMedia.addEventListener('change', syncImmersiveMode)
  } else {
    immersiveMedia.addListener(syncImmersiveMode)
  }

  updateCurrentTime()
  await loadScreenData()
  clockTimer = window.setInterval(updateCurrentTime, 1000)
  refreshTimer = window.setInterval(loadScreenData, 30000)
})

onUnmounted(() => {
  if (clockTimer) window.clearInterval(clockTimer)
  if (refreshTimer) window.clearInterval(refreshTimer)
  if (immersiveMedia?.removeEventListener) {
    immersiveMedia.removeEventListener('change', syncImmersiveMode)
  } else {
    immersiveMedia?.removeListener(syncImmersiveMode)
  }
  document.documentElement.style.overflow = overflowSnapshot.htmlOverflow
  document.body.style.overflow = overflowSnapshot.bodyOverflow
  document.body.style.overscrollBehavior = overflowSnapshot.bodyOverscroll
})
</script>

<style scoped>
.showcase-screen {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  background:
    radial-gradient(circle at 20% 18%, rgba(255, 143, 122, 0.16), transparent 24%),
    radial-gradient(circle at 82% 12%, rgba(88, 203, 255, 0.16), transparent 24%),
    linear-gradient(135deg, #140c12 0%, #512334 24%, #15233f 58%, #09131f 100%);
  color: #f5f7ff;
}

.screen-noise,
.screen-gridlines,
.screen-orb {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.screen-noise {
  opacity: 0.18;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
  background-size: 56px 56px;
  mask-image: linear-gradient(180deg, transparent, rgba(0, 0, 0, 0.8) 16%, rgba(0, 0, 0, 1));
}

.screen-gridlines {
  background:
    linear-gradient(90deg, transparent 0, rgba(255, 255, 255, 0.04) 50%, transparent 100%),
    linear-gradient(180deg, transparent 0, rgba(255, 255, 255, 0.035) 50%, transparent 100%);
  background-size: 100% 140px, 220px 100%;
  opacity: 0.36;
}

.screen-orb {
  filter: blur(40px);
  opacity: 0.42;
}

.orb-left {
  left: -12%;
  top: 14%;
  width: 36vw;
  height: 36vw;
  background: radial-gradient(circle, rgba(255, 143, 122, 0.38), transparent 62%);
}

.orb-right {
  inset: auto -8% 6% auto;
  width: 32vw;
  height: 32vw;
  background: radial-gradient(circle, rgba(88, 203, 255, 0.34), transparent 60%);
}

.screen-shell {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 18px;
  max-width: 1760px;
  margin: 0 auto;
  padding: 92px 22px 26px;
}

.screen-grid {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr) 360px;
  gap: 18px;
  align-items: start;
}

.screen-column {
  min-width: 0;
}

.side-column {
  display: grid;
  gap: 18px;
  align-content: start;
}

.showcase-screen.immersive {
  height: 100vh;
}

.showcase-screen.immersive .screen-shell {
  width: 100%;
  height: 100vh;
  max-width: none;
  padding: 76px 8px 8px;
  gap: 10px;
}

.showcase-screen.immersive .screen-grid {
  flex: 1;
  min-height: 0;
  grid-template-columns: minmax(470px, 25vw) minmax(0, 1fr) minmax(540px, 28vw);
  gap: 10px;
  align-items: stretch;
}

.showcase-screen.immersive .screen-column {
  height: 100%;
}

.showcase-screen.immersive .side-column {
  height: 100%;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  grid-auto-rows: minmax(0, 1fr);
  align-content: stretch;
  align-items: stretch;
  gap: 10px;
}

.showcase-screen.immersive .side-column-left {
  grid-template-columns: minmax(0, 0.98fr) minmax(0, 1.02fr);
}

.showcase-screen.immersive .screen-widget {
  height: 100%;
  min-height: 0;
}

.showcase-screen.immersive .widget-span-2 {
  grid-column: 1 / -1;
}

.showcase-screen.immersive :deep(.distribution-layout) {
  grid-template-columns: 128px minmax(0, 1fr);
  gap: 10px;
}

.showcase-screen.immersive :deep(.distribution-chart) {
  height: 126px;
}

.showcase-screen.immersive :deep(.distribution-list) {
  gap: 8px;
}

.showcase-screen.immersive :deep(.distribution-row) {
  padding: 8px 10px;
}

.showcase-screen.immersive :deep(.trend-chart) {
  height: 176px;
  margin-top: 8px;
}

.showcase-screen.immersive :deep(.trend-headline strong) {
  font-size: 28px;
}

.showcase-screen.immersive :deep(.feed-list) {
  max-height: 250px;
  gap: 8px;
}

.showcase-screen.immersive :deep(.feed-item) {
  padding: 10px 12px;
}

.showcase-screen.immersive :deep(.tower-group) {
  gap: 4px;
}

.showcase-screen.immersive :deep(.summary-ribbon) {
  padding: 4px 0 2px;
}

@media (min-width: 1680px) {
  .screen-shell {
    max-width: 1860px;
  }

  .screen-grid {
    grid-template-columns: 460px minmax(0, 1fr) 520px;
  }

  .side-column {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    align-items: start;
  }

  .side-column-left {
    grid-template-columns: minmax(0, 0.96fr) minmax(0, 1.04fr);
  }

  .widget-span-2 {
    grid-column: 1 / -1;
  }
}

@media (max-width: 1679px) {
  .screen-grid {
    grid-template-columns: 300px minmax(0, 1fr) 340px;
  }
}

@media (max-width: 1360px) {
  .screen-grid {
    grid-template-columns: 1fr;
  }

  .screen-shell {
    padding-top: 88px;
  }
}

@media (max-width: 768px) {
  .screen-shell {
    padding: 84px 14px 20px;
  }

  .screen-grid,
  .side-column {
    gap: 14px;
  }
}
</style>
