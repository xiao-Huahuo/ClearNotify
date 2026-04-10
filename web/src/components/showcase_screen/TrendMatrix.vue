<template>
  <LuminousFrame :title="title" :eyebrow="eyebrow" :subtitle="subtitle" :accent-start="accentStart" :accent-end="accentEnd">
    <div class="trend-headline">
      <strong>{{ headlineValue }}</strong>
      <span>{{ headlineLabel }}</span>
    </div>
    <div ref="chartRef" class="trend-chart"></div>
  </LuminousFrame>
</template>

<script setup>
import { onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import LuminousFrame from './LuminousFrame.vue'

defineOptions({ name: 'TrendMatrix' })

const props = defineProps({
  title: { type: String, required: true },
  eyebrow: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  headlineValue: { type: String, default: '—' },
  headlineLabel: { type: String, default: '' },
  accentStart: { type: String, default: '#ff8f7a' },
  accentEnd: { type: String, default: '#58cbff' },
  items: { type: Array, default: () => [] },
})

const chartRef = ref(null)
let chart = null

const renderChart = () => {
  if (!chartRef.value) return
  if (!chart) chart = echarts.init(chartRef.value)

  chart.setOption({
    animationDuration: 800,
    backgroundColor: 'transparent',
    grid: { top: 16, right: 10, bottom: 24, left: 36 },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(10, 14, 24, 0.92)',
      borderColor: 'rgba(255,255,255,0.12)',
      textStyle: { color: '#f4f7ff' },
    },
    xAxis: {
      type: 'category',
      data: props.items.map((item) => item.label),
      axisLabel: { color: 'rgba(255,255,255,0.48)', fontSize: 10 },
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.12)' } },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
      axisLabel: { color: 'rgba(255,255,255,0.45)', fontSize: 10 },
    },
    series: [{
      type: 'line',
      smooth: 0.45,
      symbol: 'circle',
      symbolSize: 6,
      data: props.items.map((item) => item.value),
      lineStyle: {
        width: 3,
        color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
          { offset: 0, color: props.accentStart },
          { offset: 1, color: props.accentEnd },
        ]),
      },
      itemStyle: {
        color: props.accentEnd,
        borderColor: '#fff',
        borderWidth: 1,
      },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: `${props.accentEnd}66` },
          { offset: 1, color: 'rgba(0,0,0,0)' },
        ]),
      },
    }],
  }, true)
}

const handleResize = () => chart?.resize()

onMounted(() => {
  renderChart()
  window.addEventListener('resize', handleResize)
})

watch(() => props.items, renderChart, { deep: true })

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
})
</script>

<style scoped>
.trend-headline {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.trend-headline strong {
  font-family: 'Bahnschrift', 'DIN Alternate', sans-serif;
  font-size: 34px;
  color: #fff;
}

.trend-headline span {
  color: rgba(255, 255, 255, 0.56);
  font-size: 12px;
  letter-spacing: 0.14em;
}

.trend-chart {
  height: 220px;
  margin-top: 12px;
}
</style>
