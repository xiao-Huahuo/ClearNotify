<template>
  <div
    class="cloudcycle-page"
    :class="{
      'sidebar-visible': sidebarOpen && !isMobile,
      'inspector-visible': inspectorOpen && !isMobile,
    }"
  >
    <div class="ambient ambient-one"></div>
    <div class="ambient ambient-two"></div>
    <div class="ambient ambient-three"></div>
    <div class="grid-haze"></div>

    <transition name="intro-fade">
      <CloudCycleHero
        v-if="showIntro"
        :run-mode="runMode"
        :leaving="introLeaving"
        @enter="enterMainStage"
      />
    </transition>

    <CloudCycleSidebar
      :open="sidebarOpen"
      :is-mobile="isMobile"
      :connection-state="connectionState"
      :conversations="conversations"
      :active-conversation-id="activeConversationId"
      @create="createConversation"
      @select="selectConversation"
      @delete="deleteConversation"
      @close="sidebarOpen = false"
    />

    <main class="cloudcycle-center" :class="{ ready: !showIntro }">
      <div v-if="!showIntro && messages.length" class="stage-toolbar">
        <div class="mode-switcher">
          <button class="mode-btn" :class="{ active: runMode === 'agent' }" type="button" @click="setRunMode('agent')">
            Agent
          </button>
          <button class="mode-btn" :class="{ active: runMode === 'chat' }" type="button" @click="setRunMode('chat')">
            Chat
          </button>
        </div>
        <div class="toolbar-status" :class="connectionState">{{ connectionText }}</div>
      </div>

      <section class="conversation-stage">
        <CloudCycleConversationPanel
          v-model:input-text="inputText"
          :messages="messages"
          :pending-files="pendingFiles"
          :loading="loading"
          :can-send="canSend"
          :show-landing="!messages.length"
          :run-mode="runMode"
          @send="sendMessage()"
          @pick-file="pickFile"
          @remove-file="removePendingFile"
          @toggle-trace="toggleMessageTrace"
          @set-mode="setRunMode"
        />
      </section>
    </main>

    <CloudCycleInspector
      :open="inspectorOpen"
      :is-mobile="isMobile"
      :loading="loading"
      :run-mode="runMode"
      :connection-state="connectionState"
      :agent-result="agentResult"
      :trace-timeline="traceTimeline"
      @close="inspectorOpen = false"
    />

    <button
      v-if="!showIntro"
      class="edge-handle edge-handle-left"
      type="button"
      :class="{ open: sidebarOpen }"
      :style="leftHandleStyle"
      @click="sidebarOpen = !sidebarOpen"
    >
      <span>{{ sidebarOpen ? '收起会话' : '历史会话' }}</span>
    </button>

    <button
      v-if="!showIntro"
      class="edge-handle edge-handle-right"
      type="button"
      :class="{ open: inspectorOpen }"
      :style="rightHandleStyle"
      @click="inspectorOpen = !inspectorOpen"
    >
      <span>{{ inspectorOpen ? '收起轨迹' : '推理轨迹' }}</span>
    </button>

    <input
      ref="fileInputRef"
      class="hidden-input"
      type="file"
      accept=".pdf,.doc,.docx,.xls,.xlsx,.txt,image/*"
      multiple
      @change="handleFileUpload"
    />
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { apiClient, API_ROUTES } from '@/router/api_routes.js';
import { useUserStore } from '@/stores/auth.js';
import CloudCycleConversationPanel from '@/components/agent/CloudCycleConversationPanel.vue';
import CloudCycleHero from '@/components/agent/CloudCycleHero.vue';
import CloudCycleInspector from '@/components/agent/CloudCycleInspector.vue';
import CloudCycleSidebar from '@/components/agent/CloudCycleSidebar.vue';

const route = useRoute();
const userStore = useUserStore();

const fileInputRef = ref(null);
const inputText = ref('');
const loading = ref(false);
const messages = ref([]);
const conversations = ref([]);
const pendingFiles = ref([]);
const traceTimeline = ref([]);
const agentResult = ref(null);
const activeConversationId = ref(null);
const runMode = ref(localStorage.getItem('cloudcycle_mode') || 'agent');
const connectionState = ref('disconnected');
const isMobile = ref(window.innerWidth <= 1180);
const sidebarOpen = ref(false);
const inspectorOpen = ref(false);
const showIntro = ref(false);
const introLeaving = ref(false);
const socketRef = ref(null);

