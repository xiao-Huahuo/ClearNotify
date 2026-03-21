<template>
  <div class="dashboard-container">
    <div class="header-section">
      <h1 class="page-title">数据分析</h1>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>正在分析您的海量数据...</span>
    </div>

    <!-- 仪表盘主体网格 -->
    <div v-else class="dashboard-grid">
      <!-- ================= 左侧列 (上5/12 下7/12) ================= -->
      <div class="col-left">
        <!-- RAG 命中趋势 -->
        <div class="widget widget-rag-trend">
          <div class="widget-header">
            <h3 class="widget-title">RAG 命中趋势</h3>
            <div class="widget-actions">
               <span
                 class="action-tag"
                 :class="{ active: ragChartType === 'line' }"
                 @click="ragChartType = 'line'"
               >曲线</span>
               <span
                 class="action-tag"
                 :class="{ active: ragChartType === 'bar' }"
                 @click="ragChartType = 'bar'"
               >柱状</span>
            </div>
            <div class="widget-actions scope-toggle" v-if="isAdmin">
              <span class="action-tag" :class="{ active: ragScope === 'me' }" @click="ragScope = 'me'">个人</span>
              <span class="action-tag" :class="{ active: ragScope === 'all' }" @click="ragScope = 'all'">全体</span>
            </div>
          </div>
          <div class="chart-content">
            <RagTrendChart :chartData="ragSeriesData" :compareData="isAdmin ? ragSeriesCompare : null" :chartType="ragChartType" />
          </div>
        </div>

        <!-- 通知类型玫瑰图 -->
        <div class="widget widget-rose-pie">
          <div class="widget-header">
            <h3 class="widget-title">通知类型分布</h3>
            <div class="widget-actions" v-if="isAdmin">
              <span class="action-tag" :class="{ active: noticeScope === 'me' }" @click="noticeScope = 'me'">个人</span>
              <span class="action-tag" :class="{ active: noticeScope === 'all' }" @click="noticeScope = 'all'">全体</span>
            </div>
          </div>
          <h3 class="widget-title">通知类型分布</h3>
          <div class="chart-content">
            <NoticeTypeRoseChart :chartData="noticeChartData" />
          </div>
        </div>
      </div>

      <!-- ================= 中间列 (四块布局) ================= -->
      <div class="col-center">
        <div class="center-grid">
          <div class="widget widget-time-curve span-2">
            <div class="widget-header">
              <h3 class="widget-title">节省时间趋势</h3>
              <div class="widget-actions">
                <span class="action-tag" :class="{ active: timeChartType === 'line' }" @click="timeChartType = 'line'">曲线</span>
                <span class="action-tag" :class="{ active: timeChartType === 'bar' }" @click="timeChartType = 'bar'">柱状</span>
              </div>
              <div class="widget-actions scope-toggle" v-if="isAdmin">
                <span class="action-tag" :class="{ active: timeScope === 'me' }" @click="timeScope = 'me'">个人</span>
                <span class="action-tag" :class="{ active: timeScope === 'all' }" @click="timeScope = 'all'">全体</span>
              </div>
            </div>
            <div class="chart-content">
              <TimeSavedChart
                :chartData="timeSeriesData"
                :compareData="isAdmin ? timeSeriesCompare : null"
                :chartType="timeChartType"
              />
            </div>
          </div>

          <div class="widget widget-vector-scatter">
            <div class="widget-header">
              <h3 class="widget-title">向量散点评估</h3>
              <div class="widget-actions scope-toggle" v-if="isAdmin">
                <span class="action-tag" :class="{ active: vectorScope === 'me' }" @click="vectorScope = 'me'">个人</span>
                <span class="action-tag" :class="{ active: vectorScope === 'all' }" @click="vectorScope = 'all'">全体</span>
              </div>
            </div>
            <div class="chart-content">
              <VectorScatterChart :chartData="vectorScatterData" />
            </div>
          </div>

          <div class="widget widget-materials-block">
            <div class="widget-header">
              <h3 class="widget-title">高频材料分析</h3>
              <div class="widget-actions">
                <span class="action-tag" :class="{ active: materialsChartType === 'pie' }" @click="materialsChartType = 'pie'">饼图</span>
                <span class="action-tag" :class="{ active: materialsChartType === 'scatter' }" @click="materialsChartType = 'scatter'">点云</span>
                <span class="action-tag" :class="{ active: materialsChartType === 'wordCloud' }" @click="materialsChartType = 'wordCloud'">词云</span>
              </div>
              <div class="widget-actions scope-toggle" v-if="isAdmin">
                <span class="action-tag" :class="{ active: materialsScope === 'me' }" @click="materialsScope = 'me'">个人</span>
                <span class="action-tag" :class="{ active: materialsScope === 'all' }" @click="materialsScope = 'all'">全体</span>
              </div>
            </div>
            <div class="chart-content">
              <MaterialsPieChart v-if="materialsChartType === 'pie'" :chartData="materialsChartData" />
              <MaterialsScatterChart v-else-if="materialsChartType === 'scatter'" :chartData="materialsChartData" />
              <MaterialsWordCloud v-else-if="materialsChartType === 'wordCloud'" :chartData="materialsChartData" />
            </div>
          </div>
        </div>
      </div>

      <!-- ================= 右侧列 ================= -->
      <div class="col-right">
        <div class="widget widget-time-cards">
          <div v-if="isAdmin" class="time-cards-grid">
            <div class="time-card-grid card-personal-avg">
              <span class="card-label">个人平均节省时间</span>
              <span class="card-value">{{ statsData?.avg_time_saved_minutes || 0 }} <small>分钟/篇</small></span>
            </div>
            <div class="time-card-grid card-personal-total">
              <span class="card-label">个人总计节省时间</span>
              <span class="card-value">{{ statsData?.total_time_saved_minutes || 0 }} <small>分钟</small></span>
            </div>
            <div class="time-card-grid card-all-avg">
              <span class="card-label">全体用户平均节省时间</span>
              <span class="card-value">{{ statsAll?.avg_time_saved_minutes || 0 }} <small>分钟/篇</small></span>
            </div>
            <div class="time-card-grid card-all-total">
              <span class="card-label">全体用户总计节省时间</span>
              <span class="card-value">{{ statsAll?.total_time_saved_minutes || 0 }} <small>分钟</small></span>
            </div>
          </div>
          <div v-else class="time-cards-container">
            <div class="time-card card-bottom">
              <span class="card-label">总计节省时间</span>
              <span class="card-value">{{ statsData?.total_time_saved_minutes || 0 }} <small>分钟</small></span>
            </div>
            <div class="time-card card-top">
              <span class="card-label">平均节省时间</span>
              <span class="card-value">{{ statsData?.avg_time_saved_minutes || 0 }} <small>分钟/篇</small></span>
            </div>
          </div>
        </div>

        <div class="widget widget-difficulty-bar">
          <h3 class="widget-title">通知难度评估</h3>
          <div class="widget-actions scope-toggle" v-if="isAdmin">
             <span class="action-tag" :class="{ active: difficultyScope === 'me' }" @click="difficultyScope = 'me'">个人</span>
             <span class="action-tag" :class="{ active: difficultyScope === 'all' }" @click="difficultyScope = 'all'">全体</span>
          </div>
          <div class="chart-content">
             <DifficultyBarChart :chartData="difficultyChartData" />
          </div>
        </div>

        <div class="widget widget-recent-history">
          <h3 class="widget-title">最近处理</h3>
          <div class="history-content" v-if="recentHistory">
             <div class="mock-history-item">
                <span class="time">{{ formatDate(recentHistory.created_time) }}</span>
                <p class="text">{{ recentHistory.handling_matter || formatName(recentHistory.original_text) }}</p>
                <div class="history-tags">
                   <span class="h-tag">{{ recentHistory.target_audience || '未知对象' }}</span>
                </div>
             </div>
          </div>
          <div class="chart-placeholder" v-else>暂无历史记录</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useUserStore } from '@/stores/auth.js';
