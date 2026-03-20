<template>
  <div class="settings-container">
    <div class="settings-header">
      <h1 class="page-title">系统设置</h1>
    </div>

    <!-- 加载状态 -->
    <div v-if="settingsStore.loading" class="loading-state">
      加载中...
    </div>

    <!-- 主体内容 -->
    <div class="settings-content" v-else-if="userStore.token">
      <!-- 个人资料大卡片 -->
      <div class="profile-card widget">
        <div class="profile-avatar" @click="showAvatarEditor = true" style="cursor: pointer;" title="点击修改头像">
          <img v-if="displayAvatar" :src="displayAvatar" alt="avatar" class="user-avatar" />
          <svg v-else viewBox="0 0 24 24" width="60" height="60" stroke="#ccc" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
            <circle cx="12" cy="7" r="4"></circle>
          </svg>
        </div>
        <div class="profile-details">
          <h2 class="username">{{ userStore.user?.uname || '加载中...' }}</h2>
          <p class="user-email">{{ userStore.user?.email || '暂无邮箱' }}</p>
          <div class="profile-actions">
            <button class="action-btn outline" @click="showAvatarEditor = true">更换头像</button>
            <button class="action-btn outline">编辑资料</button>
          </div>
        </div>
      </div>

      <!-- 设置模块网格 -->
      <div class="settings-grid">
        <!-- 模块：系统偏好 (从 Profile 迁移过来并扩充) -->
        <div class="settings-section widget">
          <h3 class="section-title">系统偏好</h3>
          <div class="setting-list">
            <!-- 默认 AI 改写风格 -->
            <div class="setting-item">
              <div class="setting-info">
                <div class="icon-wrap">
                  <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
                </div>
                <div class="text-wrap">
                  <p class="name">默认 AI 改写受众</p>
                  <p class="desc">设置您最常用的通知阅读群体</p>
                </div>
              </div>
              <div class="setting-control">
                <select class="custom-select" v-model="settingsStore.settings.default_audience" @change="handleSettingChange('default_audience')">
                  <option value="none">未设置 (默认原意)</option>
                  <option value="elderly">老年人 (大字、白话、防骗)</option>
                  <option value="student">学生 (条理清晰、重点突出)</option>
                  <option value="worker">打工人 (极简、快速获取时间地点)</option>
                </select>
              </div>
            </div>

            <!-- 主题风格 -->
            <div class="setting-item">
              <div class="setting-info">
                <div class="icon-wrap">
                  <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>
                </div>
                <div class="text-wrap">
                  <p class="name">整体明暗主题</p>
                  <p class="desc">切换界面的亮色或暗色模式</p>
                </div>
              </div>
              <div class="setting-control">
                <div class="toggle-group">
                  <button class="toggle-btn" :class="{ active: settingsStore.settings.theme_mode === 'light' }" @click="handleThemeChange('light')">浅色</button>
                  <button class="toggle-btn" :class="{ active: settingsStore.settings.theme_mode === 'dark' }" @click="handleThemeChange('dark')">深色</button>
                  <button class="toggle-btn" :class="{ active: settingsStore.settings.theme_mode === 'system' }" @click="handleThemeChange('system')">跟随系统</button>
                </div>
              </div>
            </div>

            <!-- 通知提醒 -->
            <div class="setting-item">
              <div class="setting-info">
                <div class="icon-wrap">
                  <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg>
                </div>
                <div class="text-wrap">
                  <p class="name">系统通知</p>
                  <p class="desc">接收系统更新或任务完成的提示</p>
                </div>
              </div>
              <div class="setting-control">
                 <label class="switch">
                    <input type="checkbox" v-model="settingsStore.settings.system_notifications" @change="handleSettingChange('system_notifications')">
                    <span class="slider round"></span>
                 </label>
              </div>
            </div>
          </div>
        </div>

        <!-- 模块：个人账户与安全 -->
        <div class="settings-section widget">
          <h3 class="section-title">账户与安全</h3>
          <div class="setting-list">

            <div class="setting-item">
              <div class="setting-info">
                <div class="icon-wrap">
                  <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
                </div>
                <div class="text-wrap">
                  <p class="name">登录密码</p>
                  <p class="desc">您已设置密码，建议定期更换</p>
                </div>
              </div>
              <div class="setting-control">
                <button class="action-btn outline small">修改密码</button>
              </div>
            </div>

            <div class="setting-item">
              <div class="setting-info">
                <div class="icon-wrap">
                  <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path><polyline points="22,6 12,13 2,6"></polyline></svg>
                </div>
                <div class="text-wrap">
                  <p class="name">绑定邮箱</p>
                  <p class="desc">{{ userStore.user?.email || '未绑定' }}</p>
                </div>
              </div>
              <div class="setting-control">
                <button class="action-btn outline small">更改邮箱</button>
              </div>
            </div>

            <div class="setting-item danger-item">
              <div class="setting-info">
                <div class="icon-wrap danger-icon">
                  <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M21 4H8l-7 8 7 8h13a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2z"></path><line x1="18" y1="9" x2="12" y2="15"></line><line x1="12" y1="9" x2="18" y2="15"></line></svg>
                </div>
                <div class="text-wrap">
                  <p class="name danger-text">注销账号</p>
                  <p class="desc">永久删除您的账号及所有解析历史</p>
                </div>
              </div>
              <div class="setting-control">
                <button class="action-btn danger small">申请注销</button>
              </div>
            </div>
          </div>
        </div>

        <!-- 退出登录 (整块红色 Widget) -->
        <div class="logout-widget widget" @click="handleLogout" style="cursor: pointer;">
           <svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
             <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
             <polyline points="16 17 21 12 16 7"></polyline>
             <line x1="21" y1="12" x2="9" y2="12"></line>
           </svg>
           <span>退出当前账号</span>
        </div>

      </div>
    </div>

    <!-- 未登录状态 -->
    <div v-else class="login-prompt widget">
      <!-- 移除这里的默认文字和按钮，只渲染 Modal 弹窗 -->
      <div class="empty-icon">
        <svg viewBox="0 0 24 24" width="48" height="48" stroke="#ccc" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
      </div>
      <h2>您尚未登录</h2>
      <p class="desc">登录后即可管理您的个人资产和 AI 偏好设置</p>
      <button @click="openLoginModal" class="primary-btn">立即登录 / 注册</button>
    </div>

    <!-- 弹窗：登录/注册 (复用 Home.vue 里的设计) -->
    <Modal :isOpen="showModal" @close="closeModal">
      <!-- 这个容器包裹了图标、标题和表单，在切换时由于 key 的存在，整个容器会平滑过渡 -->
      <div class="auth-modal-content">
        <div class="logo-area-transition">
          <h1 class="logo-text">ClearNotify</h1>
        </div>

        <!-- 使用动态高度包裹容器来实现上下平滑撑开 -->
        <div class="form-transition-container" :style="{ height: containerHeight + 'px' }">
          <transition
            name="form-slide"
            @before-enter="onBeforeEnter"
            @enter="onEnter"
            @after-enter="onAfterEnter"
            @leave="onLeave"
          >
            <!-- 使用绝对定位来实现平滑滑动切换，避免高度瞬间变化和挤压 -->
            <div v-if="currentForm === 'login'" class="form-wrapper login-wrapper-abs" key="login">
              <LoginForm
                @success="handleLoginSuccess"
                @switch-to-register="currentForm = 'register'"
              />
            </div>
            <div v-else-if="currentForm === 'register'" class="form-wrapper register-wrapper-abs" key="register">
              <RegisterForm
                @switch-to-login="currentForm = 'login'"
                @success="handleLoginSuccess"
              />
            </div>
          </transition>
        </div>
      </div>
    </Modal>

    <!-- 头像编辑弹窗 -->
    <Modal :isOpen="showAvatarEditor" @close="showAvatarEditor = false">
      <AvatarEditor @close="showAvatarEditor = false" />
    </Modal>

  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { useUserStore } from '@/stores/auth.js';
