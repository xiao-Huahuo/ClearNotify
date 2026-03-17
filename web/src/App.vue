<script setup>
import { onMounted } from 'vue';
import { useUserStore } from '@/stores/user';
import { useSettingsStore } from '@/stores/settings';
import Sidebar from '@/components/common/Sidebar.vue';
import Header from '@/components/common/Header.vue';

const userStore = useUserStore();
const settingsStore = useSettingsStore();

onMounted(async () => {
  // 应用启动时，如果已登录，自动拉取用户信息和设置并应用
  if (userStore.token) {
    await userStore.fetchUser();
    await settingsStore.fetchSettings();
  }
});
</script>

<template>
  <div class="app-layout">
    <Sidebar />
    <div class="content-wrapper">
      <Header />
      <div class="main-content">
        <router-view />
      </div>
    </div>
  </div>
</template>

<style>
body {
  font-family: Arial, sans-serif;
  margin: 0;
  padding: 0;
  height: 100vh;
}
.app-layout {
  display: flex;
  height: 100vh;
}
.content-wrapper {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
}
.main-content {
  flex: 1;
  overflow-y: auto;
  background-color: var(--content-bg); /* 使用 CSS 变量 */
  padding: 20px;
}
</style>
