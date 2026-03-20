<template>
  <div class="chart-wrapper">
    <div v-if="loading" class="placeholder-text">词云组件加载中...</div>
    <div ref="chartRef" class="echarts-container" v-show="!loading"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick, shallowRef } from 'vue';
import { useRouter } from 'vue-router';
import * as echarts from 'echarts/core';
import { TitleComponent, TooltipComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';

echarts.use([TitleComponent, TooltipComponent, CanvasRenderer]);

const props = defineProps({
  chartData: { type: Object, default: () => ({}) }
});

const router = useRouter();
const chartRef = ref(null);
const myChart = shallowRef(null);
const loading = ref(true);

const initChart = async () => {
  try {
    await import('echarts-wordcloud');
    loading.value = false;
    await nextTick();
    if (chartRef.value) {
      if (myChart.value) myChart.value.dispose();
      myChart.value = echarts.init(chartRef.value);
      updateChart();
      myChart.value.on('click', (params) => {
        if (params.name && params.name !== '暂无数据') {
          router.push({ path: '/search', query: { q: params.name } });
        }
      });
    }
  } catch (error) {
    console.error("加载 echarts-wordcloud 失败", error);
  }
};

const updateChart = () => {
  if (!myChart.value) return;

  const dataArray = Object.entries(props.chartData || {}).map(([name, value]) => ({ name, value }));
  if (dataArray.length === 0) dataArray.push({ name: '暂无数据', value: 0 });

  myChart.value.setOption({
    tooltip: { show: true, formatter: '{b}: {c} 次' },
    series: [{
      type: 'wordCloud',
      shape: 'square',
      keepAspect: false,
      left: 0, top: 0, right: 0, bottom: 0,
      width: '100%', height: '100%',
      sizeRange: [14, 52],
      rotationRange: [-30, 30],
      rotationStep: 15,
      gridSize: 4,
      drawOutOfBound: false,
      layoutAnimation: true,
      textStyle: {
        fontFamily: 'sans-serif',
        fontWeight: 'bold',
        color() {
          const colors = ['#c0392b', '#e74c3c', '#e67e22', '#8e44ad', '#2980b9', '#16a085', '#27ae60'];
          return colors[Math.floor(Math.random() * colors.length)];
        }
      },
      emphasis: { focus: 'self', textStyle: { textShadowBlur: 5, textShadowColor: '#333' } },
      data: dataArray
    }]
  }, true);
};

watch(() => props.chartData, () => {
  if (!loading.value) nextTick(() => updateChart());
}, { deep: true });

const handleResize = () => { if (myChart.value) myChart.value.resize(); };

onMounted(() => { initChart(); window.addEventListener('resize', handleResize); });
onUnmounted(() => { window.removeEventListener('resize', handleResize); if (myChart.value) myChart.value.dispose(); });
</script>

<style scoped>
.chart-wrapper { width: 100%; height: 100%; display: flex; flex-direction: column; }
.echarts-container { flex: 1; width: 100%; min-height: 250px; }
.placeholder-text { color: #999; font-size: 14px; text-align: center; padding: 20px; }
</style>
