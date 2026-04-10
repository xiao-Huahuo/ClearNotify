<template>
  <section class="conversation-panel" :class="{ pristine: isPristine }">
    <div ref="scrollWrapRef" class="message-scroll" :class="{ pristine: isPristine, docked: !isPristine }">
      <div v-if="isPristine" class="landing-stage">
        <p class="landing-mark">CloudCycle</p>
        <h1>CloudCycle</h1>
        <p class="landing-subtitle">一个专注于直接对话与自主智能体推理的入口。</p>

        <div class="landing-pills">
          <button class="landing-pill" :class="{ active: runMode === 'agent' }" type="button" @click="$emit('set-mode', 'agent')">
            智能体模式
          </button>
          <button class="landing-pill" :class="{ active: runMode === 'chat' }" type="button" @click="$emit('set-mode', 'chat')">
            对话模式
          </button>
        </div>

        <div v-if="pendingFiles.length" class="pending-files landing-pending-files">
          <div v-for="file in pendingFiles" :key="file.name" class="pending-chip">
            <span>{{ file.name }}</span>
            <button type="button" @click="$emit('remove-file', file.name)">移除</button>
          </div>
        </div>

        <div class="composer-panel landing-panel">
          <div class="composer-shell">
            <textarea
              :value="inputText"
              rows="2"
              class="composer-input"
              placeholder="给 CloudCycle 一个明确任务，或上传材料。按 Enter 发送，Shift + Enter 换行。"
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
      </div>

      <article
        v-for="message in messages"
        :key="message.id"
        class="message-row"
        :class="message.role"
      >
        <button
          v-if="message.role === 'assistant'"
          class="assistant-avatar"
          type="button"
          @click="$emit('open-sidebar')"
        >
          <span class="assistant-orb">
            <span class="assistant-orb-core"></span>
            <span class="assistant-orb-ring assistant-orb-ring-one"></span>
            <span class="assistant-orb-ring assistant-orb-ring-two"></span>
            <span class="assistant-orb-glow"></span>
          </span>
        </button>

        <div class="message-card" :class="message.role">
          <div class="message-meta">
            <strong>{{ message.role === 'user' ? '你' : 'CloudCycle' }}</strong>
            <span>{{ getMessageStateText(message) }}</span>
          </div>

          <div v-if="message.files?.length" class="message-files">
            <span v-for="file in message.files" :key="file" class="file-chip">{{ file }}</span>
          </div>

          <div
            v-if="message.role === 'assistant' && showAgentTrace(message)"
            class="live-trace-stage"
          >
            <div class="thinking-loader">
              <ThinkingLoader />
            </div>

              <article
                v-if="getVisibleTrace(message)"
                class="thinking-item live"
                :class="getVisibleTrace(message).kind"
              >
                <div class="thinking-item-meta">
                  <span>{{ getVisibleTrace(message).kind === 'thought' ? '思考中' : getVisibleTrace(message).title }}</span>
                  <small>{{ getVisibleTrace(message).time }}</small>
                </div>
                <p>{{ getVisibleTrace(message).title }}</p>
                <p v-if="getVisibleTrace(message).input" class="trace-io"><strong>输入：</strong> {{ getVisibleTrace(message).input }}</p>
                <p v-if="getVisibleTrace(message).output" class="trace-io"><strong>输出：</strong> {{ getVisibleTrace(message).output }}</p>
              </article>

              <article v-else class="thinking-item live placeholder">
                <div class="thinking-item-meta">
                  <span>思考中...</span>
                  <small>CloudCycle 智能体</small>
                </div>
                <p>正在规划下一步并准备调用工具。</p>
              </article>
          </div>

          <div
            v-else-if="message.role === 'assistant' && showMessageLoader(message)"
            class="message-loading-state"
          >
            <div class="thinking-loader compact">
              <ThinkingLoader />
            </div>
            <span>正在生成回复...</span>
          </div>

          <div
            v-if="message.role === 'assistant' && message.content"
            class="markdown-body markdown-content"
            v-html="renderMarkdown(message.content)"
          ></div>
          <div v-else-if="message.role === 'user'" class="message-content plain-content">{{ message.content }}</div>
        </div>
      </article>
    </div>

    <div v-if="!isPristine" class="composer-panel docked" :class="{ 'from-landing': dockFromLanding }">
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
          placeholder="给 CloudCycle 一个明确任务，或上传材料。按 Enter 发送，Shift + Enter 换行。"
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
import { computed, nextTick, ref, watch } from 'vue';
import MarkdownIt from 'markdown-it';
import ThinkingLoader from '../../../super-comonents/loader.vue';

