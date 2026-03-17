<template>
  <div class="profile-container">
    <div class="profile-header">
      <h1 class="page-title">个人中心</h1>
      <button v-if="userStore.token" class="more-settings-btn" @click="$router.push('/settings')">
        <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
        更多设置
      </button>
    </div>

    <!-- 登录状态 -->
    <div v-if="userStore.token" class="profile-content">

      <!-- 顶部用户信息卡片 -->
      <div class="user-card widget">
        <div class="avatar-placeholder">
          <!-- 默认用户头像 -->
          <svg viewBox="0 0 24 24" width="40" height="40" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
            <circle cx="12" cy="7" r="4"></circle>
          </svg>
        </div>
        <div class="user-info-text">
          <h2 class="username">{{ userStore.user?.uname || '加载中...' }}</h2>
          <p class="user-email">{{ userStore.user?.email || '暂无邮箱' }}</p>
          <span class="status-badge">账号状态：正常</span>
        </div>
      </div>

      <!-- 数据微盘概览 -->
      <div class="stats-mini-board">
        <div class="stat-item widget" @click="$router.push('/feature-b')" style="cursor: pointer;">
          <div class="stat-icon">
            <svg viewBox="0 0 24 24" width="24" height="24" stroke="#000" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
          </div>
          <div class="stat-text">
            <span class="stat-label">总处理文档</span>
            <span class="stat-value">{{ statsData?.total_parsed_count || 0 }} <small>篇</small></span>
          </div>
        </div>
        <div class="stat-item widget highlight-widget" @click="$router.push('/feature-b')" style="cursor: pointer;">
          <div class="stat-icon highlight-icon">
             <svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
          </div>
          <div class="stat-text highlight-text">
            <span class="stat-label">累计为您节省</span>
            <span class="stat-value">{{ statsData?.total_time_saved_minutes || 0 }} <small>分钟</small></span>
          </div>
        </div>
      </div>

    </div>

    <!-- 未登录状态 -->
    <div v-else class="login-prompt widget">
      <div class="empty-icon">
        <svg viewBox="0 0 24 24" width="48" height="48" stroke="#ccc" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
      </div>
      <h2>您尚未登录</h2>
      <p class="desc">登录后即可查看您的数据概览与个人中心</p>
      <button @click="openLoginModal" class="primary-btn">立即登录 / 注册</button>
    </div>

    <!-- 弹窗 -->
    <Modal :isOpen="showModal" @close="closeModal">
      <LoginForm
        v-if="currentForm === 'login'"
        @success="handleLoginSuccess"
        @switch-to-register="currentForm = 'register'"
      />
      <RegisterForm
        v-if="currentForm === 'register'"
        @switch-to-login="currentForm = 'login'"
        @success="currentForm = 'login'"
      />
    </Modal>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useUserStore } from '@/stores/user';
import { apiClient, API_ROUTES } from '@/router/api_routes';
import Modal from '@/components/common/Modal.vue';
import LoginForm from '@/components/Home/LoginForm.vue';
import RegisterForm from '@/components/Home/RegisterForm.vue';

const userStore = useUserStore();
const showModal = ref(false);
const currentForm = ref('login');
const statsData = ref(null);

onMounted(async () => {
  if (userStore.token) {
    userStore.fetchUser();

    // 获取真实的统计数据以渲染个人中心的微盘
    try {
      const res = await apiClient.get(API_ROUTES.ANALYSIS_ME);
      statsData.value = res.data;
    } catch (error) {
      console.error("获取统计数据失败:", error);
    }
  }
});

const openLoginModal = () => {
  currentForm.value = 'login';
  showModal.value = true;
};

const closeModal = () => {
  showModal.value = false;
};

const handleLoginSuccess = () => {
  closeModal();
};
</script>

<style scoped>
.profile-container {
  padding: 30px;
  max-width: 900px;
  margin: 0 auto;
  height: 100%;
  box-sizing: border-box;
}

.profile-header {
  margin-bottom: 30px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  font-size: 28px;
  font-weight: bold;
  color: var(--color-text-dark);
  margin: 0;
}

.more-settings-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background-color: #f5f5f5;
  color: #333;
  border: none;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
  font-weight: bold;
}

.more-settings-btn:hover {
  background-color: #e0e0e0;
}

.profile-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 基础卡片样式 */
.widget {
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
  padding: 24px;
  border: 1px solid rgba(0,0,0,0.02);
}

/* 顶部用户信息卡片 */
.user-card {
  display: flex;
  align-items: center;
  gap: 24px;
}

.avatar-placeholder {
  width: 80px;
  height: 80px;
  background-color: #f5f5f5;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
}

.user-info-text {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.username {
  margin: 0;
  font-size: 24px;
  font-weight: 800;
  color: #000;
}

.user-email {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.status-badge {
  display: inline-block;
  background-color: #e8f5e9;
  color: #2e7d32;
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 20px;
  font-weight: bold;
  width: max-content;
  margin-top: 4px;
}

/* 数据微盘 */
.stats-mini-board {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 20px;
  transition: transform 0.2s;
}

.stat-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.06);
}

.stat-icon {
  width: 50px;
  height: 50px;
  background-color: #f5f5f5;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-text {
  display: flex;
  flex-direction: column;
}

.stat-label {
  font-size: 13px;
  color: #666;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 24px;
  font-weight: 900;
  color: #000;
  line-height: 1;
}

.stat-value small {
  font-size: 12px;
  font-weight: normal;
  color: #999;
}

/* 强调高亮的卡片 */
.highlight-widget {
  background: var(--color-primary);
  color: #000;
}
.highlight-icon {
  background: rgba(0,0,0,0.05);
  color: #000;
}
.highlight-text .stat-label,
.highlight-text .stat-value small {
  color: rgba(0,0,0,0.6);
}

/* 未登录状态 */
.login-prompt {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 60px 20px;
}

.empty-icon {
  margin-bottom: 20px;
}

.login-prompt h2 {
  margin: 0 0 10px 0;
  font-size: 20px;
}

.login-prompt .desc {
  color: #999;
  margin: 0 0 30px 0;
  font-size: 14px;
}

.primary-btn {
  background: #000;
  color: #fff;
  border: none;
  padding: 12px 30px;
  border-radius: 24px;
  font-size: 15px;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.2s;
}

.primary-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0,0,0,0.15);
}
</style>
