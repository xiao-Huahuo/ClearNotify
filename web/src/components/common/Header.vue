<template>
  <header class="app-header">
    <div class="search-bar">
      <input type="text" placeholder="Search..." v-model="searchQuery" @keyup.enter="handleSearch" />
      <button @click="handleSearch" class="search-btn">
        <span class="search-icon">🔍</span>
        Search
      </button>
    </div>
    <div class="header-right">
      <button class="feature-btn">A</button>
      <button class="feature-btn">B</button>
      <button class="feature-btn">C</button>
      <div class="user-profile">
        <span v-if="userStore.user">Welcome, {{ userStore.user.uname }}</span>
        <div class="avatar"></div>
        <button v-if="userStore.token" @click="handleLogout" class="logout-btn">Logout</button>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useUserStore } from '@/stores/user';

const searchQuery = ref('');
const router = useRouter();
const userStore = useUserStore();

const handleSearch = () => {
  if (searchQuery.value.trim()) {
    router.push({ path: '/search', query: { q: searchQuery.value } });
  }
};

const handleLogout = () => {
  userStore.logout();
  router.push('/');
};
</script>

<style scoped>
.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 20px;
  background-color: #fff;
  border-bottom: 1px solid #e0e0e0;
}

.search-bar {
  display: flex;
  align-items: center;
  background-color: rgba(255, 255, 255, 0.8);
  border: 1px solid #ccc;
  border-radius: 20px;
  padding: 5px 10px;
  flex: 1;
  max-width: 500px;
}

.search-bar input {
  border: none;
  background: transparent;
  outline: none;
  flex: 1;
}

.search-btn {
  background: #4285f4;
  color: white;
  border: none;
  border-radius: 15px;
  padding: 5px 10px;
  cursor: pointer;
  display: flex;
  align-items: center;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

.feature-btn {
  background: #f0f0f0;
  border: 1px solid #ccc;
  border-radius: 5px;
  padding: 5px 10px;
  cursor: pointer;
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 10px;
}

.avatar {
  width: 32px;
  height: 32px;
  background-color: #ccc;
  border-radius: 50%;
}

.logout-btn {
  background: none;
  border: none;
  color: #4285f4;
  cursor: pointer;
}
</style>
