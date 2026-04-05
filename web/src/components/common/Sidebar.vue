<template>
  <!-- Drawer overlay (icon mode only) -->
  <transition name="drawer-slide">
    <div v-if="isIconMode && drawerOpen" class="sidebar-drawer" @click.self="drawerOpen = false">
      <div class="sidebar-inner">
        <div class="logo" @click="goHome" style="cursor:pointer">
          <button class="hamburger-btn" @click.stop="drawerOpen = false" title="收起">
            <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
          </button>
          <img src="@/assets/photos/main-icon.png" alt="icon" class="logo-icon" v-if="hasIcon" @error="hasIcon = false" />
          云上观策
        </div>
        <nav class="nav-list">
          <router-link v-for="item in visibleNavItems" :key="item.to" :to="item.to" class="nav-item" active-class="active" @click="drawerOpen = false">
            <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" v-html="item.icon"></svg>
            <span>{{ item.label }}</span>
          </router-link>
        </nav>
        <div class="sidebar-footer">
          <div v-if="!userStore.token" class="login-btn" @click="emitLogin">登录</div>
          <div v-else class="user-info">
            <img v-if="displayAvatar" :src="displayAvatar" class="avatar" alt="avatar" />
            <div v-else class="avatar-placeholder">
              <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
            </div>
            <span class="username">{{ userStore.user?.username }}</span>
          </div>
          <div class="footer-actions">
            <router-link to="/settings" class="footer-icon-btn" title="设置" @click="drawerOpen = false">
              <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.6 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.6a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
            </router-link>
            <button class="footer-icon-btn" @click="showMore = !showMore" title="更多">
              <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none"><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/><circle cx="5" cy="12" r="1"/></svg>
            </button>
          </div>
          <div v-if="showMore" class="more-menu">
            <div class="more-item" @click="showAbout = true; showMore = false">关于</div>
            <div class="more-item" @click="showPermission = true; showMore = false">权限说明</div>
            <div class="more-item" @click="showFaq = true; showMore = false">常见问题</div>
          </div>
        </div>
      </div>
    </div>
  </transition>

  <!-- Preview mode sidebar -->
  <div v-if="!isIconMode" class="sidebar sidebar-preview">
    <div class="logo" @click="goHome" style="cursor:pointer">
      <img src="@/assets/photos/main-icon.png" alt="icon" class="logo-icon" v-if="hasIcon" @error="hasIcon = false" />
      云上观策
    </div>
    <nav class="nav-list">
      <router-link v-for="item in visibleNavItems" :key="item.to" :to="item.to" class="nav-item" active-class="active">
        <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" v-html="item.icon"></svg>
        <span>{{ item.label }}</span>
      </router-link>
    </nav>
    <div class="sidebar-footer">
      <div v-if="!userStore.token" class="login-btn" @click="emitLogin">登录</div>
      <div v-else class="user-info">
        <img v-if="displayAvatar" :src="displayAvatar" class="avatar" alt="avatar" />
        <div v-else class="avatar-placeholder">
          <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
        </div>
        <span class="username">{{ userStore.user?.username }}</span>
      </div>
      <div class="footer-actions">
        <router-link to="/settings" class="footer-icon-btn" title="设置">
          <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.6 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.6a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
        </router-link>
        <button class="footer-icon-btn" @click="showMore = !showMore" title="更多">
          <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none"><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/><circle cx="5" cy="12" r="1"/></svg>
        </button>
      </div>
      <div v-if="showMore" class="more-menu">
        <div class="more-item" @click="showAbout = true; showMore = false">关于</div>
        <div class="more-item" @click="showPermission = true; showMore = false">权限说明</div>
        <div class="more-item" @click="showFaq = true; showMore = false">常见问题</div>
      </div>
    </div>
  </div>

  <!-- Icon mode narrow capsule -->
  <div v-if="isIconMode" class="sidebar sidebar-icon-mode">
    <div class="icon-logo" @click="goHome" title="主页" style="cursor:pointer">
      <img src="@/assets/photos/main-icon.png" alt="icon" class="logo-icon" v-if="hasIcon" @error="hasIcon = false" />
      <svg v-else viewBox="0 0 24 24" width="22" height="22" stroke="currentColor" stroke-width="2" fill="none"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/></svg>
    </div>
    <nav class="icon-nav">
      <router-link v-for="item in visibleNavItems" :key="item.to" :to="item.to" class="icon-nav-item" active-class="active" :title="item.label">
        <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" v-html="item.icon"></svg>
      </router-link>
    </nav>
    <div class="icon-footer">
      <router-link to="/settings" class="icon-nav-item" title="设置">
        <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.6 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.6a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
      </router-link>
    </div>
  </div>

  <!-- Dialogs -->
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
        <p><strong>Q: 如何开始使用？</strong><br/>A: 登录后即可访问所有功能模块。</p>
        <p><strong>Q: 数据如何更新？</strong><br/>A: 系统定期自动同步最新政策数据。</p>
        <button class="dialog-close" @click="showFaq = false">关闭</button>
      </div>
    </div>
  </teleport>
