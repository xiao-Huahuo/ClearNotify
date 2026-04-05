<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue';
import { useRoute } from 'vue-router';
import { useUserStore } from '@/stores/auth.js';
import { useSettingsStore } from '@/stores/settings';
import Sidebar from '@/components/common/Sidebar.vue';
import Header from '@/components/common/Header.vue';
import AuthModal from '@/components/common/AuthModal.vue';
import { getHotTags } from '@/api/news';

const userStore = useUserStore();
const settingsStore = useSettingsStore();
const route = useRoute();
const showAuthModal = ref(false);
const isIconMode = ref(true);
const sidebarRef = ref(null);
const headerTags = ref([]);

const isStandalonePage = computed(() => route.meta?.standalone === true);

const openAuthModal = () => { showAuthModal.value = true; };

onMounted(async () => {
  settingsStore.initAppearance();
  window.addEventListener('open-login-modal', openAuthModal);
  if (userStore.token) {
    await userStore.fetchUser();
    await settingsStore.fetchSettings();
  }
  try {
    const res = await getHotTags(6);
    headerTags.value = res.data?.items?.map(t => t.name || t) || [];
  } catch (_) {}
});

onUnmounted(() => {
  window.removeEventListener('open-login-modal', openAuthModal);
});
</script>

<template>
  <template v-if="isStandalonePage">
    <div class="standalone-page">
      <router-view />
      <AuthModal :is-open="showAuthModal" @close="showAuthModal = false" />
    </div>
  </template>
  <template v-else>
    <div class="app-layout">
      <Sidebar ref="sidebarRef" :is-icon-mode="isIconMode" />
      <div class="content-wrapper">
        <Header
          v-model:is-icon-mode="isIconMode"
          :header-tags="headerTags"
          :sidebar-ref="sidebarRef"
        />
        <div class="main-content">
          <router-view />
        </div>
      </div>
      <AuthModal :is-open="showAuthModal" @close="showAuthModal = false" />
    </div>
  </template>
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
  background-color: var(--content-bg);
  padding: 20px;
}
.standalone-page {
  width: 100vw;
  height: 100vh;
  overflow: hidden;
}
</style>
