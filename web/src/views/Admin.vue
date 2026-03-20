<template>
  <div class="admin-page">
    <div class="admin-header">
      <h1 class="page-title">管理员控制台</h1>
      <button class="refresh-btn" @click="loadAll">刷新</button>
    </div>

    <div v-if="!isAdmin" class="no-permission">无权限访问</div>
    <template v-else>

      <!-- 统计概览 -->
      <div class="stats-row">
        <div class="stat-card">
          <span class="stat-num">{{ stats.total_users ?? '-' }}</span>
          <span class="stat-label">注册用户</span>
        </div>
        <div class="stat-card">
          <span class="stat-num">{{ stats.total_messages ?? '-' }}</span>
          <span class="stat-label">总解析次数</span>
        </div>
        <div class="stat-card">
          <span class="stat-num">{{ stats.active_users ?? '-' }}</span>
          <span class="stat-label">活跃用户</span>
        </div>
      </div>

      <!-- 管理员专属4卡片 -->
      <div class="time-cards-row">
        <div class="time-card personal">
          <span class="tc-label">个人平均节省</span>
          <span class="tc-value">{{ myStats?.avg_time_saved_minutes || 0 }} <small>分钟/篇</small></span>
        </div>
        <div class="time-card personal">
          <span class="tc-label">个人总计节省</span>
          <span class="tc-value">{{ myStats?.total_time_saved_minutes || 0 }} <small>分钟</small></span>
        </div>
        <div class="time-card global">
          <span class="tc-label">全体平均节省</span>
          <span class="tc-value">{{ allStats?.avg_time_saved_minutes || 0 }} <small>分钟/篇</small></span>
        </div>
        <div class="time-card global">
          <span class="tc-label">全体总计节省</span>
          <span class="tc-value">{{ allStats?.total_time_saved_minutes || 0 }} <small>分钟</small></span>
        </div>
      </div>

      <!-- 节省时间趋势（双曲线） -->
      <div class="section">
        <div class="section-label-row">
          <span class="section-label">节省时间趋势</span>
          <div class="toggle-group">
            <span class="action-tag" :class="{ active: timeChartType === 'line' }" @click="timeChartType = 'line'">曲线</span>
            <span class="action-tag" :class="{ active: timeChartType === 'bar' }" @click="timeChartType = 'bar'">柱状</span>
          </div>
        </div>
        <div ref="timeChartRef" class="chart-area"></div>
      </div>

      <!-- 图表切换区（个人/全体） -->
      <div class="section">
        <div class="section-label-row">
          <span class="section-label">分布分析</span>
          <div class="toggle-group">
            <span class="action-tag" :class="{ active: distScope === 'personal' }" @click="distScope = 'personal'">个人</span>
            <span class="action-tag" :class="{ active: distScope === 'all' }" @click="distScope = 'all'">全体</span>
          </div>
        </div>
        <div class="dist-grid">
          <div>
            <div class="chart-sub-label">通知类型分布</div>
            <div ref="roseChartRef" class="chart-area-sm"></div>
          </div>
          <div>
            <div class="chart-sub-label">高频材料分析</div>
            <div ref="scatterChartRef" class="chart-area-sm"></div>
          </div>
          <div>
            <div class="chart-sub-label">核心材料 Top5</div>
            <div ref="barChartRef" class="chart-area-sm"></div>
          </div>
          <div>
            <div class="chart-sub-label">通知难度评估</div>
            <div ref="diffChartRef" class="chart-area-sm"></div>
          </div>
        </div>
      </div>

      <!-- 用户列表 -->
      <div class="section">
        <div class="section-label-row">
          <span class="section-label">用户管理</span>
        </div>
        <div v-if="usersLoading" class="loading-text">加载中...</div>
        <table v-else class="user-table">
          <thead>
            <tr>
              <th>头像</th><th>UID</th><th>用户名</th><th>邮箱</th><th>注册时间</th><th>身份</th><th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in users" :key="u.uid">
              <td>
                <img v-if="u.avatar_url" :src="u.avatar_url" class="user-avatar-thumb" alt="avatar" />
                <div v-else class="avatar-placeholder-sm">
                  <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                </div>
              </td>
              <td>{{ u.uid }}</td>
              <td>{{ u.uname }}</td>
              <td>{{ u.email }}</td>
              <td>{{ u.created_time?.slice(0, 10) }}</td>
              <td>
                <span :class="u.is_admin ? 'badge-admin' : 'badge-user'">
                  {{ u.is_admin ? '管理员' : '普通用户' }}
                </span>
              </td>
              <td class="action-cell">
                <button class="tbl-btn" @click="toggleAdmin(u.uid)" :disabled="u.uid === selfUid">
                  {{ u.is_admin ? '撤销管理员' : '设为管理员' }}
                </button>
                <button class="tbl-btn danger" @click="deleteUser(u.uid)" :disabled="u.uid === selfUid">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 用户解析量图表 -->
      <div class="section">
        <span class="section-label">各用户解析量</span>
        <div class="bar-list">
          <div v-for="item in stats.user_message_counts || []" :key="item.user_id" class="bar-row">
            <span class="bar-uid">UID {{ item.user_id }}</span>
            <div class="bar-track">
              <div class="bar-fill" :style="{ width: barWidth(item.count) }"></div>
            </div>
            <span class="bar-count">{{ item.count }}</span>
          </div>
        </div>
      </div>

    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue';
