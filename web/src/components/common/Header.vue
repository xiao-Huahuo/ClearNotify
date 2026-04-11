<template>
  <header class="app-header" :class="{ 'appearance-transitioning': isAppearanceTransitioning }">
    <div class="header-left-controls">
    <!-- Hamburger button: only visible in icon mode -->
    <button v-if="isIconMode" class="icon-btn hamburger-btn" @click="$emit('update:isIconMode', false)" title="展开侧边栏">
      <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <line x1="3" y1="6" x2="21" y2="6"></line>
        <line x1="3" y1="12" x2="21" y2="12"></line>
        <line x1="3" y1="18" x2="21" y2="18"></line>
      </svg>
    </button>

    
    <!-- Back button -->
    <button class="icon-btn back-btn" @click="goBack" title="返回">
      <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <line x1="19" y1="12" x2="5" y2="12"></line>
        <polyline points="12 19 5 12 12 5"></polyline>
      </svg>
    </button>
    </div>

    <div class="search-section" v-if="showSearch">
      <UnifiedSearchBox
        v-model="searchQuery"
        v-model:types="searchTypes"
        size="header"
        placeholder="搜索政策、文章、历史、智能体..."
        source="header_search_dropdown"
        @submit="handleSearchSubmit"
      />
    </div>
    <div class="spacer" v-else></div>

    <div class="user-actions">
      <!-- Sidebar mode toggle -->
      <button class="icon-btn" @click="$emit('update:isIconMode', !isIconMode)" :title="isIconMode ? '展开侧边栏' : '收起侧边栏'">
        <svg v-if="isIconMode" viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="3" width="18" height="18" rx="2"></rect>
          <line x1="9" y1="3" x2="9" y2="21"></line>
          <polyline points="13 8 17 12 13 16"></polyline>
        </svg>
        <svg v-else viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="3" width="18" height="18" rx="2"></rect>
          <line x1="9" y1="3" x2="9" y2="21"></line>
          <polyline points="15 8 11 12 15 16"></polyline>
        </svg>
      </button>

      <!-- 鏄庢殫鍒囨崲寮€鍏?-->
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

      <button
        class="scheme-switch"
        :class="{ 'is-switching': isSchemeSwitching }"
        type="button"
        :disabled="isSchemeSwitching"
        :aria-label="`切换品牌色系，当前：${currentSchemeLabel}，点击切换到：${nextSchemeLabel}`"
        :title="`切换品牌色系，当前：${currentSchemeLabel}，点击切换到：${nextSchemeLabel}`"
        @click.stop.prevent="handleColorSchemeToggle"
      >
        <span class="scheme-switch__inner"></span>
      </button>

      <!-- 閫氱煡鍥炬爣 -->
      <button class="icon-btn" @click="toggleNotification" :title="settingsStore.settings.system_notifications ? '关闭系统通知' : '开启系统通知'">
        <svg v-if="settingsStore.settings.system_notifications" viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
          <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
        </svg>
        <svg v-else viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
          <path d="M18.63 13A17.89 17.89 0 0 1 18 8"></path>
          <path d="M6.26 6.26A5.86 5.86 0 0 0 6 8c0 7-3 9-3 9h14"></path>
          <path d="M18 8a6 6 0 0 0-9.33-5"></path>
          <line x1="1" y1="1" x2="23" y2="23"></line>
        </svg>
      </button>

      <!-- 鐢ㄦ埛澶村儚鍖?-->
      <div class="user-profile" @click="handleUserClick" title="个人中心">
        <button v-if="!userStore.token" @click.stop="emitLoginEvent" class="login-capsule">登录</button>
        <template v-else>
          <img v-if="displayAvatar" :src="displayAvatar" alt="avatar" class="header-avatar" />
          <div v-else class="header-avatar-placeholder">
            <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
          </div>
        </template>
      </div>

      <!-- 閫€鍑虹櫥褰曟寜閽?-->
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
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { trackHistoryEvent } from '@/api/history';
import UnifiedSearchBox from '@/components/common/UnifiedSearchBox.vue';
import { useUserStore } from '@/stores/auth.js';
import { useAppearanceTransition } from '@/composables/useAppearanceTransition';
import { COLOR_SCHEME_OPTIONS, useSettingsStore } from '@/stores/settings';
import { resolveAvatarUrl } from '@/utils/avatar.js';
import { buildSearchRouteQuery, normalizeSearchTypes } from '@/utils/unifiedSearch';

