<template>
  <section class="conversation-panel">
    <div ref="scrollWrapRef" class="message-scroll">
      <div v-if="showLanding && !messages.length" class="landing-stage">
        <p class="landing-mark">CloudCycle</p>
        <h1>云小圆</h1>
        <p class="landing-subtitle">一个既能直接聊天，也能进入自主推理循环的 Agent 中心。</p>
        <div class="landing-pills">
          <button class="landing-pill" :class="{ active: runMode === 'agent' }" type="button" @click="$emit('set-mode', 'agent')">
            Agent 模式
          </button>
          <button class="landing-pill" :class="{ active: runMode === 'chat' }" type="button" @click="$emit('set-mode', 'chat')">
            Chat 模式
          </button>
        </div>
      </div>

      <article
        v-for="message in messages"
        :key="message.id"
        class="message-row"
        :class="message.role"
      >
        <div v-if="message.role === 'assistant'" class="assistant-avatar">
          <span class="assistant-orb"></span>
        </div>

        <div class="message-card" :class="message.role">
          <div class="message-meta">
            <strong>{{ message.role === 'user' ? '你' : '云小圆' }}</strong>
            <span>
              {{
                message.traceStreaming
                  ? '思考中'
                  : message.streaming
                    ? '流式输出中'
                    : '已完成'
              }}
            </span>
          </div>

          <div v-if="message.files?.length" class="message-files">
            <span v-for="file in message.files" :key="file" class="file-chip">{{ file }}</span>
          </div>

          <div
            v-if="message.role === 'assistant' && (message.traceEntries?.length || message.traceStreaming)"
            class="thinking-shell"
            :class="{ streaming: message.traceStreaming }"
          >
            <button class="thinking-toggle" type="button" @click="$emit('toggle-trace', message.id)">
              <div>
                <span>思考过程与工具调用</span>
                <small>{{ message.traceEntries?.length || 0 }} 条{{ message.traceStreaming ? '，正在更新' : '' }}</small>
              </div>
              <strong>{{ message.traceExpanded || message.traceStreaming ? '收起' : '展开' }}</strong>
            </button>

            <transition name="trace-reveal">
              <div v-if="message.traceExpanded || message.traceStreaming" class="thinking-body">
                <TransitionGroup name="trace-item-fade" tag="div" class="thinking-list">
                  <article
                    v-for="trace in message.traceEntries || []"
                    :key="trace.id"
                    class="thinking-item"
                    :class="trace.kind"
                  >
                    <div class="thinking-item-meta">
                      <span>{{ trace.kind === 'thought' ? '思考' : trace.title }}</span>
                      <small>{{ trace.time }}</small>
                    </div>
                    <p>{{ trace.title }}</p>
                    <p v-if="trace.input" class="trace-io"><strong>输入：</strong>{{ trace.input }}</p>
                    <p v-if="trace.output" class="trace-io"><strong>输出：</strong>{{ trace.output }}</p>
                  </article>
                </TransitionGroup>
              </div>
            </transition>
          </div>

          <div
            v-if="message.role === 'assistant'"
            class="markdown-body message-content markdown-content"
            v-html="renderMarkdown(message.content)"
          ></div>
          <div v-else class="message-content">{{ message.content }}</div>
        </div>
      </article>
    </div>

    <div class="composer-panel" :class="{ landing: showLanding && !messages.length }">
      <div v-if="pendingFiles.length" class="pending-files">
        <div v-for="file in pendingFiles" :key="file.name" class="pending-chip">
          <span>{{ file.name }}</span>
          <button type="button" @click="$emit('remove-file', file.name)">移除</button>
        </div>
      </div>

      <div class="composer-shell">
        <textarea
          :value="inputText"
          rows="2"
          class="composer-input"
          placeholder="给云小圆一句明确指令，或直接上传材料。Enter 发送，Shift + Enter 换行。"
          @input="$emit('update:inputText', $event.target.value)"
          @keydown="onKeydown"
        ></textarea>

        <div class="composer-actions">
          <button class="secondary-btn" type="button" @click="$emit('pick-file')">
            上传文件
          </button>
          <button class="primary-btn" type="button" :disabled="!canSend || loading" @click="$emit('send')">
            {{ loading ? '处理中' : '发送' }}
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { nextTick, ref, watch } from 'vue';
import MarkdownIt from 'markdown-it';
import 'github-markdown-css/github-markdown-light.css';

