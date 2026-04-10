<template>
  <div
    ref="sidebarRootRef"
    class="sidebar"
    :class="[isIconMode ? 'sidebar-icon-mode' : 'sidebar-preview', { 'appearance-transitioning': isAppearanceTransitioning }]"
  >
    <div class="logo" @click="goHome" v-show="!isIconMode">
      <img src="@/assets/photos/main-icon.png" alt="icon" class="logo-icon" v-if="hasIcon" @error="hasIcon = false" />
      <span class="logo-text">云上观策</span>
    </div>

    <nav class="nav-list">
      <router-link
        v-for="item in visiblePrimaryNavItems"
        :key="item.to"
        :to="item.to"
        class="nav-item"
        active-class="active"
        :title="item.label"
      >
        <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" v-html="item.icon"></svg>
        <span class="nav-label">{{ item.label }}</span>
      </router-link>

      <div
        v-if="visiblePolicyHallItems.length"
        class="nav-group"
        :class="{ active: isPolicyHallActive, expanded: policyGroupExpanded }"
      >
        <button
          ref="policyGroupButtonRef"
          type="button"
          class="nav-item nav-item-button nav-group-toggle"
          :class="{ active: isPolicyHallActive }"
          :title="policyGroupExpanded ? '收起政策大厅' : '展开政策大厅'"
          :aria-expanded="policyGroupExpanded ? 'true' : 'false'"
          @click="togglePolicyGroup"
        >
          <svg class="policy-group-icon" viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" v-html="policyHallIcon"></svg>
          <span class="nav-label">政策大厅</span>
          <svg
            v-show="!isIconMode"
            class="nav-caret"
            viewBox="0 0 24 24"
            width="14"
            height="14"
            stroke="currentColor"
            stroke-width="2"
            fill="none"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <polyline points="6 9 12 15 18 9"></polyline>
          </svg>
        </button>

        <transition name="submenu-reveal">
          <div v-if="policyGroupExpanded && !isIconMode" class="nav-submenu">
            <router-link
              v-for="item in visiblePolicyHallItems"
              :key="item.to"
              :to="item.to"
              class="nav-item nav-subitem"
              active-class="active"
              :title="item.label"
            >
              <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" v-html="item.icon"></svg>
              <span class="nav-label">{{ item.label }}</span>
            </router-link>
          </div>
        </transition>
      </div>

      <router-link
        v-for="item in visibleSecondaryNavItems"
        :key="item.to"
        :to="item.to"
        class="nav-item"
        active-class="active"
        :title="item.label"
      >
        <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" v-html="item.icon"></svg>
        <span class="nav-label">{{ item.label }}</span>
      </router-link>

      <router-link to="/settings" class="nav-item" title="设置" v-show="isIconMode">
        <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none">
          <circle cx="12" cy="12" r="3"/>
          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.6 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.6a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
        </svg>
        <span class="nav-label">设置</span>
      </router-link>
    </nav>

    <div class="sidebar-footer" v-show="!isIconMode">
      <div v-if="!userStore.token" class="login-btn" @click="emitLogin">登录</div>
      <div v-else class="user-info">
        <img v-if="displayAvatar" :src="displayAvatar" class="avatar" alt="avatar" />
        <div v-else class="avatar-placeholder">
          <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
            <circle cx="12" cy="7" r="4"/>
          </svg>
        </div>
        <span class="username">{{ userStore.user?.username }}</span>
      </div>
      <div class="footer-actions">
        <router-link to="/settings" class="footer-icon-btn" title="设置">
          <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none">
            <circle cx="12" cy="12" r="3"/>
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.6 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.6a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
          </svg>
        </router-link>
        <button class="footer-icon-btn" @click="showMore = !showMore" title="更多">
          <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none">
            <circle cx="12" cy="12" r="1"/>
            <circle cx="19" cy="12" r="1"/>
            <circle cx="5" cy="12" r="1"/>
          </svg>
        </button>
      </div>
      <div v-if="showMore" class="more-menu">
        <div class="more-item" @click="showAbout = true; showMore = false">关于</div>
        <div class="more-item" @click="showPermission = true; showMore = false">权限说明</div>
        <div class="more-item" @click="showFaq = true; showMore = false">常见问题</div>
      </div>
    </div>
  </div>

  <teleport to="body">
    <transition name="flyout-reveal">
      <div
        v-if="policyGroupExpanded && isIconMode && visiblePolicyHallItems.length"
        ref="policyFlyoutRef"
        class="policy-flyout-capsule"
        :style="policyFlyoutStyle"
      >
        <router-link
          v-for="item in visiblePolicyHallItems"
          :key="item.to"
          :to="item.to"
          class="policy-flyout-item"
          active-class="active"
          :title="item.label"
          :aria-label="item.label"
          @click="handlePolicyFlyoutNavigate"
        >
          <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" v-html="item.icon"></svg>
        </router-link>
      </div>
    </transition>
  </teleport>

  <teleport to="body">
    <div v-if="showAbout" class="dialog-overlay" @click.self="showAbout = false">
      <div class="dialog">
        <h3>关于云上观策</h3>
        <p>云上观策是一个智能政策分析与知识管理平台，帮助用户高效获取、分析和管理政策信息。</p>
        <button class="dialog-close" @click="showAbout = false">关闭</button>
      </div>
    </div>
    <div v-if="showPermission" class="dialog-overlay" @click.self="showPermission = false">
      <div class="dialog">
        <h3>权限说明</h3>
        <p>普通用户可访问主要功能模块。管理员用户额外拥有系统管理权限，可管理用户和系统配置。</p>
        <button class="dialog-close" @click="showPermission = false">关闭</button>
      </div>
    </div>
    <div v-if="showFaq" class="dialog-overlay" @click.self="showFaq = false">
      <div class="dialog">
        <h3>常见问题</h3>
        <p><strong>Q: 如何开始使用？</strong><br />A: 登录后即可访问主要功能模块。</p>
        <p><strong>Q: 数据如何更新？</strong><br />A: 系统会定期自动同步最新政策数据。</p>
        <button class="dialog-close" @click="showFaq = false">关闭</button>
      </div>
    </div>
  </teleport>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useUserStore } from '@/stores/auth.js';
