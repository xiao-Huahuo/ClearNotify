<template>
  <div class="profile-container">
    <div class="profile-header">
      <PolicyTitle title="个人中心" />
      <button v-if="userStore.token" class="more-settings-btn" @click="router.push('/settings')">
        <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="3"></circle>
          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
        </svg>
        更多设置
      </button>
    </div>

    <div v-if="loading && userStore.token" class="loading-state widget-card">
      <div class="spinner"></div>
      <span>正在整理你的个人工作台...</span>
    </div>

    <div v-else-if="userStore.token" class="profile-content">
      <div class="hero-grid">
        <div class="hero-card">
          <div class="hero-main">
            <div class="avatar-shell" title="点击修改头像" @click="showAvatarEditor = true">
              <img v-if="displayAvatar" :src="displayAvatar" alt="avatar" class="user-avatar" />
              <svg v-else viewBox="0 0 24 24" width="42" height="42" stroke="currentColor" stroke-width="1.8" fill="none" stroke-linecap="round" stroke-linejoin="round">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                <circle cx="12" cy="7" r="4"></circle>
              </svg>
            </div>

            <div class="hero-copy">
              <div class="hero-title-row">
                <h2 class="username">{{ userStore.user?.uname || '加载中...' }}</h2>
                <span class="role-badge" :class="roleBadgeClass">{{ roleLabel }}</span>
              </div>
              <p class="user-email">{{ userStore.user?.email || '暂无邮箱' }}</p>
              <div class="meta-row">
                <span class="status-pill" :class="userStore.user?.email_verified ? 'status-pill--ok' : 'status-pill--warn'">
                  {{ userStore.user?.email_verified ? '邮箱已验证' : '邮箱待验证' }}
                </span>
                <span class="status-pill">注册于 {{ formatShortDate(userStore.user?.created_time) }}</span>
                <span class="status-pill">最近登录 {{ formatShortDate(userStore.user?.last_login) }}</span>
              </div>
              <p class="hero-desc">{{ activitySummary }}</p>
            </div>
          </div>

          <div class="hero-actions">
            <button class="hero-btn hero-btn--primary" @click="router.push('/data-analysis-and-visualization')">查看数据分析</button>
            <button class="hero-btn hero-btn--ghost" @click="router.push('/settings')">进入设置中心</button>
            <button v-if="isAdmin" class="hero-btn hero-btn--ghost" @click="router.push('/admin')">管理员控制台</button>
            <button v-else-if="isCertified" class="hero-btn hero-btn--ghost" @click="router.push('/certified-analysis')">认证分析视图</button>
            <button v-if="canRequestUpgrade" class="hero-btn hero-btn--ghost" :disabled="permissionLoading" @click="handlePermissionAction('upgrade')">
              {{ permissionActionLabel }}
            </button>
            <button v-if="canRequestDowngrade" class="hero-btn hero-btn--danger" :disabled="permissionLoading" @click="handlePermissionAction('downgrade')">申请降级</button>
            <button class="hero-btn hero-btn--ghost" @click="handleLogout">退出登录</button>
          </div>
        </div>

        <div class="hero-side">
          <div class="focus-card focus-card--primary">
            <span class="focus-label">累计节省时间</span>
            <span class="focus-value">{{ statsData?.total_time_saved_minutes || 0 }} <small>分钟</small></span>
            <p class="focus-hint">{{ efficiencyTag }}</p>
          </div>
          <div class="focus-card focus-card--cool">
            <span class="focus-label">RAG 命中率</span>
            <span class="focus-value">{{ ragHitRate }}<small>%</small></span>
            <p class="focus-hint">共 {{ statsData?.rag_metrics?.query_count || 0 }} 次检索请求</p>
          </div>
        </div>
      </div>

      <div class="stats-row">
        <div class="stat-card stat-card--primary">
          <div class="stat-icon stat-icon--primary">
            <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
              <line x1="16" y1="13" x2="8" y2="13"></line>
              <line x1="16" y1="17" x2="8" y2="17"></line>
            </svg>
          </div>
          <div class="stat-copy">
            <span class="stat-num">{{ statsData?.total_parsed_count || 0 }}</span>
            <span class="stat-label">总解析数</span>
          </div>
        </div>

        <div class="stat-card stat-card--secondary">
          <div class="stat-icon stat-icon--secondary">
            <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none">
              <circle cx="12" cy="12" r="10"></circle>
              <polyline points="12 6 12 12 16 14"></polyline>
            </svg>
          </div>
          <div class="stat-copy">
            <span class="stat-num">{{ statsData?.avg_time_saved_minutes || 0 }}</span>
            <span class="stat-label">平均节省分钟/篇</span>
          </div>
        </div>

        <div class="stat-card stat-card--cool">
          <div class="stat-icon stat-icon--cool">
            <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none">
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
            </svg>
          </div>
          <div class="stat-copy">
            <span class="stat-num">{{ favoriteCount }}</span>
            <span class="stat-label">收藏条目</span>
          </div>
        </div>

        <div class="stat-card stat-card--mint">
          <div class="stat-icon stat-icon--mint">
            <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none">
              <polyline points="9 11 12 14 22 4"></polyline>
              <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path>
            </svg>
          </div>
          <div class="stat-copy">
            <span class="stat-num">{{ pendingTodoCount }}</span>
            <span class="stat-label">待办事项</span>
          </div>
        </div>

        <div class="stat-card stat-card--neutral">
          <div class="stat-icon stat-icon--neutral">
            <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none">
              <path d="M8 6h13"></path>
              <path d="M8 12h13"></path>
              <path d="M8 18h13"></path>
              <path d="M3 6h.01"></path>
              <path d="M3 12h.01"></path>
              <path d="M3 18h.01"></path>
            </svg>
          </div>
          <div class="stat-copy">
            <span class="stat-num">{{ recentHistory.length }}</span>
            <span class="stat-label">最近动态条目</span>
          </div>
        </div>

        <div class="stat-card stat-card--accent">
          <div class="stat-icon stat-icon--accent">
            <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none">
              <path d="M12 20V10"></path>
              <path d="M18 20V4"></path>
              <path d="M6 20v-4"></path>
            </svg>
          </div>
          <div class="stat-copy">
            <span class="stat-num">{{ completedTodoCount }}</span>
            <span class="stat-label">已完成待办</span>
          </div>
        </div>
      </div>

      <div class="section quick-section">
        <div class="section-head">
          <span class="section-label">快捷入口</span>
          <span class="section-hint">延续当前工作流的下一步动作</span>
        </div>
        <div class="quick-grid">
          <button v-for="action in quickActions" :key="action.label" class="quick-card" @click="router.push(action.to)">
            <span class="quick-icon" :class="`quick-icon--${action.tone}`" v-html="action.icon"></span>
            <span class="quick-title">{{ action.label }}</span>
            <span class="quick-desc">{{ action.desc }}</span>
          </button>
        </div>
      </div>

      <div class="content-grid">
        <div class="section section-history">
          <div class="section-head">
            <span class="section-label">最近解析</span>
            <button class="section-link" @click="router.push('/history')">查看全部</button>
          </div>
          <div v-if="recentHistory.length" class="list-block">
            <button v-for="item in recentHistory" :key="item.id" class="list-item" @click="restoreHistory(item.id)">
              <div class="list-main">
                <span class="list-title">{{ getMessageTitle(item) }}</span>
                <span class="list-desc">{{ formatPreview(item.original_text, 84) }}</span>
              </div>
              <div class="list-meta">
                <span class="list-time">{{ formatMiniDate(item.created_time) }}</span>
                <span class="mini-tag">{{ item.chat_analysis?.notice_type || '文档' }}</span>
              </div>
            </button>
          </div>
          <div v-else class="empty-panel">还没有解析记录，先去上传或粘贴一份政策文件。</div>
        </div>

        <div class="side-stack">
          <div class="section">
            <div class="section-head">
              <span class="section-label">最近收藏</span>
              <button class="section-link" @click="router.push('/favorites')">查看全部</button>
            </div>
            <div v-if="recentFavorites.length" class="mini-list">
              <button v-for="item in recentFavorites" :key="item.fav.id" class="mini-item" @click="openFavorite(item.message)">
                <div class="mini-copy">
                  <span class="mini-title">{{ getMessageTitle(item.message) }}</span>
                  <span class="mini-sub">{{ formatMiniDate(item.fav.created_time) }}</span>
                </div>
                <span class="mini-tag mini-tag--solid">{{ item.message?.chat_analysis?.notice_type || '收藏' }}</span>
              </button>
            </div>
            <div v-else class="empty-panel">暂无收藏，看到重要政策时可以先星标沉淀。</div>
          </div>

          <div class="section">
            <div class="section-head">
              <span class="section-label">待办进度</span>
              <button class="section-link" @click="router.push('/todo')">查看全部</button>
            </div>
            <div v-if="recentTodos.length" class="mini-list">
              <div v-for="todo in recentTodos" :key="todo.id" class="mini-item mini-item--todo">
                <button class="todo-toggle" :class="{ done: todo.is_done }" @click.stop="toggleTodo(todo)">
                  <svg v-if="todo.is_done" viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2.5" fill="none">
                    <polyline points="20 6 9 17 4 12"></polyline>
                  </svg>
                </button>
                <div class="mini-copy">
                  <span class="mini-title">{{ todo.title }}</span>
                  <span class="mini-sub">{{ todo.deadline || (todo.is_done ? '已完成' : '待处理') }}</span>
                </div>
                <span class="mini-tag" :class="todo.is_done ? 'mini-tag--done' : 'mini-tag--pending'">{{ todo.is_done ? '完成' : '待办' }}</span>
              </div>
            </div>
            <div v-else class="empty-panel">暂无待办事项，解析生成或手动新增后会出现在这里。</div>
          </div>
        </div>
      </div>

      <div class="section">
        <div class="section-head">
          <span class="section-label">个人画像</span>
          <span class="section-hint">基于最近解析习惯自动归纳的工作偏好</span>
        </div>
        <div class="insight-grid">
          <div class="metric-card metric-card--primary">
            <span class="metric-label">主处理类型</span>
            <span class="metric-value">{{ topNoticeType.label }}</span>
            <span class="metric-foot">共 {{ topNoticeType.value }} 次</span>
          </div>
          <div class="metric-card metric-card--secondary">
            <span class="metric-label">复杂度偏好</span>
            <span class="metric-value">{{ complexityPreference }}</span>
            <span class="metric-foot">来自最近解析结果结构分布</span>
          </div>
          <div class="metric-card metric-card--cool">
            <span class="metric-label">检索相关度</span>
            <span class="metric-value">{{ ragAvgScore }}</span>
            <span class="metric-foot">平均分，越高越稳定</span>
          </div>
          <div class="metric-card metric-card--mint">
            <span class="metric-label">工作标签</span>
            <span class="metric-value">{{ workStyleTag }}</span>
            <span class="metric-foot">综合解析、收藏与待办生成</span>
          </div>
        </div>

        <div class="insight-panels">
          <div class="insight-panel">
            <div class="insight-title">高频材料 Top3</div>
            <div class="chip-group">
              <span v-for="item in topMaterials" :key="item.label" class="insight-chip insight-chip--primary">{{ item.label }} · {{ item.value }}</span>
              <span v-if="!topMaterials.length" class="insight-chip insight-chip--muted">暂无材料画像</span>
            </div>
          </div>

          <div class="insight-panel">
            <div class="insight-title">风险提示关键词</div>
            <div class="chip-group">
              <span v-for="item in topRisks" :key="item.label" class="insight-chip insight-chip--secondary">{{ item.label }} · {{ item.value }}</span>
              <span v-if="!topRisks.length" class="insight-chip insight-chip--muted">暂无风险画像</span>
            </div>
          </div>

          <div class="insight-panel">
            <div class="insight-title">偏好快照</div>
            <div class="chip-group">
              <span class="insight-chip insight-chip--cool">主题 {{ themeLabel }}</span>
              <span class="insight-chip insight-chip--cool">色系 {{ colorSchemeLabel }}</span>
              <span class="insight-chip insight-chip--cool">通知 {{ settingsStore.settings.system_notifications ? '开启' : '关闭' }}</span>
              <span class="insight-chip insight-chip--cool">默认对象 {{ audienceLabel }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="login-prompt widget-card">
      <div class="empty-icon">
        <svg viewBox="0 0 24 24" width="48" height="48" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
          <circle cx="12" cy="7" r="4"></circle>
        </svg>
      </div>
      <h2>你尚未登录</h2>
      <p class="desc">登录后即可查看你的个人驾驶舱、动态摘要和偏好画像。</p>
      <button class="primary-btn" @click="openLoginModal">立即登录 / 注册</button>
    </div>

    <Modal :isOpen="showAvatarEditor" @close="showAvatarEditor = false">
      <AvatarEditor @close="showAvatarEditor = false" @saved="handleAvatarSaved" />
    </Modal>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import PolicyTitle from '@/components/common/PolicyTitle.vue';
import Modal from '@/components/common/Modal.vue';
import AvatarEditor from '@/components/common/AvatarEditor.vue';
import { getChatMessage, getChatMessages } from '@/api/ai.js';
import { apiClient, API_ROUTES } from '@/router/api_routes.js';
import { useUserStore } from '@/stores/auth.js';
import { useSettingsStore } from '@/stores/settings.js';

const router = useRouter();
const userStore = useUserStore();
const settingsStore = useSettingsStore();

const loading = ref(true);
const permissionLoading = ref(false);
const statsData = ref(null);
const recentHistory = ref([]);
const recentFavorites = ref([]);
const recentTodos = ref([]);
const allTodos = ref([]);
const favoriteCount = ref(0);
const showAvatarEditor = ref(false);

const quickActionIcons = {
  parse: '<svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="8" y1="13" x2="16" y2="13"></line><line x1="8" y1="17" x2="13" y2="17"></line></svg>',
  analysis: '<svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none"><path d="M3 3v18h18"></path><path d="M7 14l4-4 3 3 5-7"></path></svg>',
  history: '<svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none"><path d="M3 12a9 9 0 1 0 3-6.7"></path><path d="M3 3v6h6"></path><path d="M12 7v5l3 3"></path></svg>',
  favorite: '<svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>',
  todo: '<svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none"><polyline points="9 11 12 14 22 4"></polyline><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path></svg>',
  admin: '<svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none"><path d="M12 3l7 4v5c0 5-3.5 8-7 9-3.5-1-7-4-7-9V7l7-4z"></path><path d="M9 12l2 2 4-4"></path></svg>',
  certified: '<svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none"><circle cx="12" cy="8" r="5"></circle><path d="M8.21 13.89L7 22l5-3 5 3-1.21-8.11"></path></svg>',
  settings: '<svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82A1.65 1.65 0 0 0 3 14H3a2 2 0 0 1 0-4h.09c.7 0 1.33-.4 1.62-1.03A1.65 1.65 0 0 0 4.38 7.15l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06c.5.5 1.26.65 1.91.38A1.65 1.65 0 0 0 10 3.09V3a2 2 0 0 1 4 0v.09c0 .7.4 1.33 1.03 1.62.65.27 1.41.12 1.91-.38l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06c-.5.5-.65 1.26-.38 1.91.29.63.92 1.03 1.62 1.03H21a2 2 0 0 1 0 4h-.09c-.7 0-1.33.4-1.62 1.03z"></path></svg>',
};

const roleMap = {
  admin: '管理员',
  certified: '认证主体',
  normal: '普通用户',
};

const audienceMap = {
  none: '保留原意',
  elderly: '老年人',
  student: '学生',
  worker: '打工人',
};

const themeMap = {
  light: '浅色',
  dark: '深色',
  system: '跟随系统',
};

const colorSchemeMap = {
  classic: '经典红',
  'wine-coral': '酒红珊瑚',
  coral: '珊瑚蓝',
};

const isAdmin = computed(() => userStore.user?.role === 'admin');
const isCertified = computed(() => userStore.user?.role === 'certified');
const canRequestUpgrade = computed(() => Boolean(userStore.token) && userStore.user?.role !== 'admin');
const canRequestDowngrade = computed(() => Boolean(userStore.token) && userStore.user?.role !== 'normal');

const roleLabel = computed(() => roleMap[userStore.user?.role] || '普通用户');
const roleBadgeClass = computed(() => {
  if (isAdmin.value) return 'role-admin';
  if (isCertified.value) return 'role-certified';
  return 'role-normal';
});

const displayAvatar = computed(() => {
  const avatarUrl = userStore.user?.avatar_url;
  if (!avatarUrl) return null;
  if (avatarUrl.startsWith('default:')) {
    return `/src/assets/photos/default-avatars/${avatarUrl.substring(8)}`;
  }
  return avatarUrl;
});

const confirmedTodos = computed(() => allTodos.value.filter((todo) => todo.is_confirmed));
const pendingTodoCount = computed(() => confirmedTodos.value.filter((todo) => !todo.is_done).length);
const completedTodoCount = computed(() => confirmedTodos.value.filter((todo) => todo.is_done).length);

const ragHitRate = computed(() => Math.round((Number(statsData.value?.rag_metrics?.hit_rate) || 0) * 100));
const ragAvgScore = computed(() => (Number(statsData.value?.rag_metrics?.avg_score) || 0).toFixed(2));

const topNoticeType = computed(() => {
  const first = rankEntries(statsData.value?.notice_type_distribution, 1)[0];
  return first || { label: '暂无记录', value: 0 };
});

const topMaterials = computed(() => rankEntries(statsData.value?.materials_freq, 3));
const topRisks = computed(() => rankEntries(statsData.value?.risks_freq, 4));

const complexityPreference = computed(() => {
  const distribution = statsData.value?.complexity_distribution || {};
  const candidates = [
    { label: '偏重办理难度', weight: weightedComplexity(distribution, 'handling_complexity') },
    { label: '偏重语言复杂度', weight: weightedComplexity(distribution, 'language_complexity') },
    { label: '偏重风险识别', weight: weightedComplexity(distribution, 'risk_level') },
  ].sort((a, b) => b.weight - a.weight);

  return candidates[0]?.weight ? candidates[0].label : '暂无明显偏好';
});

const efficiencyTag = computed(() => {
  const total = statsData.value?.total_time_saved_minutes || 0;
  const avg = statsData.value?.avg_time_saved_minutes || 0;
  if (total >= 180 || avg >= 12) return '已进入高频使用阶段，时间收益很稳定。';
  if (total >= 60 || avg >= 6) return '已经形成固定节奏，继续收藏重点材料会更省时。';
  if (total > 0) return '节省效果已开始积累，后续会随解析量继续放大。';
  return '首份解析完成后，这里会开始累计你的节省收益。';
});

const workStyleTag = computed(() => {
  if (pendingTodoCount.value >= 6) return '推进执行型';
  if (favoriteCount.value >= 8) return '资料沉淀型';
  if (ragHitRate.value >= 65) return '检索协同型';
  if (recentHistory.value.length >= 4) return '高频快读型';
  return '轻量起步型';
});

const activitySummary = computed(() => {
  const parsed = statsData.value?.total_parsed_count || 0;
  if (!parsed && favoriteCount.value === 0 && pendingTodoCount.value === 0) {
    return '从一次解析开始，个人中心会自动沉淀你的重点材料、处理习惯和后续待办。';
  }
  return `已累计解析 ${parsed} 份记录，收藏 ${favoriteCount.value} 条重点内容，当前有 ${pendingTodoCount.value} 项待办在推进。`;
});

const permissionActionLabel = computed(() => (isCertified.value ? '申请升级管理员' : '申请成为认证主体'));
const themeLabel = computed(() => themeMap[settingsStore.settings.theme_mode] || '跟随系统');
const colorSchemeLabel = computed(() => colorSchemeMap[settingsStore.settings.color_scheme] || '经典红');
const audienceLabel = computed(() => audienceMap[settingsStore.settings.default_audience] || '保留原意');

const quickActions = computed(() => {
  const items = [
    {
      label: '继续解析',
      desc: '返回首页，继续上传、粘贴或改写政策内容。',
      to: '/home',
      tone: 'primary',
      icon: quickActionIcons.parse,
    },
    {
      label: '数据分析',
      desc: '查看个人解析分布、趋势和图表结果。',
      to: '/data-analysis-and-visualization',
      tone: 'secondary',
      icon: quickActionIcons.analysis,
    },
    {
      label: '会话历史',
      desc: '快速恢复最近记录，延续上次工作上下文。',
      to: '/history',
      tone: 'cool',
      icon: quickActionIcons.history,
    },
    {
      label: '收藏夹',
      desc: `当前已沉淀 ${favoriteCount.value} 条重点内容。`,
      to: '/favorites',
      tone: 'mint',
      icon: quickActionIcons.favorite,
    },
    {
      label: '待办中心',
      desc: `还有 ${pendingTodoCount.value} 项待办等待推进。`,
      to: '/todo',
      tone: 'accent',
      icon: quickActionIcons.todo,
    },
  ];

  if (isAdmin.value) {
    items.push({
      label: '管理控制台',
      desc: '查看平台总览、分布分析与用户状态。',
      to: '/admin',
      tone: 'neutral',
      icon: quickActionIcons.admin,
    });
  } else if (isCertified.value) {
    items.push({
      label: '认证分析',
      desc: '进入认证主体专属分析与视图页面。',
      to: '/certified-analysis',
      tone: 'neutral',
      icon: quickActionIcons.certified,
    });
  } else {
    items.push({
      label: '系统设置',
      desc: '调整主题、通知和默认受众偏好。',
      to: '/settings',
      tone: 'neutral',
      icon: quickActionIcons.settings,
    });
  }

  return items;
});

function rankEntries(source, limit = 3) {
  return Object.entries(source || {})
    .sort((a, b) => b[1] - a[1])
    .slice(0, limit)
    .map(([label, value]) => ({ label, value }));
}

function weightedComplexity(distribution, category) {
  return (distribution[`${category}-高`] || 0) * 3
    + (distribution[`${category}-中`] || 0) * 2
    + (distribution[`${category}-低`] || 0);
}

function formatShortDate(value) {
  if (!value) return '暂无';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '暂无';
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).replaceAll('/', '-');
}