import { apiClient, API_ROUTES } from '@/router/api_routes';
import TimeSavedChart from '@/components/Analysis/TimeSavedChart.vue';
import NoticeTypeRoseChart from '@/components/Analysis/NoticeTypeRoseChart.vue';
import MaterialsPieChart from '@/components/Analysis/MaterialsPieChart.vue';
import MaterialsScatterChart from '@/components/Analysis/MaterialsScatterChart.vue';
import MaterialsWordCloud from '@/components/Analysis/MaterialsWordCloud.vue';
import DifficultyBarChart from '@/components/Analysis/DifficultyBarChart.vue';
import RagTrendChart from '@/components/Analysis/RagTrendChart.vue';
import VectorScatterChart from '@/components/Analysis/VectorScatterChart.vue';

const userStore = useUserStore();
const loading = ref(true);
const statsData = ref(null);
const statsAll = ref(null);
const recentHistory = ref(null);
const isAdmin = computed(() => !!userStore.user?.is_admin);

const noticeScope = ref('me');
const timeScope = ref('me');
const materialsScope = ref('me');
const difficultyScope = ref('me');
const ragScope = ref('me');
const vectorScope = ref('me');

const noticeChartData = computed(() => {
  if (noticeScope.value === 'all' && statsAll.value) return statsAll.value.notice_type_distribution;
  return statsData.value?.notice_type_distribution;
});