defineProps({
  isIconMode: { type: Boolean, default: true },
  sidebarRef: { type: Object, default: null },
});

const emit = defineEmits(['update:isIconMode']);

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();
const settingsStore = useSettingsStore();

const colorSchemes = COLOR_SCHEME_OPTIONS;
const isAgentShell = computed(() => route.name === 'agent');
const visibleSchemeValue = computed(() => (isAgentShell.value ? 'coral' : settingsStore.settings.color_scheme));
const { isAppearanceTransitioning } = useAppearanceTransition([isAgentShell]);

const isDark = ref(false);
const isSchemeSwitching = ref(false);
const searchQuery = ref(String(route.query.q || ''));
const searchTypes = ref(normalizeSearchTypes(route.query.types));
let themeObserver = null;

const currentSchemeIndex = computed(() => {
  const currentValue = visibleSchemeValue.value;
  const matchedIndex = colorSchemes.findIndex(item => item.value === currentValue);
  return matchedIndex >= 0 ? matchedIndex : 0;
});

const currentSchemeLabel = computed(() => colorSchemes[currentSchemeIndex.value].label);
const nextSchemeValue = computed(() => settingsStore.getNextColorScheme(settingsStore.settings.color_scheme));
const nextSchemeLabel = computed(() => {
  const targetScheme = colorSchemes.find(item => item.value === nextSchemeValue.value);
  return targetScheme?.label ?? colorSchemes[0].label;
});

const syncThemeFromDom = () => {
  isDark.value = document.documentElement.getAttribute('data-theme') === 'dark';
};

const toggleTheme = async () => {
  const newTheme = isDark.value ? 'light' : 'dark';
  settingsStore.applyTheme(newTheme);
  settingsStore.settings.theme_mode = newTheme;
  if (userStore.token) await settingsStore.updateSettings({ theme_mode: newTheme });
  syncThemeFromDom();
};

const handleColorSchemeToggle = async () => {
  if (isSchemeSwitching.value) return;
  isSchemeSwitching.value = true;
  try {
    await settingsStore.setColorScheme(nextSchemeValue.value, {
      persist: Boolean(userStore.token),
    });
  } finally {
    isSchemeSwitching.value = false;
  }
};

const showSearch = computed(() => route.name !== 'login' && route.name !== 'register');
const trackHeaderSearch = (query, types = []) => {
  if (!userStore.token || !query) return;
  const routeQuery = buildSearchRouteQuery(query, types);
  trackHistoryEvent({
    domain: 'search',
    event_type: 'searched',
    subject_type: 'search_query',
    title: query,
    summary: `搜索: ${query}`,
    route_path: `/search?${new URLSearchParams(routeQuery).toString()}`,
    icon: 'search',
    search_text: query,
    extra: {
      query,
      source: 'header_search',
      types,
    },
  }).catch(() => {});
};

const handleSearchSubmit = ({ query, types }) => {
  if (!query) return;
  trackHeaderSearch(query, types);
  router.push({
    path: '/search',
    query: buildSearchRouteQuery(query, types),
  });
};

const displayAvatar = computed(() => {
  return resolveAvatarUrl(userStore.user?.avatar_url);
});

const goBack = () => router.back();
const emitLoginEvent = () => window.dispatchEvent(new CustomEvent('open-login-modal'));
const handleUserClick = () => { if (userStore.token) router.push('/profile'); };
const handleLogout = () => { if (confirm('确定要退出登录吗？')) { userStore.logout(); router.push('/showcase'); } };

