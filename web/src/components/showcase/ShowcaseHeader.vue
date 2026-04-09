<template>
  <header class="sc-header" :class="{ scrolled, 'transparent-top': transparentTop, 'top-light': topText === 'light' }">
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
        <button class="sc-btn-ghost" @click="$router.push('/profile')" v-if="userStore.token">我的</button>
        <button class="sc-btn-ghost" @click="openLogin" v-else>登录</button>
        <button class="sc-btn-primary" @click="$router.push('/')">进入系统</button>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
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
})

const userStore = useUserStore()
const scrolled = ref(false)
const noImg = ref(false)

const onScroll = () => { scrolled.value = window.scrollY > 40 }

onMounted(() => {
  onScroll()
  window.addEventListener('scroll', onScroll)
})
onUnmounted(() => {
  window.removeEventListener('scroll', onScroll)
})

const openLogin = () => window.dispatchEvent(new CustomEvent('open-login-modal'))
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
.sc-btn-ghost { background: none; border: 1px solid #ddd; color: #444; padding: 7px 18px; border-radius: 20px; cursor: pointer; font-size: 13px; transition: all 0.2s; }
.sc-header.transparent-top.top-light:not(.scrolled) .sc-btn-ghost { background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.4); color: #fff; }
.sc-btn-ghost:hover { background: rgba(255,255,255,0.3); }
.sc-btn-primary { background: #c0392b; border: none; color: #fff; padding: 8px 20px; border-radius: 20px; cursor: pointer; font-size: 13px; font-weight: 600; transition: all 0.2s; }
.sc-btn-primary:hover { background: #e74c3c; transform: translateY(-1px); box-shadow: 0 4px 12px rgba(192,57,43,0.4); }
</style>