const timeSeriesData = computed(() => {
  if (timeScope.value === 'all' && statsAll.value) return statsAll.value.time_saved_distribution;
  return statsData.value?.time_saved_distribution;
});

const timeSeriesCompare = computed(() => {
  if (!statsAll.value) return null;
  return timeScope.value === 'me' ? (statsAll.value.time_saved_distribution || {}) : null;
});

const materialsChartData = computed(() => {
  if (materialsScope.value === 'all' && statsAll.value) return statsAll.value.materials_freq;
  return statsData.value?.materials_freq;
});

const difficultyChartData = computed(() => {
  if (difficultyScope.value === 'all' && statsAll.value) return statsAll.value.complexity_distribution;
  return statsData.value?.complexity_distribution;
});

const ragSeriesData = computed(() => {
  if (ragScope.value === 'all' && statsAll.value) return statsAll.value.rag_series || {};
  return statsData.value?.rag_series || {};
});

const ragSeriesCompare = computed(() => {
  return null;
});

const vectorScatterData = computed(() => {
  if (vectorScope.value === 'all' && statsAll.value) return statsAll.value.vector_scatter || [];
  return statsData.value?.vector_scatter || [];
});

// 图表类型控制
const timeChartType = ref('line'); // 默认曲线图
const materialsChartType = ref('scatter'); // 默认点云图
const ragChartType = ref('line');

const formatDate = (dateString) => {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return `${date.getMonth()+1}-${date.getDate()} ${date.getHours()}:${date.getMinutes()}`;
};

const formatName = (text) => {
  if (!text) return '未命名文档';
  const cleanText = text.replace(/\s+/g, ' ');
  return cleanText.length > 20 ? cleanText.substring(0, 20) + '...' : cleanText;
};

onMounted(async () => {
  if (!userStore.token) {
    alert("请先登录查看数据分析");
    return;
  }

  try {
    const tasks = [apiClient.get(API_ROUTES.ANALYSIS_ME)];
    if (isAdmin.value) {
      tasks.push(apiClient.get(API_ROUTES.ADMIN_ANALYSIS_ALL));
    }
    const [meRes, allRes] = await Promise.all(tasks);
    statsData.value = meRes.data;
    if (allRes) statsAll.value = allRes.data;

    // 获取最近一条历史记录
    const historyRes = await apiClient.get(API_ROUTES.CHAT_MESSAGE, { params: { limit: 1 } });
    if (historyRes.data && historyRes.data.length > 0) {
       recentHistory.value = historyRes.data[0];
    }
  } catch (error) {
    console.error("获取统计数据失败:", error);
  } finally {
    setTimeout(() => {
      loading.value = false;
    }, 500);
  }
});
</script>

<style scoped>
.dashboard-container {
  padding: 20px 30px;
  height: 100%;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
}

.page-title {
  font-size: 24px;
  font-weight: bold;
  margin: 0 0 20px 0;
  color: var(--color-text-dark);
}

.loading-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #999;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #eee;
  border-radius: 50%;
  border-top-color: var(--color-primary);
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ======= 网格布局核心 ======= */
.dashboard-grid {
  flex: 1;
  display: grid;
  grid-template-columns: 2.8fr 4.4fr 2.8fr;
  gap: 20px;
  min-height: 0;
}

.col-left, .col-center, .col-right {
  display: flex;
  flex-direction: column;
  gap: 20px;
  height: 100%;
}

.center-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  grid-template-rows: 1.2fr 1fr;
  gap: 20px;
  flex: 1;
  min-height: 0;
}

.center-grid .span-2 {
  grid-column: span 2;
}

.col-right {
    overflow-y: auto;
    scrollbar-width: none; /* Firefox */
    -ms-overflow-style: none;  /* Internet Explorer 10+ */
}
.col-right::-webkit-scrollbar {
    display: none; /* WebKit */
}

/* ======= Widget 基础样式 ======= */
.widget {
  background: #ffffff;
  border-radius: 0;
  box-shadow: none;
  border: 1px solid #e8e8e8;
  border-top: 3px solid #c0392b;
  padding: 16px;
  display: flex;
  flex-direction: column;
  position: relative;
  transition: all 0.3s ease;
}

.widget-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
  flex-shrink: 0;
  flex-wrap: wrap;
  gap: 8px;
}

.widget-title {
  font-size: 16px;
  font-weight: 800;
  color: #000;
  margin: 0;
  letter-spacing: 1px;
}

