<template>
  <Modal :isOpen="isOpen" @close="emit('close')">
    <form class="security-card" @submit.prevent="handleSubmit">
      <div class="header-row">
        <div>
          <p class="eyebrow">{{ modeConfig.eyebrow }}</p>
          <h3 class="title">{{ modeConfig.title }}</h3>
          <p class="subtitle">{{ modeConfig.subtitle }}</p>
        </div>
        <button type="button" class="close-btn" @click="emit('close')">关闭</button>
      </div>

      <template v-if="requiresTarget">
        <div class="field-group">
          <label class="field-label">{{ modeConfig.targetLabel }}</label>
          <div class="input-row">
            <input
              v-model="target"
              :type="mode === 'bind-email' ? 'email' : 'text'"
              class="field-input"
              :placeholder="modeConfig.targetPlaceholder"
            />
          </div>
        </div>

        <div class="field-group">
          <label class="field-label">图形验证码</label>
          <div class="inline-row">
            <div class="input-row input-row--grow">
              <input
                v-model="captchaAnswer"
                type="text"
                class="field-input"
                maxlength="4"
                placeholder="输入右侧验证码"
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
        </div>

        <div class="field-group">
          <label class="field-label">验证码</label>
          <div class="inline-row">
            <div class="input-row input-row--grow">
              <input
                v-model="code"
                type="text"
                class="field-input"
                maxlength="6"
                placeholder="输入收到的验证码"
              />
            </div>
            <button type="button" class="secondary-btn" :disabled="!canSendCode" @click="handleSendCode">
              {{ sendingCode ? '发送中...' : '发送验证码' }}
            </button>
          </div>
        </div>
      </template>

      <template v-if="mode === 'set-password'">
        <div class="field-group">
          <label class="field-label">新密码</label>
          <div class="input-row">
            <input v-model="newPassword" type="password" class="field-input" placeholder="至少 6 位密码" />
          </div>
        </div>
        <div class="field-group">
          <label class="field-label">确认新密码</label>
          <div class="input-row">
            <input v-model="confirmPassword" type="password" class="field-input" placeholder="再次输入新密码" />
          </div>
        </div>
      </template>

      <template v-else-if="mode === 'change-password'">
        <div class="field-group">
          <label class="field-label">当前密码</label>
          <div class="input-row">
            <input v-model="currentPassword" type="password" class="field-input" placeholder="输入当前密码" />
          </div>
        </div>
        <div class="field-group">
          <label class="field-label">新密码</label>
          <div class="input-row">
            <input v-model="newPassword" type="password" class="field-input" placeholder="至少 6 位密码" />
          </div>
        </div>
        <div class="field-group">
          <label class="field-label">确认新密码</label>
          <div class="input-row">
            <input v-model="confirmPassword" type="password" class="field-input" placeholder="再次输入新密码" />
          </div>
        </div>
      </template>

      <p v-if="previewCode" class="preview-box">沙箱验证码：<strong>{{ previewCode }}</strong></p>
      <p v-if="statusMessage" class="status-box">{{ statusMessage }}</p>
      <p v-if="errorMessage" class="error-box">{{ errorMessage }}</p>

      <div class="actions">
        <button type="button" class="ghost-btn" @click="emit('close')">取消</button>
        <button type="submit" class="primary-btn" :disabled="submitting || captchaLoading">
          {{ submitting ? '提交中...' : modeConfig.submitLabel }}
        </button>
      </div>
    </form>
  </Modal>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import Modal from '@/components/common/Modal.vue';
import {
  bindEmail,
  bindPhone,
  changePassword,
  getCaptcha,
  sendEmailCode,
  sendPhoneCode,
  setPassword,
} from '@/api/user';
import { useUserStore } from '@/stores/auth.js';

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false,
  },
  mode: {
    type: String,
    required: true,
  },
});

const emit = defineEmits(['close', 'updated']);
const userStore = useUserStore();

const target = ref('');
const code = ref('');
const captchaId = ref('');
const captchaSvg = ref('');
const captchaAnswer = ref('');
const currentPassword = ref('');
const newPassword = ref('');
const confirmPassword = ref('');

const previewCode = ref('');
const statusMessage = ref('');
const errorMessage = ref('');

const captchaLoading = ref(false);
const sendingCode = ref(false);
const submitting = ref(false);