function formatMiniDate(value) {
  if (!value) return '--';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '--';
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).replace('/', '-');
}

function getMessageTitle(message) {
  const rawText = `${message?.original_text || ''}`.replace(/\s+/g, ' ').trim();
  if (!rawText) return message?.chat_analysis?.notice_type || '未命名记录';
  return rawText.length > 26 ? `${rawText.slice(0, 26)}...` : rawText;
}

function formatPreview(text, limit = 84) {
  const normalized = `${text || ''}`.replace(/\s+/g, ' ').trim();
  if (!normalized) return '暂无内容摘要';
  return normalized.length > limit ? `${normalized.slice(0, limit)}...` : normalized;
}

function openLoginModal() {
  window.dispatchEvent(new CustomEvent('open-login-modal'));
}

async function handleAvatarSaved() {
  showAvatarEditor.value = false;
  await userStore.fetchUser();
}

function handleLogout() {
  if (!confirm('确定要退出登录吗？')) return;
  userStore.logout();
  router.push('/');
}

async function restoreHistory(id) {
  if (!id) return;
  try {
    const res = await getChatMessage(id);
    sessionStorage.setItem('restoredChatMessage', JSON.stringify(res.data));
    router.push('/home');
  } catch (error) {
    alert(error.response?.data?.detail || '恢复记录失败');
  }
}

