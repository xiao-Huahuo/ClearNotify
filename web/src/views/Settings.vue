<template>
  <div class="settings-container">
    <div class="settings-header">
      <PolicyTitle title="系统设置" />
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
        <div class="profile-side-actions">
          <button class="profile-logout-link" @click="handleLogout">退出当前账号</button>
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
                <div class="toggle-group theme-mode-toggle">
                  <button type="button" class="toggle-btn" :class="{ active: settingsStore.settings.theme_mode === 'light' }" @click.stop="handleThemeChange('light')">浅色</button>
                  <button type="button" class="toggle-btn" :class="{ active: settingsStore.settings.theme_mode === 'dark' }" @click.stop="handleThemeChange('dark')">深色</button>
                  <button type="button" class="toggle-btn" :class="{ active: settingsStore.settings.theme_mode === 'system' }" @click.stop="handleThemeChange('system')">跟随系统</button>
                </div>
              </div>
            </div>

            <!-- 全局配色 -->
            <div class="setting-item">
              <div class="setting-info">
                <div class="icon-wrap">
                  <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><circle cx="13.5" cy="6.5" r="2.5"></circle><circle cx="6.5" cy="12" r="2.5"></circle><circle cx="13.5" cy="17.5" r="2.5"></circle><line x1="8.8" y1="10.8" x2="11.2" y2="7.8"></line><line x1="8.8" y1="13.2" x2="11.2" y2="16.2"></line></svg>
                </div>
                <div class="text-wrap">
                  <p class="name">全局配色方案</p>
                  <p class="desc">切换经典红、酒红珊瑚与智能体专用的珊瑚蓝色系</p>
                </div>
              </div>
              <div class="setting-control">
                <div class="toggle-group">
                  <button type="button" class="toggle-btn" :disabled="isColorSchemeUpdating" :class="{ active: settingsStore.settings.color_scheme === 'classic' }" @click.stop="handleColorSchemeChange('classic')">经典红</button>
                  <button type="button" class="toggle-btn" :disabled="isColorSchemeUpdating" :class="{ active: settingsStore.settings.color_scheme === 'wine-coral' }" @click.stop="handleColorSchemeChange('wine-coral')">酒红珊瑚</button>
                  <button type="button" class="toggle-btn" :disabled="isColorSchemeUpdating" :class="{ active: settingsStore.settings.color_scheme === 'coral' }" @click.stop="handleColorSchemeChange('coral')">珊瑚蓝</button>
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

    <!-- 头像编辑弹窗 -->
    <Modal :isOpen="showAvatarEditor" @close="showAvatarEditor = false">
      <AvatarEditor @close="showAvatarEditor = false" />
    </Modal>

  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import PolicyTitle from '@/components/common/PolicyTitle.vue';
import { useRouter } from 'vue-router';
import { useUserStore } from '@/stores/auth.js';
import { useSettingsStore } from '@/stores/settings';
import Modal from '@/components/common/Modal.vue';
import AvatarEditor from '@/components/common/AvatarEditor.vue';
import { resolveAvatarUrl } from '@/utils/avatar.js';

const router = useRouter();
const userStore = useUserStore();
const settingsStore = useSettingsStore();

const showAvatarEditor = ref(false);
const isColorSchemeUpdating = ref(false);

const displayAvatar = computed(() => {
    return resolveAvatarUrl(userStore.user?.avatar_url);
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

const handleColorSchemeChange = async (scheme) => {
    if (isColorSchemeUpdating.value) return;
    isColorSchemeUpdating.value = true;
    try {
        await settingsStore.setColorScheme(scheme, { persist: true });
    } finally {
        isColorSchemeUpdating.value = false;
    }
};

const handleLogout = () => {
  if (confirm('确定要退出登录吗？')) {
    userStore.logout();
    router.push('/showcase');
  }
};

// 弹窗相关方法
const openLoginModal = () => {
  window.dispatchEvent(new CustomEvent('open-login-modal'));
};

</script>

<style scoped>
.settings-container {
  padding: 16px 20px 24px;
  max-width: 1180px;
  margin: 0 auto;
  height: 100%;
  box-sizing: border-box;
  overflow-y: auto;
}

.settings-header {
  margin-bottom: 18px;
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
  color: var(--text-secondary);
}

.settings-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.settings-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.3fr) minmax(300px, 0.9fr);
  gap: 18px;
  align-items: start;
}

