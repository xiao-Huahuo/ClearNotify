<template>
  <div class="chart-wrapper">
    <div ref="chartRef" class="echarts-container"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue';
import * as echarts from 'echarts/core';
import { BarChart } from 'echarts/charts';
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  DatasetComponent,
  TransformComponent,
  GraphicComponent
} from 'echarts/components';
import { LabelLayout, UniversalTransition } from 'echarts/features';
import { CanvasRenderer } from 'echarts/renderers';

echarts.use([
  TitleComponent,
  TooltipComponent,
  GridComponent,
  DatasetComponent,
  TransformComponent,
  GraphicComponent, // 必须要引入这个才能使用 graphic 绘制自定义图形
  BarChart,
  LabelLayout,
  UniversalTransition,
  CanvasRenderer
]);

const props = defineProps({
  chartData: {
    type: Object,
    default: () => ({})
  }
});

const chartRef = ref(null);
let myChart = null;

const initChart = () => {
  if (chartRef.value) {
    if (myChart != null && myChart != "" && myChart != undefined) {
      myChart.dispose();
    }
    myChart = echarts.init(chartRef.value);
    updateChart();
  }
};

const updateChart = () => {
  if (!myChart) return;

  const data = props.chartData || {};

  const categories = [
    { key: 'language_complexity', name: '语言' },
    { key: 'handling_complexity', name: '办理' },
    { key: 'risk_level', name: '风险' }
  ];

  const levels = ['低', '中', '高'];

  const barColors = [
    '#d4ff80', '#a2f0a8', '#70e2d0',  // 语言：低，中，高 （偏绿-青）
    '#3ed3f8', '#00e2dc', '#00b4e0',  // 办理：低，中，高 （纯青）
    '#0086e4', '#00539e', '#002059'   // 风险：低，中，高 （青-深蓝）
  ];

  const xAxisData = [];
  const seriesData = [];
  let colorIndex = 0;

  categories.forEach((cat, index) => {
    levels.forEach(level => {
      xAxisData.push(`${cat.name}\n${level}`);
      const dataKey = `${cat.key}-${level}`;
      const val = data[dataKey] || 0;

      seriesData.push({
        value: val,
        itemStyle: {
          color: barColors[colorIndex],
          borderRadius: [4, 4, 0, 0]
        }
      });
      colorIndex++;
    });
  });

  const option = {
    grid: {
      left: '0%',
      right: '0%',
      bottom: '15%', // 留出空间给下方的横线和文字
      top: '15%',
      containLabel: true
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: function (params) {
        const item = params[0];
        const parts = item.name.split('\n');
        return `${parts[0]}复杂度 (${parts[1]}): <strong>${item.value}</strong> 篇`;
      },
      backgroundColor: 'rgba(255, 255, 255, 0.9)',
      borderColor: '#eee',
      textStyle: { color: '#333' }
    },
    xAxis: {
      type: 'category',
      data: xAxisData,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: {
        color: '#666',
        fontSize: 11,
        formatter: function(value) {
          return value.split('\n')[1];
        }
      }
    },
    yAxis: {
      type: 'value',
      show: false, // 隐藏 Y 轴
    },
    series: [
      {
        type: 'bar',
        data: seriesData,
        barWidth: '60%',
        label: {
          show: true,
          position: 'top',
          color: '#000',
          fontWeight: 'bold',
          formatter: '{c}'
        },
        animationDelay: function (idx) {
          return idx * 50;
        }
      }
    ],
    // 用 graphic 方式灵活且稳妥地在横轴下方绘制带横线的分组标签
    graphic: [
      {
        type: 'group',
        left: '5%',
        bottom: 0,
        children: [
          { type: 'line', shape: { x1: 0, y1: 0, x2: 60, y2: 0 }, style: { stroke: '#ccc' } },
          { type: 'text', style: { text: '语言', fill: '#666', font: '12px sans-serif', x: 18, y: 5 } }
        ]
      },
      {
        type: 'group',
        left: 'center', // 居中
        bottom: 0,
        children: [
           { type: 'line', shape: { x1: -30, y1: 0, x2: 30, y2: 0 }, style: { stroke: '#ccc' } },
           { type: 'text', style: { text: '办理', fill: '#666', font: '12px sans-serif', x: -12, y: 5 } }
        ]
      },
      {
         type: 'group',
         right: '5%',
         bottom: 0,
         children: [
            { type: 'line', shape: { x1: 0, y1: 0, x2: 60, y2: 0 }, style: { stroke: '#ccc' } },
            { type: 'text', style: { text: '风险', fill: '#666', font: '12px sans-serif', x: 18, y: 5 } }
         ]
      }
    ]
  };

  myChart.setOption(option, true);
};

watch(() => props.chartData, () => {
  nextTick(() => {
    updateChart();
  });
}, { deep: true });

const handleResize = () => {
  if (myChart) {
    myChart.resize();
  }
};

onMounted(() => {
  initChart();
  window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
  if (myChart) {
    myChart.dispose();
  }
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
  min-height: 180px;
}
</style>
