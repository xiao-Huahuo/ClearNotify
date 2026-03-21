<template>
  <div class="agent-page">
    <aside class="agent-sidebar" :class="{ closed: !sidebarOpen }">
      <div class="sidebar-header">
        <span class="title">对话</span>
        <div class="sidebar-actions">
          <button class="new-btn" @click="createConversation">新建</button>
          <button class="hide-btn" @click="toggleSidebar">收起</button>
        </div>
      </div>
      <div class="conversation-list">
        <button
          v-for="item in conversations"
          :key="item.id"
          class="conversation-item"
          :class="{ active: item.id === activeConversationId }"
          @click="selectConversation(item.id)"
        >
          <span class="name">{{ item.title }}</span>
          <span class="time">{{ formatTime(item.updated_time) }}</span>
        </button>
      </div>
    </aside>

    <main class="agent-main" :class="{ shifted: drawerOpen }">
      <div class="agent-header">
        <div>
          <h1>ClearFlow 智能体</h1>
          <p>简洁、可执行、可追溯。</p>
        </div>
      </div>

      <div class="chat-panel">
        <div class="chat-toolbar">
          <div class="toolbar-actions">
            <button class="tool-btn" @click="createConversation">新对话</button>
            <button class="tool-btn ghost" @click="openHistory">历史记录</button>
          </div>
          <label class="llm-select">
            <span class="label">LLM</span>
            <select v-model="selectedModel" disabled>
              <option value="kimi">KIMI</option>
            </select>
          </label>
        </div>
        <div ref="messageWrapRef" class="message-list">
          <div
            v-for="(msg, index) in messages"
            :key="index"
            class="message-row"
            :class="msg.role"
          >
            <div class="message-bundle" :class="{ trace: msg.role === 'trace' }">
              <div v-if="msg.files?.length" class="file-stack">
                <span v-for="(file, fIndex) in msg.files" :key="fIndex" class="file-chip">{{ file }}</span>
              </div>
              <div v-if="msg.content" class="bubble" :class="msg.role">
                <div
                  v-if="msg.role === 'assistant' || msg.role === 'trace'"
                  class="bubble-content"
                  v-html="renderMarkdown(msg.content)"
                ></div>
                <div v-else-if="msg.content" class="bubble-content">{{ msg.content }}</div>
              </div>
            </div>
          </div>
          <div v-if="loading" class="typing">智能体正在分析...</div>
        </div>

        <div class="quick-prompts">
          <button
            v-for="(prompt, index) in quickPrompts"
            :key="index"
            class="prompt-chip"
            @click="sendMessage(prompt)"
          >
            {{ prompt }}
          </button>
        </div>

        <div class="chat-input">
          <div class="input-tools">
            <label class="upload-btn">
              上传文件
              <input type="file" hidden @change="handleFileUpload" />
            </label>
            <span class="file-name" v-if="uploadedFileName">{{ uploadedFileName }}</span>
          </div>
          <textarea
            v-model="inputText"
            rows="3"
            placeholder="粘贴通知或描述办理需求..."
            @keydown.enter.exact.prevent="sendMessage()"
          ></textarea>
          <button class="send-btn" :disabled="loading" @click="sendMessage()">发送</button>
        </div>
      </div>
    </main>

    <button class="sidebar-toggle" :class="{ open: sidebarOpen }" @click="toggleSidebar">
      <span class="arrow">&gt;</span>
    </button>

    <div class="drawer-toggle" @click="toggleDrawer">
      <span class="arrow" :class="{ open: drawerOpen }">&gt;</span>
    </div>

    <aside class="agent-drawer" :class="{ open: drawerOpen }">
      <div class="drawer-content">
        <div class="panel">
          <div class="panel-title">结构化结果</div>
          <div class="structured-grid">
            <div class="structured-item">
              <span class="label">办理事项</span>
              <span class="value">{{ structured.handling_matter || '待生成' }}</span>
            </div>
            <div class="structured-item">
              <span class="label">适用对象</span>
              <span class="value">{{ structured.target_audience || '待生成' }}</span>
            </div>
            <div class="structured-item">
              <span class="label">时间节点</span>
              <span class="value">{{ structured.time_deadline || '待生成' }}</span>
            </div>
            <div class="structured-item">
              <span class="label">地点/入口</span>
              <span class="value">{{ structured.location_entrance || '待生成' }}</span>
            </div>
          </div>
        </div>

        <div class="panel">
          <div class="panel-title">办理流程</div>
          <ul class="list" v-if="(agentResult?.process_steps || []).length">
            <li v-for="(item, index) in agentResult.process_steps" :key="index">{{ item }}</li>
          </ul>
          <div v-else class="placeholder">等待生成流程</div>
        </div>

        <div class="panel">
          <div class="panel-title">材料清单</div>
          <ul class="list" v-if="(agentResult?.materials || []).length">
            <li v-for="(item, index) in agentResult.materials" :key="index">{{ item }}</li>
          </ul>
          <div v-else class="placeholder">等待生成材料</div>
        </div>

        <div class="panel">
          <div class="panel-title">注意事项</div>
          <ul class="list" v-if="(agentResult?.notices || []).length">
            <li v-for="(item, index) in agentResult.notices" :key="index">{{ item }}</li>
          </ul>
          <div v-else class="placeholder">等待生成注意事项</div>
        </div>

        <div class="panel">
          <div class="panel-title">时间线</div>
          <div v-if="(agentResult?.timeline || []).length" class="timeline">
            <div class="timeline-item" v-for="(item, index) in agentResult.timeline" :key="index">
              <span class="timeline-time">{{ item.time }}</span>
              <span class="timeline-event">{{ item.event }}</span>
            </div>
          </div>
          <div v-else class="placeholder">等待生成时间节点</div>
        </div>

        <div class="panel">
          <div class="panel-title">证据链</div>
          <div v-if="(agentResult?.evidence || []).length" class="evidence-list">
            <div class="evidence-item" v-for="(item, index) in agentResult.evidence" :key="index">
              <div class="evidence-title">{{ item.title || '知识条目' }}</div>
              <div class="evidence-meta">
                <span class="score">相似度 {{ item.score }}</span>
                <span class="tag" v-if="item.category">{{ item.category }}</span>
                <span class="tag" v-for="(tag, tIndex) in (item.tags || []).slice(0,2)" :key="tIndex">{{ tag }}</span>
              </div>
              <div class="evidence-snippet">{{ item.snippet || '暂无片段' }}</div>
            </div>
          </div>
          <div v-else class="placeholder">等待生成证据链</div>
        </div>

        <div class="panel">
          <div class="panel-title">执行过程</div>
          <ul class="list" v-if="(agentResult?.tool_calls || []).length">
            <li v-for="(item, index) in agentResult.tool_calls" :key="index">
              {{ item.tool }} | 输入: {{ item.input }} | 输出: {{ item.output }}
            </li>
          </ul>
          <div v-else class="placeholder">等待工具调用</div>
        </div>
      </div>
    </aside>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onBeforeUnmount } from 'vue';
