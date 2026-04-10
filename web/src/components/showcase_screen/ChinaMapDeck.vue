<template>
  <LuminousFrame
    title="中国公共信号主舞台"
    eyebrow="China Geo Deck"
    subtitle="支持缩放漫游、三维姿态感知、流光扫描与厚度表达"
    :accent-start="screenPalette.coral"
    :accent-end="screenPalette.cyan"
  >
    <div class="map-layout">
      <div ref="stageRef" class="map-stage" @pointermove="handlePointerMove" @pointerleave="handlePointerLeave">
        <div class="map-depth depth-a"></div>
        <div class="map-depth depth-b"></div>
        <div class="map-depth depth-c"></div>

        <div class="orbit orbit-a"></div>
        <div class="orbit orbit-b"></div>
        <div class="orbit orbit-c"></div>
        <div class="scan-beam"></div>

        <div class="map-tilt" :style="tiltStyle">
          <div class="map-chart-shell">
            <div ref="chartRef" class="map-chart"></div>
          </div>
        </div>
      </div>

      <aside class="map-side">
        <div class="side-group">
          <span class="side-label">地图提示</span>
          <strong class="side-title">拖动与滚轮可以继续缩放和漫游</strong>
          <p class="side-text">鼠标移动会驱动地图舞台轻微偏转，营造展示级立体视差。地图本体仍保留省级 hover 与缩放能力。</p>
        </div>

        <div class="side-group">
          <span class="side-label">区域热度排行</span>
          <div class="region-list">
            <div v-for="region in topRegions" :key="region.name" class="region-item">
              <span class="region-name">{{ region.name }}</span>
              <div class="region-bar">
                <div class="region-fill" :style="{ width: `${region.percent}%` }"></div>
              </div>
              <span class="region-value">{{ region.value }}</span>
            </div>
          </div>
        </div>

        <div class="side-summary">
          <div class="summary-chip">
            <span>覆盖省份</span>
            <strong>{{ geoData.length }}</strong>
          </div>
          <div class="summary-chip">
            <span>已审核文件</span>
            <strong>{{ formatCompactNumber(summary.approved_docs) }}</strong>
          </div>
          <div class="summary-chip">
            <span>累计反馈</span>
            <strong>{{ formatCompactNumber(summary.total_opinions) }}</strong>
          </div>
        </div>
      </aside>
    </div>
  </LuminousFrame>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import LuminousFrame from './LuminousFrame.vue'
import { formatCompactNumber, provinceCoords, screenPalette } from './screenTheme'

defineOptions({ name: 'ChinaMapDeck' })

const props = defineProps({
  geoData: {
    type: Array,
    default: () => [],
  },
  summary: {
    type: Object,
    default: () => ({}),
  },
})

const chartRef = ref(null)
const stageRef = ref(null)
const tiltX = ref(-14)
const tiltY = ref(0)
const targetTiltX = ref(-14)
const targetTiltY = ref(0)
const rafId = ref(0)

let chart = null
let resizeObserver = null

const topRegions = computed(() => {
  const sorted = [...props.geoData].sort((a, b) => b.value - a.value).slice(0, 5)
  const max = Math.max(...sorted.map((item) => item.value), 1)
  return sorted.map((item) => ({
    ...item,
    percent: Math.max(12, Math.round((item.value / max) * 100)),
  }))
})

const tiltStyle = computed(() => ({
  transform: `rotateX(${tiltX.value}deg) rotateY(${tiltY.value}deg)`,
}))

const animateTilt = () => {
  tiltX.value += (targetTiltX.value - tiltX.value) * 0.08
  tiltY.value += (targetTiltY.value - tiltY.value) * 0.08
  rafId.value = window.requestAnimationFrame(animateTilt)
}

const buildScatterData = () =>
  topRegions.value
    .filter((item) => provinceCoords[item.name])
    .map((item) => ({
      name: item.name,
      value: [...provinceCoords[item.name], item.value],
    }))

const ensureChinaMap = async () => {
  if (echarts.getMap('china')) return true
  try {
    const response = await fetch('https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json')
    const geoJson = await response.json()
    echarts.registerMap('china', geoJson)
    return true
  } catch (error) {
    console.warn('中国地图 GeoJSON 加载失败', error)
    return false
  }
}

