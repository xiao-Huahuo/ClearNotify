<template>
  <div class="login-wrapper">
    <div class="form-container">
      <div class="logo-area">
        <img src="@/assets/photos/main-icon.png" alt="icon" class="main-icon" v-if="hasIcon" @error="hasIcon = false" />
        <h1 class="logo-text">
          <span v-for="(ch, i) in 'ClearNotify'" :key="i" class="letter" :style="{ animationDelay: `${i * 0.06}s` }">{{ ch }}</span>
        </h1>
      </div>

      <form class="form" @submit.prevent="handleLogin">
        <div class="flex-column">
          <label>用户名 / Username</label>
        </div>
        <div class="inputForm">
          <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" class="input-icon"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
          <input v-model="username" type="text" class="input" placeholder="Enter your username" required />
        </div>

        <div class="flex-column">
          <label>密码 / Password</label>
        </div>
        <div class="inputForm">
          <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" class="input-icon"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
          <input v-model="password" type="password" class="input" placeholder="Enter your password" required />
        </div>

        <div class="flex-row">
          <span class="span" @click="$router.push('/register')">没有账号？去注册</span>
        </div>

        <button class="button-submit" type="submit" :disabled="loading">
          {{ loading ? '登录中...' : '登 录' }}
        </button>

        <p class="error-msg" v-if="errorMessage">{{ errorMessage }}</p>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useUserStore } from '@/stores/auth.js';
import { useRouter } from 'vue-router';

const username = ref('');
const password = ref('');
const userStore = useUserStore();
const router = useRouter();
const loading = ref(false);
const errorMessage = ref('');
const hasIcon = ref(true);

const handleLogin = async () => {
  loading.value = true;
  errorMessage.value = '';
  try {
    await userStore.login(username.value, password.value);
    router.push('/');
  } catch (error) {
    errorMessage.value = error.response?.data?.detail || error.message || '登录失败';
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.login-wrapper {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #111;
  padding: 20px;
}

.form-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 30px;
}

.logo-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
}

.main-icon {
  width: 60px;
  height: 60px;
  filter: drop-shadow(0px 4px 8px rgba(192,57,43,0.4)) brightness(0) invert(1);
}

.logo-text {
  font-size: 36px;
  font-weight: 800;
  margin: 0;
  letter-spacing: 2px;
  display: flex;
}

.letter {
  display: inline-block;
  color: #fff;
  animation: letterFloat 0.6s cubic-bezier(0.22, 1, 0.36, 1) both;
  opacity: 0;
}

@keyframes letterFloat {
  from { opacity: 0; transform: translateY(24px); }
  to   { opacity: 1; transform: translateY(0); }
}

.form {
  display: flex;
  flex-direction: column;
  gap: 15px;
  background: linear-gradient(160deg, #c0392b 0%, #7b1a1a 40%, #1a1a1a 100%);
  padding: 40px;
  width: 450px;
  border-radius: 10px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif;
  box-shadow: 0 20px 60px rgba(192,57,43,0.3), 0 4px 20px rgba(0,0,0,0.5);
}

::placeholder {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif;
  color: #aaa;
}

.flex-column > label {
  color: rgba(255,255,255,0.85);
  font-weight: 600;
  font-size: 14px;
}

.inputForm {
  border: 1.5px solid rgba(255,255,255,0.15);
  border-radius: 6px;
  height: 50px;
  display: flex;
  align-items: center;
  padding-left: 15px;
  transition: 0.2s ease-in-out;
  background-color: rgba(255,255,255,0.08);
  margin-bottom: 10px;
}

.input-icon { color: rgba(255,255,255,0.5); }

.input {
  margin-left: 10px;
  border-radius: 6px;
  border: none;
  width: 100%;
  height: 100%;
  font-size: 15px;
  background: transparent;
  color: #fff;
}

.input:focus { outline: none; }

.inputForm:focus-within {
  border: 1.5px solid #e74c3c;
  background-color: rgba(255,255,255,0.12);
}

.flex-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 10px;
  justify-content: flex-end;
}

.span {
  font-size: 14px;
  color: rgba(255,255,255,0.7);
  font-weight: 500;
  cursor: pointer;
  transition: color 0.2s;
  text-decoration: underline;
}
.span:hover { color: #fff; }

.button-submit {
  position: relative;
  display: inline-block;
  padding: 15px 30px;
  text-align: center;
  letter-spacing: 2px;
  background: transparent;
  transition: ease-out 0.4s;
  border: 2px solid rgba(255,255,255,0.6);
  border-radius: 6px;
  box-shadow: inset 0 0 0 0 #fff;
  margin: 10px 0;
  color: white;
  font-size: 16px;
  font-weight: bold;
  height: 55px;
  width: 100%;
  cursor: pointer;
}

.button-submit:hover {
  color: #c0392b;
  box-shadow: inset 0 -100px 0 0 #fff;
}

.button-submit:active { transform: scale(0.98); }
.button-submit:disabled { opacity: 0.7; cursor: not-allowed; }

.error-msg {
  color: #ffcccc;
  text-align: center;
  font-size: 14px;
  margin: 0;
  font-weight: 500;
}
</style>