const toggleNotification = async () => {
  if (!userStore.token) return;
  settingsStore.settings.system_notifications = !settingsStore.settings.system_notifications;
  await settingsStore.updateSettings({ system_notifications: settingsStore.settings.system_notifications });
};

onMounted(() => {
  syncThemeFromDom();
  themeObserver = new MutationObserver(syncThemeFromDom);
  themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
});

watch(
  () => route.query.q,
  (value) => {
    searchQuery.value = String(value || '');
  }
);

watch(
  () => route.query.types,
  (value) => {
    searchTypes.value = normalizeSearchTypes(value);
  }
);

onBeforeUnmount(() => {
  themeObserver?.disconnect();
});
</script>

<style scoped>
.app-header {
  position: relative;
  z-index: 40;
  overflow: visible;
  width: min(1100px, calc(100% - 32px), 66.666%);
  margin: 12px auto 0;
  height: 56px;
  background: var(--header-bg);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  flex-shrink: 0;
  border-radius: 999px;
  backdrop-filter: blur(18px);
  box-shadow: var(--shell-shadow), inset 0 0 0 1px var(--shell-glass-border);
  transition: background 0.45s ease, box-shadow 0.45s ease, color 0.35s ease;
}

.header-left-controls {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.back-btn {
  margin-right: 0;
  flex-shrink: 0;
}

.hamburger-btn {
  margin-right: 0;
  flex-shrink: 0;
}

.search-section {
  position: relative;
  z-index: 45;
  display: flex;
  flex-direction: column;
  gap: 4px;
  width: 360px;
}

.search-bar {
  display: flex;
  align-items: center;
  background-color: var(--shell-glass-bg);
  border: 1px solid var(--shell-glass-border);
  border-radius: var(--border-radius-pill);
  padding: 5px 10px;
  transition: background 0.35s ease, border-color 0.35s ease, box-shadow 0.35s ease;
}
.search-bar:focus-within { background-color: var(--shell-glass-hover); }

.search-bar input {
  border: none;
  background: transparent;
  outline: none;
  flex: 1;
  padding: 5px;
  font-size: 14px;
  color: var(--shell-text);
}
.search-bar input::placeholder { color: var(--shell-text-muted); }

.search-clear,
.search-btn {
  background: none;
  color: var(--shell-text-muted);
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s;
}
.search-clear:hover,
.search-btn:hover { color: var(--shell-text); }

.search-dropdown {
  position: absolute;
  top: calc(100% + 10px);
  left: 0;
  width: 100%;
  max-height: 360px;
  overflow-y: auto;
  padding: 10px;
  border-radius: 20px;
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  box-shadow: 0 18px 36px color-mix(in srgb, var(--color-primary) 14%, transparent);
  z-index: 30;
}

.search-dropdown-title {
  padding: 4px 8px 8px;
  color: var(--text-secondary);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.search-dropdown-item {
  width: 100%;
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 8px;
  border: none;
  background: transparent;
  border-radius: 14px;
  color: var(--text-primary);
  cursor: pointer;
  text-align: left;
  transition: background 0.18s ease;
}

.search-dropdown-item:hover {
  background: color-mix(in srgb, var(--color-primary) 8%, var(--card-bg));
}

.search-dropdown-item.is-active {
  background: color-mix(in srgb, var(--color-primary) 10%, var(--card-bg));
}

.dropdown-badge {
  flex-shrink: 0;
  padding: 4px 8px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 700;
  background: color-mix(in srgb, var(--color-primary) 12%, var(--card-bg));
  color: var(--color-primary-dark);
}

.dropdown-badge.accent {
  background: color-mix(in srgb, var(--color-accent-cool) 12%, var(--card-bg));
  color: var(--color-accent-cool);
}

.dropdown-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.dropdown-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.4;
}

.dropdown-subtitle {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.search-dropdown-empty {
  padding: 10px 8px 4px;
  color: var(--text-secondary);
  font-size: 12px;
}

.tag-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  padding: 0 4px;
}

.tag-chip {
  background: rgba(255,255,255,0.15);
  border: 1px solid rgba(255,255,255,0.3);
  border-radius: var(--border-radius-pill, 999px);
  color: rgba(255,255,255,0.9);
  font-size: 11px;
  padding: 2px 8px;
  cursor: pointer;
  transition: background 0.2s;
  white-space: nowrap;
}
.tag-chip:hover { background: rgba(255,255,255,0.28); }

.spacer { flex: 1; }

.user-actions {
  display: flex;
  align-items: center;
  gap: 15px;
}

.icon-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--shell-text-muted);
  transition: color 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}