const renderMap = async () => {
  if (!chartRef.value) return
  const loaded = await ensureChinaMap()
  if (!loaded) return

  if (!chart) {
    chart = echarts.init(chartRef.value)
  }

  const max = Math.max(...props.geoData.map((item) => item.value), 1)
  chart.setOption({
    animationDuration: 900,
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(10, 14, 24, 0.94)',
      borderColor: 'rgba(255,255,255,0.12)',
      textStyle: { color: '#f4f7ff' },
      formatter: (params) => `${params.name}<br/>信号值：${params.value || 0}`,
    },
    visualMap: {
      show: false,
      min: 0,
      max,
      inRange: {
        color: ['#1a2438', '#24395f', screenPalette.cyan, screenPalette.coral],
      },
    },
    geo: {
      map: 'china',
      roam: true,
      zoom: 1.08,
      top: 10,
      bottom: 10,
      label: { show: false },
      itemStyle: {
        areaColor: '#1a2236',
        borderColor: 'rgba(95, 209, 255, 0.35)',
        borderWidth: 1,
        shadowBlur: 20,
        shadowColor: 'rgba(95, 209, 255, 0.12)',
      },
      emphasis: {
        label: { show: true, color: '#fff', fontSize: 11 },
        itemStyle: {
          areaColor: '#ff8f7a',
          borderColor: '#ffd6bf',
        },
      },
    },
    series: [
      {
        type: 'map',
        geoIndex: 0,
        data: props.geoData,
      },
      {
        type: 'effectScatter',
        coordinateSystem: 'geo',
        rippleEffect: {
          scale: 5,
          brushType: 'stroke',
        },
        symbolSize: (value) => Math.max(10, Math.min(24, value[2] / 2 + 10)),
        itemStyle: {
          color: screenPalette.gold,
          shadowBlur: 20,
          shadowColor: screenPalette.coral,
        },
        label: {
          show: true,
          position: 'top',
          formatter: '{b}',
          color: '#f4f7ff',
          fontSize: 10,
        },
        data: buildScatterData(),
      },
    ],
  }, true)
}

const handleResize = () => chart?.resize()

const handlePointerMove = (event) => {
  const rect = stageRef.value?.getBoundingClientRect()
  if (!rect) return
  const offsetX = (event.clientX - rect.left) / rect.width - 0.5
  const offsetY = (event.clientY - rect.top) / rect.height - 0.5
  targetTiltY.value = offsetX * 12
  targetTiltX.value = -14 - offsetY * 10
}

const handlePointerLeave = () => {
  targetTiltX.value = -14
  targetTiltY.value = 0
}

onMounted(() => {
  animateTilt()
  nextTick(() => {
    renderMap()
    handleResize()
  })
  if (window.ResizeObserver && stageRef.value) {
    resizeObserver = new ResizeObserver(() => {
      renderMap()
      handleResize()
    })
    resizeObserver.observe(stageRef.value)
  }
  window.addEventListener('resize', handleResize)
})

watch(() => props.geoData, renderMap, { deep: true })

onUnmounted(() => {
  window.cancelAnimationFrame(rafId.value)
  window.removeEventListener('resize', handleResize)
  resizeObserver?.disconnect()
  chart?.dispose()
})
</script>

<style scoped>
.map-layout {
  display: grid;
  grid-template-columns: 1fr;
  grid-template-rows: minmax(0, 1fr) auto;
  gap: 14px;
  align-items: stretch;
  min-height: 0;
}

.map-stage {
  position: relative;
  height: clamp(420px, calc(100vh - 430px), 600px);
  perspective: 1200px;
  overflow: hidden;
}

.map-depth,
.orbit,
.scan-beam,
.map-tilt {
  position: absolute;
  inset: 0;
}

.map-depth {
  inset: auto 6% 8% 6%;
  border-radius: 40px;
  transform: translateY(0);
  background: linear-gradient(180deg, rgba(255, 143, 122, 0.1), rgba(88, 203, 255, 0.08));
  filter: blur(18px);
}

.depth-a { transform: translateY(30px); opacity: 0.45; }
.depth-b { transform: translateY(54px); opacity: 0.32; }
.depth-c { transform: translateY(76px); opacity: 0.22; }

.orbit {
  border-radius: 50%;
  border: 1px solid rgba(95, 209, 255, 0.14);
}

.orbit-a {
  inset: 10% 12% 16% 12%;
  animation: orbit-spin 18s linear infinite;
}

