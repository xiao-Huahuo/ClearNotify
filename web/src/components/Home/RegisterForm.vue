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
      <p class="logo-subtitle">手机号注册优先，也保留邮箱密码注册</p>
    </div>

    <form class="form" @submit.prevent="handleRegister">
      <div class="auth-tabs">
        <button
          type="button"
          class="auth-tab"
          :class="{ active: mode === 'phone' }"
          @click="mode = 'phone'"
        >
          手机号注册
        </button>
        <button
          type="button"
          class="auth-tab"
          :class="{ active: mode === 'email' }"
          @click="mode = 'email'"
        >
          邮箱注册
        </button>
      </div>

      <template v-if="mode === 'phone'">
        <div class="flex-column">
          <label>用户名（可选）</label>
        </div>
        <div class="inputForm">
          <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" class="input-icon">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
            <circle cx="12" cy="7" r="4"></circle>
          </svg>
          <input v-model="phoneUsername" type="text" class="input" placeholder="不填将自动生成用户名" />
        </div>

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
          <label>登录密码（可选）</label>
        </div>
        <div class="inputForm">
          <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" class="input-icon">
            <rect x="3" y="11" width="18" height="11" rx="2"></rect>
            <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
          </svg>
          <input
            v-model="phonePassword"
            type="password"
            class="input"
            placeholder="留空则注册后建议尽快补设密码"
          />
        </div>
        <p class="tip-text">设置密码后，后续可直接用手机号或用户名 + 密码登录。</p>

        <div class="flex-column">
          <label>图形验证码</label>
        </div>
        <div class="captcha-row">
          <div class="inputForm inputForm--captcha">
            <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" class="input-icon">
              <rect x="3" y="4" width="18" height="16" rx="2"></rect>
              <path d="M7 8h10M7 12h4M7 16h8"></path>
            </svg>
            <input
              v-model="captchaAnswer"
              type="text"
              class="input"
              maxlength="4"
              placeholder="输入右侧验证码"
              required
            />
          </div>
          <button
            type="button"
            class="captcha-visual"
            :disabled="captchaLoading"
            @click="refreshCaptcha"
            v-html="captchaSvg"
          ></button>
        </div>

        <div class="flex-column">
          <label>短信验证码</label>
        </div>
        <div class="code-row">
          <div class="inputForm inputForm--code">
            <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" class="input-icon">
              <path d="M9 12l2 2 4-4"></path>
              <path d="M21 12c.552 0 1-.449.973-1A10 10 0 1 0 12 22c.551.027 1-.421 1-.973V18"></path>
            </svg>
            <input
              v-model="phoneCode"
              type="text"
              class="input"
              maxlength="6"
              placeholder="输入 6 位验证码"
              required
            />
          </div>
          <button
            type="button"
            class="send-code-btn"
            :disabled="!canSendPhoneCode"
            @click="handleSendPhoneCode"
          >
            {{ sendingPhoneCode ? '发送中...' : '发送验证码' }}
          </button>
        </div>
        <p class="tip-text">发送验证码后不会再强制刷新图形验证码。如需重发，可手动点击图片刷新。</p>
      </template>

      <template v-else>
        <div class="flex-column">
          <label>用户名</label>
        </div>
        <div class="inputForm">
          <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" class="input-icon">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
            <circle cx="12" cy="7" r="4"></circle>
          </svg>
          <input v-model="emailUsername" type="text" class="input" placeholder="请输入用户名" required />
        </div>

        <div class="flex-column">
          <label>邮箱</label>
        </div>
        <div class="inputForm">
          <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" class="input-icon">
            <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
            <polyline points="22,6 12,13 2,6"></polyline>
          </svg>
          <input v-model="email" type="email" class="input" placeholder="请输入邮箱地址" required />
        </div>

        <div class="flex-column">
          <label>密码</label>
        </div>
        <div class="inputForm">
          <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" class="input-icon">
            <rect x="3" y="11" width="18" height="11" rx="2"></rect>
            <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
          </svg>
          <input v-model="emailPassword" type="password" class="input" placeholder="至少 6 位密码" required />
        </div>

        <div class="flex-column">
          <label>确认密码</label>
        </div>
        <div class="inputForm">
          <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" class="input-icon">
            <rect x="3" y="11" width="18" height="11" rx="2"></rect>
            <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
          </svg>
          <input v-model="emailPasswordConfirm" type="password" class="input" placeholder="再次输入密码" required />
        </div>

        <div v-if="emailVerificationPending" class="verify-panel">
          <div class="flex-column">
            <label>邮箱验证码</label>
          </div>
          <div class="code-row">
            <div class="inputForm inputForm--code">
              <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" class="input-icon">
                <path d="M9 12l2 2 4-4"></path>
                <path d="M21 12c.552 0 1-.449.973-1A10 10 0 1 0 12 22c.551.027 1-.421 1-.973V18"></path>
              </svg>
              <input
                v-model="emailVerificationCode"
                type="text"
                class="input"
                maxlength="6"
                placeholder="输入邮箱收到的验证码"
              />
            </div>
            <button
              type="button"
              class="send-code-btn"
              :disabled="verifyingEmail"
              @click="handleVerifyEmail"
            >
              {{ verifyingEmail ? '验证中...' : '完成验证' }}
            </button>
          </div>
          <button
            type="button"
            class="text-action"
            :disabled="resendingEmailCode"
            @click="handleResendVerification"
          >
            {{ resendingEmailCode ? '重发中...' : '重发邮箱验证码' }}
          </button>
        </div>
      </template>

      <p v-if="statusMessage" class="status-msg">{{ statusMessage }}</p>
      <p v-if="previewCode" class="preview-box">沙箱验证码：<strong>{{ previewCode }}</strong></p>
      <p v-if="errorMessage" class="error-msg">{{ errorMessage }}</p>

      <div class="flex-row">
        <span class="span" @click="$emit('switch-to-login')">已有账号？去登录</span>
      </div>

      <div v-if="mode === 'phone'" class="action-stack">
        <button
          type="button"
          class="button-secondary"
          :disabled="!canOneClickRegister"
          @click="handleOneClickRegister"
        >
          {{ submitting ? '处理中...' : '手机号一键注册' }}
        </button>
        <button class="button-submit" type="submit" :disabled="submitting || captchaLoading">
          {{ submitting ? '提交中...' : '完成注册' }}
        </button>
        <p class="tip-text action-hint">一键注册会直接使用沙箱验证码完成注册并自动登录。若未设置密码，建议登录后立即到账户安全补设密码。</p>
      </div>
      <button v-else class="button-submit" type="submit" :disabled="submitting">
        {{ submitting ? '提交中...' : '注册' }}
      </button>
    </form>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import {
  getCaptcha,
  phoneRegister,
  register,
  resendVerification,
  sendPhoneCode,
  verifyEmail,
} from '@/api/user';
import { useUserStore } from '@/stores/auth.js';