const props = defineProps({
  messages: { type: Array, default: () => [] },
  pendingFiles: { type: Array, default: () => [] },
  inputText: { type: String, default: '' },
  loading: { type: Boolean, default: false },
  canSend: { type: Boolean, default: false },
  showLanding: { type: Boolean, default: false },
  runMode: { type: String, default: 'agent' },
});

const emit = defineEmits(['update:inputText', 'send', 'pick-file', 'remove-file', 'toggle-trace', 'set-mode']);

const markdown = new MarkdownIt({ linkify: true, breaks: true });
const scrollWrapRef = ref(null);

const renderMarkdown = (text) => markdown.render(text || '');

const scrollToBottom = () => {
  if (!scrollWrapRef.value) return;
  scrollWrapRef.value.scrollTo({
    top: scrollWrapRef.value.scrollHeight,
    behavior: 'smooth',
  });
};

const onKeydown = (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    emit('send');
  }
};

watch(
  () => [props.messages.length, props.loading, props.messages.at(-1)?.content, props.messages.at(-1)?.traceEntries?.length],
  async () => {
    await nextTick();
    scrollToBottom();
  },
  { deep: true }
);
</script>

<style scoped>
.conversation-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  border-radius: 34px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.8), rgba(255, 255, 255, 0.68)),
    linear-gradient(150deg, rgba(119, 172, 255, 0.1), rgba(255, 255, 255, 0));
  border: 1px solid rgba(255, 255, 255, 0.62);
  box-shadow:
    0 28px 56px rgba(17, 41, 83, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.78);
  backdrop-filter: blur(20px);
  overflow: hidden;
  transition:
    background 0.45s ease,
    border-color 0.45s ease,
    box-shadow 0.45s ease;
}

.conversation-panel,
.conversation-panel * {
  transition-property: background, background-color, border-color, color, box-shadow, opacity, filter;
  transition-duration: 0.45s;
  transition-timing-function: ease;
}

.message-scroll {
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding: 24px 24px 12px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.landing-stage {
  margin: auto;
  padding: 24px;
  text-align: center;
  transform: translateY(-4%);
  animation: landingRise 0.9s cubic-bezier(0.22, 1, 0.36, 1);
}

.landing-mark,
.landing-subtitle {
  margin: 0;
}

.landing-mark {
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: rgba(17, 39, 76, 0.46);
}

.landing-stage h1 {
  margin: 18px 0 12px;
  font-size: clamp(46px, 6vw, 74px);
  line-height: 1;
  letter-spacing: -0.05em;
  color: #10213f;
}

.landing-subtitle {
  max-width: 680px;
  font-size: 16px;
  line-height: 1.9;
  color: rgba(16, 33, 63, 0.66);
}

.landing-pills {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 22px;
}

.landing-pill {
  border: none;
  padding: 10px 14px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.62);
  color: rgba(16, 33, 63, 0.6);
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}

.landing-pill.active {
  background:
    linear-gradient(135deg, rgba(76, 132, 255, 0.16), rgba(47, 211, 193, 0.16)),
    rgba(255, 255, 255, 0.78);
  color: #15305a;
}

.message-row {
  display: flex;
  gap: 14px;
}

.message-row.user {
  justify-content: flex-end;
}

.assistant-avatar {
  flex-shrink: 0;
  width: 34px;
  display: flex;
  align-items: flex-start;
  justify-content: center;
}

.assistant-orb {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background:
    radial-gradient(circle at 30% 30%, rgba(255, 255, 255, 0.96), rgba(255, 255, 255, 0.2) 24%, transparent 28%),
    linear-gradient(160deg, #6ca7ff, #47d6cb 58%, #ffb88b);
  box-shadow: 0 10px 24px rgba(58, 113, 212, 0.26);
}

.message-card {
  max-width: min(80%, 920px);
  padding: 16px 18px;
  border-radius: 24px;
}

.message-card.assistant {
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(255, 255, 255, 0.68);
  color: #11274c;
  box-shadow: 0 20px 34px rgba(17, 41, 83, 0.08);
}

.message-card.user {
  background:
    linear-gradient(135deg, rgba(85, 136, 255, 0.96), rgba(53, 209, 191, 0.92)),
    linear-gradient(180deg, rgba(255, 255, 255, 0.16), rgba(255, 255, 255, 0));
  color: #ffffff;
  box-shadow: 0 22px 40px rgba(51, 114, 220, 0.22);
}

.message-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
  font-size: 11px;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.message-meta strong {
  font-size: 12px;
}

.message-meta span {
  opacity: 0.66;
}

.message-files {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
}

.file-chip {
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 11px;
  color: inherit;
  background: rgba(17, 39, 76, 0.08);
}

.message-card.user .file-chip {
  background: rgba(255, 255, 255, 0.18);
}

.thinking-shell {
  margin-bottom: 12px;
  border-radius: 18px;
  overflow: hidden;
  background:
    linear-gradient(180deg, rgba(17, 39, 76, 0.05), rgba(17, 39, 76, 0.02)),
    rgba(255, 255, 255, 0.62);
  border: 1px solid rgba(17, 39, 76, 0.06);
}

.thinking-shell.streaming {
  box-shadow: 0 20px 34px rgba(53, 114, 220, 0.08);
}

.thinking-toggle {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 16px;
  border: none;
  background: transparent;
  color: inherit;
  cursor: pointer;
}

.thinking-toggle span,
.thinking-toggle small,
.thinking-toggle strong {
  display: block;
}

.thinking-toggle span {
  font-size: 13px;
  font-weight: 700;
  text-align: left;
}

.thinking-toggle small {
  margin-top: 4px;
  font-size: 11px;
  color: rgba(17, 39, 76, 0.52);
  text-align: left;
}

.thinking-toggle strong {
  font-size: 12px;
  color: rgba(17, 39, 76, 0.62);
}

.thinking-body {
  padding: 0 16px 16px;
}

.thinking-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.thinking-item {
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.58);
  border: 1px solid rgba(17, 39, 76, 0.05);
}