function openFavorite(message) {
  if (!message?.id) return;
  restoreHistory(message.id);
}

function rebuildRecentTodos() {
  recentTodos.value = allTodos.value.filter((todo) => todo.is_confirmed).slice(0, 4);
}

async function toggleTodo(todo) {
  if (!todo?.id) return;
  try {
    const res = await apiClient.patch(`/todo/${todo.id}/toggle`);
    const updatedTodo = res.data;
    allTodos.value = allTodos.value.map((item) => (item.id === updatedTodo.id ? updatedTodo : item));
    rebuildRecentTodos();
  } catch (error) {
    console.warn('切换待办状态失败', error);
  }
}

async function handlePermissionAction(mode) {
  if (permissionLoading.value) return;
  permissionLoading.value = true;
  try {
    if (mode === 'downgrade') {
      if (!confirm('确认降级为普通用户吗？此操作会立即生效。')) return;
      const res = await apiClient.post(API_ROUTES.REQUEST_PERMISSION_DOWNGRADE);
      if (userStore.user) userStore.user.role = 'normal';
      alert(res.data?.message || '已降级为普通用户');
      return;
    }

    const res = await apiClient.post(API_ROUTES.REQUEST_PERMISSION_UPGRADE);
    alert(res.data?.message || '升级申请已提交');
  } catch (error) {
    alert(error.response?.data?.detail || '权限操作失败');
  } finally {
    permissionLoading.value = false;
  }
}

