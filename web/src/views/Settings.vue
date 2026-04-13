<template>
  <div class="settings-container">
    <div class="settings-header">
      <PolicyTitle title="系统设置" />
    </div>

    <div v-if="settingsStore.loading && userStore.token" class="loading-state widget">
      <AgentLoader :size="46" />
      <span>正在加载你的偏好设置...</span>
    </div>

    <div v-else-if="userStore.token" class="settings-content">
      <section class="profile-card widget">
        <div class="profile-main">
          <div class="profile-avatar" @click="showAvatarEditor = true">
            <img v-if="displayAvatar" :src="displayAvatar" alt="avatar" class="user-avatar" />
            <svg v-else viewBox="0 0 24 24" width="56" height="56" stroke="#ccc" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
              <circle cx="12" cy="7" r="4"></circle>
            </svg>
          </div>

          <div class="profile-copy">
            <div class="profile-title-row">
              <h2 class="username">{{ userStore.user?.uname || '未命名用户' }}</h2>
              <span class="role-badge">{{ roleLabel }}</span>
            </div>

            <div class="identity-list">
              <p class="identity-item">邮箱：{{ emailText }}</p>
              <p class="identity-item">手机号：{{ phoneText }}</p>
            </div>

            <div class="badge-row">
              <span class="status-pill" :class="userStore.user?.email_verified ? 'status-pill--ok' : 'status-pill--warn'">
                {{ userStore.user?.email_verified ? '邮箱已验证' : '邮箱未验证' }}
              </span>
              <span class="status-pill" :class="userStore.user?.phone_verified ? 'status-pill--ok' : 'status-pill--warn'">
                {{ userStore.user?.phone_verified ? '手机号已验证' : '手机号未验证' }}
              </span>
              <span class="status-pill">
                {{ userStore.user?.password_login_enabled ? '已设置登录密码' : '尚未设置登录密码' }}
              </span>
              <span class="status-pill">偏好登录：{{ preferredLoginText }}</span>
            </div>
          </div>
        </div>

        <div class="profile-actions">
          <button class="action-btn outline" @click="showAvatarEditor = true">更换头像</button>
          <button class="action-btn outline" @click="router.push('/profile')">查看个人页</button>
          <LogoutPillButton @click="handleLogout" />
        </div>
      </section>

      <div class="settings-grid">
        <section class="settings-section widget">
          <h3 class="section-title">系统偏好</h3>
          <div class="setting-list">
            <div class="setting-item">
              <div class="setting-info">
                <div class="icon-wrap">
                  <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="3"></circle>
                    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
                  </svg>
                </div>
                <div class="text-wrap">
                  <p class="name">默认改写受众</p>
                  <p class="desc">设置最常用的政策解读受众风格。</p>
                </div>
              </div>
              <div class="setting-control">
                <select class="custom-select" v-model="settingsStore.settings.default_audience" @change="handleSettingChange('default_audience')">
                  <option value="none">未设置</option>
                  <option value="elderly">老年人</option>
                  <option value="student">学生</option>
                  <option value="worker">务工群体</option>
                </select>
              </div>
            </div>

            <div class="setting-item">
              <div class="setting-info">
                <div class="icon-wrap">
                  <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
                  </svg>
                </div>
                <div class="text-wrap">
                  <p class="name">主题模式</p>
                  <p class="desc">切换浅色、深色或跟随系统。</p>
                </div>
              </div>
              <div class="setting-control">
                <div class="toggle-group">
                  <button type="button" class="toggle-btn" :class="{ active: settingsStore.settings.theme_mode === 'light' }" @click="handleThemeChange('light')">浅色</button>
                  <button type="button" class="toggle-btn" :class="{ active: settingsStore.settings.theme_mode === 'dark' }" @click="handleThemeChange('dark')">深色</button>
                  <button type="button" class="toggle-btn" :class="{ active: settingsStore.settings.theme_mode === 'system' }" @click="handleThemeChange('system')">跟随系统</button>
                </div>
              </div>
            </div>

            <div class="setting-item">
              <div class="setting-info">
                <div class="icon-wrap">
                  <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="13.5" cy="6.5" r="2.5"></circle>
                    <circle cx="6.5" cy="12" r="2.5"></circle>
                    <circle cx="13.5" cy="17.5" r="2.5"></circle>
                    <line x1="8.8" y1="10.8" x2="11.2" y2="7.8"></line>
                    <line x1="8.8" y1="13.2" x2="11.2" y2="16.2"></line>
                  </svg>
                </div>
                <div class="text-wrap">
                  <p class="name">配色方案</p>
                  <p class="desc">切换当前界面的主色调。</p>
                </div>
              </div>
              <div class="setting-control">
                <div class="toggle-group">
                  <button type="button" class="toggle-btn" :disabled="isColorSchemeUpdating" :class="{ active: settingsStore.settings.color_scheme === 'classic' }" @click="handleColorSchemeChange('classic')">经典红</button>
                  <button type="button" class="toggle-btn" :disabled="isColorSchemeUpdating" :class="{ active: settingsStore.settings.color_scheme === 'wine-coral' }" @click="handleColorSchemeChange('wine-coral')">酒红珊瑚</button>
                  <button type="button" class="toggle-btn" :disabled="isColorSchemeUpdating" :class="{ active: settingsStore.settings.color_scheme === 'coral' }" @click="handleColorSchemeChange('coral')">珊瑚蓝</button>
                </div>
              </div>
            </div>

            <div class="setting-item">
              <div class="setting-info">
                <div class="icon-wrap">
                  <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
                    <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
                  </svg>
                </div>
                <div class="text-wrap">
                  <p class="name">系统通知</p>
                  <p class="desc">接收任务完成、系统更新等提醒。</p>
                </div>
              </div>
              <div class="setting-control">
                <label class="switch">
                  <input type="checkbox" v-model="settingsStore.settings.system_notifications" @change="handleSettingChange('system_notifications')" />
                  <span class="slider round"></span>
                </label>
              </div>
            </div>
          </div>
        </section>

        <section class="settings-section widget">
          <h3 class="section-title">账户与安全</h3>
          <div class="setting-list">
            <div class="setting-item">
              <div class="setting-info">
                <div class="icon-wrap">
                  <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="7" y="2" width="10" height="20" rx="2"></rect>
                    <line x1="11" y1="18" x2="13" y2="18"></line>
                  </svg>
                </div>
                <div class="text-wrap">
                  <p class="name">登录手机号</p>
                  <p class="desc">{{ phoneText }} · {{ userStore.user?.phone_verified ? '已验证' : '未验证' }}</p>
                </div>
              </div>
              <div class="setting-control">
                <button class="action-btn outline small" @click="openSecurityModal('bind-phone')">
                  {{ userStore.user?.login_phone ? '更换手机号' : '绑定手机号' }}
                </button>
              </div>
            </div>

            <div class="setting-item">
              <div class="setting-info">
                <div class="icon-wrap">
                  <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
                    <polyline points="22,6 12,13 2,6"></polyline>
                  </svg>
                </div>
                <div class="text-wrap">
                  <p class="name">绑定邮箱</p>
                  <p class="desc">{{ emailText }} · {{ userStore.user?.email_verified ? '已验证' : '未验证' }}</p>
                </div>
              </div>
              <div class="setting-control">
                <button class="action-btn outline small" @click="openSecurityModal('bind-email')">
                  {{ userStore.user?.email ? '更换邮箱' : '绑定邮箱' }}
                </button>
              </div>
            </div>

            <div class="setting-item">
              <div class="setting-info">
                <div class="icon-wrap">
                  <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                    <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                  </svg>
                </div>
                <div class="text-wrap">
                  <p class="name">登录密码</p>
                  <p class="desc">{{ userStore.user?.password_login_enabled ? '已设置，可用手机号、邮箱或用户名 + 密码登录' : '未设置，建议现在补充，避免后续只能通过找回密码重设' }}</p>
                </div>
              </div>
              <div class="setting-control">
                <button class="action-btn outline small" @click="openSecurityModal(userStore.user?.password_login_enabled ? 'change-password' : 'set-password')">
                  {{ passwordActionText }}
                </button>
              </div>
            </div>

            <div class="setting-item">
              <div class="setting-info">
                <div class="icon-wrap">
                  <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12 20V10"></path>
                    <path d="M18 20V4"></path>
                    <path d="M6 20v-4"></path>
                  </svg>
                </div>
                <div class="text-wrap">
                  <p class="name">登录方式记录</p>
                  <p class="desc">偏好登录：{{ preferredLoginText }}，最近一次：{{ lastLoginText }}</p>
                </div>
              </div>
              <div class="setting-control">
                <span class="inline-note">忘记密码时会优先使用已绑定的手机号或邮箱</span>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>

    <div v-else class="login-prompt widget">
      <div class="empty-icon">
        <svg viewBox="0 0 24 24" width="48" height="48" stroke="#ccc" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
          <circle cx="12" cy="7" r="4"></circle>
        </svg>
      </div>
      <h2>你还没有登录</h2>
      <p class="login-desc">登录后即可管理你的账号绑定信息、密码和个性化偏好。</p>
      <button @click="openLoginModal" class="primary-cta">立即登录 / 注册</button>
    </div>

    <Modal :isOpen="showAvatarEditor" @close="showAvatarEditor = false">
      <AvatarEditor @close="showAvatarEditor = false" />
    </Modal>

    <AccountSecurityModal
      :is-open="showSecurityModal"
      :mode="securityMode"
      @close="showSecurityModal = false"
      @updated="handleAccountUpdated"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import PolicyTitle from '@/components/common/PolicyTitle.vue';
