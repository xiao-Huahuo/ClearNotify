<template>
  <div class="form-container">
    <div class="logo-area">
      <img
        v-if="hasIcon"
        src="@/assets/photos/main-icon.png"
        alt="icon"
        class="main-icon"
        @error="hasIcon = false"
      />
      <h1 class="logo-text">
        <span
          v-for="(ch, index) in titleChars"
          :key="`${ch}-${index}`"
          class="letter"
          :style="{ animationDelay: `${index * 0.06}s` }"
        >
          {{ ch }}
        </span>
      </h1>
      <p class="logo-subtitle">支持手机号 + 密码、手机号一键登录，以及邮箱 / 用户名 + 密码登录</p>
    </div>

    <form class="form" @submit.prevent="handleLogin">
      <div class="auth-tabs">
        <button
          type="button"
          class="auth-tab"
          :class="{ active: mode === 'phone' }"
          @click="mode = 'phone'"
        >
          手机号登录
        </button>
        <button
          type="button"
          class="auth-tab"
          :class="{ active: mode === 'quick' }"
          @click="mode = 'quick'"
        >
          手机号一键登录
        </button>
        <button
          type="button"
          class="auth-tab"
          :class="{ active: mode === 'identity' }"
          @click="mode = 'identity'"
        >
          邮箱 / 用户名
        </button>
      </div>

      <template v-if="mode === 'phone'">
        <div class="flex-column">
          <label>手机号</label>
        </div>
        <div class="inputForm">
          <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" class="input-icon">
            <rect x="7" y="2" width="10" height="20" rx="2"></rect>
            <line x1="11" y1="18" x2="13" y2="18"></line>
          </svg>
          <input v-model="phone" type="text" class="input" placeholder="请输入 11 位手机号" required />
        </div>

        <div class="flex-column">
          <label>密码</label>
        </div>
        <div class="inputForm">
          <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" class="input-icon">
            <rect x="3" y="11" width="18" height="11" rx="2"></rect>
            <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
          </svg>
          <input v-model="phonePassword" type="password" class="input" placeholder="请输入登录密码" required />
        </div>
        <p class="tip-text">如果你是一键注册后还没设置密码，请用“忘记密码”通过已绑定手机号补设密码。</p>
      </template>

      <template v-else-if="mode === 'quick'">
        <div class="flex-column">
          <label>手机号</label>
        </div>
        <div class="inputForm">
          <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" class="input-icon">
            <rect x="7" y="2" width="10" height="20" rx="2"></rect>
            <line x1="11" y1="18" x2="13" y2="18"></line>
          </svg>
          <input v-model="phone" type="text" class="input" placeholder="请输入 11 位手机号" required />
        </div>
        <p class="tip-text">沙箱模式下会自动获取并填写验证码，你只需要输入手机号即可完成登录。</p>
      </template>

      <template v-else>
        <div class="flex-column">
          <label>邮箱 / 用户名</label>
        </div>
        <div class="inputForm">
          <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" class="input-icon">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
            <circle cx="12" cy="7" r="4"></circle>
          </svg>
          <input
            v-model="identity"
            type="text"
            class="input"
            placeholder="请输入邮箱或用户名"
            required
          />
        </div>

        <div class="flex-column">
          <label>密码</label>
        </div>
        <div class="inputForm">
          <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" class="input-icon">
            <rect x="3" y="11" width="18" height="11" rx="2"></rect>
            <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
          </svg>
          <input v-model="password" type="password" class="input" placeholder="请输入密码" required />
        </div>
        <p class="tip-text">手机号账号请切换到“手机号登录”，邮箱和用户名在这里登录。</p>
      </template>

      <p v-if="statusMessage" class="status-msg">{{ statusMessage }}</p>
      <p v-if="errorMessage" class="error-msg">{{ errorMessage }}</p>

      <div class="flex-row">
        <span class="span" @click="$emit('switch-to-register')">没有账号？去注册</span>
        <span class="span span-muted" @click="$emit('switch-to-recover')">忘记密码</span>
      </div>

      <button class="button-submit" type="submit" :disabled="loading">
        {{ loading ? '登录中...' : submitText }}
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';
import { sendPhoneCode } from '@/api/user';
import { useUserStore } from '@/stores/auth.js';

const emit = defineEmits(['success', 'switch-to-register', 'switch-to-recover']);
const userStore = useUserStore();

const titleChars = '云析观策'.split('');
const hasIcon = ref(true);

const mode = ref('phone');
const phone = ref('');
const phonePassword = ref('');
const identity = ref('');
const password = ref('');

const statusMessage = ref('');
const errorMessage = ref('');

const loading = ref(false);
const submitText = ref('登录');

const handleQuickLogin = async () => {
  const { data } = await sendPhoneCode({
    phone: phone.value,
    purpose: 'login',
  });
  if (!data.preview_code) {
    throw new Error('当前环境未开启沙箱短信预览，暂不支持手机号一键登录');
  }
  statusMessage.value = '沙箱验证码已自动获取，正在登录...';
  await userStore.loginWithPhone(phone.value, data.preview_code);
};

