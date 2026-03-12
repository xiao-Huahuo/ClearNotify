<template>
  <div class="home-container">
    <div class="header">
      <h1>ClearNotify - 通知智能解读引擎</h1>
      <div v-if="userStore.token" class="user-info">
        <span>Welcome, {{ userStore.user?.uname }}</span>
        <button @click="handleLogout" class="logout-btn">Logout</button>
      </div>
      <div v-else>
        <button @click="openLoginModal" class="login-btn">Login / Register</button>
      </div>
    </div>

    <!-- 主体内容始终显示 -->
    <div class="input-section">
      <textarea
        v-model="inputText"
        placeholder="在此粘贴通知内容，或上传文件..."
        rows="10"
      ></textarea>

      <div class="actions">
        <input type="file" @change="handleFileUpload" />
        <button @click="submitToAI" :disabled="loading" class="submit-btn">
          {{ loading ? '解读中...' : '智能解读' }}
        </button>
      </div>
    </div>

    <div v-if="aiResponse" class="response-section">
      <h3>解读结果：</h3>
      <div class="result-content">{{ aiResponse }}</div>
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
import { chatWithAI } from '@/api/ai';
import Modal from '@/components/common/Modal.vue';
import LoginForm from '@/components/Home/LoginForm.vue';
import RegisterForm from '@/components/Home/RegisterForm.vue';

const userStore = useUserStore();
const inputText = ref('');
const aiResponse = ref('');
const loading = ref(false);

const showModal = ref(false);
const currentForm = ref('login'); // 'login' or 'register'

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

const handleFileUpload = (event) => {
  const file = event.target.files[0];
  if (file) {
    const reader = new FileReader();
    reader.onload = (e) => {
      inputText.value = e.target.result;
    };
    reader.readAsText(file);
  }
};

const submitToAI = async () => {
  // 检查登录状态
  if (!userStore.token) {
    openLoginModal();
    return;
  }

  if (!inputText.value.trim()) {
    alert('请输入内容');
    return;
  }

  loading.value = true;
  aiResponse.value = '';

  try {
    const response = await chatWithAI(inputText.value);
    aiResponse.value = response.data.reply;
  } catch (error) {
    console.error(error);
    if (error.response?.status === 401) {
       userStore.logout();
       openLoginModal();
    } else {
       alert('AI 服务暂时不可用: ' + (error.response?.data?.detail || error.message));
    }
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.home-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  font-family: Arial, sans-serif;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  border-bottom: 1px solid #eee;
  padding-bottom: 10px;
}
.user-info {
  display: flex;
  align-items: center;
}
.login-btn {
  background-color: #2196F3;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}
.logout-btn {
  background-color: #f44336;
  color: white;
  border: none;
  padding: 5px 10px;
  cursor: pointer;
  border-radius: 3px;
  margin-left: 10px;
}
.input-section textarea {
  width: 100%;
  padding: 10px;
  margin-bottom: 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 14px;
  box-sizing: border-box;
}
.actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.submit-btn {
  background-color: #4CAF50;
  color: white;
  border: none;
  padding: 10px 20px;
  cursor: pointer;
  border-radius: 4px;
  font-size: 16px;
}
.submit-btn:disabled {
  background-color: #ccc;
}
.response-section {
  margin-top: 30px;
  padding: 20px;
  background-color: #f9f9f9;
  border: 1px solid #e0e0e0;
  border-radius: 5px;
}
.result-content {
  white-space: pre-wrap;
  line-height: 1.6;
}
</style>
