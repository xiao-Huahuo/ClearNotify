<template>
  <header class="app-header">
    <div class="search-bar">
      <input type="text" placeholder="Search..." v-model="searchQuery" @keyup.enter="handleSearch" />
      <button @click="handleSearch" class="search-btn">
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
  background-color: var(--header-bg);
  border-bottom: 1px solid var(--border-color);
  box-shadow: none;
}

.search-bar {
  display: flex;
  align-items: center;
  background-color: #f5f7fa;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-pill); /* 两边圆的圆角矩形 */
  padding: 5px 10px;
  flex: 1;
  max-width: 500px;
  transition: border-color 0.3s;
}

.search-bar:focus-within {
  border-color: var(--color-middle);
}

.search-bar input {
  border: none;
  background: transparent;
  outline: none;
  flex: 1;
  padding-left: 10px;
}

.search-btn {
  background: #000; /* 黑色底色 */
  color: #fff; /* 白色文字 */
  border: none;
  border-radius: var(--border-radius-pill); /* 两边圆的圆角矩形 */
  padding: 8px 20px;
  cursor: pointer;
  display: flex;
  align-items: center;
  font-weight: bold;
  font-size: 14px;
  transition: transform 0.2s, background-color 0.2s;
}

.search-btn:hover {
  background-color: #333;
  transform: scale(1.05);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

.feature-btn {
  background: #f0f0f0;
  border: 1px solid #ccc;
  border-radius: var(--border-radius-pill); /* 统一圆角 */
  padding: 6px 15px;
  cursor: pointer;
  transition: all 0.3s;
}

.feature-btn:hover {
  background: var(--color-middle);
  color: white;
  border-color: var(--color-middle);
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 10px;
}

.avatar {
  width: 32px;
  height: 32px;
  background: #ccc;
  border-radius: 50%;
}

.logout-btn {
  background: none;
  border: none;
  color: var(--color-text-dark);
  cursor: pointer;
  font-weight: 500;
  padding: 5px 10px;
  border-radius: var(--border-radius-main);
}

.logout-btn:hover {
  background-color: rgba(0,0,0,0.05);
}
</style>
