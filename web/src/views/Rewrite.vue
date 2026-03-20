<template>
  <div class="independent-layout">
    <!-- 顶部导航 -->
    <div class="nav-header">
      <button @click="goBack" class="back-btn">
        返回
      </button>
      <h2>多版本改写引擎</h2>
      <div style="width: 80px;"></div> <!-- 占位平衡居中 -->
    </div>

    <div class="rewrite-container">

      <!-- 初始输入与配置区 -->
      <div v-if="!showResult" class="setup-section">
        <!-- 上传区域 (复用主页的极简风格) -->
        <div
          class="upload-area"
          @click="triggerFileUpload"
          @dragover.prevent
          @drop.prevent="handleDrop"
          :class="{ 'disabled': loading }"
        >
          <div class="upload-buttons">
            <button class="action-btn" @click.stop="triggerFileUpload" :disabled="loading">
              本地上传
            </button>
            <button class="action-btn" @click.stop="handleUrlUpload" :disabled="loading">
              URL上传
            </button>
          </div>
          <p class="upload-hint">点击或拖拽上传需要改写的文档 (支持 TXT, PDF, Word, Excel)</p>
          <input type="file" ref="fileInput" style="display: none" @change="handleFileUpload" accept=".txt,.pdf,.doc,.docx,.xls,.xlsx" />
        </div>

        <div v-if="loading" class="loading-banner">
          <div class="spinner"></div>
          <span>正在智能处理中...</span>
        </div>

        <!-- 改写配置区 -->
        <div class="config-area" v-if="inputText && !loading">
          <p class="section-label">1. 请选择目标版本（或输入自定义群体）：</p>

          <div class="version-tags">
            <span
              v-for="tag in predefinedVersions"
              :key="tag"
              class="v-tag"
              :class="{ 'active': selectedVersion === tag }"
              @click="selectVersion(tag)"
            >
              {{ tag }}
            </span>
          </div>

          <div class="custom-input-wrapper">
            <input
              type="text"
              class="custom-version-input"
              placeholder="或者在此输入您的个性化受众 (例如: 听障人士、小学生...)"
              v-model="customVersion"
              @input="handleCustomInput"
            />
          </div>

          <button class="submit-btn" @click="startRewrite" :disabled="!activeVersion">
            开始改写
          </button>
          <p v-if="!activeVersion" class="error-hint">请选择或输入需要改写的版本</p>
        </div>

        <!-- 历史记录列表 -->
        <div class="history-list-section" v-if="!inputText && historyMessages.length > 0">
          <h3 class="section-label">或者从历史记录中选择：</h3>
          <div class="history-items">
            <div class="h-item" v-for="msg in historyMessages" :key="msg.id" @click="selectHistoryItem(msg)">
              <span class="h-time">{{ formatDate(msg.created_time) }}</span>
              <span class="h-text">{{ formatName(msg.original_text) }}</span>
              <span class="h-arrow">→</span>
            </div>
          </div>
        </div>

      </div>

      <!-- 改写结果对比区 -->
      <div v-else class="result-section">

        <!-- 顶部控制栏 -->
        <div class="result-controls">
          <div class="version-selector">
            <span class="label">当前版本：</span>
            <span class="current-v">{{ activeVersion }}</span>
            <button class="re-select-btn" @click="resetConfig">重新选择</button>
          </div>
          <button class="submit-btn rewrite-again" @click="executeRewrite" :disabled="isRewriting">
            {{ isRewriting ? '正在生成...' : '再次生成' }}
          </button>
        </div>

        <!-- 双栏对比 -->
        <div class="compare-grid">
          <!-- 左侧：原文 -->
          <div class="compare-box">
            <h3 class="box-title">原文</h3>
            <div class="text-content original">
              <a v-if="currentFileUrl" :href="currentFileUrl" target="_blank" class="file-link">点击查看上传的原文件</a>
              <br v-if="currentFileUrl" />
              {{ currentMessageData?.original_text || inputText }}
            </div>
          </div>

          <!-- 右侧：改写结果 -->
          <div class="compare-box result-box">
            <h3 class="box-title highlight">{{ activeVersion }}</h3>

            <div v-if="isRewriting" class="loading-state">
              <div class="spinner"></div>
              <p>AI 正在努力改写中...</p>
            </div>

            <div v-else class="text-content rewritten">
              <!-- 这里直接展示纯文本结果，通过拆解对象 -->
              <div v-if="currentMessageData" class="structured-text">
                <p v-if="currentMessageData.target_audience"><strong>适用对象：</strong>{{ currentMessageData.target_audience }}</p>
                <p v-if="currentMessageData.handling_matter"><strong>办理事项：</strong>{{ currentMessageData.handling_matter }}</p>
                <p v-if="currentMessageData.time_deadline"><strong>时间：</strong>{{ currentMessageData.time_deadline }}</p>
                <p v-if="currentMessageData.location_entrance"><strong>地点/入口：</strong>{{ currentMessageData.location_entrance }}</p>
                <p v-if="currentMessageData.required_materials"><strong>所需材料：</strong>{{ currentMessageData.required_materials }}</p>
                <p v-if="currentMessageData.handling_process"><strong>办理流程：</strong><br/>{{ currentMessageData.handling_process }}</p>
                <p v-if="currentMessageData.precautions"><strong>注意事项：</strong>{{ currentMessageData.precautions }}</p>
                <p v-if="currentMessageData.risk_warnings"><strong>风险提醒：</strong>{{ currentMessageData.risk_warnings }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { createChatMessage, createChatMessageWithFile, uploadAndExtractDocument, rewriteChatMessage, getChatMessages } from '@/api/ai';
import { useUserStore } from '@/stores/auth.js';

const router = useRouter();
const userStore = useUserStore();

// 状态
const inputText = ref('');
const currentFileUrl = ref(null); // 保存当前解析文件的URL
const fileInput = ref(null);
const loading = ref(false);
const isRewriting = ref(false);
const showResult = ref(false);

const predefinedVersions = ['学生版', '老人版', '家属转述版', '极简版', '客服答复版'];
const selectedVersion = ref('');
const customVersion = ref('');

const historyMessages = ref([]);
const currentMessageId = ref(null); // 如果是从历史记录选的或者是刚创建的
const currentMessageData = ref(null); // 保存后端的返回对象

// 计算当前生效的版本
const activeVersion = computed(() => {
  return customVersion.value.trim() || selectedVersion.value;
});

onMounted(async () => {
  if (!userStore.token) {
    alert("请先登录");
    router.push('/');
    return;
  }
  // 加载历史记录供选择
  try {
    const res = await getChatMessages({ limit: 5 });
    historyMessages.value = res.data;
  } catch(e) {
    console.error(e);
  }
});

// --- 事件处理 ---

const goBack = () => {
  if (showResult.value) {
    // 如果在结果页，返回配置页
    showResult.value = false;
  } else {
    // 退出独立页面，回到框架
    window.location.href = '/feature-a';
  }
};

const triggerFileUpload = () => {
  if (loading.value) return;
  fileInput.value.click();
};

const handleFileUpload = (event) => {
  const file = event.target.files[0];
  processFile(file);
};

const handleDrop = (event) => {
  if (loading.value) return;
  const file = event.dataTransfer.files[0];
  processFile(file);
};

const processFile = async (file) => {
  if (!file) return;

  loading.value = true;
  currentMessageId.value = null; // 新文件，清空历史 ID
  currentFileUrl.value = null;
  inputText.value = '';

  try {
    // 调用通用文档上传接口
    const uploadRes = await uploadAndExtractDocument(file);
    const { extracted_text, file_url } = uploadRes.data;

    // 把提取出来的纯文本显示在配置区域供用户确认
    inputText.value = extracted_text;
    currentFileUrl.value = file_url; // 保存文件 URL 以便后续存储或展示

  } catch (error) {
    console.error(error);
    alert('文件提取失败: ' + (error.response?.data?.detail || error.message));
  } finally {
    loading.value = false;
    if (fileInput.value) {
       fileInput.value.value = ''; // 清空 input
    }
  }
};

const handleUrlUpload = () => {
  if (loading.value) return;
  const url = prompt("请输入 URL:");
  if (url) {
    inputText.value = `URL: ${url}`;
    currentMessageId.value = null;
    currentFileUrl.value = null;
  }
};

const selectVersion = (tag) => {
  selectedVersion.value = tag;
  customVersion.value = ''; // 选中 tag 时清空自定义输入
};

const handleCustomInput = () => {
  selectedVersion.value = ''; // 输入自定义内容时清空 tag 选中状态
};

const selectHistoryItem = (msg) => {
  inputText.value = msg.original_text;
  currentMessageId.value = msg.id;
  currentMessageData.value = msg;
  currentFileUrl.value = msg.file_url;
};

const resetConfig = () => {
  showResult.value = false;
};

// --- API 调用逻辑 ---

const startRewrite = async () => {
  if (!activeVersion.value) return;

  showResult.value = true;
  await executeRewrite();
};

const executeRewrite = async () => {
  isRewriting.value = true;
  try {
    let msgId = currentMessageId.value;

    // 如果是全新上传的文件（没有 msgId），先调用创建接口存库
    if (!msgId) {
      let createRes;
      if (currentFileUrl.value) {
          createRes = await createChatMessageWithFile(inputText.value, currentFileUrl.value);
      } else {
          createRes = await createChatMessage(inputText.value);
      }
      msgId = createRes.data.id;
      currentMessageId.value = msgId;
    }

    // 调用 PATCH 接口进行改写
    const rewriteRes = await rewriteChatMessage(msgId, activeVersion.value);
    currentMessageData.value = rewriteRes.data;

  } catch (error) {
    console.error(error);
    alert('改写失败，请重试');
    showResult.value = false;
  } finally {
    isRewriting.value = false;
  }
};

// 格式化工具
const formatName = (text) => {
  if (!text) return '未命名文档';
  const cleanText = text.replace(/\s+/g, ' ');
  return cleanText.length > 30 ? cleanText.substring(0, 30) + '...' : cleanText;
};

const formatDate = (dateString) => {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return `${date.getMonth()+1}-${date.getDate()} ${date.getHours()}:${date.getMinutes()}`;
};
</script>

<style scoped>
/* 独立页面布局，脱离 Sidebar */
.independent-layout {
  min-height: 100vh;
  background-color: #ffffff;
  display: flex;
  flex-direction: column;
}

.nav-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 30px;
  border-bottom: 1px solid var(--border-color);
  background-color: #fff;
}

