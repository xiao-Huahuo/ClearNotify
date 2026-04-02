<template>
  <header class="app-header">
    <div class="search-bar" v-if="showSearch">
      <input type="text" v-model="searchQuery" @keyup.enter="handleSearch" placeholder="搜索文档..." />
      <button class="search-btn" @click="handleSearch">
        <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
      </button>
    </div>
    <div class="spacer" v-else></div>

    <div class="user-actions">
      <select class="palette-select" :value="settingsStore.settings.color_scheme" @change="toggleColorScheme($event)">
        <option value="classic">经典红灰</option>
        <option value="morandi">莫兰迪</option>
        <option value="graphite">石墨灰</option>
      </select>

      <!-- 明暗切换开关 -->
      <label class="theme-switch" title="切换明暗模式">
        <input class="theme-switch__checkbox" type="checkbox" :checked="isDark" @change="toggleTheme" />
        <div class="theme-switch__container">
          <div class="theme-switch__clouds"></div>
          <div class="theme-switch__stars-container">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 144 55" fill="none">
              <path fill-rule="evenodd" clip-rule="evenodd" d="M135.831 3.00688C135.055 3.85027 134.111 4.29946 133 4.35447C134.111 4.40947 135.055 4.85867 135.831 5.71206C136.607 6.55545 136.996 7.56878 136.996 8.75C136.996 7.56878 137.385 6.55545 138.161 5.71206C138.937 4.85867 139.881 4.40947 141 4.35447C139.881 4.29946 138.937 3.85027 138.161 3.00688C137.385 2.16348 136.996 1.15016 136.996 0C136.996 1.15016 136.607 2.16348 135.831 3.00688ZM123.831 23.0069C123.055 23.8503 122.111 24.2995 121 24.3545C122.111 24.4095 123.055 24.8587 123.831 25.7121C124.607 26.5555 124.996 27.5688 124.996 28.75C124.996 27.5688 125.385 26.5555 126.161 25.7121C126.937 24.8587 127.881 24.4095 129 24.3545C127.881 24.2995 126.937 23.8503 126.161 23.0069C125.385 22.1635 124.996 21.1502 124.996 20C124.996 21.1502 124.607 22.1635 123.831 23.0069ZM97.831 43.0069C97.055 43.8503 96.1114 44.2995 95 44.3545C96.1114 44.4095 97.055 44.8587 97.831 45.7121C98.607 46.5555 98.9959 47.5688 98.9959 48.75C98.9959 47.5688 99.3849 46.5555 100.161 45.7121C100.937 44.8587 101.881 44.4095 103 44.3545C101.881 44.2995 100.937 43.8503 100.161 43.0069C99.3849 42.1635 98.9959 41.1502 98.9959 40C98.9959 41.1502 98.607 42.1635 97.831 43.0069Z" fill="white"/>
            </svg>
          </div>
          <div class="theme-switch__circle-container">
            <div class="theme-switch__sun-moon-container">
              <div class="theme-switch__moon">
                <div class="theme-switch__spot"></div>
                <div class="theme-switch__spot"></div>
                <div class="theme-switch__spot"></div>
              </div>
            </div>
          </div>
        </div>
      </label>

      <!-- 通知图标 (对接 settingsStore) -->
      <button class="icon-btn" @click="toggleNotification" :title="settingsStore.settings.system_notifications ? '关闭系统通知' : '开启系统通知'">
        <!-- 开启通知：普通铃铛 -->
        <svg v-if="settingsStore.settings.system_notifications" viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
          <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
        </svg>
        <!-- 关闭通知：带斜杠的铃铛 -->
        <svg v-else viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
          <path d="M18.63 13A17.89 17.89 0 0 1 18 8"></path>
          <path d="M6.26 6.26A5.86 5.86 0 0 0 6 8c0 7-3 9-3 9h14"></path>
          <path d="M18 8a6 6 0 0 0-9.33-5"></path>
          <line x1="1" y1="1" x2="23" y2="23"></line>
        </svg>
      </button>

      <!-- 用户头像区 -->
      <div class="user-profile" @click="handleUserClick" title="个人中心">
        <button v-if="!userStore.token" @click.stop="emitLoginEvent" class="login-capsule">登录</button>
        <template v-else>
            <img v-if="displayAvatar" :src="displayAvatar" alt="avatar" class="header-avatar" />
            <div v-else class="header-avatar-placeholder">
              <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
            </div>
        </template>
      </div>

      <!-- 退出登录按钮 (恢复) -->
      <button v-if="userStore.token" class="icon-btn logout-btn" @click="handleLogout" title="退出登录">
        <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
          <polyline points="16 17 21 12 16 7"></polyline>
          <line x1="21" y1="12" x2="9" y2="12"></line>
        </svg>
      </button>
    </div>
  </header>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useUserStore } from '@/stores/auth.js';
import { useSettingsStore } from '@/stores/settings';

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();
const settingsStore = useSettingsStore();

const isDark = ref(false);

