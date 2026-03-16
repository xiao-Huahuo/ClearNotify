<template>
  <div class="sidebar">
    <div class="logo">
      <img src="@/assets/photos/main-icon.png" alt="icon" class="logo-icon" v-if="hasIcon" @error="hasIcon = false" />
      ClearNotify
    </div>
    <nav>
      <router-link to="/" class="nav-item" active-class="active">
        <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" class="nav-icon"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>
        主页
      </router-link>
      <router-link to="/feature-a" class="nav-item" active-class="active">
        <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" class="nav-icon"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
        文件处理
      </router-link>
      <router-link to="/feature-b" class="nav-item" active-class="active">
        <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" class="nav-icon"><polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 17 12 22 22 17"></polyline><polyline points="2 12 12 17 22 12"></polyline></svg>
        数据分析
      </router-link>
      <router-link to="/feature-c" class="nav-item" active-class="active">
        <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" class="nav-icon"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
        会话历史
      </router-link>
      <router-link to="/profile" class="nav-item" active-class="active">
        <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" class="nav-icon"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
        我的
      </router-link>
    </nav>
    <div class="sidebar-footer">
      <div class="settings-btn" title="设置">
        <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
const hasIcon = ref(true); // 如果图标不存在，优雅降级
</script>

<style scoped>
.sidebar {
  width: 200px;
  background-color: var(--sidebar-bg);
  color: var(--color-text-dark);
  height: 100vh;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  /* 去掉边框线，和右边融为一体 */
}
.logo {
  padding: 20px;
  font-size: 20px;
  font-weight: bold;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  /* 去掉底边框线 */
  color: var(--color-text-dark);
}
.logo-icon {
  width: 24px;
  height: 24px;
  /* 可以使用 CSS 滤镜将黑色图标变为与主题匹配的颜色，但按要求此处应该是黑色的，所以原样显示即可 */
}
nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 10px 0;
}
.nav-item {
  padding: 10px 20px;
  color: #666;
  text-decoration: none;
  transition: all 0.2s;
  border-radius: 12px;
  margin: 4px 10px;
  display: flex;
  align-items: center;
  gap: 12px;
}
.nav-item:hover {
  background-color: #f5f7fa;
  color: #000;
}

/* 选中项：淡蓝色背景，水晶蓝文字和图标 */
.nav-item.active {
  background-color: #e6f7ff; /* 淡蓝色底色 */
  color: #00a8ff; /* 水晶蓝文字 */
  font-weight: bold;
}
.nav-item.active .nav-icon {
  color: #00a8ff; /* 水晶蓝图标 */
}

.sidebar-footer {
  padding: 20px;
  display: flex;
  align-items: center;
}
.settings-btn {
  color: #999;
  cursor: pointer;
  transition: color 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}
.settings-btn:hover {
  color: #000;
}
</style>