</template>

<script setup>
import { ref, computed, defineExpose } from 'vue';
import { useRouter } from 'vue-router';
import { useUserStore } from '@/stores/auth.js';

const props = defineProps({
  isIconMode: { type: Boolean, default: true },
});

const userStore = useUserStore();
const router = useRouter();
const hasIcon = ref(true);
const drawerOpen = ref(false);
const showMore = ref(false);
const showAbout = ref(false);
const showPermission = ref(false);
const showFaq = ref(false);

const navItems = [
  { to: '/', label: '主页', icon: '<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>' },
  { to: '/discovery-home', label: '发现', icon: '<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>' },
  { to: '/data-analysis-and-visualization', label: '数据分析', icon: '<polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>' },
  { to: '/agent', label: 'ClearFlow智能体', icon: '<rect x="3" y="3" width="18" height="14" rx="2"/><path d="M7 21h10"/><path d="M9 17v4"/><path d="M15 17v4"/>' },
  { to: '/history', label: '会话历史', icon: '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>' },
  { to: '/favorites', label: '我的收藏', icon: '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>' },
  { to: '/todo', label: '办事进度', icon: '<polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>' },
  { to: '/profile', label: '我的', icon: '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>' },
  { to: '/admin', label: '管理员', icon: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>', adminOnly: true },
];

const visibleNavItems = computed(() =>
  navItems.filter(item => !item.adminOnly || userStore.user?.is_admin)
);

const displayAvatar = computed(() => {
  const url = userStore.user?.avatar_url;
  if (!url) return null;
  if (url.startsWith('default:')) return `/src/assets/photos/default-avatars/${url.substring(8)}`;
  return url;
});

const goHome = () => router.push('/');
const emitLogin = () => window.dispatchEvent(new CustomEvent('open-login-modal'));
const openDrawer = () => { drawerOpen.value = true; };

defineExpose({ openDrawer });
</script>

<style scoped>
/* ── Shared sidebar base ── */
.sidebar {
  background: var(--sidebar-bg-gradient);
  color: #fff;
  height: 100vh;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

/* ── Preview mode ── */
.sidebar-preview {
  width: 200px;
  overflow: hidden;
  transition: width 0.3s cubic-bezier(0.4,0,0.2,1);
}

/* ── Icon mode (narrow capsule) ── */
.sidebar-icon-mode {
  width: 60px;
  align-items: center;
  border-radius: 0 16px 16px 0;
  padding: 8px 0;
  transition: width 0.3s cubic-bezier(0.4,0,0.2,1);
}

/* ── Logo ── */
.logo {
  padding: 16px 20px;
  font-size: 17px;
  font-weight: bold;
  display: flex;
  align-items: center;
  gap: 10px;
  color: #fff;
  letter-spacing: 1px;
  flex-shrink: 0;
}
.logo-icon { width: 24px; height: 24px; filter: brightness(0) invert(1); }

.icon-logo {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
  border-radius: 50%;
  transition: background 0.2s;
  flex-shrink: 0;
}
.icon-logo:hover { background: rgba(255,255,255,0.15); }
.icon-logo .logo-icon { width: 24px; height: 24px; }

/* ── Nav list (preview + drawer) ── */
.nav-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 8px 12px;
  gap: 2px;
  overflow-y: auto;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  color: rgba(255,255,255,0.8);
  text-decoration: none;
  font-size: 14px;
  transition: all 0.2s;
}
.nav-item:hover { background: rgba(255,255,255,0.15); color: #fff; }
.nav-item.active { background: rgba(255,255,255,0.25); color: #fff; }

/* ── Icon nav (icon mode) ── */
.icon-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  width: 100%;
  padding: 0 8px;
}
.icon-nav-item {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  color: rgba(255,255,255,0.75);
  text-decoration: none;
  transition: all 0.2s;
}
.icon-nav-item:hover { background: rgba(255,255,255,0.15); color: #fff; }
.icon-nav-item.active { background: rgba(255,255,255,0.25); color: #fff; }

.icon-footer {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 0;
}

/* ── Sidebar footer (preview + drawer) ── */
.sidebar-footer {
  padding: 12px;
  border-top: 1px solid rgba(255,255,255,0.1);
  flex-shrink: 0;
  position: relative;
}
.login-btn {
  text-align: center;
  padding: 8px;
  border-radius: 8px;
  background: rgba(255,255,255,0.15);
  cursor: pointer;
  font-size: 14px;
  margin-bottom: 8px;
  transition: background 0.2s;
}
.login-btn:hover { background: rgba(255,255,255,0.25); }
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
  border: 1px solid rgba(255,255,255,0.4);
  flex-shrink: 0;
}
.avatar-placeholder {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: rgba(255,255,255,0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.username {
  font-size: 13px;
  color: rgba(255,255,255,0.9);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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
  color: rgba(255,255,255,0.75);
  background: none;
  border: none;
  cursor: pointer;
  text-decoration: none;
  transition: all 0.2s;
}
.footer-icon-btn:hover { background: rgba(255,255,255,0.15); color: #fff; }

.more-menu {
  position: absolute;
  bottom: calc(100% + 4px);
  left: 12px;
  background: var(--card-bg, #fff);
  color: var(--text-primary, #333);
  border-radius: 10px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
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
.more-item:hover { background: rgba(0,0,0,0.06); }

/* ── Drawer ── */
.sidebar-drawer {
  position: fixed;
  inset: 0;
  z-index: 200;
  background: rgba(0,0,0,0.35);
  display: flex;
}
.sidebar-inner {
  width: 200px;
  background: var(--sidebar-bg-gradient);
  color: #fff;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.drawer-slide-enter-active,
.drawer-slide-leave-active { transition: opacity 0.3s ease; }
.drawer-slide-enter-active .sidebar-inner,
.drawer-slide-leave-active .sidebar-inner { transition: transform 0.3s cubic-bezier(0.4,0,0.2,1); }
.drawer-slide-enter-from { opacity: 0; }
.drawer-slide-enter-from .sidebar-inner { transform: translateX(-100%); }
.drawer-slide-leave-to { opacity: 0; }
.drawer-slide-leave-to .sidebar-inner { transform: translateX(-100%); }

/* ── Hamburger ── */
.hamburger-btn {
  background: none;
  border: none;
  color: rgba(255,255,255,0.85);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px;
  border-radius: 6px;
  transition: background 0.2s;
  flex-shrink: 0;
}
.hamburger-btn:hover { background: rgba(255,255,255,0.15); color: #fff; }

/* ── Dialogs ── */
.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.4);
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
  box-shadow: 0 8px 32px rgba(0,0,0,0.18);
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
  background: var(--primary-color, #c0392b);
  color: #fff;
  cursor: pointer;
  font-size: 14px;
  transition: opacity 0.2s;
}
.dialog-close:hover { opacity: 0.85; }
</style>