import MarkdownIt from 'markdown-it';
import { useRoute } from 'vue-router';
import { apiClient, API_ROUTES } from '@/router/api_routes.js';
import { useUserStore } from '@/stores/auth.js';

const userStore = useUserStore();
const route = useRoute();
const inputText = ref('');
const loading = ref(false);
const agentResult = ref(null);
const messageWrapRef = ref(null);
const drawerOpen = ref(false);
const sidebarOpen = ref(false);
const conversations = ref([]);
const activeConversationId = ref(null);
const uploadedFileName = ref('');
const pendingFiles = ref([]);
const selectedModel = ref('kimi');
const markdown = new MarkdownIt({ linkify: true, breaks: true });

const messages = ref([
  {
    role: 'assistant',
    content: '我是通知办理智能体。把通知内容粘贴给我，我会生成办理清单、证据链和风险提示。'
  }
]);

const quickPrompts = [
  '请输出办理清单与材料清单',
  '帮我检查风险与注意事项',
  '生成办理流程与时间线'
];

const structured = computed(() => agentResult.value?.structured || {});
const renderMarkdown = (text) => markdown.render(text || '');

const socketRef = ref(null);
let doneResolver = null;

const scrollToBottom = () => {
  if (!messageWrapRef.value) return;
  messageWrapRef.value.scrollTop = messageWrapRef.value.scrollHeight;
};

