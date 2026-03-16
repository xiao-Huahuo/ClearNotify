<template>
  <div class="chart-wrapper">
    <div ref="chartRef" class="echarts-container"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue';
import * as echarts from 'echarts/core';
import { GraphChart } from 'echarts/charts';
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  DatasetComponent,
  TransformComponent
} from 'echarts/components';
import { LabelLayout, UniversalTransition } from 'echarts/features';
import { CanvasRenderer } from 'echarts/renderers';

// 注册必须的组件
echarts.use([
  TitleComponent,
  TooltipComponent,
  GridComponent,
  DatasetComponent,
  TransformComponent,
  GraphChart,
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

// 初始化 ECharts
const initChart = () => {
  if (chartRef.value) {
    if (myChart != null && myChart != "" && myChart != undefined) {
      myChart.dispose();
    }
    myChart = echarts.init(chartRef.value);
    updateChart();
  }
};

// 更新图表配置
const updateChart = () => {
  if (!myChart) return;

  const dataArray = Object.entries(props.chartData || {})
    .sort((a, b) => b[1] - a[1]) // 按词频降序
    .map(([name, value]) => ({
      name,
      value
    }));

  if (dataArray.length === 0) {
    dataArray.push({ name: '暂无数据', value: 0 });
  }

  const option = {
    tooltip: {
      formatter: function (param) {
        if (param.dataType === 'node') {
          return `${param.name}: ${param.value} 次`;
        }
      },
      backgroundColor: 'rgba(255, 255, 255, 0.9)',
      borderColor: '#eee',
      textStyle: { color: '#333' }
    },
    animationDuration: 1500,
    animationEasingUpdate: 'quinticInOut',
    series: [
      {
        name: '高频材料',
        type: 'graph',
        layout: 'force',
        data: dataArray.map((item, index) => ({
          name: item.name,
          value: item.value,
          // 词频越高，symbolSize 越大
          symbolSize: 20 + Math.sqrt(item.value) * 10,
          itemStyle: {
            color: ['#002059', '#00e2dc', '#d4ff80', '#b3e5fc', '#81d4fa'][index % 5],
          },
          label: {
            show: true,
            position: 'bottom',
            formatter: '{b}',
            color: '#666',
            fontSize: 12,
            distance: 5
          }
        })),
        // 力导向图的配置
        force: {
          repulsion: 120, // 节点之间的斥力因子
          edgeLength: 30,
          gravity: 0.2 // 中心引力
        },
        roam: false, // 禁止拖拽和缩放
        draggable: true,
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
  min-height: 250px;
}
</style>
