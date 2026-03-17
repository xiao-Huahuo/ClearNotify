<template>
  <div class="chart-wrapper">
    <!-- 将图表容器高度绑定到是否展开的状态，使用 CSS transition 平滑过渡 -->
    <div
      ref="chartRef"
      class="echarts-container"
      :style="{ height: containerHeight + 'px' }"
    ></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick, computed } from 'vue';
import * as echarts from 'echarts/core';
import { BarChart } from 'echarts/charts';
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  DatasetComponent,
  TransformComponent
} from 'echarts/components';
import { LabelLayout, UniversalTransition } from 'echarts/features';
import { CanvasRenderer } from 'echarts/renderers';

echarts.use([
  TitleComponent,
  TooltipComponent,
  GridComponent,
  DatasetComponent,
  TransformComponent,
  BarChart,
  LabelLayout,
  UniversalTransition,
  CanvasRenderer
]);

const props = defineProps({
  chartData: {
    type: Object,
    default: () => ({})
  },
  isExpanded: {
    type: Boolean,
    default: false
  }
});

const chartRef = ref(null);
let myChart = null;

// 每个条目的高度，用来计算展开时的总高度
const ITEM_HEIGHT = 40;
const BASE_HEIGHT = 220; // 5 * 40 + 20

const sortedDataArray = computed(() => {
  return Object.entries(props.chartData || {})
    .sort((a, b) => b[1] - a[1]) // 降序排序
    .map(([name, value]) => ({ name, value }));
});

const containerHeight = computed(() => {
  if (props.isExpanded && sortedDataArray.value.length > 5) {
    // 展开时：根据实际数据量计算精确高度，配合 padding (10+10=20) 保证每个条目物理高度完美恒定
    return Math.max(BASE_HEIGHT, sortedDataArray.value.length * ITEM_HEIGHT + 20);
  } else {
    // 收起时：固定高度
    return BASE_HEIGHT;
  }
});

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

  let renderData = sortedDataArray.value;
  if (!props.isExpanded) {
     // 如果未展开，只取前 5 条
     renderData = sortedDataArray.value.slice(0, 5);
  }

  // 使用展开/收起后的数据进行渲染，不再进行 reverse，
  // 通过下方 yAxis 的 inverse: true 来保证最大值始终在上方
  const renderDataToUse = [...renderData];

  if (renderDataToUse.length === 0) {
    renderDataToUse.push({ name: '暂无材料', value: 0 });
  }

  const yAxisData = renderDataToUse.map(item => item.name);
  const seriesData = renderDataToUse.map(item => item.value);

  const option = {
    grid: {
      left: '2%',
      right: '10%',
      bottom: 10, // 改为绝对值，防止百分比在高度变换时引起 top5 物理坐标漂移
      top: 10,
      containLabel: true
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: '{b}: {c} 次',
      backgroundColor: 'rgba(255, 255, 255, 0.9)',
      borderColor: '#eee',
      textStyle: { color: '#333' }
    },
    xAxis: {
      type: 'value',
      show: false // 不显示 x 轴
    },
    yAxis: {
      type: 'category',
      inverse: true, // 【核心修改点】使用 inverse 代替数组 reverse，这样元素的 index 永远不变，ECharts 动画时就不会发生跳跃和飞移
      data: yAxisData,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: {
        color: '#333',
        fontWeight: 'bold',
        fontSize: 12,
        width: 80,
        overflow: 'truncate'
      }
    },
    series: [
      {
        type: 'bar',
        data: seriesData,
        barWidth: 12, // 细长的胶囊形
        itemStyle: {
          borderRadius: 6, // 胶囊圆角
          // 使用渐变色 #00e2dc -> #d4ff80
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#00e2dc' },
            { offset: 1, color: '#d4ff80' }
          ])
        },
        label: {
          show: true,
          position: 'right', // 放在右侧
          formatter: '{c}',
          color: '#666',
          fontSize: 12,
          fontWeight: 'bold'
        },
        animationDurationUpdate: 500,
        animationEasingUpdate: 'cubicInOut'
      }
    ]
  };

  // 此处使用 false (默认行为) 以执行增量合并，从而使新增项和删除项平滑过渡，同时维持 top5 原有动画状态
  myChart.setOption(option, false);
};

// 监听数据变化或者展开状态变化
watch(() => [props.chartData, props.isExpanded], () => {
  nextTick(() => {
    // 高度由于 :style 的 computed 属性会变化，ECharts 需要 resize() 来适应新高度
    if (myChart) {
      myChart.resize({
        height: containerHeight.value
      });
      updateChart();
    }
  });
}, { deep: true });

const handleResize = () => {
  if (myChart) {
    myChart.resize({
        height: containerHeight.value
    });
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
  display: flex;
  flex-direction: column;
}

.echarts-container {
  width: 100%;
  transition: height 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}
</style>