import { useSettingsStore } from '@/stores/settings';
import Modal from '@/components/common/Modal.vue';
import AvatarEditor from '@/components/common/AvatarEditor.vue';
import LoginForm from '@/components/Home/LoginForm.vue';
import RegisterForm from '@/components/Home/RegisterForm.vue';

const router = useRouter();
const userStore = useUserStore();
const settingsStore = useSettingsStore();

const showAvatarEditor = ref(false);

const showModal = ref(false);
const currentForm = ref('login');
const containerHeight = ref(350); // 默认登录框高度

const displayAvatar = computed(() => {
    if (!userStore.user?.avatar_url) return null;
    const url = userStore.user.avatar_url;
    if (url.startsWith('default:')) {
        const defaultName = url.substring(8);
        return `/src/assets/photos/default-avatars/${defaultName}`;
    }
    return url;
});

onMounted(async () => {
  if (userStore.token) {
    userStore.fetchUser();
    await settingsStore.fetchSettings();
  } else {
    openLoginModal(); // 如果直接通过 URL 进入设置页且未登录，自动弹窗
  }
});

const handleSettingChange = async (key) => {
    await settingsStore.updateSettings({
        [key]: settingsStore.settings[key]
    });
};

const handleThemeChange = async (theme) => {
    settingsStore.settings.theme_mode = theme;
    await handleSettingChange('theme_mode');
};