import { useAppearanceTransition } from '@/composables/useAppearanceTransition';

const props = defineProps({
  isIconMode: { type: Boolean, default: true },
});

const userStore = useUserStore();
const route = useRoute();
const router = useRouter();
const hasIcon = ref(true);
const showMore = ref(false);
const showAbout = ref(false);
const showPermission = ref(false);
const showFaq = ref(false);
const sidebarRootRef = ref(null);
const policyGroupButtonRef = ref(null);
const policyFlyoutRef = ref(null);
const policyGroupExpanded = ref(false);
const policyFlyoutTop = ref(12);
const policyFlyoutLeft = ref(84);
const isAgentShell = computed(() => route.name === 'agent');
const { isAppearanceTransitioning } = useAppearanceTransition([isAgentShell]);

const policyHallIcon = '<path d="M3 10h18"/><path d="M5 20V10"/><path d="M9 20V10"/><path d="M15 20V10"/><path d="M19 20V10"/><path d="M2 20h20"/><path d="M12 4 3 10h18z"/>';

const primaryNavItems = [
  { to: '/home', label: '主页', icon: '<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>' },
  { to: '/agent', label: '云小圆', icon: '<rect x="3" y="3" width="18" height="14" rx="2"/><path d="M7 21h10"/><path d="M9 17v4"/><path d="M15 17v4"/>' },
  { to: '/showcase/discovery', label: '发现', icon: '<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>' },
  { to: '/public-opinion-hall', label: '民生大厅', icon: '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>' },
];

