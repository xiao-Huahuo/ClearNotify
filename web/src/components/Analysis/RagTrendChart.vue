<template>
  <div class="chart-wrapper">
    <div ref="chartRef" class="echarts-container"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue';
import * as echarts from 'echarts/core';
import { LineChart, BarChart } from 'echarts/charts';
import { TooltipComponent, GridComponent, LegendComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';

echarts.use([LineChart, BarChart, TooltipComponent, GridComponent, LegendComponent, CanvasRenderer]);

const props = defineProps({
  chartData: { type: Object, default: () => ({}) },
  compareData: { type: Object, default: () => null },
  chartType: { type: String, default: 'line' }
});

const chartRef = ref(null);
let myChart = null;

const buildSeries = (baseData, namePrefix, color) => {
  const keys = Object.keys(baseData || {});
  const avgScore = keys.map((key) => baseData[key]?.avg_score ?? 0);
  const hitRate = keys.map((key) => baseData[key]?.hit_rate ?? 0);
  const type = props.chartType;
  return [
    {
      name: `${namePrefix}命中率`,
      data: hitRate,
      type,
      smooth: true,
      showSymbol: false,
      itemStyle: { color },
      lineStyle: { width: 2, color }
    },
    {
      name: `${namePrefix}相关度`,
      data: avgScore,
      type,
      smooth: true,
      showSymbol: false,
      itemStyle: { color: '#2e86de' },
      lineStyle: { width: 2, color: '#2e86de' }
    }
  ];
};

const updateChart = () => {
  if (!myChart) return;
  const baseData = props.chartData || {};
  const compareData = props.compareData || null;
  const xAxisData = Object.keys(baseData);
  const series = buildSeries(baseData, '个人', '#c0392b');
  if (compareData) {
    const compareKeys = Object.keys(compareData);
    const mergedKeys = Array.from(new Set([...xAxisData, ...compareKeys])).sort();
    const alignData = (data) => {
      const aligned = {};
      mergedKeys.forEach((key) => {
        aligned[key] = data[key] || { avg_score: 0, hit_rate: 0 };
      });
      return aligned;
    };
    const alignedBase = alignData(baseData);
    const alignedCompare = alignData(compareData);
    const seriesMe = buildSeries(alignedBase, '个人', '#c0392b');
    const seriesAll = buildSeries(alignedCompare, '全体', '#3498db');
    series.length = 0;
    series.push(...seriesMe, ...seriesAll);
    xAxisData.length = 0;
    xAxisData.push(...mergedKeys);
  }

  const option = {
    grid: { left: '3%', right: '4%', bottom: '6%', top: '12%', containLabel: true },
    tooltip: { trigger: 'axis' },
    legend: {
      right: 0,
      textStyle: { color: '#999', fontSize: 11 }
    },
    xAxis: {
      type: 'category',
      data: xAxisData,
      axisLine: { lineStyle: { color: '#eee' } },
      axisLabel: { color: '#999' },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 1,
      axisLabel: { color: '#999' },
      splitLine: { lineStyle: { color: '#f5f5f5', type: 'dashed' } }
    },
    series
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
watch(() => props.compareData, () => nextTick(updateChart), { deep: true });
watch(() => props.chartType, () => nextTick(updateChart));

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