async function fetchFavoritesSummary() {
  recentFavorites.value = [];
  favoriteCount.value = 0;
  try {
    const res = await apiClient.get(API_ROUTES.FAVORITE);
    const favorites = Array.isArray(res.data) ? res.data : [];
    favoriteCount.value = favorites.length;

    const summary = await Promise.all(
      favorites.slice(0, 4).map(async (fav) => {
        try {
          const messageRes = await getChatMessage(fav.chat_message_id);
          return { fav, message: messageRes.data };
        } catch (error) {
          console.warn(`加载收藏消息 ${fav.chat_message_id} 失败`, error);
          return null;
        }
      }),
    );

    recentFavorites.value = summary.filter(Boolean);
  } catch (error) {
    console.warn('加载收藏摘要失败', error);
  }
}

async function fetchTodoSummary() {
  recentTodos.value = [];
  allTodos.value = [];
  try {
    const res = await apiClient.get(`${API_ROUTES.TODO}?confirmed_only=false`);
    allTodos.value = Array.isArray(res.data) ? res.data : [];
    rebuildRecentTodos();
  } catch (error) {
    console.warn('加载待办摘要失败', error);
  }
}

async function fetchProfileData() {
  loading.value = true;
  statsData.value = null;
  recentHistory.value = [];

  try {
    await Promise.allSettled([userStore.fetchUser(), settingsStore.fetchSettings()]);
    if (!userStore.token || !userStore.user) return;

    const [analysisRes, historyRes] = await Promise.allSettled([
      apiClient.get(API_ROUTES.ANALYSIS_ME),
      getChatMessages({ limit: 4, sort_by: 'created_time', sort_order: 'desc' }),
      fetchFavoritesSummary(),
      fetchTodoSummary(),
    ]);

    if (analysisRes.status === 'fulfilled') {
      statsData.value = analysisRes.value.data || null;
    } else {
      console.warn('加载个人统计失败', analysisRes.reason);
    }

    if (historyRes.status === 'fulfilled') {
      recentHistory.value = Array.isArray(historyRes.value.data) ? historyRes.value.data : [];
    } else {
      console.warn('加载最近解析失败', historyRes.reason);
    }
  } catch (error) {
    console.warn('加载个人中心失败', error);
  } finally {
    loading.value = false;
  }
}