let themeObserver = null;
const syncThemeFromDom = () => {
  isDark.value = document.documentElement.getAttribute('data-theme') === 'dark';
};

const toggleTheme = async () => {
  const newTheme = isDark.value ? 'light' : 'dark';
  settingsStore.applyTheme(newTheme);
  settingsStore.settings.theme_mode = newTheme;
  if (userStore.token) {
    await settingsStore.updateSettings({ theme_mode: newTheme });
  }
  syncThemeFromDom();
};

const toggleColorScheme = (event) => {
  const scheme = event.target.value;
  settingsStore.updateColorScheme(scheme);
};

const searchQuery = ref('');

// 某些页面可能不需要搜索栏
const showSearch = computed(() => {
  return route.name !== 'login' && route.name !== 'register';
});

const handleSearch = () => {
  if (searchQuery.value.trim()) {
    router.push({ path: '/search', query: { q: searchQuery.value } });
  }
};

const displayAvatar = computed(() => {
    if (!userStore.user?.avatar_url) return null;
    const url = userStore.user.avatar_url;
    if (url.startsWith('default:')) {
        const defaultName = url.substring(8);
        return `/src/assets/photos/default-avatars/${defaultName}`;
    }
    return url;
});

const emitLoginEvent = () => {
  window.dispatchEvent(new CustomEvent('open-login-modal'));
};

const handleUserClick = () => {
  if (userStore.token) {
    router.push('/profile');
  }
};

const handleLogout = () => {
  if (confirm('确定要退出登录吗？')) {
    userStore.logout();
    router.push('/');
  }
};

const toggleNotification = async () => {
  if (!userStore.token) return;
  // 直接更新 pinia store 并向后端发请求
  settingsStore.settings.system_notifications = !settingsStore.settings.system_notifications;
  await settingsStore.updateSettings({
      system_notifications: settingsStore.settings.system_notifications
  });
};

onMounted(() => {
  syncThemeFromDom();
  themeObserver = new MutationObserver(() => {
    syncThemeFromDom();
  });
  themeObserver.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['data-theme'],
  });
});

onBeforeUnmount(() => {
  themeObserver?.disconnect();
});
</script>

<style scoped>
.app-header {
  height: 56px;
  background: var(--header-bg);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  flex-shrink: 0;
}

.search-bar {
  display: flex;
  align-items: center;
  background-color: rgba(255,255,255,0.18);
  border: 1px solid rgba(255,255,255,0.25);
  border-radius: var(--border-radius-pill);
  padding: 5px 10px;
  width: 300px;
  transition: background 0.3s;
}
.search-bar:focus-within {
  background-color: rgba(255,255,255,0.28);
}

.search-bar input {
  border: none;
  background: transparent;
  outline: none;
  flex: 1;
  padding: 5px;
  font-size: 14px;
  color: #fff;
}
.search-bar input::placeholder { color: rgba(255,255,255,0.65); }

.search-btn {
  background: none;
  color: rgba(255,255,255,0.8);
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s;
}
.search-btn:hover { color: #fff; }

.spacer { flex: 1; }

.user-actions {
  display: flex;
  align-items: center;
  gap: 15px;
}

.palette-select {
  height: 30px;
  border: 1px solid rgba(255,255,255,0.4);
  border-radius: 8px;
  background: rgba(255,255,255,0.15);
  color: #fff;
  padding: 0 8px;
  outline: none;
  font-size: 12px;
}

.palette-select option {
  color: #222;
}

.icon-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: rgba(255,255,255,0.85);
  transition: color 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}