.nav-header h2 {
  margin: 0;
  font-size: 20px;
  color: var(--color-text-dark);
}

.back-btn {
  background: none;
  border: 1px solid #ccc;
  padding: 8px 20px;
  border-radius: 20px;
  cursor: pointer;
  font-size: 14px;
  font-weight: bold;
  color: #000;
  transition: all 0.2s;
}

.back-btn:hover {
  background-color: #f5f5f5;
}

.rewrite-container {
  flex: 1;
  max-width: 1000px;
  margin: 0 auto;
  width: 100%;
  padding: 40px 20px;
}

/* 上传区 */
.upload-area {
  background-color: #fff;
  border: 2px dashed #e0e0e0;
  border-radius: 20px;
  padding: 80px 40px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  margin-bottom: 30px;
}
.upload-area:hover {
  border-color: #000;
  background-color: #fafafa;
}
.upload-buttons {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-bottom: 15px;
}
.action-btn {
  background-color: #f5f5f5;
  border: none;
  border-radius: var(--border-radius-pill);
  padding: 8px 25px;
  font-size: 14px;
  font-weight: bold;
  color: #000;
  cursor: pointer;
  transition: all 0.2s;
}
.action-btn:hover {
  background-color: #eee;
}
.upload-hint {
  font-size: 14px;
  color: #999;
  margin: 0;
}

