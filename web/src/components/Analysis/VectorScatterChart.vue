<template>
  <div class="chart-wrapper">
    <div ref="chartRef" class="echarts-container"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue';
import * as echarts from 'echarts/core';
import { ScatterChart } from 'echarts/charts';
import { TooltipComponent, GridComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';

echarts.use([ScatterChart, TooltipComponent, GridComponent, CanvasRenderer]);

const props = defineProps({
  chartData: { type: Array, default: () => [] }
});

const chartRef = ref(null);
let myChart = null;

const updateChart = () => {
  if (!myChart) return;
  const points = (props.chartData || []).map((item) => [
    item.x || 0,
    item.y || 0,
    item.size || 8,
    item.label || ''
  ]);

  const option = {
    grid: { left: '6%', right: '6%', bottom: '10%', top: '8%', containLabel: true },
    tooltip: {
      formatter: (params) => {
        const [x, y, size, label] = params.value;
        return `长度: ${x}<br/>难度: ${y}<br/>权重: ${size}<br/>类型: ${label}`;
      }
    },
    xAxis: {
      type: 'value',
      name: '文本长度',
      axisLabel: { color: '#999' },
      splitLine: { lineStyle: { color: '#f5f5f5', type: 'dashed' } }
    },
    yAxis: {
      type: 'value',
      name: '综合难度',
      min: 0,
      max: 3.5,
      axisLabel: { color: '#999' },
      splitLine: { lineStyle: { color: '#f5f5f5', type: 'dashed' } }
    },
    series: [
      {
        type: 'scatter',
        data: points,
        symbolSize: (val) => val[2],
        itemStyle: {
          color: '#c0392b',
          opacity: 0.7
        }
      }
    ]
  };
  myChart.setOption(option, true);
};

const initChart = () => {
  if (!chartRef.value) return;
  if (myChart) myChart.dispose();
  myChart = echarts.init(chartRef.value);
  updateChart();
};

const handleResize = () => {
  if (myChart) myChart.resize();
};

watch(() => props.chartData, () => nextTick(updateChart), { deep: true });

onMounted(() => {
  initChart();
  window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
  if (myChart) myChart.dispose();
});
</script>

<style scoped>
.chart-wrapper {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.echarts-container {
  flex: 1;
  width: 100%;
  min-height: 200px;
}
</style>