let doneResolver = null;
let messageIdSeed = 1;
let traceIdSeed = 1;
let traceSeenSignatures = new Set();
let currentAssistantMessageId = null;
const traceQueue = ref([]);
let traceQueueTimer = null;

const canSend = computed(() => Boolean(inputText.value.trim() || pendingFiles.value.length));
const introSessionKey = computed(() => `cloudcycle_intro_seen_${userStore.token || 'guest'}`);
const leftHandleStyle = computed(() => {
  if (isMobile.value) return null;
  return { left: sidebarOpen.value ? '288px' : '10px' };
});
const rightHandleStyle = computed(() => {
  if (isMobile.value) return null;
  return { right: inspectorOpen.value ? '360px' : '10px' };
});
const connectionText = computed(() => {
  if (connectionState.value === 'ready') return '已连接';
  if (connectionState.value === 'connecting') return '连接中';
  if (connectionState.value === 'error') return '连接异常';
  return '未连接';
});

const makeMessage = (role, content = '', extra = {}) => ({
  id: messageIdSeed++,
  role,
  content,
  traceEntries: [],
  traceExpanded: false,
  traceStreaming: false,
  ...extra,
});

const requestLogin = () => window.dispatchEvent(new CustomEvent('open-login-modal'));

const setRunMode = (mode) => {
  runMode.value = mode === 'chat' ? 'chat' : 'agent';
  localStorage.setItem('cloudcycle_mode', runMode.value);
};

const updateResponsiveState = () => {
  isMobile.value = window.innerWidth <= 1180;
};

const nowTimeLabel = () => {
  const date = new Date();
  return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}:${String(
    date.getSeconds()
  ).padStart(2, '0')}`;
};

const shortText = (value, max = 220) => {
  const text = String(value || '').replace(/\s+/g, ' ').trim();
  if (!text) return '';
  return text.length > max ? `${text.slice(0, max)}...` : text;
};

const getCurrentAssistantMessage = () =>
  messages.value.find((item) => item.id === currentAssistantMessageId && item.role === 'assistant');

const ensureCurrentAssistantMessage = () => {
  let message = getCurrentAssistantMessage();
  if (message) return message;

  message = makeMessage('assistant', '', {
    streaming: false,
    traceExpanded: true,
    traceStreaming: true,
    traceEntries: [],
  });
  messages.value.push(message);
  currentAssistantMessageId = message.id;
  return message;
};

const buildTraceView = (entry) => {
  const tool = String(entry?.tool || '').trim() || 'tool';
  const input = shortText(entry?.input || '');
  const output = shortText(entry?.output || '');

  if (tool === 'agent_thought') {
    return {
      kind: 'thought',
      title: input || output || '无思考内容',
      input: '',
      output: '',
    };
  }

  return {
    kind: 'tool',
    title: tool,
    input,
    output,
  };
};

const appendTraceTimeline = (entry) => {
  const view = buildTraceView(entry);
  const signature = `${view.kind}|${view.title}|${view.input}|${view.output}`;
  if (traceSeenSignatures.has(signature)) return;
  traceSeenSignatures.add(signature);

  const normalized = {
    id: traceIdSeed++,
    time: nowTimeLabel(),
    ...view,
  };

  traceTimeline.value.push(normalized);

  const assistantMessage = ensureCurrentAssistantMessage();
  assistantMessage.traceEntries = [...(assistantMessage.traceEntries || []), normalized];
  assistantMessage.traceStreaming = true;
  assistantMessage.traceExpanded = true;
};

const clearTraceQueueTimer = () => {
  if (traceQueueTimer) {
    clearTimeout(traceQueueTimer);
    traceQueueTimer = null;
  }
};

const scheduleTraceQueue = () => {
  if (traceQueueTimer || !traceQueue.value.length) return;
  traceQueueTimer = setTimeout(() => {
    traceQueueTimer = null;
    const nextEntry = traceQueue.value.shift();
    if (nextEntry) appendTraceTimeline(nextEntry);
    if (traceQueue.value.length) scheduleTraceQueue();
  }, 220);
};

const enqueueTrace = (entry) => {
  traceQueue.value.push(entry);
  scheduleTraceQueue();
};

const resetRunRuntime = () => {
  traceTimeline.value = [];
  traceSeenSignatures = new Set();
  agentResult.value = null;
  currentAssistantMessageId = null;
  traceQueue.value = [];
  clearTraceQueueTimer();
};

const toggleMessageTrace = (messageId) => {
  const target = messages.value.find((item) => item.id === messageId);
  if (!target) return;
  target.traceExpanded = !target.traceExpanded;
};

const fetchConversations = async () => {
  if (!userStore.token) return;
  const response = await apiClient.get(API_ROUTES.AGENT_CONVERSATIONS);
  conversations.value = response.data || [];
};

const loadMessages = async (conversationId) => {
  const response = await apiClient.get(API_ROUTES.AGENT_MESSAGES(conversationId));
  messages.value = (response.data || []).map((item) =>
    makeMessage(item.role, item.content, {
      traceEntries: [],
      traceExpanded: false,
      traceStreaming: false,
    })
  );
  resetRunRuntime();
};

const createConversation = async () => {
  if (!userStore.token) {
    requestLogin();
    return;
  }

  const now = new Date();
  const title = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(
    now.getDate()
  ).padStart(2, '0')} ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')} 对话`;
  const response = await apiClient.post(API_ROUTES.AGENT_CONVERSATIONS, { title });
  await fetchConversations();
  activeConversationId.value = response.data.id;
  messages.value = [];
  resetRunRuntime();
  if (isMobile.value) sidebarOpen.value = false;
};