onMounted(async () => {
  if (!userStore.token) {
    loading.value = false;
    return;
  }

  await fetchProfileData();
});
</script>

<style scoped>
.profile-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 16px 20px 24px;
  height: 100%;
  box-sizing: border-box;
  overflow-y: auto;
}

.profile-header,
.section-head,
.hero-title-row,
.hero-main {
  display: flex;
  align-items: center;
}

.profile-header,
.section-head {
  justify-content: space-between;
  gap: 12px;
}

.widget-card,
.hero-card,
.section,
.focus-card,
.stat-card,
.quick-card,
.metric-card,
.insight-panel {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  box-shadow: 0 14px 34px color-mix(in srgb, var(--color-primary) 8%, transparent);
}

.more-settings-btn,
.hero-btn,
.section-link,
.primary-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.more-settings-btn {
  border: 1px solid color-mix(in srgb, var(--color-primary) 14%, var(--border-color));
  background: color-mix(in srgb, var(--color-primary) 7%, var(--card-bg));
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 700;
  border-radius: 999px;
  padding: 8px 14px;
}

.more-settings-btn:hover {
  color: var(--text-primary);
  background: color-mix(in srgb, var(--color-primary) 12%, var(--card-bg));
}

.loading-state {
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 12px;
  color: var(--text-secondary);
  font-size: 14px;
}