const emit = defineEmits(['success', 'switch-to-login']);
const userStore = useUserStore();

const titleChars = '云析观策'.split('');
const hasIcon = ref(true);
const mode = ref('phone');

const phoneUsername = ref('');
const phone = ref('');
const phonePassword = ref('');
const phoneCode = ref('');

const emailUsername = ref('');
const email = ref('');
const emailPassword = ref('');
const emailPasswordConfirm = ref('');
const emailVerificationCode = ref('');
const registeredEmail = ref('');

const captchaId = ref('');
const captchaSvg = ref('');
const captchaAnswer = ref('');

const previewCode = ref('');
const statusMessage = ref('');
const errorMessage = ref('');

const emailVerificationPending = ref(false);
const submitting = ref(false);
const captchaLoading = ref(false);
const sendingPhoneCode = ref(false);
const verifyingEmail = ref(false);
const resendingEmailCode = ref(false);

const canSendPhoneCode = computed(() => (
  !sendingPhoneCode.value
  && !captchaLoading.value
  && !submitting.value
  && phone.value.trim()
  && captchaAnswer.value.trim()
));

const canOneClickRegister = computed(() => (
  mode.value === 'phone'
  && !sendingPhoneCode.value
  && !submitting.value
  && !captchaLoading.value
  && phone.value.trim()
  && captchaAnswer.value.trim()
));

const refreshCaptcha = async () => {
  captchaLoading.value = true;
  try {
    const { data } = await getCaptcha();
    captchaId.value = data.captcha_id;
    captchaSvg.value = data.svg;
    captchaAnswer.value = '';
  } catch (error) {
    errorMessage.value = error.response?.data?.detail || '图形验证码加载失败';
  } finally {
    captchaLoading.value = false;
  }
};

const clearMessages = () => {
  statusMessage.value = '';
  errorMessage.value = '';
  previewCode.value = '';
};

const buildPhoneRegisterPayload = (verificationCode = phoneCode.value) => ({
  uname: phoneUsername.value.trim() || undefined,
  phone: phone.value,
  code: verificationCode,
  pwd: phonePassword.value.trim() || undefined,
});

const performPhoneRegister = async (verificationCode = phoneCode.value) => {
  const { data } = await phoneRegister(buildPhoneRegisterPayload(verificationCode));
  await userStore.applyAccessToken(data.access_token);
  emit('success');
};

const handleSendPhoneCode = async () => {
  sendingPhoneCode.value = true;
  clearMessages();
  try {
    const { data } = await sendPhoneCode({
      phone: phone.value,
      purpose: 'register',
      captcha_id: captchaId.value,
      captcha_answer: captchaAnswer.value,
    });
    previewCode.value = data.preview_code || '';
    statusMessage.value = '验证码已发送，填写后即可完成注册。';
  } catch (error) {
    errorMessage.value = error.response?.data?.detail || '验证码发送失败';
  } finally {
    sendingPhoneCode.value = false;
  }
};