const formatTime = (value) => {
  if (!value) return '';
  const date = new Date(value);
  return `${date.getMonth() + 1}-${date.getDate()} ${date.getHours()}:${String(date.getMinutes()).padStart(2, '0')}`;
};

const fetchConversations = async () => {
  const res = await apiClient.get(API_ROUTES.AGENT_CONVERSATIONS);
  conversations.value = res.data || [];
};

const loadMessages = async (conversationId) => {
  const res = await apiClient.get(API_ROUTES.AGENT_MESSAGES(conversationId));
  messages.value = res.data?.map((item) => ({ role: item.role, content: item.content })) || [];
  await nextTick();
  scrollToBottom();
};

const createConversation = async () => {
  const now = new Date();
  const title = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(
    now.getDate()
  ).padStart(2, '0')} ${String(now.getHours()).padStart(2, '0')}:${String(
    now.getMinutes()
  ).padStart(2, '0')} 对话`;
  const res = await apiClient.post(API_ROUTES.AGENT_CONVERSATIONS, { title });
  await fetchConversations();
  activeConversationId.value = res.data.id;
  messages.value = [
    { role: 'assistant', content: '新对话已创建，请输入通知内容。' }
  ];
};

const selectConversation = async (id) => {
  activeConversationId.value = id;
  await loadMessages(id);
};

const openWebSocket = (wsUrl) => new Promise((resolve, reject) => {
  console.log('[AgentWS] connecting', wsUrl);
  const ws = new WebSocket(wsUrl);
  const timer = setTimeout(() => {
    console.warn('[AgentWS] timeout', wsUrl);
    ws.close();
    reject(new Error('timeout'));
  }, 3000);
  ws.onopen = () => {
    console.log('[AgentWS] open', wsUrl);
    clearTimeout(timer);
    resolve(ws);
  };
  ws.onerror = () => {
    console.error('[AgentWS] error', wsUrl);
    clearTimeout(timer);
    reject(new Error('error'));
  };
});

const connectSocket = async () => {
  if (!userStore.token) return;
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
  const isDev = window.location.port === '5173';
  const wsUrl = isDev
    ? `${protocol}://127.0.0.1:8080/agent/ws?token=${encodeURIComponent(userStore.token)}`
    : `${protocol}://${window.location.host}/agent/ws?token=${encodeURIComponent(userStore.token)}`;

  try {
    socketRef.value = await openWebSocket(wsUrl);
  } catch (e) {
    socketRef.value = null;
  }

  if (!socketRef.value) {
    loading.value = false;
    messages.value.push({ role: 'assistant', content: '智能体连接失败，请确认后端已在 8080 端口启动。' });
    return;
  }

  socketRef.value.onmessage = (event) => {
    console.log('[AgentWS] message', event.data?.slice?.(0, 200));
    const data = JSON.parse(event.data);
    if (data.type === 'conversation') {
      activeConversationId.value = data.conversation_id;
      fetchConversations();
      return;
    }
    if (data.type === 'result') {
      agentResult.value = data.agent_result;
      if (!drawerOpen.value) drawerOpen.value = true;
      return;
    }
    if (data.type === 'trace') {
      const lines = ['**执行过程**'];
      (data.tool_calls || []).forEach((item) => {
        const tool = item.tool || 'tool';
        const input = item.input ? `输入: ${item.input}` : '';
        const output = item.output ? `输出: ${item.output}` : '';
        lines.push(`- ${tool} ${input} ${output}`.trim());
      });
      messages.value.push({ role: 'trace', content: lines.join('\n') });
      nextTick(scrollToBottom);
      return;
    }
    if (data.type === 'trace_step') {
      const item = data.tool_call || {};
      const tool = item.tool || 'tool';
      const input = item.input ? `输入: ${item.input}` : '';
      const output = item.output ? `输出: ${item.output}` : '';
      messages.value.push({
        role: 'trace',
        content: `**执行步骤**\n- ${tool} ${input} ${output}`.trim()
      });
      nextTick(scrollToBottom);
      return;
    }
    if (data.type === 'chunk') {
      const last = messages.value[messages.value.length - 1];
      if (!last || last.role !== 'assistant' || last.streaming !== true) {
        messages.value.push({ role: 'assistant', content: data.content, streaming: true });
      } else {
        last.content += data.content;
      }
      nextTick(scrollToBottom);
      return;
    }
    if (data.type === 'done') {
      const last = messages.value[messages.value.length - 1];
      if (last) last.streaming = false;
      loading.value = false;
      fetchConversations();
      if (doneResolver) {
        doneResolver();
        doneResolver = null;
      }
      nextTick(scrollToBottom);
    }
  };
  socketRef.value.onclose = () => {
    console.warn('[AgentWS] closed');
    socketRef.value = null;
  };
};