.widget-actions {
  display: flex;
  gap: 5px;
  background: #f5f5f5;
  padding: 4px;
  border-radius: 8px;
  z-index: 10;
}
.widget-actions.scope-toggle {
  background: transparent;
  padding: 0;
}

.widget-rose-pie > .widget-title {
  display: none;
}

.action-tag {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 6px;
  cursor: pointer;
  color: #666;
  transition: all 0.2s;
}

.action-tag.active {
  background: #c0392b;
  color: #fff;
  font-weight: bold;
}

.expand-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: #999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px;
  border-radius: 50%;
  transition: all 0.2s;
}

.expand-btn:hover {
  background: #f5f5f5;
  color: #333;
}

.chart-placeholder {
  flex: 1;
  background: #fafafa;
  border: 1px dashed #eee;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ccc;
  font-size: 14px;
  margin-top: 10px;
}

.chart-content {
  flex: 1;
  width: 100%;
  height: 100%;
  min-height: 150px;
}

.chart-content-expandable {
  width: 100%;
}


/* ======= 比例划分 ======= */
.widget-time-curve { flex: 5; min-height: 0; }
.widget-rose-pie { flex: 7; min-height: 0; }

.widget-time-cards {
  padding: 0;
  background: transparent;
  box-shadow: none;
  min-height: 0;
}

.widget-rag-trend { min-height: 0; }
.widget-vector-scatter { min-height: 0; }
.widget-materials-block { min-height: 0; }
.widget-difficulty-bar { flex: 1; min-height: 0; }
.widget-recent-history { flex: 1; min-height: 0; }


/* ======= 特殊组件：节省时间层叠卡片 ======= */
.time-cards-container {
  position: relative;
  width: 100%;
  height: 100%;
}

.time-cards-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.time-card-grid {
  border-radius: 12px;
  padding: 16px;
  border: 1px solid #eee;
  border-left: 3px solid #c0392b;
  background: #fff;
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 100px;
}

.card-personal-avg { background: #fff0f0; border-left-color: #c0392b; }
.card-personal-total { background: #111; color: #fff; border-left-color: #111; }
.card-all-avg { background: #ecf5ff; border-left-color: #2980b9; }
.card-all-total { background: #0b2233; color: #fff; border-left-color: #0b2233; }

.time-card-grid .card-label { font-size: 12px; font-weight: 700; }
.time-card-grid .card-value { font-size: 22px; font-weight: 900; }

.time-card {
  position: absolute;
  border-radius: 16px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

/* 右下底层卡片 (总计时间) */
.card-bottom {
  right: 0;
  bottom: 0;
  width: 65%;
  height: 80%;
  background: #000;
  color: #fff;
  z-index: 1;
  cursor: pointer;
}
.card-bottom .card-label { color: #aaa; }

/* 左上顶层卡片 (平均时间) */
.card-top {
  left: 0;
  top: 0;
  width: 65%;
  height: 80%;
  background: var(--color-primary);
  color: #000;
  z-index: 2;
  border: 1px solid rgba(0,0,0,0.05);
}

/* 核心互动效果：鼠标悬浮底层卡片时，它浮上来放大，顶层卡片缩下去 */
.time-cards-container:hover .card-bottom {
  z-index: 3;
  transform: scale(1.05) translate(-10px, -10px);
  box-shadow: 0 15px 40px rgba(0,0,0,0.3);
}

.time-cards-container:hover .card-top {
  z-index: 1;
  transform: scale(0.95) translate(10px, 10px);
  opacity: 0.8;
}

.card-label {
  font-size: 13px;
  font-weight: bold;
  margin-bottom: 8px;
}

.card-value {
  font-size: 32px;
  font-weight: 900;
  line-height: 1;
}

.card-value small {
  font-size: 14px;
  font-weight: normal;
}

/* ======= 历史记录卡片 ======= */
.history-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  margin-top: 10px;
}
.mock-history-item {
  background: #fafafa;
  padding: 15px;
  border-radius: 12px;
  border: 1px solid #eee;
  cursor: pointer;
  transition: all 0.2s;
}
.mock-history-item:hover {
  background: #fff;
  border-color: #000;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  transform: translateY(-2px);
}
.mock-history-item .time {
  font-size: 12px;
  color: #999;
  display: block;
  margin-bottom: 8px;
}
.mock-history-item .text {
  margin: 0 0 10px 0;
  font-size: 15px;
  color: #000;
  font-weight: bold;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.4;
}
.history-tags {
  display: flex;
}
.h-tag {
  background: #000;
  color: #fff;
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 11px;
}
</style>