import { apiClient, API_ROUTES } from '@/router/api_routes.js';
import { useUserStore } from '@/stores/user';
import * as echarts from 'echarts/core';
import { LineChart, BarChart, PieChart, GraphChart } from 'echarts/charts';
import { TitleComponent, TooltipComponent, GridComponent, LegendComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';

echarts.use([LineChart, BarChart, PieChart, GraphChart, TitleComponent, TooltipComponent, GridComponent, LegendComponent, CanvasRenderer]);

const userStore = useUserStore();
const isAdmin = computed(() => userStore.user?.is_admin);
const selfUid = computed(() => userStore.user?.uid);

const users = ref([]);
const stats = ref({});
const myStats = ref(null);
const allStats = ref(null);
const usersLoading = ref(true);
const timeChartType = ref('line');
const distScope = ref('personal');

const timeChartRef = ref(null);
const roseChartRef = ref(null);
const scatterChartRef = ref(null);
const barChartRef = ref(null);
const diffChartRef = ref(null);

let timeChart = null, roseChart = null, scatterChart = null, barChart = null, diffChart = null;

onMounted(() => { if (isAdmin.value) loadAll(); });
onUnmounted(() => { [timeChart, roseChart, scatterChart, barChart, diffChart].forEach(c => c?.dispose()); });

async function loadAll() {
  usersLoading.value = true;
  try {
    const [usersRes, statsRes, myRes, allRes] = await Promise.all([
      apiClient.get(API_ROUTES.ADMIN_USERS),
      apiClient.get(API_ROUTES.ADMIN_STATS),
      apiClient.get(API_ROUTES.ANALYSIS_ME),
      apiClient.get(API_ROUTES.ADMIN_ANALYSIS_ALL),
    ]);
    users.value = usersRes.data;
    stats.value = statsRes.data;
    myStats.value = myRes.data;
    allStats.value = allRes.data;
    await nextTick();
    renderAllCharts();
  } catch (e) {
    console.warn('管理员数据加载失败', e);
  } finally {
    usersLoading.value = false;
  }
}

function renderAllCharts() {
  renderTimeChart();
  renderDistCharts();
}

function renderTimeChart() {
  if (!timeChartRef.value) return;
  if (!timeChart) timeChart = echarts.init(timeChartRef.value);
  const myDist = myStats.value?.time_saved_distribution || {};
  const allDist = allStats.value?.time_saved_distribution || {};
  const keys = Array.from(new Set([...Object.keys(myDist), ...Object.keys(allDist)]));
  timeChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['个人节省', '全体节省'], top: 0 },
    grid: { top: 36, bottom: 24, left: 40, right: 20 },
    xAxis: { type: 'category', data: keys, axisLabel: { fontSize: 10 } },
    yAxis: { type: 'value', name: '分钟' },
    series: [
      {
        name: '个人节省', type: timeChartType.value,
        data: keys.map(k => myDist[k] || 0),
        itemStyle: { color: '#c0392b' }, smooth: true,
        areaStyle: timeChartType.value === 'line' ? { color: 'rgba(192,57,43,0.1)' } : undefined,
      },
      {
        name: '全体节省', type: timeChartType.value,
        data: keys.map(k => allDist[k] || 0),
        itemStyle: { color: '#2980b9' }, smooth: true,
        areaStyle: timeChartType.value === 'line' ? { color: 'rgba(41,128,185,0.1)' } : undefined,
      }
    ]
  }, true);
}