import Modal from '@/components/common/Modal.vue';
import AvatarEditor from '@/components/common/AvatarEditor.vue';
import AccountSecurityModal from '@/components/settings/AccountSecurityModal.vue';
import AgentLoader from '@/components/ui/AgentLoader.vue';
import LogoutPillButton from '@/components/ui/LogoutPillButton.vue';
import { useUserStore } from '@/stores/auth.js';
import { useSettingsStore } from '@/stores/settings';
import { resolveAvatarUrl } from '@/utils/avatar.js';

const router = useRouter();
const userStore = useUserStore();
const settingsStore = useSettingsStore();

const showAvatarEditor = ref(false);
const showSecurityModal = ref(false);
const securityMode = ref('bind-phone');
const isColorSchemeUpdating = ref(false);

const displayAvatar = computed(() => resolveAvatarUrl(userStore.user?.avatar_url));
const emailText = computed(() => userStore.user?.email || '未绑定邮箱');
const phoneText = computed(() => userStore.user?.login_phone || '未绑定手机号');
const passwordActionText = computed(() => (userStore.user?.password_login_enabled ? '修改密码' : '设置密码'));

const roleLabel = computed(() => {
  if (userStore.user?.role === 'admin') return '管理员';
  if (userStore.user?.role === 'certified') return '认证主体';
  return '普通用户';
});