const handleOneClickRegister = async () => {
  submitting.value = true;
  clearMessages();
  try {
    const { data } = await sendPhoneCode({
      phone: phone.value,
      purpose: 'register',
      captcha_id: captchaId.value,
      captcha_answer: captchaAnswer.value,
    });
    if (!data.preview_code) {
      throw new Error('当前环境未开启沙箱短信预览，暂不支持一键注册');
    }
    previewCode.value = data.preview_code;
    phoneCode.value = data.preview_code;
    statusMessage.value = '验证码已自动获取，正在完成注册...';
    await performPhoneRegister(data.preview_code);
  } catch (error) {
    errorMessage.value = error.response?.data?.detail || error.message || '一键注册失败';
  } finally {
    submitting.value = false;
  }
};

const handleEmailRegister = async () => {
  if (emailPassword.value !== emailPasswordConfirm.value) {
    throw new Error('两次输入的密码不一致');
  }
  const { data } = await register({
    uname: emailUsername.value,
    email: email.value,
    pwd: emailPassword.value,
  });
  registeredEmail.value = email.value.trim();
  emailVerificationPending.value = true;
  previewCode.value = data.preview_code || '';
  statusMessage.value = '注册成功，请完成邮箱验证后再登录。';
};

const handleVerifyEmail = async () => {
  verifyingEmail.value = true;
  errorMessage.value = '';
  try {
    await verifyEmail(registeredEmail.value, emailVerificationCode.value);
    statusMessage.value = '邮箱验证成功，正在返回登录页。';
    emailVerificationPending.value = false;
    window.setTimeout(() => emit('switch-to-login'), 700);
  } catch (error) {
    errorMessage.value = error.response?.data?.detail || '邮箱验证失败';
  } finally {
    verifyingEmail.value = false;
  }
};

const handleResendVerification = async () => {
  resendingEmailCode.value = true;
  errorMessage.value = '';
  try {
    const { data } = await resendVerification(registeredEmail.value);
    previewCode.value = data.preview_code || '';
    statusMessage.value = data.message || '验证码已重新发送';
  } catch (error) {
    errorMessage.value = error.response?.data?.detail || '验证码重发失败';
  } finally {
    resendingEmailCode.value = false;
  }
};

const handleRegister = async () => {
  submitting.value = true;
  errorMessage.value = '';
  statusMessage.value = '';
  try {
    if (mode.value === 'phone') {
      await performPhoneRegister();
    } else {
      await handleEmailRegister();
    }
  } catch (error) {
    errorMessage.value = error.response?.data?.detail || error.message || '注册失败';
  } finally {
    submitting.value = false;
  }
};

watch(mode, async () => {
  clearMessages();
  if (mode.value === 'phone') {
    await refreshCaptcha();
  }
});

onMounted(() => {
  refreshCaptcha();
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
  grid-template-columns: repeat(2, minmax(0, 1fr));
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

.inputForm--captcha,
.inputForm--code {
  flex: 1;
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
  margin: -2px 0 2px;
  font-size: 12px;
  color: rgba(255, 247, 245, 0.64);
}

.captcha-row,
.code-row {
  display: flex;
  gap: 10px;
}

.captcha-visual,
.send-code-btn,
.text-action,
.button-secondary {
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.05);
  color: rgba(255, 247, 245, 0.86);
  cursor: pointer;
  min-height: 48px;
  transition: border-color 0.2s ease, transform 0.2s ease;
}

.captcha-visual {
  width: 138px;
  overflow: hidden;
}

.captcha-visual :deep(svg) {
  display: block;
  width: 100%;
  height: 100%;
}

.send-code-btn {
  min-width: 118px;
  padding: 0 14px;
  font-weight: 700;
}

.send-code-btn:hover,
.captcha-visual:hover,
.text-action:hover,
.button-secondary:hover {
  border-color: rgba(95, 209, 255, 0.3);
  transform: translateY(-1px);
}

.verify-panel {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.text-action {
  align-self: flex-start;
  min-height: 36px;
  padding: 0 14px;
  border-radius: 999px;
}

.preview-box,
.status-msg,
.error-msg {
  border-radius: 14px;
  padding: 10px 12px;
  font-size: 13px;
  line-height: 1.5;
  margin: 0;
}

.preview-box {
  background: rgba(255, 219, 100, 0.12);
  border: 1px solid rgba(255, 219, 100, 0.28);
  color: #ffe7a0;
}

.status-msg {
  background: rgba(128, 250, 176, 0.12);
  border: 1px solid rgba(128, 250, 176, 0.22);
  color: #c7fdd8;
}

.error-msg {
  background: rgba(255, 143, 122, 0.12);
  border: 1px solid rgba(255, 143, 122, 0.24);
  color: #ffd7cf;
}

.flex-row {
  display: flex;
  justify-content: flex-end;
}

.span {
  color: var(--auth-coral);
  font-size: 13px;
  cursor: pointer;
}

.action-stack {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.action-hint {
  margin: 0;
}

.button-secondary {
  min-height: 46px;
  font-weight: 700;
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

.button-submit:disabled,
.button-secondary:disabled,
.send-code-btn:disabled,
.captcha-visual:disabled,
.text-action:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

@media (max-width: 560px) {
  .form {
    padding: 28px 20px;
  }

  .captcha-row,
  .code-row {
    flex-direction: column;
  }

  .captcha-visual,
  .send-code-btn {
    width: 100%;
  }
}
</style>