function getDistData() {
  return distScope.value === 'personal' ? myStats.value : allStats.value;
}

function renderDistCharts() {
  const d = getDistData();
  if (!d) return;

  // 玫瑰图
  if (roseChartRef.value) {
    if (!roseChart) roseChart = echarts.init(roseChartRef.value);
    const roseData = Object.entries(d.notice_type_distribution || {}).map(([name, value]) => ({ name, value }));
    roseChart.setOption({
      color: ['#c0392b', '#e67e22', '#f1c40f', '#7f8c8d', '#95a5a6'],
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      series: [{ type: 'pie', roseType: 'radius', radius: ['15%', '75%'], center: ['50%', '55%'],
        itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
        label: { show: true, formatter: '{b}\n{c}', fontSize: 10 },
        animationType: 'expansion', animationEasing: 'cubicOut', startAngle: 90, clockwise: true,
        data: roseData.sort((a, b) => a.value - b.value) }]
    }, true);
  }

  // 点云
  if (scatterChartRef.value) {
    if (!scatterChart) scatterChart = echarts.init(scatterChartRef.value);
    const nodes = Object.entries(d.materials_freq || {}).slice(0, 15).map(([name, value], i) => ({
      name, value,
      symbolSize: Math.max(36, 28 + Math.sqrt(value) * 12),
      itemStyle: { color: ['#c0392b','#e67e22','#f1c40f','#7f8c8d','#922b21'][i % 5] },
      label: { show: true, position: 'bottom', formatter: '{b}', fontSize: 10 }
    }));
    scatterChart.setOption({
      tooltip: { formatter: p => p.dataType === 'node' ? `${p.name}: ${p.value}次` : '' },
      series: [{ type: 'graph', layout: 'force', data: nodes,
        force: { repulsion: 200, gravity: 0.08, layoutAnimation: true }, roam: false, draggable: true }]
    }, true);
  }

  // Top5柱状
  if (barChartRef.value) {
    if (!barChart) barChart = echarts.init(barChartRef.value);
    const top5 = Object.entries(d.materials_freq || {}).sort((a,b) => b[1]-a[1]).slice(0,5);
    barChart.setOption({
      tooltip: { trigger: 'axis' },
      grid: { top: 10, bottom: 30, left: 60, right: 10 },
      xAxis: { type: 'value' },
      yAxis: { type: 'category', data: top5.map(i=>i[0]), axisLabel: { fontSize: 10 } },
      series: [{ type: 'bar', data: top5.map(i=>i[1]),
        itemStyle: { color: p => ['#c0392b','#e67e22','#f1c40f','#7f8c8d','#922b21'][p.dataIndex % 5] } }]
    }, true);
  }

  // 难度
  if (diffChartRef.value) {
    if (!diffChart) diffChart = echarts.init(diffChartRef.value);
    const cd = d.complexity_distribution || {};
    const cats = [...new Set(Object.keys(cd).map(k => k.split('-')[0]))];
    const levels = ['高', '中', '低'];
    diffChart.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      legend: { data: levels, top: 0, textStyle: { fontSize: 10 } },
      grid: { top: 30, bottom: 24, left: 50, right: 10 },
      xAxis: { type: 'category', data: cats, axisLabel: { fontSize: 9 } },
      yAxis: { type: 'value' },
      series: levels.map((lv, i) => ({
        name: lv, type: 'bar', stack: 'total',
        data: cats.map(c => cd[`${c}-${lv}`] || 0),
        itemStyle: { color: ['#c0392b','#e67e22','#27ae60'][i] }
      }))
    }, true);
  }
}

watch(timeChartType, () => renderTimeChart());
watch(distScope, () => renderDistCharts());

async function toggleAdmin(uid) {
  try {
    const res = await apiClient.patch(`/admin/users/${uid}/toggle-admin`);
    const u = users.value.find(u => u.uid === uid);
    if (u) u.is_admin = res.data.is_admin;
  } catch (e) { console.warn(e); }
}

async function deleteUser(uid) {
  if (!confirm('确认删除该用户？此操作不可撤销。')) return;
  try {
    await apiClient.delete(`/admin/users/${uid}`);
    users.value = users.value.filter(u => u.uid !== uid);
  } catch (e) { console.warn(e); }
}