const props = defineProps({
  messages: { type: Array, default: () => [] },
  pendingFiles: { type: Array, default: () => [] },
  inputText: { type: String, default: '' },
  loading: { type: Boolean, default: false },
  canSend: { type: Boolean, default: false },
  showLanding: { type: Boolean, default: false },
  dockFromLanding: { type: Boolean, default: false },
  runMode: { type: String, default: 'agent' },
});

const emit = defineEmits(['update:inputText', 'send', 'pick-file', 'remove-file', 'set-mode', 'open-sidebar']);

const markdown = new MarkdownIt({ linkify: true });
const scrollWrapRef = ref(null);

const isPristine = computed(() => props.showLanding && !props.messages.length);

const renderMarkdown = (text) => markdown.render(text || '');

const isCurrentAssistantMessage = (message) => (
  message.role === 'assistant' && props.messages.at(-1)?.id === message.id
);

const getVisibleTrace = (message) => {
  const traceEntries = message.traceEntries || [];
  return traceEntries.length ? traceEntries[traceEntries.length - 1] : null;
};

const showAgentTrace = (message) => (
  props.runMode === 'agent' && isCurrentAssistantMessage(message) && message.traceStreaming
);

const showMessageLoader = (message) => (
  isCurrentAssistantMessage(message) && props.loading && !message.content && !showAgentTrace(message)
);

const getMessageStateText = (message) => {
  if (message.role === 'user') return '已发送';
  if (showAgentTrace(message)) return '思考中';
  if (showMessageLoader(message)) return '生成中';
  if (message.streaming) return '输出中';
  return '已完成';
};

const scrollToBottom = () => {
  if (!scrollWrapRef.value || isPristine.value) return;
  scrollWrapRef.value.scrollTo({
    top: scrollWrapRef.value.scrollHeight,
    behavior: props.loading ? 'auto' : 'smooth',
  });
};

const onKeydown = (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    emit('send');
  }
};

watch(
  () => [
    props.messages.length,
    props.loading,
    props.messages.at(-1)?.content,
    props.messages.at(-1)?.traceEntries?.length,
    props.pendingFiles.length,
    isPristine.value,
  ],
  async () => {
    await nextTick();
    scrollToBottom();
  },
  { deep: true }
);
</script>

<style scoped>
@property --composer-glow-angle {
  syntax: '<angle>';
  inherits: false;
  initial-value: 0deg;
}

.conversation-panel {
  position: relative;
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
  transition-property: background, background-color, border-color, color, box-shadow, opacity, filter, transform;
  transition-duration: 0.45s;
  transition-timing-function: ease;
}