.thinking-item-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.thinking-item-meta span {
  font-size: 12px;
  font-weight: 700;
}

.thinking-item-meta small {
  font-size: 11px;
  color: rgba(17, 39, 76, 0.48);
}

.thinking-item p {
  margin: 8px 0 0;
  font-size: 12px;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-word;
}

.trace-io strong {
  font-weight: 700;
}

.message-content {
  font-size: 15px;
  line-height: 1.85;
  white-space: pre-wrap;
  word-break: break-word;
}

.markdown-content :deep(*) {
  color: inherit;
}

.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3) {
  margin-top: 0.2em;
  margin-bottom: 0.45em;
}

.markdown-content :deep(p),
.markdown-content :deep(ul),
.markdown-content :deep(ol),
.markdown-content :deep(blockquote) {
  margin-top: 0.35em;
  margin-bottom: 0.35em;
}

.composer-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 22px 22px;
}

.composer-panel.landing {
  padding-top: 12px;
}

.pending-files {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 12px;
  width: min(40vw, 760px);
  max-width: 100%;
}

.pending-chip {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.62);
  color: #15315c;
  font-size: 12px;
}

.pending-chip button {
  border: none;
  background: transparent;
  color: rgba(21, 49, 92, 0.64);
  cursor: pointer;
}

.composer-shell {
  position: relative;
  width: min(40vw, 760px);
  max-width: 100%;
  padding: 10px 12px 8px;
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.76);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.72),
    0 22px 44px rgba(16, 33, 63, 0.08);
  overflow: visible;
}

.composer-shell::before,
.composer-shell::after {
  content: '';
  position: absolute;
  border-radius: inherit;
  pointer-events: none;
  transition:
    opacity 0.4s ease,
    box-shadow 0.4s ease,
    filter 0.4s ease,
    transform 0.4s ease;
}

.composer-shell::before {
  inset: -4px;
  border: 1px solid rgba(101, 145, 240, 0.26);
  box-shadow:
    0 0 0 1px rgba(96, 208, 195, 0.12),
    0 0 18px rgba(89, 137, 255, 0.12),
    0 0 30px rgba(69, 210, 192, 0.08);
  opacity: 0.88;
  z-index: 0;
}

.composer-shell::after {
  inset: -16px;
  background:
    radial-gradient(circle at 18% 50%, rgba(95, 147, 255, 0.16), transparent 36%),
    radial-gradient(circle at 82% 50%, rgba(60, 214, 195, 0.14), transparent 32%);
  filter: blur(18px);
  animation: composerGlowPulse 5.2s ease-in-out infinite;
  opacity: 0.78;
  z-index: -1;
}

.composer-shell:focus-within::before {
  border-color: rgba(101, 145, 240, 0.38);
  box-shadow:
    0 0 0 1px rgba(96, 208, 195, 0.2),
    0 0 24px rgba(89, 137, 255, 0.16),
    0 0 38px rgba(69, 210, 192, 0.12);
}

.composer-shell:focus-within::after {
  opacity: 0.96;
  filter: blur(20px);
}

.composer-input {
  width: 100%;
  border: none;
  resize: none;
  background: transparent;
  color: #10213f;
  font-size: 15px;
  line-height: 1.65;
  min-height: 68px;
  outline: none;
  position: relative;
  z-index: 1;
}

