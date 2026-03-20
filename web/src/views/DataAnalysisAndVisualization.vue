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
        <!-- 节省时间曲线图 -->
        <div class="widget widget-time-curve">
          <div class="widget-header">
            <h3 class="widget-title">节省时间趋势</h3>
            <div class="widget-actions">
               <span
                 class="action-tag"
                 :class="{ active: timeChartType === 'line' }"
                 @click="timeChartType = 'line'"
               >曲线</span>
               <span
                 class="action-tag"
                 :class="{ active: timeChartType === 'bar' }"
                 @click="timeChartType = 'bar'"
               >柱状</span>
            </div>
          </div>
          <div class="chart-content">
            <TimeSavedChart :chartData="statsData?.time_saved_distribution" :chartType="timeChartType" />
          </div>
        </div>

        <!-- 通知类型玫瑰图 -->
        <div class="widget widget-rose-pie">
          <h3 class="widget-title">通知类型分布</h3>
          <div class="chart-content">
            <NoticeTypeRoseChart :chartData="statsData?.notice_type_distribution" />
          </div>
        </div>
      </div>

      <!-- ================= 中间列 (上3/4 下1/4) ================= -->
      <div class="col-center">
        <!-- 高频材料统计图 -->
        <div class="widget widget-cloud-scatter">
          <div class="widget-header">
            <h3 class="widget-title">高频材料分析</h3>
            <div class="widget-actions">
               <span
                 class="action-tag"
                 :class="{ active: materialsChartType === 'pie' }"
                 @click="materialsChartType = 'pie'"
               >饼图</span>
               <span
                 class="action-tag"
                 :class="{ active: materialsChartType === 'scatter' }"
                 @click="materialsChartType = 'scatter'"
               >点云</span>
               <span
                 class="action-tag"
                 :class="{ active: materialsChartType === 'wordCloud' }"
                 @click="materialsChartType = 'wordCloud'"
               >词云</span>
            </div>
          </div>
          <div class="chart-content">
            <MaterialsPieChart v-if="materialsChartType === 'pie'" :chartData="statsData?.materials_freq" />
            <MaterialsScatterChart v-else-if="materialsChartType === 'scatter'" :chartData="statsData?.materials_freq" />
            <MaterialsWordCloud v-else-if="materialsChartType === 'wordCloud'" :chartData="statsData?.materials_freq" />
          </div>
        </div>

        <!-- 节省时间叠放卡片 -->
        <div class="widget widget-time-cards">
          <div class="time-cards-container">
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
      </div>

      <!-- ================= 右侧列 (1/3, 1/3, 1/3) ================= -->
      <div class="col-right">
        <!-- TOP5 所需材料 -->
        <div class="widget widget-top-materials" :class="{ 'expanded': isMaterialsExpanded }">
          <div class="widget-header">
             <h3 class="widget-title">核心材料 Top5</h3>
             <button class="expand-btn" @click="isMaterialsExpanded = !isMaterialsExpanded">
                <svg v-if="!isMaterialsExpanded" viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" class="css-i6dzq1"><polyline points="6 9 12 15 18 9"></polyline></svg>
                <svg v-else viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" class="css-i6dzq1"><polyline points="18 15 12 9 6 15"></polyline></svg>
             </button>
          </div>
          <div class="chart-content-expandable">
            <TopMaterialsBarChart :chartData="statsData?.materials_freq" :isExpanded="isMaterialsExpanded" />
          </div>
        </div>

        <!-- 通知难度分布 -->
        <div class="widget widget-difficulty-bar" v-show="!isMaterialsExpanded">
          <h3 class="widget-title">通知难度评估</h3>
          <div class="chart-content">
             <DifficultyBarChart :chartData="statsData?.complexity_distribution" />
          </div>
        </div>

        <!-- 最近会话历史 -->
        <div class="widget widget-recent-history" v-show="!isMaterialsExpanded">
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
import { ref, onMounted } from 'vue';
import { useUserStore } from '@/stores/auth.js';
import { apiClient, API_ROUTES } from '@/router/api_routes';
import TimeSavedChart from '@/components/Analysis/TimeSavedChart.vue';
import NoticeTypeRoseChart from '@/components/Analysis/NoticeTypeRoseChart.vue';
import MaterialsPieChart from '@/components/Analysis/MaterialsPieChart.vue';
import MaterialsScatterChart from '@/components/Analysis/MaterialsScatterChart.vue';
import MaterialsWordCloud from '@/components/Analysis/MaterialsWordCloud.vue';
import TopMaterialsBarChart from '@/components/Analysis/TopMaterialsBarChart.vue';
import DifficultyBarChart from '@/components/Analysis/DifficultyBarChart.vue';

const userStore = useUserStore();
const loading = ref(true);
const statsData = ref(null);
const recentHistory = ref(null);

// 图表类型控制
const timeChartType = ref('line'); // 默认曲线图
const materialsChartType = ref('scatter'); // 默认点云图
const isMaterialsExpanded = ref(false);

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
    // 获取统计数据
    const res = await apiClient.get(API_ROUTES.ANALYSIS_ME);
    statsData.value = res.data;

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

.widget-cloud-scatter { flex: 3; min-height: 0; }
.widget-time-cards {
  flex: 1;
  padding: 0;
  background: transparent;
  box-shadow: none;
  min-height: 0;
}

.widget-top-materials { flex: 1; min-height: 0; }
.widget-difficulty-bar { flex: 1; min-height: 0; }
.widget-recent-history { flex: 1; min-height: 0; }

.widget-top-materials.expanded {
    flex: 3;
}


/* ======= 特殊组件：节省时间层叠卡片 ======= */
.time-cards-container {
  position: relative;
  width: 100%;
  height: 100%;
}

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