const policyHallItems = [
  { to: '/policy-swipe', label: '政策推荐', icon: '<path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>' },
  { to: '/policy-publish-center', label: '政策发布', icon: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>', certifiedOnly: true },
  { to: '/certified-analysis', label: '发布追踪', icon: '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>', certifiedOnly: true },
];

const secondaryNavItems = [
  { to: '/todo', label: '办事进度', icon: '<polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>' },
  { to: '/favorites', label: '我的收藏', icon: '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>' },
  { to: '/history', label: '会话历史', icon: '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>' },
  { to: '/data-analysis-and-visualization', label: '数据分析', icon: '<polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>' },
  { to: '/admin', label: '管理员', icon: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>', adminOnly: true },
  { to: '/profile', label: '我的', icon: '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>' },
];

const isNavItemVisible = (item) => {
  if (item.adminOnly && userStore.user?.role !== 'admin') return false;
  if (item.certifiedOnly && !['certified', 'admin'].includes(userStore.user?.role)) return false;
  return true;
};

const visiblePrimaryNavItems = computed(() => primaryNavItems.filter(isNavItemVisible));
const visiblePolicyHallItems = computed(() => policyHallItems.filter(isNavItemVisible));
const visibleSecondaryNavItems = computed(() => secondaryNavItems.filter(isNavItemVisible));
const isPolicyHallActive = computed(() => policyHallItems.some(item => item.to === route.path));
const policyFlyoutStyle = computed(() => ({
  top: `${policyFlyoutTop.value}px`,
  left: `${policyFlyoutLeft.value}px`,
}));

const closePolicyGroup = () => {
  policyGroupExpanded.value = false;
};

const syncPolicyFlyoutPosition = async () => {
  if (!props.isIconMode || !policyGroupExpanded.value || !policyGroupButtonRef.value) return;
  const rect = policyGroupButtonRef.value.getBoundingClientRect();
  policyFlyoutLeft.value = rect.right + 12;
  policyFlyoutTop.value = rect.top;
  await nextTick();
  if (!policyFlyoutRef.value) return;
  const viewportPadding = 12;
  const flyoutHeight = policyFlyoutRef.value.offsetHeight || 0;
  const centeredTop = rect.top + rect.height / 2 - flyoutHeight / 2;
  const maxTop = Math.max(viewportPadding, window.innerHeight - flyoutHeight - viewportPadding);
  policyFlyoutTop.value = Math.min(Math.max(viewportPadding, centeredTop), maxTop);
};

const togglePolicyGroup = () => {
  policyGroupExpanded.value = !policyGroupExpanded.value;
  if (props.isIconMode && policyGroupExpanded.value) {
    syncPolicyFlyoutPosition();
  }
};

const handlePolicyFlyoutNavigate = () => {
  if (props.isIconMode) {
    closePolicyGroup();
  }
};

const handleGlobalPointerDown = (event) => {
  if (!policyGroupExpanded.value || !props.isIconMode) return;
  const target = event.target;
  if (policyGroupButtonRef.value?.contains(target)) return;
  if (policyFlyoutRef.value?.contains(target)) return;
  closePolicyGroup();
};

const handleViewportChange = () => {
  if (props.isIconMode && policyGroupExpanded.value) {
    syncPolicyFlyoutPosition();
  }
};

watch(
  () => route.path,
  (path) => {
    if (props.isIconMode) {
      closePolicyGroup();
      return;
    }
    if (policyHallItems.some(item => item.to === path)) {
      policyGroupExpanded.value = true;
    }
  },
  { immediate: true }
);

watch(
  () => props.isIconMode,
  (isIconMode) => {
    if (isIconMode) {
      closePolicyGroup();
      return;
    }
    if (isPolicyHallActive.value) {
      policyGroupExpanded.value = true;
    }
  }
);

watch(
  () => policyGroupExpanded.value,
  (expanded) => {
    if (expanded && props.isIconMode) {
      syncPolicyFlyoutPosition();
    }
  }
);

onMounted(() => {
  window.addEventListener('resize', handleViewportChange);
  window.addEventListener('scroll', handleViewportChange, true);
  document.addEventListener('pointerdown', handleGlobalPointerDown);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleViewportChange);
  window.removeEventListener('scroll', handleViewportChange, true);
  document.removeEventListener('pointerdown', handleGlobalPointerDown);
});

const displayAvatar = computed(() => {
  const url = userStore.user?.avatar_url;
  if (!url) return null;
  if (url.startsWith('default:')) return `/src/assets/photos/default-avatars/${url.substring(8)}`;
  return url;
});

const goHome = () => router.push('/showcase');
const emitLogin = () => window.dispatchEvent(new CustomEvent('open-login-modal'));
</script>

<style scoped>
.sidebar {
  background: var(--sidebar-bg-gradient);
  color: var(--shell-text);
  height: 100vh;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  overflow: hidden;
  transition:
    width 0.45s cubic-bezier(0.34, 1.56, 0.64, 1),
    border-radius 0.45s cubic-bezier(0.34, 1.56, 0.64, 1),
    padding 0.45s cubic-bezier(0.34, 1.56, 0.64, 1),
    box-shadow 0.45s ease,
    background 0.45s ease,
    color 0.35s ease;
}

.sidebar-preview {
  width: 200px;
  border-radius: 0;
  padding: 0;
  box-shadow: none;
}

.sidebar-icon-mode {
  width: 60px;
  align-items: center;
  justify-content: flex-start;
  border-radius: 999px;
  padding: 10px 0;
  box-shadow: var(--shell-shadow);
}

.nav-label {
  transition: opacity 0.25s ease, max-width 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  overflow: hidden;
  white-space: nowrap;
}

.sidebar-icon-mode .nav-label {
  display: none;
  opacity: 0;
  max-width: 0;
}

.sidebar-preview .nav-label {
  opacity: 1;
  max-width: 160px;
}

.logo {
  padding: 16px 20px;
  font-size: 17px;
  font-weight: bold;
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--shell-text);
  letter-spacing: 1px;
  flex-shrink: 0;
  cursor: pointer;
  transition: color 0.35s ease;
}