const selectConversation = async (conversationId) => {
  activeConversationId.value = conversationId;
  await loadMessages(conversationId);
  if (isMobile.value) sidebarOpen.value = false;
};

const deleteConversation = async (conversationId) => {
  if (!window.confirm('确定删除这个对话吗？')) return;
  await apiClient.delete(`/agent/conversations/${conversationId}`);
  if (activeConversationId.value === conversationId) {
    activeConversationId.value = null;
    messages.value = [];
    resetRunRuntime();
  }
  await fetchConversations();
  if (!activeConversationId.value && conversations.value.length) {
    await selectConversation(conversations.value[0].id);
  }
};

const getWsUrl = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
  const isDev = window.location.port === '5173';
  if (isDev) {
    return `${protocol}://127.0.0.1:8080/agent/ws?token=${encodeURIComponent(userStore.token)}`;
  }
  return `${protocol}://${window.location.host}/agent/ws?token=${encodeURIComponent(userStore.token)}`;
};

const handleSocketMessage = (raw) => {
  const data = JSON.parse(raw);

  if (data.type === 'conversation') {
    activeConversationId.value = data.conversation_id;
    fetchConversations();
    return;
  }

  if (data.type === 'result') {
    agentResult.value = data.agent_result || null;
    return;
  }

  if (data.type === 'trace_step') {
    enqueueTrace(data.tool_call || {});
    return;
  }

  if (data.type === 'chunk') {
    const assistantMessage = ensureCurrentAssistantMessage();
    assistantMessage.traceStreaming = false;
    if (assistantMessage.traceEntries?.length) {
      assistantMessage.traceExpanded = false;
    }
    assistantMessage.streaming = true;
    assistantMessage.content += data.content;
    return;
  }

  if (data.type === 'done') {
    const assistantMessage = getCurrentAssistantMessage();
    if (assistantMessage) {
      assistantMessage.streaming = false;
      assistantMessage.traceStreaming = false;
    }
    currentAssistantMessageId = null;
    loading.value = false;
    fetchConversations();
    if (doneResolver) {
      doneResolver();
      doneResolver = null;
    }
  }
};

const connectSocket = async () => {
  if (!userStore.token) return;
  if (socketRef.value && socketRef.value.readyState === WebSocket.OPEN) return;

  connectionState.value = 'connecting';

  try {
    socketRef.value = await new Promise((resolve, reject) => {
      const ws = new WebSocket(getWsUrl());
      const timer = setTimeout(() => {
        ws.close();
        reject(new Error('ws-timeout'));
      }, 4000);

      ws.onopen = () => {
        clearTimeout(timer);
        resolve(ws);
      };
      ws.onerror = () => {
        clearTimeout(timer);
        reject(new Error('ws-error'));
      };
    });

    connectionState.value = 'ready';
    socketRef.value.onmessage = (event) => handleSocketMessage(event.data);
    socketRef.value.onclose = () => {
      connectionState.value = 'disconnected';
      socketRef.value = null;
    };
  } catch (error) {
    connectionState.value = 'error';
    socketRef.value = null;
    throw error;
  }
};