/* 历史记录简易列表 */
.history-list-section {
  margin-top: 40px;
  border-top: 1px solid #eee;
  padding-top: 20px;
}
.h-item {
  display: flex;
  align-items: center;
  padding: 15px 20px;
  border-radius: 8px;
  border: 1px solid #eee;
  margin-bottom: 10px;
  cursor: pointer;
  transition: all 0.2s;
}
.h-item:hover {
  border-color: #000;
  background-color: #fafafa;
}
.h-time {
  color: #999;
  font-size: 13px;
  width: 100px;
}
.h-text {
  flex: 1;
  color: #333;
  font-weight: 500;
}
.h-arrow {
  color: #ccc;
  font-weight: bold;
}

/* 配置区 */
.config-area {
  background-color: #f9f9f9;
  padding: 30px;
  border-radius: 12px;
  margin-top: 20px;
  text-align: center;
  border: 1px solid #eee;
}
.section-label {
  font-size: 16px;
  font-weight: bold;
  color: #000;
  margin-bottom: 20px;
}

.version-tags {
  display: flex;
  justify-content: center;
  gap: 15px;
  margin-bottom: 25px;
}
.v-tag {
  background-color: #000;
  color: #fff;
  padding: 8px 20px;
  border-radius: var(--border-radius-pill);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}