.spinner {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  border: 3px solid color-mix(in srgb, var(--color-primary) 18%, transparent);
  border-top-color: var(--color-primary);
  animation: profile-spin 0.85s linear infinite;
}

@keyframes profile-spin {
  to {
    transform: rotate(360deg);
  }
}

.profile-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.hero-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.8fr) minmax(280px, 0.9fr);
  gap: 12px;
}

.hero-card {
  padding: 20px;
  background:
    radial-gradient(circle at top right, color-mix(in srgb, var(--color-accent-cool) 18%, transparent) 0%, transparent 36%),
    linear-gradient(135deg, color-mix(in srgb, var(--color-primary) 9%, var(--card-bg)) 0%, var(--card-bg) 46%, color-mix(in srgb, var(--color-secondary) 10%, var(--card-bg)) 100%);
}

.hero-main {
  gap: 18px;
  align-items: flex-start;
}

.avatar-shell {
  width: 128px;
  height: 128px;
  border-radius: 24px;
  background:
    linear-gradient(135deg, color-mix(in srgb, var(--color-primary) 18%, transparent), color-mix(in srgb, var(--color-accent-cool) 18%, transparent)),
    var(--card-bg);
  border: 1px solid color-mix(in srgb, var(--color-primary) 18%, var(--border-color));
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  flex-shrink: 0;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.avatar-shell svg {
  width: 56px;
  height: 56px;
}

.avatar-shell:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 24px color-mix(in srgb, var(--color-primary) 18%, transparent);
}

.user-avatar {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.hero-copy {
  min-width: 0;
  flex: 1;
}

.hero-title-row {
  gap: 10px;
  flex-wrap: wrap;
}

.username {
  margin: 0;
  font-size: 30px;
  font-weight: 800;
  line-height: 1.1;
  color: var(--text-primary);
}

.user-email {
  margin: 8px 0 0;
  font-size: 14px;
  color: var(--text-secondary);
}

.role-badge {
  border-radius: 999px;
  padding: 5px 10px;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.4px;
}

.role-admin {
  background: var(--color-primary);
  color: #fff;
}

.role-certified {
  background: color-mix(in srgb, var(--color-accent-cool) 20%, transparent);
  color: color-mix(in srgb, var(--color-accent-cool) 72%, var(--text-primary));
}

.role-normal {
  background: color-mix(in srgb, var(--border-color) 55%, var(--card-bg));
  color: var(--text-secondary);
}

.meta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
}

.status-pill {
  border-radius: 999px;
  padding: 6px 10px;
  font-size: 12px;
  color: var(--text-secondary);
  background: color-mix(in srgb, var(--border-color) 32%, var(--card-bg));
  border: 1px solid color-mix(in srgb, var(--border-color) 80%, transparent);
}

.status-pill--ok {
  color: color-mix(in srgb, var(--color-accent-mint) 70%, var(--text-primary));
  background: color-mix(in srgb, var(--color-accent-mint) 14%, transparent);
  border-color: color-mix(in srgb, var(--color-accent-mint) 28%, transparent);
}

.status-pill--warn {
  color: color-mix(in srgb, var(--color-secondary) 72%, var(--text-primary));
  background: color-mix(in srgb, var(--color-secondary) 14%, transparent);
  border-color: color-mix(in srgb, var(--color-secondary) 28%, transparent);
}

.hero-desc {
  margin: 14px 0 0;
  max-width: 72ch;
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-secondary);
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 18px;
}

.hero-btn {
  min-height: 40px;
  border-radius: 999px;
  padding: 0 16px;
  font-size: 13px;
  font-weight: 700;
  border: 1px solid color-mix(in srgb, var(--color-primary) 12%, var(--border-color));
}

.hero-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.hero-btn--primary {
  border: none;
  color: #fff;
  background: linear-gradient(135deg, var(--color-primary-dark), var(--color-primary), var(--color-secondary));
  box-shadow: 0 12px 22px color-mix(in srgb, var(--color-primary) 20%, transparent);
}

.hero-btn--primary:hover {
  transform: translateY(-1px);
  filter: brightness(1.03);
}

.hero-btn--ghost {
  color: var(--text-primary);
  background: color-mix(in srgb, var(--color-primary) 7%, var(--card-bg));
}

.hero-btn--ghost:hover {
  background: color-mix(in srgb, var(--color-primary) 12%, var(--card-bg));
}

.hero-btn--danger {
  color: #fff;
  border-color: transparent;
  background: linear-gradient(135deg, color-mix(in srgb, var(--color-primary-dark) 80%, #240b0c), var(--color-primary));
}

.hero-btn--danger:hover {
  filter: brightness(1.04);
}

.hero-side {
  display: grid;
  gap: 12px;
}

.focus-card {
  --focus-tone: var(--color-primary);
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  border-left: 3px solid var(--focus-tone);
  background: linear-gradient(160deg, color-mix(in srgb, var(--focus-tone) 10%, var(--card-bg)), var(--card-bg));
}

.focus-card--primary {
  --focus-tone: var(--color-primary);
}

.focus-card--cool {
  --focus-tone: var(--color-accent-cool);
}

.focus-label {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-secondary);
}

.focus-value {
  font-size: 32px;
  font-weight: 800;
  line-height: 1;
  color: var(--text-primary);
}

.focus-value small {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-muted);
}

