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

  // 将后端的 Object { "类型A": 10, "类型B": 5 } 转换为 ECharts 需要的 Array [{name: '类型A', value: 10}]
  const dataArray = Object.entries(props.chartData || {}).map(([name, value]) => ({
    name,
    value
  }));

  // 如果没有数据，渲染一个空状态或者默认样式
  if (dataArray.length === 0) {
    dataArray.push({ name: '暂无数据', value: 0 });
  }

  const option = {
    // 配合主色调：#d4ff80, #00e2dc, #002059，以及一些衍生过渡色
    color: ['#002059', '#00e2dc', '#d4ff80', '#007bb5', '#81d4fa', '#b2dfdb'],
    tooltip: {
      trigger: 'item',
      formatter: '{b} : {c} 份 ({d}%)',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#eee',
      textStyle: {
        color: '#333'
      }
    },
    // 将图例放在左上角或隐藏，这里选择隐藏，让图表主体更大
    legend: {
      show: false
    },
    series: [
      {
        name: '通知类型',
        type: 'pie',
        // 'radius' 模式：扇区圆心角展现数据的百分比，半径展现数据的大小 (南丁格尔玫瑰图核心)
        roseType: 'radius',
        radius: ['20%', '80%'], // 把饼图画得像甜甜圈一样饱满
        center: ['50%', '55%'],
        itemStyle: {
          borderRadius: 8, // 叶片圆角，柔和边缘
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: true,
          formatter: '{b}\n{c} 份',
          color: '#333',
          fontWeight: 'bold',
          lineHeight: 20
        },
        // 核心要求：每个叶片带有双折线，其中一段水平
        labelLine: {
          show: true,
          length: 15,    // 第一段引导线长度（连接扇形）
          length2: 30,   // 第二段引导线长度（水平线）
          smooth: 0.2,   // 稍微带一点平滑
          lineStyle: {
            color: '#ccc',
            width: 1.5
          }
        },
        data: dataArray.sort(function (a, b) { return a.value - b.value; }), // 排序后玫瑰图视觉呈螺旋上升，更好看
        animationType: 'scale',
        animationEasing: 'elasticOut',
        animationDelay: function (idx) {
          // 螺旋弹出的动画效果
          return Math.random() * 200;
        }
      }
    ]
  };

  myChart.setOption(option);
};

// 监听数据变化
watch(() => props.chartData, () => {
  nextTick(() => {
    updateChart();
  });
}, { deep: true });

// 监听窗口大小改变，重绘图表
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