const ensureSocketReady = async () => {
  if (socketRef.value && socketRef.value.readyState === WebSocket.OPEN) return;
  await connectSocket();
};

const ensureConversationReady = async () => {
  if (activeConversationId.value) return;
  if (conversations.value.length) {
    activeConversationId.value = conversations.value[0].id;
    await loadMessages(activeConversationId.value);
    return;
  }
  await createConversation();
};

const uploadPendingFiles = async () => {
  const sections = [];
  const labels = [];
  const files = [...pendingFiles.value];
  pendingFiles.value = [];

  for (const item of files) {
    const formData = new FormData();
    formData.append('file', item.file);
    const isImage = String(item.file.type || '').startsWith('image/');
    const routePath = isImage ? API_ROUTES.UPLOAD_OCR : API_ROUTES.UPLOAD_DOCUMENT;
    const response = await apiClient.post(routePath, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    const extractedText = String(response.data?.extracted_text || '').trim();
    if (extractedText) {
      sections.push(`【文件解析】${item.name}\n${extractedText}`);
      labels.push(item.name);
    }
  }

  return { sections, labels };
};

const sendMessage = async (textOverride) => {
  if (!userStore.token) {
    requestLogin();
    return;
  }

  const content = String(textOverride ?? inputText.value).trim();
  if (!content && !pendingFiles.value.length) return;

  loading.value = true;

  try {
    await ensureSocketReady();
    await ensureConversationReady();

    const { sections, labels } = await uploadPendingFiles();
    if (!content && !sections.length) {
      loading.value = false;
      messages.value.push(makeMessage('assistant', '上传文件里没有提取到可用文本，请换一个更清晰的文件或补充文字说明。'));
      return;
    }

    const userVisibleContent = content || `请分析我上传的 ${labels.length} 个文件。`;
    const requestParts = [content || '请分析以下材料，并给出结论。', ...sections].filter(Boolean);
    const finalMessage = requestParts.join('\n\n');

    if (!finalMessage) {
      loading.value = false;
      return;
    }

    inputText.value = '';
    resetRunRuntime();
    messages.value.push(makeMessage('user', userVisibleContent, { files: labels }));
    ensureCurrentAssistantMessage();
    await nextTick();

    socketRef.value.send(
      JSON.stringify({
        message: finalMessage,
        conversation_id: activeConversationId.value,
        mode: runMode.value,
        use_rag: true,
        top_k: 5,
      })
    );

    await new Promise((resolve) => {
      doneResolver = resolve;
    });
  } catch (error) {
    loading.value = false;
    const assistantMessage = getCurrentAssistantMessage();
    if (assistantMessage) {
      assistantMessage.traceStreaming = false;
      assistantMessage.streaming = false;
      assistantMessage.content = '连接智能体失败，请确认后端已启动并重试。';
    } else {
      messages.value.push(makeMessage('assistant', '连接智能体失败，请确认后端已启动并重试。'));
    }
    currentAssistantMessageId = null;
  }
};

const pickFile = () => fileInputRef.value?.click();

const removePendingFile = (name) => {
  pendingFiles.value = pendingFiles.value.filter((item) => item.name !== name);
};

const handleFileUpload = (event) => {
  const files = Array.from(event.target.files || []);
  files.forEach((file) => {
    pendingFiles.value.push({ file, name: file.name });
  });
  event.target.value = '';
};

const enterMainStage = () => {
  sessionStorage.setItem(introSessionKey.value, '1');
  introLeaving.value = true;
  setTimeout(() => {
    showIntro.value = false;
    introLeaving.value = false;
  }, 680);
};

const initializePage = async () => {
  if (!userStore.token) return;
  showIntro.value = sessionStorage.getItem(introSessionKey.value) !== '1';
  introLeaving.value = false;

  await fetchConversations();
  const routeConversationId = Number(route.query.conversation_id || 0);
  if (routeConversationId) {
    activeConversationId.value = routeConversationId;
    await loadMessages(routeConversationId);
  } else if (conversations.value.length) {
    activeConversationId.value = conversations.value[0].id;
    await loadMessages(activeConversationId.value);
  }

  try {
    await connectSocket();
  } catch (error) {
    messages.value.push(makeMessage('assistant', 'Agent 连接失败，请稍后重试。'));
  }
};

watch(
  () => userStore.token,
  async (token) => {
    if (!token) {
      conversations.value = [];
      messages.value = [];
      activeConversationId.value = null;
      connectionState.value = 'disconnected';
      socketRef.value?.close();
      socketRef.value = null;
      showIntro.value = false;
      return;
    }
    await initializePage();
  }
);

onMounted(async () => {
  window.addEventListener('resize', updateResponsiveState);
  await initializePage();
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', updateResponsiveState);
  socketRef.value?.close();
  clearTraceQueueTimer();
});
</script>

<style scoped>
.cloudcycle-page {
  position: relative;
  display: block;
  min-height: calc(100vh - 96px);
  height: calc(100vh - 96px);
  overflow: hidden;
  transition: background 0.6s ease;
}

.cloudcycle-page,
.cloudcycle-page * {
  transition-property: background, background-color, border-color, color, box-shadow, opacity, filter;
  transition-duration: 0.45s;
  transition-timing-function: ease;
}

.ambient,
.grid-haze {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.ambient-one {
  background: radial-gradient(circle at 8% 18%, rgba(130, 179, 255, 0.34), transparent 28%);
  animation: driftOne 18s ease-in-out infinite;
}

.ambient-two {
  background: radial-gradient(circle at 90% 16%, rgba(121, 250, 231, 0.24), transparent 24%);
  animation: driftTwo 22s ease-in-out infinite;
}

.ambient-three {
  background: radial-gradient(circle at 56% 88%, rgba(255, 189, 142, 0.16), transparent 22%);
  animation: driftThree 20s ease-in-out infinite;
}

.grid-haze {
  background-image:
    linear-gradient(rgba(92, 130, 199, 0.06) 1px, transparent 1px),
    linear-gradient(90deg, rgba(92, 130, 199, 0.06) 1px, transparent 1px);
  background-size: 42px 42px;
  mask-image: radial-gradient(circle at center, rgba(0, 0, 0, 0.8), transparent 88%);
}

.cloudcycle-center {
  position: relative;
  z-index: 1;
  width: auto;
  display: flex;
  flex-direction: column;
  gap: 18px;
  height: 100%;
  min-height: 0;
  padding: 24px;
  margin-left: 0;
  margin-right: 0;
  opacity: 0;
  transform: scale(0.985) translateY(10px);
  transition:
    opacity 0.8s cubic-bezier(0.22, 1, 0.36, 1),
    transform 0.8s cubic-bezier(0.22, 1, 0.36, 1),
    padding 0.45s ease,
    margin-left 0.55s cubic-bezier(0.22, 1, 0.36, 1),
    margin-right 0.55s cubic-bezier(0.22, 1, 0.36, 1);
}

.cloudcycle-center.ready {
  opacity: 1;
  transform: scale(1) translateY(0);
}

.cloudcycle-page.sidebar-visible .cloudcycle-center {
  margin-left: 306px;
}

.cloudcycle-page.inspector-visible .cloudcycle-center {
  margin-right: 378px;
}

.stage-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 0 8px;
  animation: toolbarFadeIn 0.9s cubic-bezier(0.22, 1, 0.36, 1);
}

.mode-switcher {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.52);
  border: 1px solid rgba(255, 255, 255, 0.56);
  box-shadow: 0 16px 36px rgba(17, 41, 83, 0.08);
  transition:
    background 0.45s ease,
    border-color 0.45s ease,
    box-shadow 0.45s ease;
}