.v-tag:hover {
  opacity: 0.8;
}
.v-tag.active {
  background-color: var(--color-primary);
  color: #000;
  font-weight: bold;
}

.custom-input-wrapper {
  margin-bottom: 30px;
}
.custom-version-input {
  width: 80%;
  max-width: 400px;
  padding: 12px 20px;
  border-radius: var(--border-radius-pill);
  border: 1px solid #ccc;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
  text-align: center;
}
.custom-version-input:focus {
  border-color: #000;
}

.submit-btn {
  background-color: var(--color-primary);
  color: #000;
  border: none;
  padding: 12px 40px;
  border-radius: var(--border-radius-pill);
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.2s;
}
.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  background-color: #c3f070;
}
.submit-btn:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.error-hint {
  color: #e53935;
  font-size: 13px;
  margin-top: 10px;
}

/* 结果对比区 */
.result-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
}
.version-selector {
  display: flex;
  align-items: center;
  gap: 10px;
}
.current-v {
  font-weight: bold;
  font-size: 18px;
  color: #000;
}
.re-select-btn {
  background: none;
  border: 1px solid #ccc;
  border-radius: var(--border-radius-pill);
  padding: 4px 12px;
  font-size: 12px;
  cursor: pointer;
}
.rewrite-again {
  padding: 8px 25px;
  font-size: 14px;
}

.compare-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 30px;
  height: 600px; /* 固定高度，内部滚动 */
}

.compare-box {
  border: 2px dashed var(--border-color);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  background-color: #fff;
}

.box-title {
  margin: 0;
  padding: 15px 20px;
  font-size: 18px;
  font-weight: bold;
  border-bottom: 1px solid #eee;
  text-align: center;
}
.box-title.highlight {
  background-color: #000;
  color: #fff;
  border-top-left-radius: 10px;
  border-top-right-radius: 10px;
}

.text-content {
  padding: 20px;
  flex: 1;
  overflow-y: auto;
  font-size: 15px;
  line-height: 1.8;
  color: #666;
  white-space: pre-wrap;
}

.text-content.original {
  background-color: #fafafa;
}

.file-link {
  color: #00a8ff;
  text-decoration: underline;
  display: inline-block;
  margin-bottom: 10px;
}

.structured-text p {
  margin-bottom: 15px;
}
.structured-text strong {
  color: #000;
}

/* Loading 态 */
.loading-state, .loading-banner {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #999;
}
.loading-banner {
  flex-direction: row;
  height: auto;
  padding: 20px;
  margin-bottom: 20px;
}
.spinner {
  width: 30px;
  height: 30px;
  border: 3px solid #eee;
  border-radius: 50%;
  border-top-color: #000;
  animation: spin 1s linear infinite;
  margin-bottom: 15px;
}
.loading-banner .spinner {
  width: 20px;
  height: 20px;
  margin-bottom: 0;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