const handleLogout = () => {
  if (confirm('确定要退出登录吗？')) {
    userStore.logout();
    router.push('/');
  }
};

// 弹窗相关方法
const openLoginModal = () => {
  currentForm.value = 'login';
  containerHeight.value = 350; // 重置高度
  showModal.value = true;
};

const closeModal = () => {
  showModal.value = false;
};

const handleLoginSuccess = () => {
  closeModal();
};

// 弹窗动画
const onBeforeEnter = (el) => {
  el.style.opacity = 0;
};

const onEnter = (el, done) => {
  nextTick(() => {
    containerHeight.value = el.offsetHeight;
    el.style.opacity = 1;
    done();
  });
};

const onAfterEnter = (el) => {
  el.style.opacity = '';
};

const onLeave = (el, done) => {
  el.style.opacity = 0;
  setTimeout(done, 400); // 等待 CSS 动画结束
};

</script>

<style scoped>
.settings-container {
  padding: 30px;
  max-width: 1000px;
  margin: 0 auto;
  height: 100%;
  box-sizing: border-box;
  overflow-y: auto;
}

.settings-header {
  margin-bottom: 30px;
}

.page-title {
  font-size: 28px;
  font-weight: bold;
  color: var(--color-text-dark);
  margin: 0;
}

.loading-state {
  text-align: center;
  padding: 40px;
  color: #666;
}

.settings-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 基础卡片样式 */
.widget {
  background: #ffffff;
  border-radius: 0;
  box-shadow: none;
  border: 1px solid #e8e8e8;
  border-left: 3px solid #c0392b;
  padding: 20px;
}

/* 个人资料大卡片 */
.profile-card {
  display: flex;
  align-items: center;
  gap: 30px;
  padding: 30px;
}

.profile-avatar {
  width: 100px;
  height: 100px;
  background-color: #f5f5f5;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  overflow: hidden;
  transition: opacity 0.2s;
}
.profile-avatar:hover {
  opacity: 0.8;
}