.mode-btn {
  border: none;
  border-radius: 999px;
  padding: 10px 14px;
  background: transparent;
  color: rgba(16, 33, 63, 0.58);
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition:
    background 0.35s ease,
    color 0.35s ease,
    transform 0.3s ease;
}

.mode-btn.active {
  background:
    linear-gradient(135deg, rgba(76, 132, 255, 0.18), rgba(47, 211, 193, 0.16)),
    rgba(255, 255, 255, 0.8);
  color: #15305a;
}

.toolbar-status {
  padding: 10px 14px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  color: rgba(16, 33, 63, 0.58);
  background: rgba(255, 255, 255, 0.52);
  border: 1px solid rgba(255, 255, 255, 0.56);
  transition: all 0.45s ease;
}

.toolbar-status.ready {
  color: #0a775c;
}

.toolbar-status.connecting {
  color: #8b5b12;
}

.toolbar-status.error {
  color: #a43a3a;
}

.conversation-stage {
  flex: 1;
  min-height: 0;
  display: flex;
  overflow: hidden;
}

.conversation-stage :deep(.conversation-panel) {
  flex: 1;
  height: 100%;
}

.cloudcycle-page :deep(.cloudcycle-sidebar:not(.mobile)) {
  position: absolute;
  left: 0;
  top: 24px;
  bottom: 24px;
}