.composer-input::placeholder {
  color: rgba(16, 33, 63, 0.42);
}

.composer-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 8px;
  position: relative;
  z-index: 1;
}

.secondary-btn,
.primary-btn {
  border: none;
  border-radius: 999px;
  padding: 12px 18px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 700;
}

.secondary-btn {
  background: rgba(17, 39, 76, 0.06);
  color: #173159;
}

.primary-btn {
  background: linear-gradient(135deg, #4d85ff, #32d2c3);
  color: #ffffff;
  box-shadow: 0 18px 32px rgba(53, 114, 220, 0.24);
}

.primary-btn:disabled {
  cursor: not-allowed;
  opacity: 0.58;
  box-shadow: none;
}

.trace-reveal-enter-active,
.trace-reveal-leave-active {
  transition: all 0.38s cubic-bezier(0.22, 1, 0.36, 1);
}

.trace-reveal-enter-from,
.trace-reveal-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

.trace-item-fade-enter-active,
.trace-item-fade-leave-active {
  transition: all 0.34s cubic-bezier(0.22, 1, 0.36, 1);
}

.trace-item-fade-enter-from,
.trace-item-fade-leave-to {
  opacity: 0;
  transform: translateY(8px) scale(0.98);
}

.trace-item-fade-move {
  transition: transform 0.34s cubic-bezier(0.22, 1, 0.36, 1);
}

@keyframes landingRise {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(-8%);
  }
}

@keyframes composerGlowPulse {
  0%, 100% {
    opacity: 0.64;
    transform: scale(0.995);
  }
  50% {
    opacity: 0.9;
    transform: scale(1.015);
  }
}

@media (max-width: 820px) {
  .message-card {
    max-width: 100%;
  }

  .message-scroll,
  .composer-panel {
    padding-left: 14px;
    padding-right: 14px;
  }

  .composer-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .pending-files,
  .composer-shell {
    width: 100%;
  }
}

:global([data-theme='dark']) .conversation-panel {
  background:
    linear-gradient(180deg, rgba(11, 18, 35, 0.84), rgba(11, 18, 35, 0.74)),
    linear-gradient(150deg, rgba(70, 126, 255, 0.16), rgba(255, 255, 255, 0));
  border-color: rgba(255, 255, 255, 0.08);
  box-shadow:
    0 28px 66px rgba(0, 0, 0, 0.36),
    inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

:global([data-theme='dark']) .landing-stage h1,
:global([data-theme='dark']) .message-card.assistant,
:global([data-theme='dark']) .pending-chip,
:global([data-theme='dark']) .composer-input,
:global([data-theme='dark']) .secondary-btn,
:global([data-theme='dark']) .thinking-shell,
:global([data-theme='dark']) .thinking-item {
  color: #edf4ff;
}

:global([data-theme='dark']) .landing-mark,
:global([data-theme='dark']) .landing-subtitle,
:global([data-theme='dark']) .thinking-toggle small,
:global([data-theme='dark']) .thinking-toggle strong,
:global([data-theme='dark']) .thinking-item-meta small,
:global([data-theme='dark']) .composer-input::placeholder,
:global([data-theme='dark']) .pending-chip button {
  color: rgba(237, 244, 255, 0.64);
}

:global([data-theme='dark']) .landing-pill,
:global([data-theme='dark']) .message-card.assistant,
:global([data-theme='dark']) .pending-chip,
:global([data-theme='dark']) .composer-shell,
:global([data-theme='dark']) .thinking-shell,
:global([data-theme='dark']) .thinking-item,
:global([data-theme='dark']) .secondary-btn {
  background: rgba(255, 255, 255, 0.06);
}

:global([data-theme='dark']) .landing-pill.active {
  background:
    linear-gradient(135deg, rgba(64, 117, 255, 0.24), rgba(41, 187, 173, 0.18)),
    rgba(255, 255, 255, 0.08);
}

:global([data-theme='dark']) .composer-shell::before {
  border-color: rgba(118, 156, 255, 0.3);
  box-shadow:
    0 0 0 1px rgba(73, 204, 188, 0.14),
    0 0 22px rgba(90, 135, 255, 0.18),
    0 0 36px rgba(73, 204, 188, 0.12);
}

:global([data-theme='dark']) .composer-shell::after {
  background:
    radial-gradient(circle at 18% 50%, rgba(95, 147, 255, 0.18), transparent 36%),
    radial-gradient(circle at 82% 50%, rgba(60, 214, 195, 0.16), transparent 32%);
}
</style>