const ensureSocketReady = async () => {
  if (socketRef.value && socketRef.value.readyState === 1) return;
  await connectSocket();
  await new Promise((resolve, reject) => {
    const start = Date.now();
    const check = () => {
      if (socketRef.value && socketRef.value.readyState === 1) resolve();
      else if (Date.now() - start > 6000) reject(new Error('ws-timeout'));
      else setTimeout(check, 100);
    };
    check();
  });
};

const ensureConversationReady = async () => {
  if (activeConversationId.value) return;
  if (conversations.value.length > 0) {
    activeConversationId.value = conversations.value[0].id;
    await loadMessages(activeConversationId.value);
    return;
  }
  const now = new Date();
  const title = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(
    now.getDate()
  ).padStart(2, '0')} ${String(now.getHours()).padStart(2, '0')}:${String(
    now.getMinutes()
  ).padStart(2, '0')} 对话`;
  const res = await apiClient.post(API_ROUTES.AGENT_CONVERSATIONS, { title });
  await fetchConversations();
  activeConversationId.value = res.data.id;
};

const sendMessage = async (textOverride) => {
  const content = (textOverride ?? inputText.value).trim();
  const hasFiles = pendingFiles.value.length > 0;
  if (!content && !hasFiles) return;
  inputText.value = '';

  loading.value = true;
  try {
    await ensureSocketReady();
  } catch (e) {
    loading.value = false;
    console.error('[AgentWS] ensure failed', e);
    messages.value.push({ role: 'assistant', content: '连接智能体失败，请刷新页面后重试。' });
    return;
  }
  await ensureConversationReady();

  const fileSections = [];
  const fileLabels = [];
  if (hasFiles) {
    const files = [...pendingFiles.value];
    pendingFiles.value = [];
    uploadedFileName.value = '';
    for (const item of files) {
      const file = item.file;
      const isImage = file.type.startsWith('image/');
      const formData = new FormData();
      formData.append('file', file);
      try {
        const url = isImage ? API_ROUTES.UPLOAD_OCR : API_ROUTES.UPLOAD_DOCUMENT;
        const res = await apiClient.post(url, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        const extracted = res.data?.extracted_text || '';
        if (extracted.trim()) {
          fileSections.push(`【文件解析】${item.name}\n${extracted}`);
          fileLabels.push(item.name);
        } else {
          messages.value.push({ role: 'assistant', content: `文件 ${item.name} 未能提取到可用文本。` });
        }
      } catch (e) {
        messages.value.push({ role: 'assistant', content: `文件 ${item.name} 解析失败。` });
      }
    }
  }

  const combinedParts = [];
  if (content) combinedParts.push(content);
  if (fileSections.length) combinedParts.push(...fileSections);
  const combinedText = combinedParts.join('\n\n');
  if (!combinedText) return;

  loading.value = true;
  messages.value.push({ role: 'user', content, files: fileLabels });
  await nextTick();
  scrollToBottom();

  socketRef.value.send(
    JSON.stringify({
      message: combinedText,
      conversation_id: activeConversationId.value,
      use_rag: true,
      top_k: 5
    })
  );
  await new Promise((resolve) => {
    doneResolver = resolve;
  });

};

const handleFileUpload = async (event) => {
  const file = event.target.files?.[0];
  if (!file) return;
  pendingFiles.value.push({ file, name: file.name });
  uploadedFileName.value = pendingFiles.value.map((item) => item.name).join('、');
  event.target.value = '';
};

const toggleDrawer = () => {
  drawerOpen.value = !drawerOpen.value;
};

const toggleSidebar = () => {
  sidebarOpen.value = !sidebarOpen.value;
};

const openHistory = () => {
  sidebarOpen.value = true;
};

onMounted(async () => {
  if (!userStore.token) {
    alert('请先登录后使用智能体');
    return;
  }
  await fetchConversations();
  const routeConversationId = Number(route.query.conversation_id || 0);
  if (routeConversationId) {
    activeConversationId.value = routeConversationId;
    await loadMessages(activeConversationId.value);
  } else if (conversations.value.length > 0) {
    activeConversationId.value = conversations.value[0].id;
    await loadMessages(activeConversationId.value);
  }
  await connectSocket();
});

onBeforeUnmount(() => {
  if (socketRef.value) socketRef.value.close();
});
</script>

<style scoped>
.agent-page {
  height: 100%;
  display: flex;
  background: #f6f4f2;
  position: relative;
  overflow: hidden;
}

.agent-sidebar {
  width: 220px;
  background: #ffffff;
  border-right: 1px solid #eee;
  padding: 18px 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow: hidden;
  transition: width 0.35s ease, opacity 0.35s ease, transform 0.35s ease;
  min-width: 0;
}
.agent-sidebar.closed {
  width: 0;
  padding: 18px 0;
  border-right: none;
  opacity: 0;
  transform: translateX(-12px);
  pointer-events: none;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.sidebar-header .title {
  font-weight: 800;
  font-size: 14px;
}
.sidebar-actions {
  display: flex;
  gap: 6px;
}

.new-btn {
  background: #c0392b;
  color: #fff;
  border: none;
  border-radius: 999px;
  padding: 6px 12px;
  font-size: 12px;
  cursor: pointer;
}
.hide-btn {
  background: #f0f0f0;
  color: #333;
  border: none;
  border-radius: 999px;
  padding: 6px 10px;
  font-size: 12px;
  cursor: pointer;
}

.conversation-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  overflow-y: auto;
}

.conversation-item {
  border: none;
  background: #f9f9f9;
  border-radius: 12px;
  padding: 10px;
  text-align: left;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.conversation-item.active {
  background: #111;
  color: #fff;
}
.conversation-item .name {
  font-size: 13px;
  font-weight: 700;
}
.conversation-item .time {
  font-size: 11px;
  color: inherit;
  opacity: 0.7;
}

.agent-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 22px 28px;
  gap: 12px;
  min-width: 0;
  transition: margin-right 0.35s ease;
  min-height: 0;
}
.agent-main.shifted {
  margin-right: 380px;
}

.agent-header h1 {
  margin: 0;
  font-size: 26px;
  font-weight: 900;
}
.agent-header p {
  margin: 4px 0 0;
  font-size: 13px;
  color: #666;
}

.chat-panel {
  flex: 1;
  background: #fff;
  border-radius: 18px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  border: 1px solid #eee;
  transition: margin-right 0.35s ease;
  min-height: 0;
}
.agent-main.shifted .chat-panel {
  margin-right: 16px;
}

.chat-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}
.toolbar-actions {
  display: flex;
  gap: 8px;
}
.tool-btn {
  border: 1px solid #ddd;
  background: #111;
  color: #fff;
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 12px;
  cursor: pointer;
}
.tool-btn.ghost {
  background: #fff;
  color: #111;
}
.llm-select {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #555;
}
.llm-select select {
  border: 1px solid #ddd;
  border-radius: 10px;
  padding: 4px 10px;
  font-size: 12px;
  background: #fafafa;
}

.message-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 0;
  scroll-behavior: smooth;
}

.message-row {
  display: flex;
}
.message-row.user { justify-content: flex-end; }
.message-row.assistant { justify-content: flex-start; }
.message-bundle {
  max-width: 75%;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.message-row.user .message-bundle { align-items: flex-end; }
.message-row.assistant .message-bundle { align-items: flex-start; }
.message-bundle.trace { align-items: flex-start; opacity: 0.9; }

.bubble {
  max-width: 100%;
  padding: 10px 14px;
  font-size: 14px;
  line-height: 1.35;
  border-radius: 14px;
  background: #f2f2f2;
  white-space: pre-wrap;
  word-break: break-word;
}
.bubble-content * {
  margin: 1px 0;
}
.bubble-content :first-child {
  margin-top: 0;
}
.bubble-content :last-child {
  margin-bottom: 0;
}
.bubble-content h1,
.bubble-content h2,
.bubble-content h3 {
  margin: 1px 0;
  font-size: 14px;
}
.bubble-content ul {
  margin: 1px 0 1px 14px;
  padding: 0;
}
.bubble-content li {
  margin: 0;
}
.bubble-content p {
  margin: 1px 0;
}
.bubble-content ol {
  margin: 1px 0 1px 14px;
  padding: 0;
}
.bubble-content blockquote {
  margin: 1px 0;
  padding-left: 10px;
  border-left: 3px solid #ddd;
  color: #555;
}
.file-stack {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.file-chip {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  background: #111;
  color: #fff;
}
.bubble.user {
  background: #e74c3c;
  color: #fff;
  border-radius: 14px;
}
.bubble.trace {
  background: #f7f7f7;
  color: #555;
  border: 1px dashed #ddd;
  font-size: 12px;
}

.typing {
  font-size: 12px;
  color: #999;
}

.quick-prompts {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.prompt-chip {
  background: #f0f0f0;
  border: none;
  border-radius: 999px;
  padding: 6px 12px;
  font-size: 12px;
  cursor: pointer;
}

.chat-input {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.input-tools {
  display: flex;
  align-items: center;
  gap: 10px;
}
.upload-btn {
  background: #111;
  color: #fff;
  border-radius: 999px;
  padding: 6px 12px;
  font-size: 12px;
  cursor: pointer;
}
.file-name {
  font-size: 12px;
  color: #666;
}

.chat-input textarea {
  border: 1px solid #ddd;
  border-radius: 16px;
  padding: 10px;
  resize: none;
  font-size: 13px;
}

.send-btn {
  align-self: flex-end;
  background: #c0392b;
  color: #fff;
  border: none;
  border-radius: 999px;
  padding: 8px 18px;
  font-weight: 700;
  cursor: pointer;
}
.send-btn:disabled { opacity: 0.6; cursor: not-allowed; }

.drawer-toggle {
  position: absolute;
  right: 0;
  top: 40%;
  width: 22px;
  height: 60px;
  background: #111;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px 0 0 12px;
  cursor: pointer;
  z-index: 10;
}
.drawer-toggle .arrow {
  font-size: 20px;
  transition: transform 0.3s ease;
}
.drawer-toggle .arrow.open { transform: rotate(180deg); }

.sidebar-toggle {
  position: absolute;
  left: 0;
  top: 40%;
  width: 22px;
  height: 60px;
  background: #111;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 0 12px 12px 0;
  cursor: pointer;
  z-index: 10;
  border: none;
}
.sidebar-toggle .arrow {
  font-size: 20px;
  transition: transform 0.3s ease;
}
.sidebar-toggle.open .arrow { transform: rotate(180deg); }

.agent-drawer {
  position: absolute;
  top: 0;
  right: -360px;
  width: 360px;
  height: 100%;
  background: #fff;
  border-left: 1px solid #eee;
  transition: right 0.35s ease;
  overflow-y: auto;
}
.agent-drawer.open { right: 0; }

.drawer-content {
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.panel {
  border: 1px solid #eee;
  border-radius: 16px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.panel-title {
  font-size: 13px;
  font-weight: 800;
}

.structured-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}
.structured-item {
  background: #f8f8f8;
  border-radius: 12px;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.structured-item .label { font-size: 11px; color: #777; }
.structured-item .value { font-size: 12px; font-weight: 700; color: #111; }

.list {
  padding-left: 18px;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 12px;
  color: #333;
}

.timeline {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.timeline-item {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #333;
}
.timeline-time { font-weight: 700; }

.evidence-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.evidence-item {
  border: 1px solid #eee;
  border-radius: 12px;
  padding: 8px;
  background: #fafafa;
}
.evidence-title { font-weight: 700; font-size: 12px; }
.evidence-meta { display: flex; gap: 6px; flex-wrap: wrap; margin: 6px 0; }
.score { font-size: 11px; color: #c0392b; font-weight: 700; }
.tag { font-size: 10px; background: #111; color: #fff; padding: 2px 6px; border-radius: 999px; }
.evidence-snippet { font-size: 11px; color: #666; line-height: 1.5; }

.placeholder {
  font-size: 12px;
  color: #aaa;
}

@media (max-width: 1100px) {
  .agent-sidebar {
    display: none;
  }
}
</style>





