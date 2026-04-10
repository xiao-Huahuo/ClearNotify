<template>
  <header class="sc-header" :class="{ scrolled: isScrolled, 'transparent-top': props.transparentTop, 'top-light': props.topText === 'light' }">
    <div class="sc-header-inner">
      <div class="sc-logo" @click="$router.push('/showcase')">
        <img src="@/assets/photos/main-icon.png" alt="" class="sc-logo-img" @error="noImg = true" v-if="!noImg" />
        <span>云上观策</span>
      </div>
      <nav class="sc-nav">
        <router-link to="/showcase" class="sc-link">首页</router-link>
        <router-link to="/showcase/discovery" class="sc-link">政策广场</router-link>
        <router-link to="/showcase/screen" class="sc-link">数据大屏</router-link>
      </nav>
      <div class="sc-actions">
        <button class="sc-btn-primary" @click="$router.push('/')">进入系统</button>
        <button v-if="!userStore.token" @click.stop="emitLoginEvent" class="login-capsule">登录</button>
        <div v-else class="user-profile" @click="handleUserClick" title="个人中心">
          <img v-if="displayAvatar" :src="displayAvatar" alt="avatar" class="header-avatar" />
          <div v-else class="header-avatar-placeholder">
            <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
          </div>
        </div>
        <button v-if="userStore.token" class="icon-btn logout-btn" @click="handleLogout" title="退出登录">
          <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
            <polyline points="16 17 21 12 16 7"></polyline>
            <line x1="21" y1="12" x2="9" y2="12"></line>
          </svg>
        </button>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/auth.js'

const props = defineProps({
  transparentTop: {
    type: Boolean,
    default: true,
  },
  topText: {
    type: String,
    default: 'dark',
  },
  forceScrolled: {
    type: Boolean,
    default: false,
  },
})

const userStore = useUserStore()
const router = useRouter()
const scrolled = ref(false)
const noImg = ref(false)
const isScrolled = computed(() => scrolled.value || props.forceScrolled)

const onScroll = () => { scrolled.value = window.scrollY > 40 }

onMounted(() => {
  onScroll()
  window.addEventListener('scroll', onScroll)
})
onUnmounted(() => {
  window.removeEventListener('scroll', onScroll)
})

const displayAvatar = computed(() => {
  if (!userStore.user?.avatar_url) return null
  const url = userStore.user.avatar_url
  if (url.startsWith('default:')) return `/src/assets/photos/default-avatars/${url.substring(8)}`
  return url
})

const emitLoginEvent = () => window.dispatchEvent(new CustomEvent('open-login-modal'))
const handleUserClick = () => { if (userStore.token) router.push('/profile') }
const handleLogout = () => { if (confirm('确定要退出登录吗？')) { userStore.logout(); router.push('/') } }
</script>

<style scoped>
.sc-header {
  position: fixed; top: 0; left: 0; right: 0; z-index: 100;
  padding: 0 40px; height: 64px;
  background: rgba(255,255,255,0.92);
  backdrop-filter: blur(12px);
  box-shadow: 0 2px 20px rgba(0,0,0,0.08);
  transition: background 0.3s, box-shadow 0.3s;
}
.sc-header.scrolled:not(.transparent-top) {
  background: rgba(255,255,255,0.92);
  backdrop-filter: blur(12px);
  box-shadow: 0 2px 20px rgba(0,0,0,0.08);
}
.sc-header.transparent-top:not(.scrolled) {
  background: transparent;
  box-shadow: none;
  backdrop-filter: none;
}
.sc-header-inner { max-width: 1200px; margin: 0 auto; height: 100%; display: flex; align-items: center; gap: 32px; }
.sc-logo { display: flex; align-items: center; gap: 8px; cursor: pointer; font-size: 18px; font-weight: 800; color: #111; text-shadow: none; }
.sc-header.transparent-top.top-light:not(.scrolled) .sc-logo { color: #fff; text-shadow: 0 1px 4px rgba(0,0,0,0.3); }
.sc-logo-img { width: 28px; height: 28px; filter: none; }
.sc-header.transparent-top.top-light:not(.scrolled) .sc-logo-img { filter: brightness(0) invert(1); }
.sc-nav { display: flex; gap: 4px; flex: 1; justify-content: center; }
.sc-link { padding: 6px 16px; border-radius: 20px; color: #444; text-decoration: none; font-size: 14px; transition: all 0.2s; }
.sc-header.transparent-top.top-light:not(.scrolled) .sc-link { color: rgba(255,255,255,0.9); }
.sc-link:hover { background: rgba(192,57,43,0.1); color: #c0392b; }
.sc-header.transparent-top.top-light:not(.scrolled) .sc-link:hover { background: rgba(255,255,255,0.22); color: #fff; }
.sc-link.router-link-active {
  color: #ff3b30;
  background: rgba(255, 59, 48, 0.12);
  box-shadow: 0 0 14px rgba(255, 59, 48, 0.45), inset 0 0 0 1px rgba(255, 59, 48, 0.28);
  text-shadow: 0 0 8px rgba(255, 59, 48, 0.55);
}
.sc-header.transparent-top:not(.scrolled) .sc-link.router-link-active {
  color: #ff4a3d;
  background: rgba(255,255,255,0.2);
  box-shadow: 0 0 14px rgba(255, 74, 61, 0.5), inset 0 0 0 1px rgba(255,255,255,0.28);
}
.sc-actions { display: flex; gap: 8px; align-items: center; }
.sc-btn-primary { background: #c0392b; border: none; color: #fff; padding: 8px 20px; border-radius: 20px; cursor: pointer; font-size: 13px; font-weight: 600; transition: all 0.2s; }
.sc-btn-primary:hover { background: #e74c3c; transform: translateY(-1px); box-shadow: 0 4px 12px rgba(192,57,43,0.4); }

.icon-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: #444;
  transition: color 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}
.icon-btn:hover { color: #111; }

.user-profile {
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.header-avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid rgba(17,17,17,0.25);
}

.header-avatar-placeholder {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background-color: rgba(17,17,17,0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(17,17,17,0.65);
}

.login-capsule {
  background-color: rgba(17,17,17,0.08);
  color: #222;
  border: 1px solid rgba(17,17,17,0.2);
  padding: 7px 16px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.2s;
}
.login-capsule:hover { background-color: rgba(17,17,17,0.14); }

.sc-header.transparent-top.top-light:not(.scrolled) .icon-btn,
.sc-header.transparent-top.top-light:not(.scrolled) .login-capsule,
.sc-header.transparent-top.top-light:not(.scrolled) .header-avatar-placeholder {
  color: #fff;
}
.sc-header.transparent-top.top-light:not(.scrolled) .login-capsule {
  background: rgba(255,255,255,0.15);
  border-color: rgba(255,255,255,0.4);
}
.sc-header.transparent-top.top-light:not(.scrolled) .header-avatar {
  border-color: rgba(255,255,255,0.55);
}
.sc-header.transparent-top.top-light:not(.scrolled) .header-avatar-placeholder {
  background: rgba(255,255,255,0.2);
}
@media (max-width: 960px) {
  .sc-header {
    padding: 0 18px;
  }

  .sc-nav {
    display: none;
  }

  .sc-header-inner {
    gap: 16px;
  }
}

@media (max-width: 640px) {
  .sc-btn-primary {
    display: none;
  }

  .sc-logo span {
    font-size: 16px;
  }
}
</style>