const handleLogin = async () => {
  loading.value = true;
  statusMessage.value = '';
  errorMessage.value = '';
  try {
    if (mode.value === 'phone') {
      await userStore.loginWithPassword(phone.value, phonePassword.value);
    } else if (mode.value === 'quick') {
      await handleQuickLogin();
    } else {
      await userStore.loginWithPassword(identity.value, password.value);
    }
    emit('success');
  } catch (error) {
    errorMessage.value = error.response?.data?.detail || '登录失败';
  } finally {
    loading.value = false;
  }
};

watch(mode, (value) => {
  statusMessage.value = '';
  errorMessage.value = '';
  if (value === 'phone') {
    submitText.value = '登录';
    identity.value = '';
    password.value = '';
    return;
  }
  if (value === 'quick') {
    submitText.value = '一键登录';
    identity.value = '';
    password.value = '';
    return;
  }
  submitText.value = '登录';
  phonePassword.value = '';
});
</script>

<style scoped>
.form-container {
  --auth-wine-deep: #140c12;
  --auth-wine-mid: #512334;
  --auth-sky-deep: #15233f;
  --auth-night: #09131f;
  --auth-coral: #ff8f7a;
  --auth-coral-soft: #ffd7cf;
  --auth-gold: #ffdb64;
  --auth-sky: #58cbff;
  --auth-sky-soft: #5fd1ff;
  --auth-mint: #80fab0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  width: min(100%, 470px);
}

.logo-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.main-icon {
  width: 64px;
  height: 64px;
  object-fit: contain;
}

.logo-text {
  font-size: 36px;
  font-weight: 800;
  margin: 0;
  letter-spacing: 2px;
  display: flex;
  text-shadow:
    0 8px 24px rgba(255, 143, 122, 0.18),
    0 0 20px rgba(88, 203, 255, 0.12);
}

.letter {
  display: inline-block;
  color: #fff7f1;
  animation: letterFloat 0.6s cubic-bezier(0.22, 1, 0.36, 1) both;
  opacity: 0;
}

.logo-subtitle {
  margin: 0;
  color: rgba(255, 247, 245, 0.74);
  font-size: 13px;
  text-align: center;
}

@keyframes letterFloat {
  from {
    opacity: 0;
    transform: translateY(24px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.form {
  position: relative;
  isolation: isolate;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: 13px;
  background: linear-gradient(
    160deg,
    rgba(20, 12, 18, 0.96) 0%,
    rgba(81, 35, 52, 0.92) 34%,
    rgba(21, 35, 63, 0.92) 72%,
    rgba(9, 19, 31, 0.97) 100%
  );
  padding: 34px;
  width: 100%;
  border-radius: 28px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(22px);
  box-shadow:
    0 28px 80px rgba(9, 19, 31, 0.46),
    0 0 0 1px rgba(255, 255, 255, 0.04) inset,
    0 0 42px rgba(255, 143, 122, 0.12);
}

.auth-tabs {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  padding: 4px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.05);
  margin-bottom: 2px;
}

.auth-tab {
  border: none;
  background: transparent;
  color: rgba(255, 247, 245, 0.7);
  min-height: 40px;
  border-radius: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: background-color 0.2s ease, color 0.2s ease;
}

.auth-tab.active {
  background: rgba(255, 143, 122, 0.16);
  color: #fffaf6;
  box-shadow: inset 0 0 0 1px rgba(255, 143, 122, 0.2);
}

.flex-column > label {
  color: rgba(255, 247, 245, 0.86);
  font-weight: 600;
  font-size: 13px;
}

.inputForm {
  border: 1.5px solid rgba(255, 255, 255, 0.12);
  border-radius: 16px;
  min-height: 48px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 14px;
  background: rgba(255, 255, 255, 0.04);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.inputForm:focus-within {
  border-color: rgba(95, 209, 255, 0.56);
  box-shadow: 0 0 0 4px rgba(95, 209, 255, 0.12);
}

.input-icon {
  color: rgba(255, 255, 255, 0.72);
  flex-shrink: 0;
}

.input {
  border: none;
  outline: none;
  background: transparent;
  width: 100%;
  color: #fff7f1;
  font-size: 14px;
}

.input::placeholder {
  color: rgba(245, 247, 255, 0.44);
}

.tip-text {
  margin: -2px 0 0;
  color: rgba(255, 247, 245, 0.62);
  font-size: 12px;
  line-height: 1.6;
}

.status-msg,
.error-msg {
  border-radius: 14px;
  padding: 10px 12px;
  font-size: 13px;
  line-height: 1.5;
  margin: 0;
}

.status-msg {
  background: rgba(128, 250, 176, 0.12);
  border: 1px solid rgba(128, 250, 176, 0.24);
  color: #d2ffe2;
}

.error-msg {
  background: rgba(255, 143, 122, 0.12);
  border: 1px solid rgba(255, 143, 122, 0.24);
  color: #ffd7cf;
}

.flex-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.span {
  color: var(--auth-coral);
  font-size: 13px;
  cursor: pointer;
}

.span-muted {
  color: rgba(255, 247, 245, 0.7);
}

.button-submit {
  border: none;
  border-radius: 18px;
  min-height: 48px;
  background: linear-gradient(135deg, var(--auth-coral) 0%, #ffb76f 100%);
  color: #26111a;
  font-weight: 800;
  font-size: 15px;
  cursor: pointer;
}

.button-submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

@media (max-width: 560px) {
  .form {
    padding: 28px 20px;
  }

  .flex-row {
    flex-direction: column;
  }
}
</style>