.cloudcycle-page :deep(.inspector-panel:not(.mobile)) {
  position: absolute;
  right: 0;
  top: 24px;
  bottom: 24px;
}

.edge-handle {
  position: absolute;
  top: 50%;
  z-index: 90;
  border: none;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.84), rgba(255, 255, 255, 0.64)),
    rgba(255, 255, 255, 0.6);
  color: rgba(16, 33, 63, 0.68);
  border-radius: 999px;
  padding: 16px 12px;
  cursor: pointer;
  box-shadow: 0 18px 38px rgba(17, 41, 83, 0.1);
  transform: translateY(-50%);
  writing-mode: vertical-rl;
  text-orientation: mixed;
  letter-spacing: 0.12em;
  transition:
    left 0.55s cubic-bezier(0.22, 1, 0.36, 1),
    right 0.55s cubic-bezier(0.22, 1, 0.36, 1),
    opacity 0.4s ease,
    transform 0.4s ease,
    background 0.45s ease,
    color 0.45s ease,
    box-shadow 0.45s ease;
}

.edge-handle:hover {
  transform: translateY(-50%) scale(1.03);
}

.edge-handle-left {
  left: 10px;
}

.edge-handle-right {
  right: 10px;
}

.edge-handle.open {
  opacity: 0.78;
  box-shadow: 0 22px 46px rgba(17, 41, 83, 0.16);
}

.hidden-input {
  display: none;
}

.intro-fade-enter-active,
.intro-fade-leave-active {
  transition: opacity 0.85s cubic-bezier(0.22, 1, 0.36, 1);
}

.intro-fade-enter-from,
.intro-fade-leave-to {
  opacity: 0;
}

@keyframes toolbarFadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes driftOne {
  0%, 100% { transform: translate3d(0, 0, 0); }
  50% { transform: translate3d(2%, 3%, 0); }
}

@keyframes driftTwo {
  0%, 100% { transform: translate3d(0, 0, 0); }
  50% { transform: translate3d(-2%, 4%, 0); }
}

@keyframes driftThree {
  0%, 100% { transform: translate3d(0, 0, 0); }
  50% { transform: translate3d(1%, -3%, 0); }
}

@media (max-width: 1180px) {
  .cloudcycle-page {
    height: auto;
    min-height: calc(100vh - 96px);
  }

  .cloudcycle-center {
    padding: 18px 14px;
    margin-left: 0 !important;
    margin-right: 0 !important;
  }

  .stage-toolbar {
    padding: 0 4px;
  }

  .edge-handle {
    top: auto;
    bottom: 16px;
    transform: none;
    writing-mode: horizontal-tb;
    letter-spacing: 0;
  }

  .edge-handle:hover {
    transform: scale(1.03);
  }

  .edge-handle-left {
    left: 14px;
  }

  .edge-handle-right {
    right: 14px;
  }
}

:global([data-theme='dark']) .cloudcycle-page {
  background: linear-gradient(180deg, rgba(4, 10, 22, 0.28), rgba(4, 10, 22, 0.12));
}

:global([data-theme='dark']) .grid-haze {
  background-image:
    linear-gradient(rgba(153, 181, 244, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(153, 181, 244, 0.05) 1px, transparent 1px);
}

:global([data-theme='dark']) .mode-switcher,
:global([data-theme='dark']) .toolbar-status,
:global([data-theme='dark']) .edge-handle {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.08);
  box-shadow: 0 22px 48px rgba(0, 0, 0, 0.24);
}

:global([data-theme='dark']) .mode-btn,
:global([data-theme='dark']) .toolbar-status,
:global([data-theme='dark']) .edge-handle {
  color: rgba(237, 244, 255, 0.72);
}

:global([data-theme='dark']) .mode-btn.active {
  background:
    linear-gradient(135deg, rgba(64, 117, 255, 0.24), rgba(41, 187, 173, 0.18)),
    rgba(255, 255, 255, 0.08);
  color: #edf4ff;
}
</style>