const maxCount = computed(() => Math.max(...(stats.value.user_message_counts || []).map(i => i.count), 1));
const barWidth = (count) => Math.round((count / maxCount.value) * 100) + '%';
</script>

<style scoped>
.admin-page { display: flex; flex-direction: column; gap: 16px; padding: 20px; overflow-y: auto; height: 100%; box-sizing: border-box; }
.admin-header { display: flex; align-items: center; justify-content: space-between; }
.page-title { font-size: 20px; font-weight: 800; color: #111; margin: 0; }
.no-permission { text-align: center; color: #aaa; padding: 60px 0; font-size: 14px; }

.stats-row { display: flex; gap: 12px; }
.stat-card { flex: 1; background: #fff; border: 1px solid #eee; border-top: 3px solid #c0392b; padding: 16px; display: flex; flex-direction: column; gap: 4px; }
.stat-num { font-size: 28px; font-weight: 800; color: #c0392b; line-height: 1; }
.stat-label { font-size: 12px; color: #888; }

/* 4卡片 */
.time-cards-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.time-card { background: #fff; border: 1px solid #eee; padding: 16px; display: flex; flex-direction: column; gap: 6px; }
.time-card.personal { border-top: 3px solid #c0392b; }
.time-card.global { border-top: 3px solid #2980b9; }
.tc-label { font-size: 11px; color: #888; }
.tc-value { font-size: 22px; font-weight: 800; color: #111; line-height: 1; }
.tc-value small { font-size: 11px; font-weight: 400; color: #aaa; }

.section { background: #fff; border: 1px solid #eee; padding: 16px; display: flex; flex-direction: column; gap: 12px; }
.section-label-row { display: flex; align-items: center; justify-content: space-between; }
.section-label { font-size: 13px; font-weight: 700; color: #111; }
.refresh-btn { background: none; border: 1px solid #ddd; padding: 4px 12px; font-size: 12px; cursor: pointer; }
.refresh-btn:hover { border-color: #c0392b; color: #c0392b; }
.loading-text { color: #aaa; font-size: 13px; }

.toggle-group { display: flex; gap: 4px; }
.action-tag { font-size: 11px; padding: 3px 10px; border-radius: 10px; background: #f0f0f0; color: #666; cursor: pointer; transition: all 0.2s; }
.action-tag.active { background: #c0392b; color: #fff; }

.chart-area { width: 100%; height: 220px; }
.dist-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.chart-sub-label { font-size: 11px; color: #888; font-weight: 600; margin-bottom: 6px; }
.chart-area-sm { width: 100%; height: 180px; }

.user-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.user-table th { text-align: left; padding: 8px 10px; background: #f9f9f9; color: #666; font-weight: 600; border-bottom: 1px solid #eee; }
.user-table td { padding: 8px 10px; border-bottom: 1px solid #f5f5f5; color: #333; vertical-align: middle; }
.badge-admin { background: #c0392b; color: #fff; padding: 2px 8px; font-size: 11px; font-weight: 700; }
.badge-user { background: #f0f0f0; color: #666; padding: 2px 8px; font-size: 11px; }
.action-cell { display: flex; gap: 6px; }
.tbl-btn { background: #f5f5f5; border: none; padding: 4px 10px; font-size: 11px; cursor: pointer; transition: background 0.2s; }
.tbl-btn:hover { background: #e0e0e0; }
.tbl-btn.danger:hover { background: #c0392b; color: #fff; }
.tbl-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.user-avatar-thumb { width: 28px; height: 28px; border-radius: 50%; object-fit: cover; }
.avatar-placeholder-sm { width: 28px; height: 28px; border-radius: 50%; background: #f0f0f0; display: flex; align-items: center; justify-content: center; color: #bbb; }

.bar-list { display: flex; flex-direction: column; gap: 8px; }
.bar-row { display: flex; align-items: center; gap: 10px; }
.bar-uid { font-size: 12px; color: #888; width: 60px; flex-shrink: 0; }
.bar-track { flex: 1; background: #f5f5f5; height: 12px; }
.bar-fill { height: 100%; background: linear-gradient(to right, #c0392b, #e67e22); transition: width 0.4s; }
.bar-count { font-size: 12px; color: #333; width: 30px; text-align: right; flex-shrink: 0; }
</style>
