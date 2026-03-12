<template>
  <div class="profile-container">
    <h1>我的</h1>
    <div v-if="userStore.token" class="user-info">
      <p>用户名: {{ userStore.user?.uname }}</p>
      <p>邮箱: {{ userStore.user?.email }}</p>
      <button @click="handleLogout" class="logout-btn">退出登录</button>
    </div>
    <div v-else class="login-prompt">
      <p>您尚未登录</p>
      <button @click="openLoginModal" class="login-btn">登录 / 注册</button>
    </div>

    <!-- 弹窗 -->
    <Modal :isOpen="showModal" @close="closeModal">
      <LoginForm
        v-if="currentForm === 'login'"
        @success="handleLoginSuccess"
        @switch-to-register="currentForm = 'register'"
      />
      <RegisterForm
        v-if="currentForm === 'register'"
        @switch-to-login="currentForm = 'login'"
        @success="currentForm = 'login'"
      />
    </Modal>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useUserStore } from '@/stores/user';
import Modal from '@/components/common/Modal.vue';
import LoginForm from '@/components/Home/LoginForm.vue';
import RegisterForm from '@/components/Home/RegisterForm.vue';

const userStore = useUserStore();
const showModal = ref(false);
const currentForm = ref('login');

onMounted(() => {
  if (userStore.token) {
    userStore.fetchUser();
  }
});

const handleLogout = () => {
  userStore.logout();
};

const openLoginModal = () => {
  currentForm.value = 'login';
  showModal.value = true;
};

const closeModal = () => {
  showModal.value = false;
};

const handleLoginSuccess = () => {
  closeModal();
};
</script>

<style scoped>
.profile-container {
  padding: 20px;
}
.user-info p {
  margin: 10px 0;
  font-size: 16px;
}
.logout-btn {
  background-color: #f44336;
  color: white;
  border: none;
  padding: 8px 16px;
  cursor: pointer;
  border-radius: 4px;
  margin-top: 10px;
}
.login-btn {
  background-color: #2196F3;
  color: white;
  border: none;
  padding: 8px 16px;
  cursor: pointer;
  border-radius: 4px;
}
</style>