.icon-btn:hover { color: var(--shell-text); }
.logout-btn:hover { color: var(--shell-text-muted); }

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
  border: 2px solid var(--shell-glass-border);
  transition: border-color 0.35s ease, box-shadow 0.35s ease;
}

.header-avatar-placeholder {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background-color: var(--shell-glass-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--shell-text-muted);
  transition: background-color 0.35s ease, color 0.35s ease;
}

.login-capsule {
  background-color: var(--shell-glass-bg);
  color: var(--shell-text);
  border: 1px solid var(--shell-glass-border);
  padding: 8px 20px;
  border-radius: var(--border-radius-pill);
  font-size: 14px;
  font-weight: bold;
  cursor: pointer;
  transition: background 0.35s ease, border-color 0.35s ease, color 0.35s ease;
}
.login-capsule:hover { background-color: var(--shell-glass-hover); }

.scheme-switch {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  border: 1px solid var(--shell-glass-border);
  background: var(--scheme-toggle-gradient);
  box-shadow:
    inset 0 0 0 1px rgba(255, 255, 255, 0.12),
    0 0 16px var(--scheme-toggle-glow);
  cursor: pointer;
  padding: 0;
  overflow: hidden;
  appearance: none;
  transition: transform 0.2s ease, box-shadow 0.35s ease, background 0.35s ease, border-color 0.35s ease;
}

.scheme-switch::before {
  content: "";
  position: absolute;
  inset: 4px;
  border-radius: 50%;
  background:
    radial-gradient(circle at 30% 28%, rgba(255, 255, 255, 0.95), rgba(255, 255, 255, 0) 44%),
    linear-gradient(145deg, rgba(255, 255, 255, 0.28), rgba(255, 255, 255, 0) 62%);
  pointer-events: none;
}

.scheme-switch__inner {
  position: absolute;
  inset: 10px;
  border-radius: 50%;
  background: rgba(7, 14, 24, 0.22);
  border: 1px solid rgba(255, 255, 255, 0.22);
  backdrop-filter: blur(3px);
  pointer-events: none;
  transition: background 0.35s ease, border-color 0.35s ease;
}

.scheme-switch:hover {
  transform: translateY(-1px);
  box-shadow:
    inset 0 0 0 1px rgba(255, 255, 255, 0.12),
    0 0 20px var(--scheme-toggle-glow);
}

.scheme-switch.is-switching {
  opacity: 0.7;
}

.scheme-switch:disabled {
  cursor: wait;
}

/* 鈹€鈹€ 鏄庢殫鍒囨崲寮€鍏?鈹€鈹€ */
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

@media (max-width: 1320px) {
  .app-header {
    width: min(calc(100% - 28px), 82%);
  }

  .search-section {
    width: 300px;
  }

  .user-actions {
    gap: 12px;
  }
}

@media (max-width: 920px) {
  .app-header {
    width: calc(100% - 20px);
    padding: 0 14px;
  }

  .search-section {
    width: 260px;
  }

  .user-actions {
    gap: 10px;
  }
}

@media (max-width: 720px) {
  .app-header {
    width: calc(100% - 16px);
  }

  .search-section {
    display: none;
  }
}
</style>