.live-trace-stage,
.live-trace-stage * {
  transition: none;
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

.message-scroll.docked {
  padding-bottom: 212px;
}

.message-scroll.pristine {
  justify-content: center;
  padding-bottom: 24px;
}

.landing-stage {
  width: min(880px, 100%);
  margin: 0 auto;
  padding: 28px 16px;
  text-align: center;
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
  margin-left: auto;
  margin-right: auto;
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
  align-items: flex-start;
  gap: 14px;
}

.message-row.user {
  justify-content: flex-end;
}

.assistant-avatar {
  appearance: none;
  flex-shrink: 0;
  width: 40px;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 4px 0 0;
  border: none;
  background: transparent;
  cursor: pointer;
  outline: none;
}

.assistant-avatar:focus-visible {
  border-radius: 999px;
  box-shadow: 0 0 0 2px rgba(88, 203, 255, 0.24);
}

.assistant-avatar:hover .assistant-orb-core,
.assistant-avatar:focus-visible .assistant-orb-core {
  filter: saturate(1.08) brightness(1.04);
}

.assistant-orb {
  position: relative;
  display: block;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  animation: assistantOrbFloat 4.6s ease-in-out infinite, assistantOrbDrift 9.8s ease-in-out infinite;
}

.assistant-orb-core,
.assistant-orb-ring,
.assistant-orb-glow {
  position: absolute;
  border-radius: 50%;
}

.assistant-orb-core {
  inset: 0;
  background:
    radial-gradient(circle at 30% 24%, rgba(255, 255, 255, 0.96), rgba(255, 255, 255, 0.2) 18%, transparent 26%),
    radial-gradient(circle at 72% 74%, rgba(255, 205, 138, 0.44), transparent 34%),
    conic-gradient(from 210deg, #ff8f7a 0deg, #ffb76f 120deg, #58cbff 248deg, #80fab0 360deg);
  box-shadow:
    inset -6px -8px 12px rgba(0, 0, 0, 0.14),
    inset 4px 4px 10px rgba(255, 255, 255, 0.28),
    0 8px 24px rgba(255, 143, 122, 0.28),
    0 0 22px rgba(88, 203, 255, 0.18);
  transform-origin: center;
  animation: assistantOrbCoreFlux 6.2s cubic-bezier(0.37, 0, 0.2, 1) infinite;
}

.assistant-orb-ring {
  border: 1px solid rgba(255, 255, 255, 0.42);
}

.assistant-orb-ring-one {
  inset: -3px;
  opacity: 0.48;
  animation: assistantOrbSpin 7.4s linear infinite, assistantOrbRingPulse 4.8s ease-in-out infinite;
}

.assistant-orb-ring-two {
  inset: -7px;
  opacity: 0.2;
  animation: assistantOrbSpinReverse 10.4s linear infinite, assistantOrbRingPulse 6.2s ease-in-out infinite reverse;
}

.assistant-orb-glow {
  inset: -14px;
  background:
    radial-gradient(circle, rgba(255, 143, 122, 0.2), transparent 52%),
    radial-gradient(circle at 70% 40%, rgba(88, 203, 255, 0.18), transparent 44%);
  filter: blur(10px);
  z-index: -1;
  animation: assistantOrbGlowPulse 4.9s ease-in-out infinite;
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

.live-trace-stage {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 12px;
}

.thinking-loader {
  --loader-color: #ff8f7a;
  position: relative;
  width: 40px;
  height: 32px;
  flex-shrink: 0;
  border-radius: 16px;
  background: rgba(255, 143, 122, 0.12);
  border: 1px solid rgba(255, 143, 122, 0.18);
}

.thinking-loader.compact {
  width: 44px;
  height: 32px;
}

.thinking-item {
  padding: 12px 14px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.58);
  border: 1px solid rgba(17, 39, 76, 0.05);
}

.thinking-item.live {
  flex: 1;
  min-width: 0;
}

.thinking-item.thought {
  background: rgba(255, 143, 122, 0.12);
  border-color: rgba(255, 143, 122, 0.28);
}

.thinking-item.tool {
  background: rgba(88, 203, 255, 0.12);
  border-color: rgba(88, 203, 255, 0.24);
}

.thinking-item.placeholder {
  background: rgba(255, 255, 255, 0.56);
  border-style: dashed;
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

.message-loading-state {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  padding: 10px 12px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.62);
  border: 1px solid rgba(17, 39, 76, 0.06);
  color: rgba(17, 39, 76, 0.72);
  font-size: 12px;
  font-weight: 600;
}

.message-content {
  word-break: break-word;
}

.plain-content {
  font-size: 15px;
  line-height: 1.78;
  white-space: pre-wrap;
}

.markdown-content {
  margin: 0;
  padding: 0;
  background: transparent !important;
  background-color: transparent !important;
  color: inherit !important;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.68;
  white-space: normal;
  word-break: break-word;
  overflow-wrap: anywhere;
}

.markdown-content :deep(*) {
  color: inherit;
  box-sizing: border-box;
}

.markdown-content :deep(a) {
  color: #2b69d1;
  text-decoration: underline;
  text-underline-offset: 0.18em;
}

.markdown-content :deep(strong) {
  font-weight: 700;
}

.markdown-content :deep(img) {
  display: block;
  max-width: 100%;
  border-radius: 14px;
}

.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3) {
  margin-top: 0.4em;
  margin-bottom: 0.38em;
  line-height: 1.28;
}

.markdown-content :deep(p),
.markdown-content :deep(ul),
.markdown-content :deep(ol),
.markdown-content :deep(blockquote) {
  margin-top: 0.42em;
  margin-bottom: 0.42em;
  line-height: 1.62;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  padding-left: 1.35em;
}

.markdown-content :deep(li) {
  margin: 0.2em 0;
}

.markdown-content :deep(pre) {
  margin: 0.75em 0;
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(17, 39, 76, 0.06);
  overflow: auto;
}

.markdown-content :deep(pre code) {
  display: block;
  white-space: pre;
}

.markdown-content :deep(code) {
  padding: 0.14em 0.38em;
  border-radius: 8px;
  background: rgba(17, 39, 76, 0.08);
  font-size: 0.92em;
}

.markdown-content :deep(blockquote) {
  padding: 0.08em 0 0.08em 0.95em;
  border-left: 3px solid rgba(17, 39, 76, 0.14);
  color: rgba(17, 39, 76, 0.78);
}

.markdown-content :deep(table) {
  width: 100%;
  margin: 0.8em 0;
  border-collapse: collapse;
  border-spacing: 0;
  font-size: 13px;
}

.markdown-content :deep(th),
.markdown-content :deep(td) {
  padding: 10px 12px;
  border: 1px solid rgba(17, 39, 76, 0.1);
  text-align: left;
  vertical-align: top;
}

.markdown-content :deep(th) {
  font-weight: 700;
  background: rgba(17, 39, 76, 0.05);
}

.markdown-content :deep(tr:nth-child(2n)) {
  background: rgba(17, 39, 76, 0.03);
}

.markdown-content :deep(hr) {
  margin: 1em 0;
  border: none;
  border-top: 1px solid rgba(17, 39, 76, 0.1);
}

.markdown-content :deep(mark) {
  padding: 0.08em 0.28em;
  border-radius: 6px;
  background: rgba(255, 194, 142, 0.34);
}

.composer-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.composer-panel.landing-panel {
  width: min(48vw, 820px);
  max-width: 100%;
  margin: 24px auto 0;
}

.composer-panel.docked {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 4;
  padding: 0 22px 34px;
  transform-origin: center top;
  background: transparent;
}

.composer-panel.docked .composer-shell::after {
  content: none;
}

.composer-panel.docked.from-landing {
  animation: composerDockIn 0.72s cubic-bezier(0.22, 1, 0.36, 1);
}

.pending-files {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 12px;
  width: min(40vw, 760px);
  max-width: 100%;
}

.landing-pending-files {
  width: min(48vw, 820px);
  justify-content: center;
  margin: 24px auto 12px;
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
  --composer-glow-angle: 0deg;
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

.composer-panel.landing-panel .composer-shell {
  width: 100%;
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
  padding: 1px;
  background:
    conic-gradient(
      from var(--composer-glow-angle),
      rgba(101, 145, 240, 0.68),
      rgba(96, 208, 195, 0.62),
      rgba(255, 194, 142, 0.44),
      rgba(101, 145, 240, 0.68)
    );
  -webkit-mask:
    linear-gradient(#fff 0 0) content-box,
    linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask:
    linear-gradient(#fff 0 0) content-box,
    linear-gradient(#fff 0 0);
  mask-composite: exclude;
  box-shadow:
    0 0 0 1px rgba(96, 208, 195, 0.12),
    0 0 18px rgba(89, 137, 255, 0.12),
    0 0 30px rgba(69, 210, 192, 0.08);
  opacity: 0.88;
  animation: composerGlowAngleShift 7.2s linear infinite;
  z-index: 0;
}

.composer-shell::after {
  inset: -46vh -24vw -52vh;
  background:
    radial-gradient(circle at 18% 50%, rgba(95, 147, 255, 0.16), transparent 34%),
    radial-gradient(circle at 82% 50%, rgba(60, 214, 195, 0.14), transparent 30%),
    radial-gradient(circle at 50% 72%, rgba(255, 194, 142, 0.12), transparent 38%);
  filter: blur(34px);
  transform: scale(1.04);
  animation: composerGlowPulse 6.2s ease-in-out infinite;
  opacity: 0.34;
  z-index: -1;
}

.composer-shell:focus-within::before {
  box-shadow:
    0 0 0 1px rgba(96, 208, 195, 0.2),
    0 0 24px rgba(89, 137, 255, 0.16),
    0 0 38px rgba(69, 210, 192, 0.12);
}

.composer-shell:focus-within::after {
  opacity: 0.44;
  filter: blur(40px);
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

@keyframes landingRise {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes composerDockIn {
  from {
    opacity: 0.22;
    transform: translateY(-28vh) scale(0.985);
  }
  68% {
    opacity: 1;
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes composerGlowPulse {
  0%, 100% {
    opacity: 0.26;
    transform: scale(1.02);
  }
  50% {
    opacity: 0.42;
    transform: scale(1.18);
  }
}

@keyframes composerGlowAngleShift {
  from {
    --composer-glow-angle: 0deg;
  }
  to {
    --composer-glow-angle: 360deg;
  }
}

@keyframes assistantOrbFloat {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-3px);
  }
}

@keyframes assistantOrbDrift {
  0%, 100% {
    filter: saturate(1) brightness(1);
  }
  35% {
    filter: saturate(1.08) brightness(1.04);
  }
  68% {
    filter: saturate(1.16) brightness(1.08);
  }
}

@keyframes assistantOrbCoreFlux {
  0%, 100% {
    transform: scale(1) rotate(0deg);
    filter: saturate(1) brightness(1);
  }
  28% {
    transform: scale(0.96) rotate(-9deg);
    filter: saturate(1.08) brightness(1.02);
  }
  54% {
    transform: scale(1.06) rotate(8deg);
    filter: saturate(1.14) brightness(1.08);
  }
  78% {
    transform: scale(0.98) rotate(-6deg);
    filter: saturate(1.1) brightness(1.04);
  }
}

@keyframes assistantOrbSpin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@keyframes assistantOrbSpinReverse {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(-360deg);
  }
}

@keyframes assistantOrbRingPulse {
  0%, 100% {
    opacity: 0.2;
  }
  50% {
    opacity: 0.5;
  }
}

@keyframes assistantOrbGlowPulse {
  0%, 100% {
    opacity: 0.44;
    transform: scale(0.98);
  }
  50% {
    opacity: 0.78;
    transform: scale(1.12);
  }
}

@media (max-width: 820px) {
  .message-card {
    max-width: 100%;
  }

  .message-scroll,
  .composer-panel.docked {
    padding-left: 14px;
    padding-right: 14px;
  }

  .message-scroll.docked {
    padding-bottom: 252px;
  }

  .landing-stage {
    padding-left: 0;
    padding-right: 0;
  }

  .composer-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .pending-files,
  .landing-pending-files,
  .composer-shell,
  .composer-panel.landing-panel {
    width: 100%;
  }

  .live-trace-stage {
    flex-direction: column;
    align-items: stretch;
  }

  .thinking-loader {
    width: 100%;
    height: 32px;
  }

  .composer-shell::after {
    inset: -34vh -16vw -40vh;
  }
}

</style>

<style>
[data-theme='dark'] .conversation-panel {
  background:
    linear-gradient(180deg, rgba(6, 9, 14, 0.97), rgba(8, 11, 16, 0.94)),
    linear-gradient(150deg, rgba(52, 88, 156, 0.1), rgba(24, 107, 97, 0.04) 58%, rgba(255, 255, 255, 0));
  border-color: rgba(118, 156, 255, 0.12);
  box-shadow:
    0 28px 66px rgba(0, 0, 0, 0.42),
    inset 0 1px 0 rgba(255, 255, 255, 0.03);
}

[data-theme='dark'] .conversation-panel .message-scroll {
  background: transparent;
}

[data-theme='dark'] .conversation-panel .landing-stage h1,
[data-theme='dark'] .conversation-panel .message-card.assistant,
[data-theme='dark'] .conversation-panel .pending-chip,
[data-theme='dark'] .conversation-panel .composer-input,
[data-theme='dark'] .conversation-panel .secondary-btn,
[data-theme='dark'] .conversation-panel .thinking-item,
[data-theme='dark'] .conversation-panel .message-loading-state {
  color: #edf4ff;
}

[data-theme='dark'] .conversation-panel .landing-mark,
[data-theme='dark'] .conversation-panel .landing-subtitle,
[data-theme='dark'] .conversation-panel .thinking-item-meta small,
[data-theme='dark'] .conversation-panel .composer-input::placeholder,
[data-theme='dark'] .conversation-panel .pending-chip button {
  color: rgba(237, 244, 255, 0.64);
}

[data-theme='dark'] .conversation-panel .landing-subtitle {
  color: rgba(237, 244, 255, 0.7);
}

[data-theme='dark'] .conversation-panel .landing-pill,
[data-theme='dark'] .conversation-panel .pending-chip,
[data-theme='dark'] .conversation-panel .composer-shell,
[data-theme='dark'] .conversation-panel .secondary-btn,
[data-theme='dark'] .conversation-panel .thinking-item.placeholder,
[data-theme='dark'] .conversation-panel .message-loading-state {
  background:
    linear-gradient(180deg, rgba(15, 25, 43, 0.92), rgba(12, 20, 34, 0.84)),
    linear-gradient(150deg, rgba(63, 118, 255, 0.08), rgba(40, 188, 172, 0.05));
  border-color: rgba(118, 156, 255, 0.12);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
}

[data-theme='dark'] .conversation-panel .message-card.assistant {
  background:
    linear-gradient(180deg, rgba(17, 19, 24, 0.98), rgba(11, 13, 18, 0.96)),
    linear-gradient(145deg, rgba(67, 97, 150, 0.05), rgba(20, 87, 80, 0.025));
  border-color: rgba(255, 255, 255, 0.05);
  box-shadow:
    0 18px 32px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.025);
}

[data-theme='dark'] .conversation-panel .message-card.user {
  background:
    linear-gradient(180deg, rgba(24, 28, 36, 0.98), rgba(18, 22, 29, 0.96)),
    linear-gradient(145deg, rgba(64, 117, 255, 0.09), rgba(41, 187, 173, 0.05));
  border: 1px solid rgba(118, 156, 255, 0.12);
  box-shadow: 0 20px 34px rgba(0, 0, 0, 0.24);
}

[data-theme='dark'] .conversation-panel .landing-pill.active {
  background:
    linear-gradient(135deg, rgba(64, 117, 255, 0.28), rgba(41, 187, 173, 0.2)),
    rgba(255, 255, 255, 0.04);
}

[data-theme='dark'] .conversation-panel .thinking-item.thought {
  background: rgba(255, 143, 122, 0.1);
  border-color: rgba(255, 143, 122, 0.18);
}

[data-theme='dark'] .conversation-panel .thinking-item.tool {
  background: rgba(88, 203, 255, 0.1);
  border-color: rgba(88, 203, 255, 0.18);
}

[data-theme='dark'] .conversation-panel .thinking-loader {
  background: rgba(255, 143, 122, 0.08);
  border-color: rgba(255, 143, 122, 0.14);
}

[data-theme='dark'] .conversation-panel .message-card.assistant .markdown-body.markdown-content {
  background: transparent !important;
  background-color: transparent !important;
  background-image: none !important;
  color: #edf4ff !important;
  color-scheme: dark !important;
}

[data-theme='dark'] .conversation-panel .message-card.assistant .markdown-body.markdown-content,
[data-theme='dark'] .conversation-panel .message-card.assistant .markdown-body.markdown-content p,
[data-theme='dark'] .conversation-panel .message-card.assistant .markdown-body.markdown-content li,
[data-theme='dark'] .conversation-panel .message-card.assistant .markdown-body.markdown-content strong,
[data-theme='dark'] .conversation-panel .message-card.assistant .markdown-body.markdown-content em,
[data-theme='dark'] .conversation-panel .message-card.assistant .markdown-body.markdown-content span,
[data-theme='dark'] .conversation-panel .message-card.assistant .markdown-body.markdown-content h1,
[data-theme='dark'] .conversation-panel .message-card.assistant .markdown-body.markdown-content h2,
[data-theme='dark'] .conversation-panel .message-card.assistant .markdown-body.markdown-content h3,
[data-theme='dark'] .conversation-panel .message-card.assistant .markdown-body.markdown-content h4,
[data-theme='dark'] .conversation-panel .message-card.assistant .markdown-body.markdown-content h5,
[data-theme='dark'] .conversation-panel .message-card.assistant .markdown-body.markdown-content h6 {
  color: inherit !important;
}

[data-theme='dark'] .conversation-panel .message-card.assistant .markdown-body.markdown-content a {
  color: #8cd9ff !important;
}

[data-theme='dark'] .conversation-panel .message-card.assistant .markdown-body.markdown-content code {
  background: rgba(255, 255, 255, 0.08) !important;
}

[data-theme='dark'] .conversation-panel .message-card.assistant .markdown-body.markdown-content pre {
  background: rgba(4, 10, 20, 0.9) !important;
  border: 1px solid rgba(118, 156, 255, 0.08) !important;
}

[data-theme='dark'] .conversation-panel .message-card.assistant .markdown-body.markdown-content pre code {
  background: transparent !important;
}

[data-theme='dark'] .conversation-panel .message-card.assistant .markdown-body.markdown-content blockquote {
  border-left-color: rgba(255, 255, 255, 0.14) !important;
  color: rgba(237, 244, 255, 0.82) !important;
}

[data-theme='dark'] .conversation-panel .message-card.assistant .markdown-body.markdown-content table,
[data-theme='dark'] .conversation-panel .message-card.assistant .markdown-body.markdown-content thead,
[data-theme='dark'] .conversation-panel .message-card.assistant .markdown-body.markdown-content tbody,
[data-theme='dark'] .conversation-panel .message-card.assistant .markdown-body.markdown-content tr,
[data-theme='dark'] .conversation-panel .message-card.assistant .markdown-body.markdown-content th,
[data-theme='dark'] .conversation-panel .message-card.assistant .markdown-body.markdown-content td {
  background: transparent !important;
  background-color: transparent !important;
  border-color: rgba(255, 255, 255, 0.1) !important;
}

[data-theme='dark'] .conversation-panel .message-card.assistant .markdown-body.markdown-content th {
  background: rgba(255, 255, 255, 0.05) !important;
}

[data-theme='dark'] .conversation-panel .message-card.assistant .markdown-body.markdown-content tr:nth-child(2n) {
  background: rgba(255, 255, 255, 0.03) !important;
}

[data-theme='dark'] .conversation-panel .message-card.assistant .markdown-body.markdown-content hr {
  border-top-color: rgba(255, 255, 255, 0.1) !important;
}

[data-theme='dark'] .conversation-panel .message-card.assistant .markdown-body.markdown-content mark {
  background: rgba(255, 194, 142, 0.22) !important;
}

[data-theme='dark'] .conversation-panel .file-chip {
  background: rgba(118, 156, 255, 0.08);
}

[data-theme='dark'] .conversation-panel .message-card.user .file-chip {
  background: rgba(255, 255, 255, 0.12);
}

[data-theme='dark'] .conversation-panel .secondary-btn {
  border: 1px solid rgba(118, 156, 255, 0.12);
}

[data-theme='dark'] .conversation-panel .composer-shell {
  background:
    linear-gradient(180deg, rgba(11, 14, 20, 0.88), rgba(9, 11, 16, 0.74)),
    linear-gradient(145deg, rgba(52, 88, 156, 0.08), rgba(24, 107, 97, 0.04));
  border-color: rgba(118, 156, 255, 0.16);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.04),
    0 22px 44px rgba(0, 0, 0, 0.34);
  backdrop-filter: blur(18px);
}

[data-theme='dark'] .conversation-panel .composer-shell:focus-within {
  border-color: rgba(128, 250, 176, 0.24);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.05),
    0 0 0 1px rgba(88, 203, 255, 0.08),
    0 24px 48px rgba(0, 0, 0, 0.38);
}

[data-theme='dark'] .conversation-panel .composer-input,
[data-theme='dark'] .conversation-panel textarea.composer-input {
  background: transparent !important;
  background-color: transparent !important;
  background-image: none !important;
  border: none !important;
  box-shadow: none !important;
  color: #edf4ff !important;
  caret-color: #80fab0;
}

[data-theme='dark'] .conversation-panel .composer-input:focus {
  background: transparent !important;
}

[data-theme='dark'] .conversation-panel .composer-input::placeholder {
  color: rgba(237, 244, 255, 0.5) !important;
}

[data-theme='dark'] .conversation-panel .composer-input:-webkit-autofill,
[data-theme='dark'] .conversation-panel .composer-input:-webkit-autofill:hover,
[data-theme='dark'] .conversation-panel .composer-input:-webkit-autofill:focus {
  -webkit-text-fill-color: #edf4ff !important;
  box-shadow: 0 0 0 1000px transparent inset !important;
  transition: background-color 99999s ease-out 0s;
}

[data-theme='dark'] .conversation-panel .assistant-orb-core {
  box-shadow:
    inset -6px -8px 12px rgba(0, 0, 0, 0.22),
    inset 4px 4px 10px rgba(255, 255, 255, 0.08),
    0 10px 28px rgba(255, 143, 122, 0.22),
    0 0 24px rgba(88, 203, 255, 0.18);
}

[data-theme='dark'] .conversation-panel .composer-shell::before {
  background:
    conic-gradient(
      from var(--composer-glow-angle),
      rgba(118, 156, 255, 0.74),
      rgba(73, 204, 188, 0.68),
      rgba(255, 194, 142, 0.46),
      rgba(118, 156, 255, 0.74)
    );
  box-shadow:
    0 0 0 1px rgba(73, 204, 188, 0.14),
    0 0 22px rgba(90, 135, 255, 0.18),
    0 0 36px rgba(73, 204, 188, 0.12);
}

[data-theme='dark'] .conversation-panel .composer-shell::after {
  background:
    radial-gradient(circle at 18% 50%, rgba(95, 147, 255, 0.18), transparent 36%),
    radial-gradient(circle at 82% 50%, rgba(60, 214, 195, 0.16), transparent 32%);
  opacity: 0.22;
}
</style>