.logo-icon {
  width: 24px;
  height: 24px;
  filter: brightness(0) invert(1);
}

.nav-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 8px 12px;
  gap: 2px;
  overflow-y: auto;
  overflow-x: hidden;
}

.sidebar-icon-mode .nav-list {
  flex: none;
  width: 100%;
  display: grid;
  justify-items: center;
  align-content: start;
  padding: 4px 0;
  gap: 1px;
  overflow: hidden;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  color: var(--shell-text-muted);
  text-decoration: none;
  font-size: 14px;
  transition: all 0.45s cubic-bezier(0.34, 1.56, 0.64, 1);
  white-space: nowrap;
  overflow: hidden;
  box-shadow: inset 0 0 0 1px transparent;
}

.nav-item-button {
  width: 100%;
  border: none;
  background: none;
  font: inherit;
  cursor: pointer;
  text-align: left;
}

.sidebar-icon-mode .nav-item {
  padding: 6px;
  gap: 0;
  border-radius: 50%;
  justify-content: center;
  align-items: center;
  width: 32px;
  height: 32px;
  margin: 0;
}

.sidebar-icon-mode .nav-item svg {
  display: block;
  margin: 0 auto;
}

.nav-item:hover {
  background: var(--sidebar-hover-bg);
  color: var(--shell-text);
}

.nav-item.active {
  background: var(--sidebar-active-bg);
  box-shadow: inset 0 0 0 1px var(--sidebar-active-border);
  color: var(--shell-text);
}