.orbit-b {
  inset: 16% 22% 24% 22%;
  border-color: rgba(255, 143, 122, 0.18);
  animation: orbit-spin-reverse 14s linear infinite;
}

.orbit-c {
  inset: 24% 30% 34% 30%;
  border-color: rgba(128, 250, 176, 0.16);
  animation: orbit-spin 10s linear infinite;
}

.scan-beam {
  inset: 12% 18% 22% 18%;
  background: linear-gradient(90deg, transparent, rgba(95, 209, 255, 0.1), rgba(255, 143, 122, 0.1), transparent);
  transform: skewX(-18deg) translateX(-80%);
  filter: blur(8px);
  animation: scan-sweep 6s ease-in-out infinite;
}

.map-tilt {
  transform-style: preserve-3d;
  will-change: transform;
}

.map-chart-shell {
  position: absolute;
  inset: 6% 6% 8% 6%;
  transform: translateZ(42px);
  background:
    radial-gradient(circle at center, rgba(95, 209, 255, 0.08), transparent 42%),
    rgba(8, 12, 20, 0.42);
  border-radius: 34px;
  box-shadow:
    0 34px 70px rgba(0, 0, 0, 0.3),
    inset 0 0 40px rgba(255, 255, 255, 0.03);
}

.map-chart {
  width: 100%;
  height: 100%;
}

.map-side {
  display: grid;
  grid-template-columns: minmax(0, 0.98fr) minmax(0, 1.02fr) 188px;
  gap: 8px;
  align-items: stretch;
}

.side-group,
.summary-chip {
  padding: 9px 10px 10px;
  background:
    linear-gradient(135deg, rgba(255, 143, 122, 0.08), transparent 34%, rgba(88, 203, 255, 0.08)),
    rgba(255, 255, 255, 0.03);
  clip-path: polygon(0 10px, 10px 0, calc(100% - 16px) 0, 100% 16px, 100% 100%, 0 100%);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.side-group {
  height: 100%;
}

.side-label,
.summary-chip span {
  display: block;
  color: rgba(255, 255, 255, 0.48);
  font-size: 10px;
  letter-spacing: 0.14em;
}

.side-title {
  display: block;
  margin-top: 6px;
  color: #fff;
  font-size: 13px;
  line-height: 1.34;
}

.side-text {
  margin: 6px 0 0;
  color: rgba(255, 255, 255, 0.62);
  font-size: 10px;
  line-height: 1.52;
}

.region-list {
  display: grid;
  gap: 4px;
  margin-top: 6px;
}

.region-item {
  display: grid;
  grid-template-columns: 44px minmax(0, 1fr) auto;
  align-items: center;
  gap: 8px;
}

.region-name,
.region-value {
  color: #eef4ff;
  font-size: 10px;
}

.region-bar {
  height: 7px;
  background: rgba(255, 255, 255, 0.06);
  overflow: hidden;
  clip-path: polygon(0 0, 100% 0, calc(100% - 6px) 100%, 0 100%);
}

.region-fill {
  height: 100%;
  background: linear-gradient(90deg, #ff8f7a, #58cbff);
  box-shadow: 0 0 18px rgba(88, 203, 255, 0.35);
}

.side-summary {
  display: grid;
  gap: 6px;
  margin-top: 0;
}

.summary-chip strong {
  display: block;
  margin-top: 6px;
  color: #fff;
  font-family: 'Bahnschrift', 'DIN Alternate', sans-serif;
  font-size: 17px;
}

@keyframes orbit-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes orbit-spin-reverse {
  from { transform: rotate(360deg); }
  to { transform: rotate(0deg); }
}

@keyframes scan-sweep {
  0% { transform: skewX(-18deg) translateX(-80%); opacity: 0; }
  20% { opacity: 1; }
  80% { opacity: 1; }
  100% { transform: skewX(-18deg) translateX(120%); opacity: 0; }
}

@media (max-width: 1480px) {
  .map-side {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .side-summary {
    grid-column: 1 / -1;
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 1280px) {
  .map-side {
    grid-template-columns: 1fr;
  }

  .side-summary {
    grid-template-columns: 1fr;
  }

  .map-stage {
    height: clamp(440px, calc(100vh - 280px), 560px);
  }
}

@media (max-width: 768px) {
  .map-stage {
    height: 460px;
  }
}
</style>
