<template>
  <div class="chart-wrapper">
    <div v-if="loading" class="placeholder-text">词云组件加载中...</div>
    <div ref="chartRef" class="echarts-container" v-show="!loading"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick, shallowRef } from 'vue';
import * as echarts from 'echarts/core';
import { TitleComponent, TooltipComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';

echarts.use([TitleComponent, TooltipComponent, CanvasRenderer]);

const props = defineProps({
  chartData: {
    type: Object,
    default: () => ({})
  }
});

const chartRef = ref(null);
const myChart = shallowRef(null);
const loading = ref(true);

const initChart = async () => {
  try {
    // 动态引入 echarts-wordcloud，避免在还没安装时阻断整个页面渲染
    await import('echarts-wordcloud');
    loading.value = false;

    await nextTick();
    if (chartRef.value) {
      if (myChart.value) {
        myChart.value.dispose();
      }
      myChart.value = echarts.init(chartRef.value);
      updateChart();
    }
  } catch (error) {
    console.error("加载 echarts-wordcloud 失败，请确保运行了 npm install echarts-wordcloud", error);
  }
};

const updateChart = () => {
  if (!myChart.value) return;

  const dataArray = Object.entries(props.chartData || {}).map(([name, value]) => ({
    name,
    value
  }));

  if (dataArray.length === 0) {
    dataArray.push({ name: '暂无数据', value: 0 });
  }

  const option = {
    tooltip: {
      show: true,
      formatter: '{b}: {c} 次'
    },
    series: [{
      type: 'wordCloud',
      shape: 'circle',
      keepAspect: false,
      left: 'center',
      top: 'center',
      width: '90%',
      height: '90%',
      right: null,
      bottom: null,
      sizeRange: [12, 50],
      rotationRange: [-45, 45],
      rotationStep: 45,
      gridSize: 8,
      drawOutOfBound: false,
      layoutAnimation: true,
      textStyle: {
        fontFamily: 'sans-serif',
        fontWeight: 'bold',
        // 随机主题色
        color: function () {
          const colors = ['#002059', '#00e2dc', '#007bb5', '#81d4fa'];
          return colors[Math.floor(Math.random() * colors.length)];
        }
      },
      emphasis: {
        focus: 'self',
        textStyle: {
          textShadowBlur: 5,
          textShadowColor: '#333'
        }
      },
      data: dataArray
    }]
  };

  myChart.value.setOption(option, true);
};

watch(() => props.chartData, () => {
  if (!loading.value) {
    nextTick(() => {
      updateChart();
    });
  }
}, { deep: true });

const handleResize = () => {
  if (myChart.value) {
    myChart.value.resize();
  }
};

onMounted(() => {
  initChart();
  window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
  if (myChart.value) {
    myChart.value.dispose();
  }
});
</script>

<style scoped>
.chart-wrapper {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.echarts-container {
  flex: 1;
  width: 100%;
  min-height: 250px;
}

.placeholder-text {
  color: #999;
  font-size: 14px;
}
</style>