const modeConfig = computed(() => {
  switch (props.mode) {
    case 'bind-phone':
      return {
        eyebrow: '手机号绑定',
        title: userStore.user?.login_phone ? '更换登录手机号' : '绑定登录手机号',
        subtitle: '绑定后可用于手机号 + 密码登录，也可用于找回密码。',
        targetLabel: '手机号',
        targetPlaceholder: '请输入 11 位手机号',
        submitLabel: userStore.user?.login_phone ? '更新手机号' : '绑定手机号',
      };
    case 'bind-email':
      return {
        eyebrow: '邮箱绑定',
        title: userStore.user?.email ? '更换邮箱' : '绑定邮箱',
        subtitle: '绑定并验证后，可用邮箱完成找回密码和密码登录。',
        targetLabel: '邮箱',
        targetPlaceholder: '请输入邮箱地址',
        submitLabel: userStore.user?.email ? '更新邮箱' : '绑定邮箱',
      };
    case 'set-password':
      return {
        eyebrow: '密码设置',
        title: '设置登录密码',
        subtitle: '给当前账号补充密码，后续即可使用手机号、邮箱或用户名密码登录。',
        submitLabel: '设置密码',
      };
    default:
      return {
        eyebrow: '密码修改',
        title: '修改登录密码',
        subtitle: '修改后，新密码会立即生效。',
        submitLabel: '修改密码',
      };
  }
});

const requiresTarget = computed(() => ['bind-phone', 'bind-email'].includes(props.mode));
const canSendCode = computed(() => (
  requiresTarget.value
  && !sendingCode.value
  && !captchaLoading.value
  && target.value.trim()
  && captchaAnswer.value.trim()
));

const resetState = () => {
  target.value = props.mode === 'bind-phone'
    ? (userStore.user?.login_phone || '')
    : props.mode === 'bind-email'
      ? (userStore.user?.email || '')
      : '';
  code.value = '';
  captchaId.value = '';
  captchaSvg.value = '';
  captchaAnswer.value = '';
  currentPassword.value = '';
  newPassword.value = '';
  confirmPassword.value = '';
  previewCode.value = '';
  statusMessage.value = '';
  errorMessage.value = '';
};

const refreshCaptcha = async () => {
  if (!requiresTarget.value) return;
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

const handleSendCode = async () => {
  sendingCode.value = true;
  errorMessage.value = '';
  statusMessage.value = '';
  try {
    if (props.mode === 'bind-phone') {
      const { data } = await sendPhoneCode({
        phone: target.value,
        purpose: 'bind_phone',
        captcha_id: captchaId.value,
        captcha_answer: captchaAnswer.value,
      });
      previewCode.value = data.preview_code || '';
    } else {
      const { data } = await sendEmailCode({
        email: target.value,
        purpose: 'bind_email',
        captcha_id: captchaId.value,
        captcha_answer: captchaAnswer.value,
      });
      previewCode.value = data.preview_code || '';
    }
    statusMessage.value = '验证码已发送，请继续完成绑定。';
  } catch (error) {
    errorMessage.value = error.response?.data?.detail || '验证码发送失败';
  } finally {
    sendingCode.value = false;
  }
};

const handleSubmit = async () => {
  submitting.value = true;
  errorMessage.value = '';
  try {
    if (props.mode === 'bind-phone') {
      await bindPhone({ phone: target.value, code: code.value });
    } else if (props.mode === 'bind-email') {
      await bindEmail({ email: target.value, code: code.value });
    } else if (props.mode === 'set-password') {
      await setPassword({
        new_password: newPassword.value,
        confirm_password: confirmPassword.value,
      });
    } else {
      await changePassword({
        current_password: currentPassword.value,
        new_password: newPassword.value,
        confirm_password: confirmPassword.value,
      });
    }
    await userStore.fetchUser();
    emit('updated');
    emit('close');
  } catch (error) {
    errorMessage.value = error.response?.data?.detail || '操作失败';
  } finally {
    submitting.value = false;
  }
};

watch(
  () => [props.isOpen, props.mode],
  async ([isOpen]) => {
    if (!isOpen) return;
    resetState();
    await refreshCaptcha();
  },
  { immediate: true },
);
</script>

<style scoped>
.security-card {
  width: min(92vw, 520px);
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 28px;
  border-radius: 28px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: linear-gradient(155deg, rgba(20, 12, 18, 0.98), rgba(81, 35, 52, 0.94) 42%, rgba(21, 35, 63, 0.94));
  box-shadow:
    0 28px 80px rgba(9, 19, 31, 0.46),
    0 0 0 1px rgba(255, 255, 255, 0.04) inset;
  color: #fff7f1;
}

.header-row {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}

.eyebrow {
  margin: 0 0 6px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.12em;
  color: rgba(255, 215, 207, 0.76);
  text-transform: uppercase;
}

.title {
  margin: 0;
  font-size: 28px;
  line-height: 1.1;
}

.subtitle {
  margin: 8px 0 0;
  color: rgba(255, 247, 245, 0.72);
  font-size: 13px;
  line-height: 1.7;
}

.close-btn,
.ghost-btn,
.secondary-btn,
.primary-btn,
.captcha-visual {
  border-radius: 16px;
  cursor: pointer;
  transition: transform 0.2s ease, border-color 0.2s ease, opacity 0.2s ease;
}

.close-btn,
.ghost-btn,
.secondary-btn,
.captcha-visual {
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 247, 245, 0.92);
}