.nav-group {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-group-toggle {
  position: relative;
}

.policy-group-icon {
  transform: scale(0.94);
  transform-origin: center;
}

.nav-caret {
  margin-left: auto;
  flex-shrink: 0;
  transition: transform 0.28s ease;
}

.nav-group.expanded .nav-caret {
  transform: rotate(180deg);
}

.nav-submenu {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-left: 12px;
  padding: 2px 0 4px 14px;
  border-left: 1px solid var(--shell-glass-border);
}

.nav-subitem {
  font-size: 13px;
  padding-top: 8px;
  padding-bottom: 8px;
}

.submenu-reveal-enter-active,
.submenu-reveal-leave-active {
  overflow: hidden;
  transition:
    max-height 0.3s ease,
    opacity 0.24s ease,
    transform 0.3s ease;
}

.submenu-reveal-enter-from,
.submenu-reveal-leave-to {
  max-height: 0;
  opacity: 0;
  transform: translateY(-8px);
}

.submenu-reveal-enter-to,
.submenu-reveal-leave-from {
  max-height: 220px;
  opacity: 1;
  transform: translateY(0);
}

.policy-flyout-capsule {
  position: fixed;
  z-index: 140;
  display: flex;
  flex-direction: column;
  gap: 6px;
  align-items: center;
  padding: 8px;
  border-radius: 999px;
  background: var(--sidebar-bg);
  border: 1px solid var(--shell-glass-border);
  box-shadow:
    var(--shell-shadow),
    inset 0 0 0 1px rgba(255, 255, 255, 0.08);
  overflow: hidden;
}

.policy-flyout-item {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  padding: 0;
  border-radius: 50%;
  color: var(--shell-text-muted);
  text-decoration: none;
  transition:
    background 0.22s ease,
    color 0.22s ease,
    box-shadow 0.22s ease,
    transform 0.22s ease;
}

.policy-flyout-item svg {
  flex-shrink: 0;
}

.policy-flyout-item:hover {
  background: var(--sidebar-hover-bg);
  color: var(--shell-text);
  transform: scale(1.04);
}

.policy-flyout-item.active {
  background: var(--sidebar-active-bg);
  box-shadow: inset 0 0 0 1px var(--sidebar-active-border);
  color: var(--shell-text);
}

.flyout-reveal-enter-active,
.flyout-reveal-leave-active {
  transform-origin: left center;
  transition:
    opacity 0.2s ease,
    transform 0.24s cubic-bezier(0.22, 1, 0.36, 1);
}

.flyout-reveal-enter-from,
.flyout-reveal-leave-to {
  opacity: 0;
  transform: translate3d(-10px, 0, 0) scale(0.96);
}

.flyout-reveal-enter-to,
.flyout-reveal-leave-from {
  opacity: 1;
  transform: translate3d(0, 0, 0) scale(1);
}

.sidebar-footer {
  padding: 12px;
  border-top: 1px solid var(--shell-glass-border);
  flex-shrink: 0;
  position: relative;
  transition: border-color 0.35s ease;
}

.login-btn {
  text-align: center;
  padding: 8px;
  border-radius: 8px;
  background: var(--shell-glass-bg);
  cursor: pointer;
  font-size: 14px;
  margin-bottom: 8px;
  transition: background 0.35s ease, color 0.35s ease, border-color 0.35s ease;
}

.login-btn:hover {
  background: var(--shell-glass-hover);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  padding: 4px 0;
}

.avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  object-fit: cover;
  border: 1px solid var(--shell-glass-border);
  flex-shrink: 0;
  transition: border-color 0.35s ease;
}

.avatar-placeholder {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--shell-glass-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: background 0.35s ease, color 0.35s ease;
}

.username {
  font-size: 13px;
  color: var(--shell-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  transition: color 0.35s ease;
}

.footer-actions {
  display: flex;
  gap: 4px;
}

.footer-icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 8px;
  color: var(--shell-text-muted);
  background: none;
  border: none;
  cursor: pointer;
  text-decoration: none;
  transition: background 0.35s ease, color 0.35s ease, border-color 0.35s ease;
}

.footer-icon-btn:hover {
  background: var(--shell-glass-hover);
  color: var(--shell-text);
}

.more-menu {
  position: absolute;
  bottom: calc(100% + 4px);
  left: 12px;
  background: var(--card-bg, #fff);
  color: var(--text-primary, #333);
  border-radius: 10px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  min-width: 120px;
  z-index: 10;
}

.more-item {
  padding: 10px 16px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.15s;
}

.more-item:hover {
  background: rgba(0, 0, 0, 0.06);
}

.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: 300;
  display: flex;
  align-items: center;
  justify-content: center;
}

.dialog {
  background: var(--card-bg, #fff);
  color: var(--text-primary, #333);
  border-radius: 14px;
  padding: 28px 32px;
  max-width: 420px;
  width: 90%;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.18);
}

.dialog h3 {
  margin: 0 0 16px;
  font-size: 18px;
}

.dialog p {
  margin: 0 0 12px;
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-secondary, #666);
}

.dialog-close {
  margin-top: 8px;
  padding: 8px 24px;
  border: none;
  border-radius: 8px;
  background: var(--color-primary, #c0392b);
  color: #fff;
  cursor: pointer;
  font-size: 14px;
  transition: opacity 0.2s;
}

.dialog-close:hover {
  opacity: 0.85;
}
</style>