/* 基础卡片样式 */
.widget {
  background: var(--card-bg);
  border-radius: 18px;
  box-shadow: 0 18px 38px color-mix(in srgb, var(--color-primary) 10%, transparent);
  border: 1px solid color-mix(in srgb, var(--color-primary) 10%, var(--border-color));
  padding: 20px;
}

/* 个人资料大卡片 */
.profile-card {
  display: flex;
  align-items: center;
  gap: 30px;
  padding: 30px;
  background:
    radial-gradient(circle at top right, color-mix(in srgb, var(--color-accent-cool) 14%, transparent), transparent 45%),
    linear-gradient(155deg, color-mix(in srgb, var(--color-primary) 9%, var(--card-bg)), var(--card-bg));
}

.profile-avatar {
  width: 100px;
  height: 100px;
  background-color: color-mix(in srgb, var(--color-primary) 10%, var(--card-bg));
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  overflow: hidden;
  transition: opacity 0.2s, transform 0.2s ease, box-shadow 0.2s ease;
  box-shadow: 0 12px 26px color-mix(in srgb, var(--color-primary) 14%, transparent);
}
.profile-avatar:hover {
  opacity: 0.8;
  transform: translateY(-2px);
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

.profile-side-actions {
  display: flex;
  align-self: stretch;
  align-items: flex-start;
  justify-content: flex-end;
  margin-left: auto;
}

.profile-logout-link {
  appearance: none;
  background: none;
  border: none;
  padding: 0;
  color: color-mix(in srgb, #ff4d4f 82%, var(--color-primary-dark));
  font-size: 14px;
  font-weight: 700;
  line-height: 1.2;
  cursor: pointer;
  text-decoration: none;
  transition: color 0.2s ease, opacity 0.2s ease;
}

.profile-logout-link:hover,
.profile-logout-link:focus-visible {
  color: #ff4d4f;
  text-decoration: underline;
  outline: none;
}

.username {
  margin: 0;
  font-size: 24px;
  font-weight: 800;
  color: var(--text-primary);
}

.user-email {
  margin: 0;
  color: var(--text-secondary);
  font-size: 15px;
}

.profile-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 10px;
}

/* 模块标题 */
.section-title {
  font-size: 18px;
  font-weight: bold;
  margin: 0 0 20px 0;
  color: var(--text-primary);
  padding-bottom: 15px;
  border-bottom: 1px solid color-mix(in srgb, var(--border-color) 82%, transparent);
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
  gap: 18px;
  border-bottom: 1px solid color-mix(in srgb, var(--border-color) 72%, transparent);
}

.setting-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.setting-info {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  min-width: 0;
  flex: 1;
}

.icon-wrap {
  width: 40px;
  height: 40px;
  background:
    linear-gradient(145deg, color-mix(in srgb, var(--color-primary) 18%, transparent), color-mix(in srgb, var(--color-secondary) 10%, transparent));
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-primary-dark);
  flex-shrink: 0;
}

.text-wrap {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 2px;
  min-width: 0;
}

.name {
  margin: 0;
  font-size: 15px;
  font-weight: bold;
  color: var(--text-primary);
}

.desc {
  margin: 0;
  font-size: 13px;
  color: var(--text-secondary);
}

/* 控件样式 */
.setting-control {
  display: flex;
  justify-content: flex-end;
  flex-shrink: 0;
}

.custom-select {
  padding: 8px 12px;
  border-radius: 12px;
  border: 1px solid color-mix(in srgb, var(--color-primary) 14%, var(--border-color));
  background-color: color-mix(in srgb, var(--color-primary) 6%, var(--card-bg));
  font-size: 14px;
  color: var(--text-primary);
  outline: none;
  cursor: pointer;
  transition: all 0.2s;
  min-width: 220px;
}

