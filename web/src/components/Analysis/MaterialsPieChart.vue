<template>
  <div class="chart-wrapper">
    <div ref="chartRef" class="echarts-container"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue';
import * as echarts from 'echarts/core';
import { PieChart } from 'echarts/charts';
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  DatasetComponent,
  TransformComponent
} from 'echarts/components';
import { LabelLayout } from 'echarts/features';
import { CanvasRenderer } from 'echarts/renderers';

// 注册必须的组件
echarts.use([
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  DatasetComponent,
  TransformComponent,
  PieChart,
  LabelLayout,
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
let themeObserver = null;

const isDarkTheme = () => document.documentElement.getAttribute('data-theme') === 'dark';

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
  const dark = isDarkTheme();

  // 取前 8 个，防止饼图太碎
  let dataArray = Object.entries(props.chartData || {})
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8)
    .map(([name, value]) => ({
      name,
      value
    }));

  if (dataArray.length === 0) {
    dataArray.push({ name: '暂无材料', value: 0 });
  }

  const option = {
    color: ['#c0392b', '#e67e22', '#f1c40f', '#7f8c8d', '#922b21', '#d35400', '#f39c12', '#95a5a6'],
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} 次 ({d}%)',
      backgroundColor: dark ? 'rgba(20, 20, 20, 0.95)' : 'rgba(255, 255, 255, 0.9)',
      borderColor: dark ? '#3a3a3a' : '#eee',
      textStyle: { color: dark ? '#f3f3f3' : '#333' }
    },
    legend: {
      orient: 'vertical',
      right: '5%',
      top: 'middle',
      icon: 'circle',
      textStyle: {
        color: dark ? '#f3f3f3' : '#666'
      }
    },
    series: [
      {
        name: '高频材料',
        type: 'pie',
        // 甜甜圈图的核心：设置两个半径
        radius: ['40%', '70%'],
        center: ['40%', '50%'], // 整体向左偏一点给 legend 留位置
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: 'transparent',
          borderWidth: 0
        },
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
            fontWeight: 'bold',
            color: dark ? '#ffffff' : '#333',
            formatter: '{b}\n{d}%'
          }
        },
        labelLine: {
          show: false
        },
        data: dataArray,
        animationType: 'scale',
        animationEasing: 'elasticOut',
        animationDelay: function (idx) {
          return Math.random() * 200;
        }
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
  themeObserver = new MutationObserver(() => {
    updateChart();
  });
  themeObserver.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['data-theme'],
  });
  window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
  themeObserver?.disconnect();
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
