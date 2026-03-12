<template>
  <div class="login-form">
    <h2>Login</h2>
    <form @submit.prevent="handleLogin">
      <div>
        <label>Username:</label>
        <input v-model="username" type="text" required />
      </div>
      <div>
        <label>Password:</label>
        <input v-model="password" type="password" required />
      </div>
      <button type="submit" :disabled="loading">
        {{ loading ? 'Logging in...' : 'Login' }}
      </button>
      <div v-if="errorMessage" class="error">{{ errorMessage }}</div>
    </form>
    <div class="switch-link">
      Don't have an account?
      <a href="#" @click.prevent="$emit('switch-to-register')">Register</a>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useUserStore } from '@/stores/user';

const emit = defineEmits(['success', 'switch-to-register']);

const username = ref('');
const password = ref('');
const errorMessage = ref('');
const loading = ref(false);
const userStore = useUserStore();

const handleLogin = async () => {
  loading.value = true;
  errorMessage.value = '';
  try {
    await userStore.login(username.value, password.value);
    emit('success');
  } catch (error) {
    errorMessage.value = error.response?.data?.detail || 'Login failed';
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.login-form {
  padding: 20px;
}
input {
  width: 100%;
  margin-bottom: 10px;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}
label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}
button {
  width: 100%;
  padding: 10px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 10px;
}
button:disabled {
  background-color: #a5d6a7;
  cursor: not-allowed;
}
.error {
  color: red;
  margin-top: 10px;
  font-size: 14px;
}
.switch-link {
  margin-top: 15px;
  text-align: center;
  font-size: 14px;
}
.switch-link a {
  color: #2196F3;
  text-decoration: none;
}
</style>