const mapLoginMethod = (value) => {
  if (value === 'phone_code') return '手机号验证码';
  if (value === 'phone_password') return '手机号 + 密码';
  if (value === 'email_password') return '邮箱 + 密码';
  if (value === 'username_password') return '用户名 + 密码';
  if (value === 'password') return '密码登录';
  return '未设置';
};

const preferredLoginText = computed(() => mapLoginMethod(userStore.user?.preferred_login_method));
const lastLoginText = computed(() => mapLoginMethod(userStore.user?.last_login_method));

onMounted(async () => {
  if (userStore.token) {
    await userStore.fetchUser();
    await settingsStore.fetchSettings();
  } else {
    openLoginModal();
  }
});

const handleSettingChange = async (key) => {
  await settingsStore.updateSettings({
    [key]: settingsStore.settings[key],
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
  if (!window.confirm('确定要退出登录吗？')) return;
  userStore.logout();
  router.push('/showcase');
};

const openSecurityModal = (mode) => {
  securityMode.value = mode;
  showSecurityModal.value = true;
};

const handleAccountUpdated = async () => {
  await userStore.fetchUser();
};

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

.widget {
  background: var(--card-bg);
  border-radius: 20px;
  box-shadow: 0 18px 38px color-mix(in srgb, var(--color-primary) 10%, transparent);
  border: 1px solid color-mix(in srgb, var(--color-primary) 10%, var(--border-color));
  padding: 20px;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  text-align: center;
  padding: 40px;
  color: var(--text-secondary);
}

.settings-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.profile-card {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: center;
  background:
    radial-gradient(circle at top right, color-mix(in srgb, var(--color-accent-cool) 14%, transparent), transparent 45%),
    linear-gradient(155deg, color-mix(in srgb, var(--color-primary) 9%, var(--card-bg)), var(--card-bg));
}

.profile-main {
  display: flex;
  gap: 22px;
  align-items: center;
  min-width: 0;
  flex: 1;
}

.profile-avatar {
  width: 104px;
  height: 104px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  cursor: pointer;
  flex-shrink: 0;
  background: color-mix(in srgb, var(--color-primary) 10%, var(--card-bg));
  box-shadow: 0 12px 26px color-mix(in srgb, var(--color-primary) 14%, transparent);
}

.user-avatar {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.profile-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.profile-title-row {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

.username {
  margin: 0;
  font-size: 28px;
  font-weight: 800;
  color: var(--text-primary);
}

.role-badge {
  border-radius: 999px;
  padding: 5px 12px;
  font-size: 12px;
  font-weight: 800;
  color: #fff;
  background: linear-gradient(135deg, var(--color-primary-dark), var(--color-primary));
}

.identity-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 18px;
}

.identity-item {
  margin: 0;
  color: var(--text-secondary);
  font-size: 14px;
}

.badge-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
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

.profile-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.settings-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.25fr) minmax(320px, 0.95fr);
  gap: 18px;
  align-items: start;
}

.settings-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-title {
  font-size: 18px;
  font-weight: 800;
  margin: 0 0 6px;
  color: var(--text-primary);
}

.setting-list {
  display: flex;
  flex-direction: column;
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 18px;
  padding: 18px 0;
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
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: var(--color-primary-dark);
  background: linear-gradient(145deg, color-mix(in srgb, var(--color-primary) 18%, transparent), color-mix(in srgb, var(--color-secondary) 10%, transparent));
}

.text-wrap {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.name {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
}

.desc {
  margin: 0;
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
}

.setting-control {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  flex-shrink: 0;
}

.inline-note {
  max-width: 220px;
  font-size: 12px;
  line-height: 1.6;
  color: var(--text-secondary);
  text-align: right;
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
  min-width: 220px;
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

.toggle-btn.active {
  background-color: var(--color-primary);
  color: #fff;
  font-weight: 700;
  box-shadow: 0 8px 20px color-mix(in srgb, var(--color-primary) 24%, transparent);
}

.toggle-btn:disabled {
  cursor: wait;
  opacity: 0.7;
}

.action-btn {
  padding: 8px 20px;
  border-radius: 999px;
  font-size: 14px;
  font-weight: 700;
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
  inset: 0;
  background-color: color-mix(in srgb, var(--text-muted) 42%, var(--border-color));
  transition: 0.4s;
}

.slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: 0.4s;
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

.login-prompt {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px;
  text-align: center;
  gap: 12px;
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
  font-size: 28px;
  color: var(--text-primary);
}

.login-desc {
  max-width: 520px;
  margin: 0;
  font-size: 14px;
  line-height: 1.8;
  color: var(--text-secondary);
}

.primary-cta {
  margin-top: 12px;
  background: linear-gradient(135deg, var(--color-primary-dark), var(--color-primary), var(--color-secondary));
  color: #fff;
  border: none;
  padding: 12px 24px;
  border-radius: 999px;
  cursor: pointer;
  font-weight: 800;
  box-shadow: 0 12px 24px color-mix(in srgb, var(--color-primary) 18%, transparent);
}

@media (max-width: 1024px) {
  .settings-grid {
    grid-template-columns: 1fr;
  }

  .profile-card {
    flex-direction: column;
    align-items: stretch;
  }

  .profile-actions {
    justify-content: flex-start;
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

  .profile-main,
  .setting-item {
    flex-direction: column;
    align-items: stretch;
  }

  .profile-avatar {
    width: 88px;
    height: 88px;
  }

  .profile-actions,
  .setting-control,
  .custom-select,
  .toggle-group,
  .primary-cta {
    width: 100%;
  }

  .toggle-group {
    border-radius: 16px;
  }

  .toggle-btn {
    flex: 1 1 0;
    min-width: 0;
  }

  .inline-note {
    max-width: none;
    text-align: left;
  }

  .login-prompt {
    padding: 34px 20px;
  }
}
</style>