.focus-hint {
  margin: 0;
  font-size: 12px;
  line-height: 1.6;
  color: var(--text-secondary);
}

.stats-row,
.quick-grid,
.insight-grid,
.insight-panels {
  display: grid;
  gap: 12px;
}

.stats-row {
  grid-template-columns: repeat(6, minmax(0, 1fr));
}

.stat-card {
  --stat-tone: var(--color-primary);
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px;
  border-left: 3px solid var(--stat-tone);
  background: linear-gradient(165deg, color-mix(in srgb, var(--stat-tone) 8%, var(--card-bg)), var(--card-bg));
}

.stat-card--primary {
  --stat-tone: var(--color-primary);
}

.stat-card--secondary {
  --stat-tone: var(--color-secondary);
}

.stat-card--cool {
  --stat-tone: var(--color-accent-cool);
}

.stat-card--mint {
  --stat-tone: var(--color-accent-mint);
}

.stat-card--neutral {
  --stat-tone: color-mix(in srgb, var(--text-secondary) 62%, var(--color-primary) 38%);
}

.stat-card--accent {
  --stat-tone: color-mix(in srgb, var(--color-secondary) 64%, var(--color-primary) 36%);
}

.stat-icon {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-icon--primary {
  color: var(--color-primary-dark);
  background: color-mix(in srgb, var(--color-primary) 16%, transparent);
}

.stat-icon--secondary {
  color: color-mix(in srgb, var(--color-secondary) 78%, var(--text-primary));
  background: color-mix(in srgb, var(--color-secondary) 16%, transparent);
}

.stat-icon--cool {
  color: color-mix(in srgb, var(--color-accent-cool) 78%, var(--text-primary));
  background: color-mix(in srgb, var(--color-accent-cool) 16%, transparent);
}

.stat-icon--mint {
  color: color-mix(in srgb, var(--color-accent-mint) 74%, var(--text-primary));
  background: color-mix(in srgb, var(--color-accent-mint) 16%, transparent);
}

.stat-icon--neutral {
  color: var(--text-secondary);
  background: color-mix(in srgb, var(--border-color) 42%, transparent);
}

.stat-icon--accent {
  color: color-mix(in srgb, var(--color-primary) 64%, var(--color-secondary) 36%);
  background: linear-gradient(135deg, color-mix(in srgb, var(--color-primary) 12%, transparent), color-mix(in srgb, var(--color-secondary) 18%, transparent));
}

.stat-copy {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.stat-num {
  font-size: 28px;
  font-weight: 800;
  line-height: 1;
  color: var(--text-primary);
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.section {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-label {
  font-size: 13px;
  font-weight: 800;
  color: var(--text-primary);
  letter-spacing: 0.3px;
}

.section-hint {
  font-size: 12px;
  color: var(--text-muted);
}

.section-link {
  min-height: 34px;
  padding: 0 14px;
  border-radius: 999px;
  border: 1px solid color-mix(in srgb, var(--color-primary) 12%, var(--border-color));
  background: color-mix(in srgb, var(--color-primary) 6%, var(--card-bg));
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 700;
}

.section-link:hover {
  color: var(--text-primary);
  background: color-mix(in srgb, var(--color-primary) 11%, var(--card-bg));
}

.quick-grid {
  grid-template-columns: repeat(6, minmax(0, 1fr));
}

.quick-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 16px;
  cursor: pointer;
  text-align: left;
  transition: transform 0.2s ease, border-color 0.2s ease;
}

.quick-card:hover {
  transform: translateY(-2px);
  border-color: color-mix(in srgb, var(--color-primary) 26%, var(--border-color));
}

.quick-icon {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.quick-icon :deep(svg) {
  display: block;
}

.quick-icon--primary {
  color: var(--color-primary-dark);
  background: color-mix(in srgb, var(--color-primary) 14%, transparent);
}

.quick-icon--secondary {
  color: color-mix(in srgb, var(--color-secondary) 74%, var(--text-primary));
  background: color-mix(in srgb, var(--color-secondary) 16%, transparent);
}

.quick-icon--cool {
  color: color-mix(in srgb, var(--color-accent-cool) 80%, var(--text-primary));
  background: color-mix(in srgb, var(--color-accent-cool) 14%, transparent);
}

.quick-icon--mint {
  color: color-mix(in srgb, var(--color-accent-mint) 74%, var(--text-primary));
  background: color-mix(in srgb, var(--color-accent-mint) 16%, transparent);
}

.quick-icon--accent {
  color: var(--color-primary);
  background: linear-gradient(135deg, color-mix(in srgb, var(--color-primary) 12%, transparent), color-mix(in srgb, var(--color-secondary) 16%, transparent));
}

.quick-icon--neutral {
  color: var(--text-secondary);
  background: color-mix(in srgb, var(--border-color) 44%, transparent);
}

.quick-title {
  font-size: 14px;
  font-weight: 800;
  color: var(--text-primary);
}

.quick-desc {
  font-size: 12px;
  line-height: 1.6;
  color: var(--text-secondary);
}

.content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(300px, 0.9fr);
  gap: 12px;
}

.side-stack {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.list-block,
.mini-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.list-item,
.mini-item {
  width: 100%;
  border: 1px solid color-mix(in srgb, var(--color-primary) 10%, var(--border-color));
  background: linear-gradient(160deg, color-mix(in srgb, var(--color-primary) 5%, var(--card-bg)), var(--card-bg));
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 14px 16px;
  text-align: left;
  transition: transform 0.2s ease, border-color 0.2s ease;
}

.list-item {
  cursor: pointer;
}

.list-item:hover,
.mini-item:hover {
  transform: translateY(-1px);
  border-color: color-mix(in srgb, var(--color-primary) 22%, var(--border-color));
}

.list-main,
.mini-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.list-title,
.mini-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.list-desc,
.mini-sub {
  font-size: 12px;
  line-height: 1.6;
  color: var(--text-secondary);
}

.list-desc {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.list-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
  flex-shrink: 0;
}

.list-time {
  font-size: 12px;
  color: var(--text-muted);
}

.mini-item--todo {
  align-items: center;
}

.mini-tag {
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 11px;
  font-weight: 700;
  white-space: nowrap;
  color: var(--text-secondary);
  background: color-mix(in srgb, var(--border-color) 40%, var(--card-bg));
}

.mini-tag--solid {
  background: color-mix(in srgb, var(--color-primary) 14%, transparent);
  color: var(--color-primary-dark);
}

.mini-tag--pending {
  background: color-mix(in srgb, var(--color-secondary) 14%, transparent);
  color: color-mix(in srgb, var(--color-secondary) 74%, var(--text-primary));
}

.mini-tag--done {
  background: color-mix(in srgb, var(--color-accent-mint) 14%, transparent);
  color: color-mix(in srgb, var(--color-accent-mint) 74%, var(--text-primary));
}

.todo-toggle {
  width: 28px;
  height: 28px;
  flex-shrink: 0;
  border-radius: 9px;
  border: 1px solid color-mix(in srgb, var(--color-primary) 18%, var(--border-color));
  background: color-mix(in srgb, var(--color-primary) 7%, var(--card-bg));
  color: transparent;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.todo-toggle:hover {
  border-color: var(--color-primary);
}

.todo-toggle.done {
  background: var(--color-primary);
  color: #fff;
  border-color: var(--color-primary);
}

.empty-panel {
  min-height: 106px;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 0 18px;
  border-radius: 14px;
  border: 1px dashed color-mix(in srgb, var(--color-primary) 18%, var(--border-color));
  color: var(--text-muted);
  font-size: 13px;
  line-height: 1.8;
  background: color-mix(in srgb, var(--color-primary) 4%, var(--card-bg));
}

.insight-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.metric-card {
  --metric-tone: var(--color-primary);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  border-left: 3px solid var(--metric-tone);
  background: linear-gradient(165deg, color-mix(in srgb, var(--metric-tone) 9%, var(--card-bg)), var(--card-bg));
}

.metric-card--primary {
  --metric-tone: var(--color-primary);
}

.metric-card--secondary {
  --metric-tone: var(--color-secondary);
}

.metric-card--cool {
  --metric-tone: var(--color-accent-cool);
}

.metric-card--mint {
  --metric-tone: var(--color-accent-mint);
}

.metric-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.metric-value {
  font-size: 26px;
  font-weight: 800;
  line-height: 1.15;
  color: var(--text-primary);
}

.metric-foot {
  font-size: 12px;
  color: var(--text-muted);
}

.insight-panels {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.insight-panel {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.insight-title {
  font-size: 13px;
  font-weight: 800;
  color: var(--text-primary);
}

.chip-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.insight-chip {
  border-radius: 999px;
  padding: 7px 12px;
  font-size: 12px;
  line-height: 1.3;
  color: var(--text-primary);
}

.insight-chip--primary {
  background: color-mix(in srgb, var(--color-primary) 12%, transparent);
}

.insight-chip--secondary {
  background: color-mix(in srgb, var(--color-secondary) 12%, transparent);
}

.insight-chip--cool {
  background: color-mix(in srgb, var(--color-accent-cool) 12%, transparent);
}

.insight-chip--muted {
  background: color-mix(in srgb, var(--border-color) 46%, var(--card-bg));
  color: var(--text-secondary);
}

.login-prompt {
  min-height: 360px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
  text-align: center;
}

.empty-icon {
  width: 88px;
  height: 88px;
  border-radius: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  background: linear-gradient(135deg, color-mix(in srgb, var(--color-primary) 10%, transparent), color-mix(in srgb, var(--color-accent-cool) 12%, transparent));
}

.login-prompt h2 {
  margin: 0;
  font-size: 26px;
  color: var(--text-primary);
}

.desc {
  max-width: 520px;
  margin: 0;
  font-size: 14px;
  line-height: 1.8;
  color: var(--text-secondary);
}

.primary-btn {
  min-height: 42px;
  padding: 0 22px;
  border: none;
  border-radius: 999px;
  color: #fff;
  font-size: 13px;
  font-weight: 800;
  background: linear-gradient(135deg, var(--color-primary-dark), var(--color-primary), var(--color-secondary));
  box-shadow: 0 12px 22px color-mix(in srgb, var(--color-primary) 20%, transparent);
}

.primary-btn:hover {
  transform: translateY(-1px);
  filter: brightness(1.03);
}

@media (max-width: 1500px) {
  .stats-row,
  .quick-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 1180px) {
  .hero-grid,
  .content-grid,
  .insight-panels {
    grid-template-columns: 1fr;
  }

  .hero-side {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .insight-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 980px) {
  .stats-row,
  .quick-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .profile-container {
    padding: 12px;
  }

  .profile-header,
  .section-head,
  .hero-title-row {
    align-items: flex-start;
    flex-direction: column;
  }

  .hero-main {
    flex-direction: column;
  }

  .avatar-shell {
    width: 108px;
    height: 108px;
  }

  .stats-row,
  .quick-grid,
  .hero-side,
  .insight-grid,
  .insight-panels {
    grid-template-columns: 1fr;
  }

  .more-settings-btn,
  .hero-btn,
  .section-link,
  .primary-btn {
    width: 100%;
  }

  .hero-actions {
    width: 100%;
  }

  .list-item,
  .mini-item {
    align-items: flex-start;
    flex-direction: column;
  }

  .list-meta {
    align-items: flex-start;
  }
}
</style>
