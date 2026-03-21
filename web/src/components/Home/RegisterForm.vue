<template>
  <form class="form" @submit.prevent="handleRegister">
    <div class="flex-column">
      <label>用户名 / Username</label>
    </div>
    <div class="inputForm">
      <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" class="input-icon"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
      <input v-model="username" type="text" class="input" placeholder="Enter your username" required />
    </div>

    <div class="flex-column">
      <label>邮箱 / Email</label>
    </div>
    <div class="inputForm">
      <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" class="input-icon"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path><polyline points="22,6 12,13 2,6"></polyline></svg>
      <input v-model="email" type="email" class="input" placeholder="Enter your email" required />
    </div>

    <div class="flex-column">
      <label>密码 / Password</label>
    </div>
    <div class="inputForm">
      <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" class="input-icon"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
      <input v-model="password" type="password" class="input" placeholder="Enter your password" required />
    </div>

    <div class="flex-column">
      <label>确认密码 / Confirm Password</label>
    </div>
    <div class="inputForm">
      <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" class="input-icon"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
      <input v-model="confirmPassword" type="password" class="input" placeholder="Confirm your password" required />
    </div>

    <div class="flex-row">
      <span class="span" @click="$emit('switch-to-login')">已有账号？去登录</span>
    </div>

    <button class="button-submit" type="submit" :disabled="loading">
      {{ loading ? '注册中...' : '注 册' }}
    </button>

    <p class="error-msg" v-if="errorMessage">{{ errorMessage }}</p>
  </form>
</template>

<script setup>
import { ref } from 'vue';
import { register, verifyEmail } from '@/api/user';
import { useUserStore } from '@/stores/auth.js';

const emit = defineEmits(['success', 'switch-to-login']);

const username = ref('');
const email = ref('');
const password = ref('');
const confirmPassword = ref('');
const errorMessage = ref('');
const loading = ref(false);
const userStore = useUserStore();

const askForCode = (previewCode) => {
  const prefix = previewCode ? `当前为本地预览模式，验证码：${previewCode}\n` : '';
  return window.prompt(`${prefix}请输入邮箱收到的验证码`);
};

const handleRegister = async () => {
  if (password.value !== confirmPassword.value) {
    errorMessage.value = '两次输入的密码不一致';
    return;
  }

  loading.value = true;
  errorMessage.value = '';
  try {
    const registerRes = await register({
      uname: username.value,
      email: email.value,
      pwd: password.value,
    });

    const code = askForCode(registerRes.data.preview_code);
    if (!code) {
      errorMessage.value = '注册成功，但尚未完成邮箱验证';
      return;
    }

    await verifyEmail(email.value, code.trim());
    await userStore.login(username.value, password.value);
    emit('success');
  } catch (error) {
    errorMessage.value = error.response?.data?.detail || 'Registration failed';
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.form {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 400px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen,
    Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif;
  background: transparent;
  padding: 0 40px 30px 40px;
}

::placeholder {
  color: #a5a5a5;
}

.flex-column > label {
  color: #f1f1f1;
  font-weight: 600;
  font-size: 13px;
}

.inputForm {
  border: 1.5px solid #a85c5c;
  border-radius: 10em;
  height: 45px;
  display: flex;
  align-items: center;
  padding-left: 15px;
  transition: 0.2s ease-in-out;
  background-color: #f6f6f6;
  margin-bottom: 5px;
}

.input-icon {
  color: #a85c5c;
}

.input {
  margin-left: 10px;
  border-radius: 10rem;
  border: none;
  width: 100%;
  height: 100%;
  font-size: 14px;
  background: transparent;
  color: #2f2f2f;
}

.input:focus {
  outline: none;
}

.inputForm:focus-within {
  border: 1.5px solid #e14b4b;
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
  margin-left: 5px;
  color: #f2d3d3;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.2s;
  text-decoration: underline;
}

.span:hover {
  opacity: 0.8;
}

.button-submit {
  position: relative;
  display: inline-block;
  padding: 12px 30px;
  text-align: center;
  letter-spacing: 2px;
  text-decoration: none;
  background: transparent;
  transition: ease-out 0.5s;
  border: 2px solid #f0b0b0;
  border-radius: 10em;
  box-shadow: inset 0 0 0 0 #f0b0b0;
  margin: 10px 0;
  color: #f6eaea;
  font-size: 16px;
  font-weight: bold;
  height: 50px;
  width: 100%;
  cursor: pointer;
}

.button-submit:hover {
  color: #3a1a1a;
  box-shadow: inset 0 -100px 0 0 #f0b0b0;
}

.button-submit:active {
  transform: scale(0.95);
}

.button-submit:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.error-msg {
  color: #ffb3b3;
  text-align: center;
  font-size: 13px;
  margin: 0;
  font-weight: 500;
}
</style>