.close-btn {
  min-height: 40px;
  padding: 0 14px;
}

.field-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field-label {
  font-size: 13px;
  font-weight: 700;
  color: rgba(255, 247, 245, 0.84);
}

.inline-row {
  display: flex;
  gap: 10px;
}

.input-row {
  min-height: 48px;
  border-radius: 16px;
  border: 1.5px solid rgba(255, 255, 255, 0.14);
  background: rgba(255, 255, 255, 0.05);
  display: flex;
  align-items: center;
  padding: 0 14px;
}

.input-row--grow {
  flex: 1;
}

.input-row:focus-within {
  border-color: rgba(95, 209, 255, 0.56);
  box-shadow: 0 0 0 4px rgba(95, 209, 255, 0.12);
}

.field-input {
  width: 100%;
  border: none;
  outline: none;
  background: transparent;
  color: #fff7f1;
  font-size: 14px;
}

.field-input::placeholder {
  color: rgba(245, 247, 255, 0.4);
}

.captcha-visual,
.secondary-btn {
  min-width: 132px;
  min-height: 48px;
  padding: 0 14px;
  font-weight: 700;
}

.captcha-visual {
  overflow: hidden;
}

.captcha-visual :deep(svg) {
  display: block;
  width: 100%;
  height: 100%;
}

.preview-box,
.status-box,
.error-box {
  margin: 0;
  padding: 10px 12px;
  border-radius: 14px;
  font-size: 13px;
  line-height: 1.5;
}

.preview-box {
  background: rgba(255, 219, 100, 0.12);
  border: 1px solid rgba(255, 219, 100, 0.28);
  color: #ffe7a0;
}

.status-box {
  background: rgba(128, 250, 176, 0.12);
  border: 1px solid rgba(128, 250, 176, 0.22);
  color: #c7fdd8;
}

.error-box {
  background: rgba(255, 143, 122, 0.12);
  border: 1px solid rgba(255, 143, 122, 0.24);
  color: #ffd7cf;
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 6px;
}

.ghost-btn,
.primary-btn {
  min-height: 46px;
  padding: 0 18px;
  font-size: 14px;
  font-weight: 800;
}

.primary-btn {
  border: none;
  color: #26111a;
  background: linear-gradient(135deg, #ff8f7a, #ffdb64 55%, #58cbff);
}

.close-btn:hover,
.ghost-btn:hover,
.secondary-btn:hover,
.primary-btn:hover,
.captcha-visual:hover {
  transform: translateY(-1px);
}

.primary-btn:disabled,
.secondary-btn:disabled,
.captcha-visual:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

@media (max-width: 640px) {
  .security-card {
    width: min(94vw, 520px);
    padding: 22px 18px;
    border-radius: 22px;
  }

  .header-row,
  .inline-row,
  .actions {
    flex-direction: column;
  }

  .close-btn,
  .ghost-btn,
  .secondary-btn,
  .primary-btn,
  .captcha-visual {
    width: 100%;
  }

  .title {
    font-size: 24px;
  }
}
</style>