.custom-select:hover {
  border-color: var(--color-primary);
}

.toggle-group {
  display: flex;
  flex-wrap: wrap;
  background-color: color-mix(in srgb, var(--color-primary) 7%, var(--card-bg));
  border: 1px solid color-mix(in srgb, var(--color-primary) 12%, var(--border-color));
  border-radius: 999px;
  padding: 4px;
  gap: 4px;
}

.toggle-btn {
  background: transparent;
  border: none;
  padding: 6px 16px;
  border-radius: 999px;
  font-size: 13px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.toggle-btn:disabled {
  cursor: wait;
  opacity: 0.7;
}

.toggle-btn.active {
  background-color: var(--color-primary);
  color: #fff;
  font-weight: bold;
  box-shadow: 0 8px 20px color-mix(in srgb, var(--color-primary) 24%, transparent);
}

.action-btn {
  padding: 8px 20px;
  border-radius: 999px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn.outline {
  background: color-mix(in srgb, var(--color-primary) 7%, var(--card-bg));
  border: 1px solid color-mix(in srgb, var(--color-primary) 12%, var(--border-color));
  color: var(--text-primary);
}

.action-btn.outline:hover {
  border-color: var(--color-primary);
  color: var(--color-primary-dark);
  transform: translateY(-1px);
}

.action-btn.small {
  padding: 6px 16px;
  font-size: 13px;
}

.action-btn.danger {
  background: color-mix(in srgb, #ff4d4f 8%, var(--card-bg));
  border: 1px solid color-mix(in srgb, #ff4d4f 56%, var(--border-color));
  color: #ff4d4f;
}

.action-btn.danger:hover {
  background: #ff4d4f;
  color: #fff;
}

/* 危险操作样式覆盖 */
.danger-icon {
  background-color: color-mix(in srgb, #ff4d4f 12%, var(--card-bg));
  color: #ff4d4f;
}
.danger-text {
  color: #ff4d4f;
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
  background-color: color-mix(in srgb, var(--text-muted) 42%, var(--border-color));
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
  background-color: var(--color-primary);
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
  gap: 10px;
}
.primary-btn {
  margin-top: 20px;
  background: var(--color-primary);
  color: #fff;
  border: none;
  padding: 10px 24px;
  border-radius: 999px;
  cursor: pointer;
  font-weight: 700;
  box-shadow: 0 12px 24px color-mix(in srgb, var(--color-primary) 18%, transparent);
}

:global([data-theme="dark"]) .settings-container .toggle-group {
  background-color: color-mix(in srgb, var(--color-primary) 8%, var(--card-bg));
}

:global([data-theme="dark"]) .settings-container .theme-mode-toggle .toggle-btn.active {
  box-shadow: 0 10px 18px color-mix(in srgb, var(--color-primary) 22%, transparent) !important;
}

@media (max-width: 1024px) {
  .settings-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .settings-container {
    padding: 14px 14px 24px;
  }

  .widget {
    padding: 18px;
    border-radius: 16px;
  }

  .profile-card {
    padding: 22px 18px;
    flex-direction: column;
    align-items: flex-start;
    gap: 18px;
  }

  .profile-side-actions {
    width: 100%;
    justify-content: flex-end;
    margin-left: 0;
    margin-top: -4px;
  }

  .profile-avatar {
    width: 88px;
    height: 88px;
  }

  .profile-actions,
  .setting-control {
    width: 100%;
  }

  .setting-item {
    flex-direction: column;
    align-items: stretch;
  }

  .custom-select,
  .toggle-group,
  .theme-mode-toggle {
    width: 100%;
  }

  .toggle-group {
    border-radius: 16px;
  }

  .toggle-btn {
    flex: 1 1 0;
    min-width: 0;
  }

  .login-prompt {
    padding: 34px 20px;
  }
}
</style>