.user-avatar {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.profile-details {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
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
  font-size: 15px;
}

.profile-actions {
  display: flex;
  gap: 12px;
  margin-top: 10px;
}

/* 模块标题 */
.section-title {
  font-size: 18px;
  font-weight: bold;
  margin: 0 0 20px 0;
  color: #000;
  padding-bottom: 15px;
  border-bottom: 1px solid #f0f0f0;
}

/* 列表样式 */
.setting-list {
  display: flex;
  flex-direction: column;
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 0;
  border-bottom: 1px solid #f9f9f9;
}

.setting-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.setting-info {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.icon-wrap {
  width: 40px;
  height: 40px;
  background-color: #f5f5f5;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
  flex-shrink: 0;
}

.text-wrap {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 2px;
}

.name {
  margin: 0;
  font-size: 15px;
  font-weight: bold;
  color: #333;
}

.desc {
  margin: 0;
  font-size: 13px;
  color: #999;
}

/* 控件样式 */
.custom-select {
  padding: 8px 12px;
  border-radius: 8px;
  border: 1px solid #ddd;
  background-color: #f9f9f9;
  font-size: 14px;
  color: #333;
  outline: none;
  cursor: pointer;
  transition: all 0.2s;
}

.custom-select:hover {
  border-color: #aaa;
}

.toggle-group {
  display: flex;
  background-color: #f5f5f5;
  border-radius: 8px;
  padding: 4px;
}

.toggle-btn {
  background: transparent;
  border: none;
  padding: 6px 16px;
  border-radius: 6px;
  font-size: 13px;
  color: #666;
  cursor: pointer;
  transition: all 0.2s;
}

.toggle-btn.active {
  background-color: #fff;
  color: #000;
  font-weight: bold;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.action-btn {
  padding: 8px 20px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn.outline {
  background: transparent;
  border: 1px solid #ddd;
  color: #333;
}

.action-btn.outline:hover {
  border-color: #000;
  color: #000;
}

.action-btn.small {
  padding: 6px 16px;
  font-size: 13px;
}

.action-btn.danger {
  background: #fff;
  border: 1px solid #ff4d4f;
  color: #ff4d4f;
}

.action-btn.danger:hover {
  background: #ff4d4f;
  color: #fff;
}

/* 危险操作样式覆盖 */
.danger-icon {
  background-color: #fff1f0;
  color: #ff4d4f;
}
.danger-text {
  color: #ff4d4f;
}

/* 整块红色退出按钮 Widget */
.logout-widget {
  background-color: #ff4d4f;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 20px;
  font-size: 16px;
  font-weight: bold;
  transition: all 0.2s;
  border: none;
}

.logout-widget:hover {
  background-color: #ff7875;
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(255, 77, 79, 0.3);
}

/* Switch 开关样式 */
.switch {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
}
.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}
.slider {
  position: absolute;
  cursor: pointer;
  top: 0; left: 0; right: 0; bottom: 0;
  background-color: #ccc;
  transition: .4s;
}
.slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: .4s;
}
input:checked + .slider {
  background-color: #000;
}
input:checked + .slider:before {
  transform: translateX(20px);
}
.slider.round {
  border-radius: 24px;
}
.slider.round:before {
  border-radius: 50%;
}

/* 未登录提示 */
.login-prompt {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px;
  text-align: center;
}
.primary-btn {
  margin-top: 20px;
  background: #000;
  color: #fff;
  border: none;
  padding: 10px 24px;
  border-radius: 24px;
  cursor: pointer;
}

/* Modal 中的表单切换过渡动画 (复用 Home 的样式) */
.auth-modal-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 0 0 0;
  background: linear-gradient(45deg, skyblue, darkblue);
  border-radius: 20px;
  width: 480px;
  min-height: 450px;
  overflow: hidden;
  transition: height 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.logo-area-transition {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
}

.auth-modal-content .logo-text {
  color: #fff;
  font-size: 28px;
  font-weight: 800;
  margin: 0;
  letter-spacing: 1px;
}

.form-transition-container {
  width: 100%;
  position: relative;
  transition: height 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.form-wrapper {
  width: 100%;
  display: flex;
  justify-content: center;
}

.login-wrapper-abs, .register-wrapper-abs {
  position: absolute;
  top: 0;
  left: 0;
}

.form-slide-enter-active,
.form-slide-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.form-slide-enter-from {
  opacity: 0;
  transform: translateY(30px);
}
.form-slide-leave-to {
  opacity: 0;
  transform: translateY(-30px);
}
</style>
