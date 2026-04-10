<template>
  <LuminousFrame :title="title" :eyebrow="eyebrow" :subtitle="subtitle" :accent-start="accentStart" :accent-end="accentEnd" compact>
    <div class="distribution-layout">
      <div ref="chartRef" class="distribution-chart"></div>
      <div class="distribution-list">
        <div v-for="item in items" :key="item.label" class="distribution-row">
          <span class="row-dot" :style="{ background: item.color }"></span>
          <span class="row-label">{{ item.label }}</span>
          <span class="row-value">{{ item.value }}</span>
        </div>
      </div>
    </div>
  </LuminousFrame>
</template>

<script setup>
import { onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import LuminousFrame from './LuminousFrame.vue'

defineOptions({ name: 'DistributionPanel' })

const props = defineProps({
  title: { type: String, required: true },
  eyebrow: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  accentStart: { type: String, default: '#ff8f7a' },
  accentEnd: { type: String, default: '#58cbff' },
  items: { type: Array, default: () => [] },
  mode: { type: String, default: 'pie' },
})

const chartRef = ref(null)
let chart = null

const renderChart = () => {
  if (!chartRef.value) return
  if (!chart) chart = echarts.init(chartRef.value)

  const pieOption = {
    color: props.items.map((item) => item.color),
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(10, 14, 24, 0.92)',
      borderColor: 'rgba(255,255,255,0.12)',
      textStyle: { color: '#f4f7ff' },
    },
    series: [{
      type: 'pie',
      radius: ['45%', '72%'],
      center: ['50%', '50%'],
      label: { show: false },
      itemStyle: { borderColor: 'rgba(8,12,20,0.95)', borderWidth: 2 },
      data: props.items.map((item) => ({ name: item.label, value: item.value })),
    }],
  }

  const barOption = {
    grid: { top: 12, right: 12, left: 12, bottom: 24 },
    xAxis: {
      type: 'category',
      data: props.items.map((item) => item.label),
      axisLabel: { color: 'rgba(255,255,255,0.5)', fontSize: 10 },
      axisTick: { show: false },
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } },
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } },
      axisLabel: { color: 'rgba(255,255,255,0.45)', fontSize: 10 },
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(10, 14, 24, 0.92)',
      borderColor: 'rgba(255,255,255,0.12)',
      textStyle: { color: '#f4f7ff' },
    },
    series: [{
      type: 'bar',
      barWidth: '52%',
      data: props.items.map((item) => ({
        value: item.value,
        itemStyle: { color: item.color, borderRadius: [6, 6, 0, 0] },
      })),
    }],
  }

  chart.setOption(props.mode === 'bar' ? barOption : pieOption, true)
}

const handleResize = () => chart?.resize()

onMounted(() => {
  renderChart()
  window.addEventListener('resize', handleResize)
})

watch(() => [props.items, props.mode], renderChart, { deep: true })

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
})
</script>

<style scoped>
.distribution-layout {
  display: grid;
  grid-template-columns: 150px minmax(0, 1fr);
  gap: 12px;
  align-items: center;
}

.distribution-chart {
  height: 160px;
}

.distribution-list {
  display: grid;
  gap: 10px;
}

.distribution-row {
  display: grid;
  grid-template-columns: 10px minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.04);
  clip-path: polygon(0 8px, 8px 0, 100% 0, 100% calc(100% - 8px), calc(100% - 8px) 100%, 0 100%);
}

.row-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  box-shadow: 0 0 12px currentColor;
}

.row-label {
  color: rgba(255, 255, 255, 0.68);
  font-size: 12px;
}

.row-value {
  color: #fff;
  font-family: 'Bahnschrift', 'DIN Alternate', sans-serif;
  font-size: 14px;
}

@media (max-width: 640px) {
  .distribution-layout {
    grid-template-columns: 1fr;
  }
}
</style>