.icon-btn:hover { color: #fff; }
.logout-btn:hover { color: rgba(255,255,255,0.7); }

.user-profile {
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.header-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid rgba(255,255,255,0.5);
}

.header-avatar-placeholder {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background-color: rgba(255,255,255,0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255,255,255,0.8);
}

.login-capsule {
  background-color: rgba(255,255,255,0.2);
  color: #fff;
  border: 1px solid rgba(255,255,255,0.4);
  padding: 8px 20px;
  border-radius: var(--border-radius-pill);
  font-size: 14px;
  font-weight: bold;
  cursor: pointer;
  transition: background 0.2s;
}

.login-capsule:hover { background-color: rgba(255,255,255,0.35); }

/* ── 明暗切换开关 (from Uiverse.io by Galahhad) ── */
.theme-switch {
  --toggle-size: 11px;
  --container-width: 5.625em;
  --container-height: 2.5em;
  --container-radius: 6.25em;
  --container-light-bg: #3D7EAE;
  --container-night-bg: #1D1F2C;
  --circle-container-diameter: 3.375em;
  --sun-moon-diameter: 2.125em;
  --sun-bg: #ECCA2F;
  --moon-bg: #C4C9D1;
  --spot-color: #959DB1;
  --circle-container-offset: calc((var(--circle-container-diameter) - var(--container-height)) / 2 * -1);
  --stars-color: #fff;
  --clouds-color: #F3FDFF;
  --back-clouds-color: #AACADF;
  --transition: .5s cubic-bezier(0, -0.02, 0.4, 1.25);
  --circle-transition: .3s cubic-bezier(0, -0.02, 0.35, 1.17);
  font-size: var(--toggle-size);
  cursor: pointer;
}
.theme-switch *, .theme-switch *::before, .theme-switch *::after {
  box-sizing: border-box; margin: 0; padding: 0; font-size: var(--toggle-size);
}
.theme-switch__checkbox { display: none; }
.theme-switch__container {
  width: var(--container-width); height: var(--container-height);
  background-color: var(--container-light-bg);
  border-radius: var(--container-radius); overflow: hidden; cursor: pointer;
  box-shadow: 0em -0.062em 0.062em rgba(0,0,0,0.25), 0em 0.062em 0.125em rgba(255,255,255,0.94);
  transition: var(--transition); position: relative;
}
.theme-switch__container::before {
  content: ""; position: absolute; z-index: 1; inset: 0;
  box-shadow: 0em 0.05em 0.187em rgba(0,0,0,0.25) inset, 0em 0.05em 0.187em rgba(0,0,0,0.25) inset;
  border-radius: var(--container-radius);
}
.theme-switch__checkbox:checked + .theme-switch__container { background-color: var(--container-night-bg); }
.theme-switch__circle-container {
  width: var(--circle-container-diameter); height: var(--circle-container-diameter);
  background-color: rgba(255,255,255,0.1); position: absolute;
  left: var(--circle-container-offset); top: var(--circle-container-offset);
  border-radius: 50%; box-shadow: inset 0 0 0 3.272em rgba(255,255,255,0.1), inset 0 0 0 3.272em rgba(255,255,255,0.1), 0 0 0 0.625em rgba(255,255,255,0.1), 0 0 0 1.25em rgba(255,255,255,0.05);
  display: flex; align-items: center; justify-content: center;
  transition: var(--circle-transition);
}
.theme-switch__checkbox:checked + .theme-switch__container .theme-switch__circle-container {
  left: calc(100% - var(--circle-container-offset) - var(--circle-container-diameter));
}
.theme-switch__sun-moon-container {
  pointer-events: none; position: relative; z-index: 2;
  width: var(--sun-moon-diameter); height: var(--sun-moon-diameter);
  background-color: var(--sun-bg); border-radius: 50%;
  box-shadow: 0.062em 0.062em 0.062em 0em rgba(254,255,239,0.61) inset, 0em -0.062em 0.062em 0em #a1872a inset;
  filter: drop-shadow(0.062em 0.125em 0.125em rgba(0,0,0,0.25)) drop-shadow(0em 0.062em 0.125em rgba(0,0,0,0.25));
  overflow: hidden; transition: var(--transition);
}
.theme-switch__checkbox:checked + .theme-switch__container .theme-switch__sun-moon-container {
  background-color: var(--moon-bg);
  box-shadow: 0.062em 0.062em 0.062em 0em rgba(254,255,239,0.61) inset, 0em -0.062em 0.062em 0em #969696 inset;
}
.theme-switch__moon {
  transform: translateX(100%); width: 100%; height: 100%;
  background-color: var(--moon-bg); border-radius: inherit; transition: var(--transition);
  box-shadow: 0.062em 0.062em 0.062em 0em rgba(254,255,239,0.61) inset, 0em -0.062em 0.062em 0em #969696 inset;
}
.theme-switch__checkbox:checked + .theme-switch__container .theme-switch__moon { transform: translateX(0); }
.theme-switch__spot {
  position: absolute; top: 0.75em; left: 0.312em;
  width: 0.75em; height: 0.75em; border-radius: 50%; background-color: var(--spot-color);
  box-shadow: 0em 0.0312em 0.062em rgba(0,0,0,0.25) inset;
}
.theme-switch__spot:nth-of-type(2) { width: 0.375em; height: 0.375em; top: 0.937em; left: 1.375em; }
.theme-switch__spot:nth-of-type(3) { width: 0.25em; height: 0.25em; top: 0.312em; left: 1em; }
.theme-switch__clouds {
  width: 1.25em; height: 1.25em; background-color: var(--clouds-color);
  border-radius: 50%; position: absolute; bottom: -0.625em; left: 0.312em;
  box-shadow: 0.937em 0.312em 0 var(--clouds-color), -0.312em -0.312em 0 0.625em var(--clouds-color), 1.437em 0.375em 0 0.5em var(--clouds-color), 0.5em -0.125em 0 0.625em var(--clouds-color), 2.187em 0 0 0.312em var(--clouds-color);
  transition: 0.5s cubic-bezier(0, -0.02, 0.4, 1.25);
}
.theme-switch__checkbox:checked + .theme-switch__container .theme-switch__clouds { bottom: -1.25em; }
.theme-switch__stars-container {
  position: absolute; color: var(--stars-color); top: -100%; left: 0.312em;
  width: 2.75em; height: auto; transition: var(--transition);
}
.theme-switch__checkbox:checked + .theme-switch__container .theme-switch__stars-container { top: 0.312em; }
</style>
