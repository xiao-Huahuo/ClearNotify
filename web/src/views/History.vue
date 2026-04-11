<template>
  <div class="history-container">
    <div class="fixed-header-area">
      <div class="header-section">
        <PolicyTitle title="会话历史" />
        <div class="header-actions">
          <button class="import-btn" @click="triggerImport">导入会话</button>
          <input ref="importInput" type="file" accept=".json,application/json" hidden @change="handleImport" />
        </div>
      </div>

      <div class="top-bar">
        <div class="filter-section">
          <span class="filter-label">记录类型:</span>
          <div class="tags-group">
            <span class="sort-tag" :class="{ active: historyMode === 'document' }" @click="switchMode('document')">通知解析</span>
            <span class="sort-tag" :class="{ active: historyMode === 'agent' }" @click="switchMode('agent')">智能体对话</span>
          </div>
          <div class="tags-group" v-if="historyMode === 'document'">
            <span class="sort-tag" :class="{ active: sortBy === 'created_time' && sortOrder === 'desc' }" @click="applySort('created_time', 'desc')">按时间降序</span>
            <span class="sort-tag" :class="{ active: sortBy === 'difficulty' }" @click="applySort('difficulty', sortOrder === 'asc' ? 'desc' : 'asc')">按复杂度</span>
            <span class="sort-tag" :class="{ active: handlingOnly }" @click="toggleHandlingOnly">仅看办理类</span>
          </div>
        </div>

        <div class="multi-select-actions" v-if="historyMode === 'document'">
          <button class="batch-action-btn" @click="toggleSelectMode" :class="{ active: isSelectMode }">
            <span v-if="!isSelectMode">多选</span>
            <span v-else>取消多选</span>
          </button>
        </div>
      </div>

      <div class="table-header" v-if="historyMode === 'document'">
        <div class="col-checkbox" v-show="isSelectMode">
          <div class="custom-checkbox" :class="{ checked: isAllSelected }" @click="toggleSelectAll">
            <svg v-if="isAllSelected" viewBox="0 0 24 24" width="12" height="12" stroke="currentColor" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
          </div>
        </div>
        <div class="col-name">任务名称</div>
        <div class="col-type">类型</div>
        <div class="col-model">难度</div>
        <div class="col-time">创建时间</div>
        <div class="col-actions">操作</div>
      </div>
      <div class="table-header" v-else>
        <div class="col-name">对话标题</div>
        <div class="col-type">类型</div>
        <div class="col-time">最近更新</div>
        <div class="col-actions">操作</div>
      </div>
    </div>

    <div class="table-container scrollable-area" ref="scrollContainer" @scroll="handleScroll">
      <div v-if="loading && messages.length === 0" class="empty-state-centered">
        <span>加载中...</span>
      </div>
      <div v-else-if="historyMode === 'document' && messages.length === 0" class="empty-state-centered">
        <span>无记录</span>
      </div>
      <div v-else-if="historyMode === 'agent' && agentConversations.length === 0" class="empty-state-centered">
        <span>暂无智能体对话</span>
      </div>

      <div v-else-if="historyMode === 'document'" class="table-body">
        <div
          v-for="(msg, index) in messages"
          :key="msg.id"
          class="table-row slide-in"
          :style="{ animationDelay: `${Math.min(index, 29) * 40}ms` }"
          :class="{ 'row-selected': selectedIds.includes(msg.id) }"
          @click="handleRowClick(msg.id)"
        >
          <div class="col-checkbox" v-show="isSelectMode">
            <div class="custom-checkbox" :class="{ checked: selectedIds.includes(msg.id) }">
              <svg v-if="selectedIds.includes(msg.id)" viewBox="0 0 24 24" width="12" height="12" stroke="currentColor" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
            </div>
          </div>
          <div class="col-name text-ellipsis" :title="msg.original_text" data-label="任务名称">
            {{ formatName(msg.original_text) }}
          </div>
          <div class="col-type" data-label="类型">
            <span class="type-text">{{ msg.chat_analysis?.notice_type || '文档' }}</span>
          </div>
          <div class="col-model" data-label="难度">
            <span class="model-badge">{{ getDifficultyLabel(msg) }}</span>
          </div>
          <div class="col-time" data-label="创建时间">{{ formatDate(msg.created_time) }}</div>
          <div class="col-actions" data-label="操作" @click.stop>
            <button class="icon-btn favorite-btn" :class="{ active: isFavorited(msg.id) }" title="收藏" @click="toggleFavorite(msg)">
              <svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" :fill="isFavorited(msg.id) ? '#f1c40f' : 'none'">
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
              </svg>
            </button>
            <button class="icon-btn" title="恢复对话" @click="restoreMessage(msg.id)">恢复</button>
            <button class="icon-btn" title="打开文件夹" @click="handleOpenFolder(msg.id)">目录</button>
            <button class="icon-btn" title="导出 JSON" @click="handleExport(msg.id)">导出</button>
            <button class="icon-btn delete-btn" title="删除记录" @click="handleDelete(msg.id)">删除</button>
          </div>
        </div>
      </div>

      <div v-else class="table-body">
        <div
          v-for="item in agentConversations"
          :key="item.id"
          class="table-row"
          @click="openAgentConversation(item.id)"
        >
          <div class="col-name text-ellipsis" :title="item.title" data-label="对话标题">
            {{ item.title }}
          </div>
          <div class="col-type" data-label="类型">
            <span class="type-text">智能体对话</span>
          </div>
          <div class="col-time" data-label="最近更新">{{ formatDate(item.updated_time) }}</div>
          <div class="col-actions" data-label="操作" @click.stop>
            <button class="icon-btn" title="进入对话" @click="openAgentConversation(item.id)">进入</button>
          </div>
        </div>
      </div>
    </div>

    <div class="floating-action-bar" v-if="historyMode === 'document'" :class="{ show: isSelectMode && selectedIds.length > 0 }">
      <div class="action-content">
        <span class="selected-count">已选择 {{ selectedIds.length }} 项</span>
        <span class="divider">|</span>
        <button class="icon-btn batch-delete-btn" title="批量删除" @click="handleBatchDelete">删除</button>
        <button class="icon-btn close-action-btn" title="取消选择" @click="clearSelection">关闭</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import PolicyTitle from '@/components/common/PolicyTitle.vue';
import { useRouter } from 'vue-router';
import {
  batchDeleteChatMessages,
  deleteChatMessage,
  exportChatMessage,
  getChatMessage,
  getChatMessages,
  importChatMessage,
  openChatMessageFolder,
} from '@/api/ai';
import { apiClient, API_ROUTES } from '@/router/api_routes.js';

const router = useRouter();
const messages = ref([]);
const loading = ref(false);
const loadingMore = ref(false);
const hasMore = ref(true);
const page = ref(0);
const PAGE_SIZE = 30;
const scrollContainer = ref(null);
const isSelectMode = ref(false);
const selectedIds = ref([]);
const sortBy = ref('created_time');
const sortOrder = ref('desc');
const handlingOnly = ref(false);
const importInput = ref(null);
const favoritesMap = ref({});
const historyMode = ref('document');
const agentConversations = ref([]);

const isAllSelected = computed(() => {
  return messages.value.length > 0 && selectedIds.value.length === messages.value.length;
});

const formatName = (text) => {
  if (!text) return '未命名文档';
  const cleanText = text.replace(/\s+/g, ' ');
  return cleanText.length > 20 ? cleanText.substring(0, 20) : cleanText;
};

const formatDate = (dateString) => {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
};

const getDifficultyLabel = (msg) => {
  const analysis = msg.chat_analysis || {};
  const values = [
    analysis.language_complexity,
    analysis.handling_complexity,
    analysis.risk_level,
  ].filter(Boolean);
  if (values.includes('高')) return '高';
  if (values.includes('中')) return '中';
  return values[0] || '低';
};

const fetchMessages = async (reset = true) => {
  if (reset) {
    loading.value = true;
    page.value = 0;
    hasMore.value = true;
    messages.value = [];
  } else {
    if (loadingMore.value || !hasMore.value) return;
    loadingMore.value = true;
  }
  try {
    const res = await getChatMessages({
      sort_by: sortBy.value,
      sort_order: sortOrder.value,
      handling_only: handlingOnly.value,
      limit: PAGE_SIZE,
      offset: page.value * PAGE_SIZE,
    });
    const newItems = res.data || [];
    if (reset) {
      messages.value = newItems;
    } else {
      messages.value.push(...newItems);
    }
    if (newItems.length < PAGE_SIZE) hasMore.value = false;
    page.value++;
  } catch (error) {
    console.error('获取历史记录失败:', error);
  } finally {
    loading.value = false;
    loadingMore.value = false;
  }
};

const handleScroll = () => {
  const el = scrollContainer.value;
  if (!el) return;
  if (el.scrollTop + el.clientHeight >= el.scrollHeight - 100) {
    fetchMessages(false);
  }
};

const fetchAgentConversations = async () => {
  loading.value = true;
  try {
    const res = await apiClient.get(API_ROUTES.AGENT_CONVERSATIONS);
    agentConversations.value = res.data || [];
  } catch (error) {
    console.error('获取智能体对话失败:', error);
  } finally {
    loading.value = false;
  }
};

const fetchFavorites = async () => {
  try {
    const res = await apiClient.get(API_ROUTES.FAVORITE);
    const map = {};
    (res.data || []).forEach((fav) => {
      map[fav.chat_message_id] = fav;
    });
    favoritesMap.value = map;
  } catch (error) {
    console.warn('加载收藏失败', error);
  }
};

const isFavorited = (id) => Boolean(favoritesMap.value[id]);

const toggleFavorite = async (msg) => {
  if (!msg?.id) return;
  const existing = favoritesMap.value[msg.id];
  try {
    if (existing) {
      await apiClient.delete(`${API_ROUTES.FAVORITE}${existing.id}`);
      const nextMap = { ...favoritesMap.value };
      delete nextMap[msg.id];
      favoritesMap.value = nextMap;
    } else {
      const res = await apiClient.post(`${API_ROUTES.FAVORITE}?chat_message_id=${msg.id}`);
      favoritesMap.value = { ...favoritesMap.value, [msg.id]: res.data };
    }
  } catch (error) {
    console.warn('收藏操作失败', error);
  }
};

const applySort = (nextSortBy, nextOrder) => {
  sortBy.value = nextSortBy;
  sortOrder.value = nextOrder;
  fetchMessages(true);
};

const toggleHandlingOnly = () => {
  handlingOnly.value = !handlingOnly.value;
  fetchMessages(true);
};

const switchMode = (mode) => {
  historyMode.value = mode;
  isSelectMode.value = false;
  clearSelection();
  if (mode === 'agent') {
    fetchAgentConversations();
  } else {
    fetchMessages(true);
  }
};

const triggerImport = () => {
  importInput.value?.click();
};

const handleImport = async (event) => {
  const file = event.target.files?.[0];
  if (!file) return;
  try {
    const res = await importChatMessage(file);
    sessionStorage.setItem('restoredChatMessage', JSON.stringify(res.data));
    await fetchMessages();
    router.push('/home');
  } catch (error) {
    alert(error.response?.data?.detail || '导入失败');
  } finally {
    event.target.value = '';
  }
};

const downloadBlob = (blob, filename) => {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};

const handleExport = async (id) => {
  try {
    const res = await exportChatMessage(id);
    downloadBlob(res.data, `chat_${id}.json`);
  } catch (error) {
    alert(error.response?.data?.detail || '导出失败');
  }
};

const restoreMessage = async (id) => {
  try {
    const res = await getChatMessage(id);
    sessionStorage.setItem('restoredChatMessage', JSON.stringify(res.data));
    router.push('/home');
  } catch (error) {
    alert(error.response?.data?.detail || '恢复失败');
  }
};

const handleOpenFolder = async (id) => {
  try {
    const res = await openChatMessageFolder(id);
    if (!res.data.opened && res.data.path) {
      alert(`无法直接打开目录，路径为：${res.data.path}`);
    }
  } catch (error) {
    alert(error.response?.data?.detail || '打开目录失败');
  }
};

const handleDelete = async (id) => {
  try {
    await deleteChatMessage(id);
    messages.value = messages.value.filter((msg) => msg.id !== id);
    selectedIds.value = selectedIds.value.filter((selectedId) => selectedId !== id);
  } catch (error) {
    alert(error.response?.data?.detail || '删除失败');
  }
};

const toggleSelectMode = () => {
  isSelectMode.value = !isSelectMode.value;
  if (!isSelectMode.value) clearSelection();
};

const toggleSelectAll = () => {
  if (isAllSelected.value) {
    selectedIds.value = [];
  } else {
    selectedIds.value = messages.value.map((msg) => msg.id);
  }
};

const handleRowClick = (id) => {
  if (!isSelectMode.value) {
    restoreMessage(id);
    return;
  }

  const index = selectedIds.value.indexOf(id);
  if (index === -1) {
    selectedIds.value.push(id);
  } else {
    selectedIds.value.splice(index, 1);
  }
};

const clearSelection = () => {
  selectedIds.value = [];
};

const handleBatchDelete = async () => {
  if (selectedIds.value.length === 0) return;
  try {
    await batchDeleteChatMessages(selectedIds.value);
    messages.value = messages.value.filter((msg) => !selectedIds.value.includes(msg.id));
    clearSelection();
    isSelectMode.value = false;
  } catch (error) {
    alert(error.response?.data?.detail || '批量删除失败');
  }
};

const openAgentConversation = (id) => {
  router.push({ path: '/agent', query: { conversation_id: id } });
};

onMounted(() => {
  fetchMessages();
  fetchFavorites();
});
</script>

<style scoped>
.history-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: var(--content-bg);
  position: relative;
  gap: 16px;
}

.fixed-header-area {
  margin: 16px 20px 0;
  padding: 18px 20px;
  background:
    radial-gradient(circle at top right, color-mix(in srgb, var(--color-accent-cool) 10%, transparent), transparent 42%),
    linear-gradient(160deg, color-mix(in srgb, var(--color-primary) 7%, var(--card-bg)), var(--card-bg));
  border: 1px solid color-mix(in srgb, var(--color-primary) 10%, var(--border-color));
  border-radius: 18px;
  box-shadow: 0 18px 34px color-mix(in srgb, var(--color-primary) 10%, transparent);
  z-index: 10;
  flex-shrink: 0;
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.page-title {
  font-size: 28px;
  font-weight: bold;
  margin-bottom: 20px;
  color: var(--color-text-dark);
}

.header-actions {
  display: flex;
  gap: 10px;
}

.import-btn {
  background: var(--color-primary);
  border: none;
  border-bottom: 3px solid var(--color-primary-dark);
  border-radius: 999px;
  color: #fff;
  padding: 7px 18px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s;
}

.import-btn:hover {
  background: var(--color-primary-light);
  border-bottom-color: var(--color-primary);
}

.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-top: 14px;
  margin-bottom: 14px;
}

.filter-section {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 15px;
  min-width: 0;
}

.filter-label {
  font-size: 14px;
  color: var(--text-secondary);
  font-weight: bold;
}

.tags-group {
  display: flex;
  gap: 10px;
}

.sort-tag {
  background-color: color-mix(in srgb, var(--color-primary) 7%, var(--card-bg));
  border: 1px solid color-mix(in srgb, var(--color-primary) 12%, var(--border-color));
  color: var(--text-secondary);
  padding: 6px 16px;
  border-radius: var(--border-radius-pill);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.sort-tag:hover {
  color: var(--text-primary);
  background: color-mix(in srgb, var(--color-primary) 12%, var(--card-bg));
}

.sort-tag.active {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: #fff;
  font-weight: bold;
}

.batch-action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background-color: color-mix(in srgb, var(--color-primary) 7%, var(--card-bg));
  border: 1px solid color-mix(in srgb, var(--color-primary) 12%, var(--border-color));
  color: var(--text-secondary);
  padding: 8px 16px;
  border-radius: var(--border-radius-pill);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.batch-action-btn:hover {
  color: var(--text-primary);
  background: color-mix(in srgb, var(--color-primary) 12%, var(--card-bg));
}

.batch-action-btn.active {
  background-color: var(--color-primary);
  color: #fff;
}

.table-header {
  display: flex;
  padding: 16px 18px 14px;
  border-bottom: 1px solid color-mix(in srgb, var(--border-color) 82%, transparent);
  font-weight: bold;
  color: var(--text-secondary);
  font-size: 13px;
  align-items: center;
}

.table-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
  margin: 0 20px 20px;
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 18px;
  box-shadow: 0 18px 34px color-mix(in srgb, var(--color-primary) 8%, transparent);
}

.scrollable-area {
  overflow-y: auto;
  padding: 0 18px 100px;
}

.table-row {
  display: flex;
  padding: 16px 0;
  border-bottom: 1px solid color-mix(in srgb, var(--border-color) 82%, transparent);
  align-items: center;
  font-size: 15px;
  transition: background-color 0.2s, box-shadow 0.2s ease, transform 0.2s ease;
  background-color: transparent;
  cursor: pointer;
}

.table-row.row-selected {
  background-color: color-mix(in srgb, var(--color-primary) 7%, var(--card-bg));
}

.table-row:hover {
  background-color: color-mix(in srgb, var(--color-primary) 4%, var(--card-bg));
}

.col-checkbox {
  width: 40px;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-shrink: 0;
}

.custom-checkbox {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 1px solid color-mix(in srgb, var(--border-color) 72%, var(--text-muted));
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  color: transparent;
}

.custom-checkbox.checked {
  background-color: var(--color-primary);
  border-color: var(--color-primary);
  color: #fff;
}

.col-name {
  flex: 3;
  padding-right: 20px;
  padding-left: 5px;
}
.col-type { flex: 1; }
.col-model { flex: 1; }
.col-time {
  flex: 1.5;
  color: var(--text-secondary);
  font-size: 14px;
}
.col-actions {
  flex: 1.4;
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  flex-wrap: wrap;
}

.text-ellipsis {
  white-space: nowrap;
  overflow: hidden;
  color: var(--text-primary);
  font-weight: bold;
}

.type-text {
  color: var(--text-secondary);
}

.model-badge {
  background-color: color-mix(in srgb, var(--color-primary) 12%, var(--card-bg));
  color: var(--color-primary-dark);
  padding: 4px 12px;
  border-radius: var(--border-radius-pill);
  font-size: 12px;
  font-weight: bold;
}

.icon-btn {
  background: color-mix(in srgb, var(--color-primary) 6%, var(--card-bg));
  border: 1px solid color-mix(in srgb, var(--color-primary) 10%, var(--border-color));
  cursor: pointer;
  padding: 6px 10px;
  border-radius: 999px;
  transition: transform 0.2s, color 0.2s;
  color: var(--text-secondary);
  font-size: 12px;
}

.icon-btn:hover {
  transform: translateY(-1px);
  color: var(--text-primary);
  border-color: var(--color-primary);
}

.favorite-btn.active {
  color: #f1c40f;
}

.delete-btn:hover {
  color: #f44336;
}

.floating-action-bar {
  position: absolute;
  bottom: 40px;
  left: 50%;
  transform: translateX(-50%) translateY(100px);
  opacity: 0;
  transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  pointer-events: none;
  z-index: 100;
}

.floating-action-bar.show {
  transform: translateX(-50%) translateY(0);
  opacity: 1;
  pointer-events: auto;
}

.action-content {
  background-color: var(--card-bg);
  border-radius: 999px;
  padding: 10px 20px;
  display: flex;
  align-items: center;
  gap: 15px;
  box-shadow: 0 20px 34px rgba(0, 0, 0, 0.16);
  border: 1px solid var(--border-color);
}

.selected-count {
  font-size: 14px;
  font-weight: bold;
  color: var(--text-primary);
}

.divider {
  color: var(--text-muted);
  font-size: 16px;
}

.empty-state-centered {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: var(--text-secondary);
  font-size: 14px;
}

@keyframes slideInDown {
  from { opacity: 0; transform: translateY(-16px); }
  to   { opacity: 1; transform: translateY(0); }
}

.slide-in {
  animation: slideInDown 0.35s ease both;
}

@media (max-width: 960px) {
  .top-bar {
    flex-direction: column;
    align-items: stretch;
  }

  .multi-select-actions {
    align-self: flex-start;
  }
}

@media (max-width: 768px) {
  .history-container {
    gap: 14px;
  }

  .fixed-header-area {
    margin: 14px 14px 0;
    padding: 16px;
  }

  .header-section {
    flex-direction: column;
    align-items: stretch;
  }

  .header-actions {
    width: 100%;
  }

  .import-btn {
    width: 100%;
  }

  .filter-section,
  .tags-group {
    gap: 8px;
  }

  .table-header {
    display: none;
  }

  .table-container {
    margin: 0 14px 18px;
  }

  .scrollable-area {
    padding: 10px 14px 92px;
  }

  .table-row {
    display: grid;
    grid-template-columns: 1fr;
    gap: 10px;
    padding: 14px 0;
  }

  .col-checkbox {
    width: auto;
    justify-content: flex-start;
    order: -1;
  }

  .col-name,
  .col-type,
  .col-model,
  .col-time,
  .col-actions {
    width: 100%;
    flex: none;
    padding: 0;
  }

  .col-type,
  .col-model,
  .col-time {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    font-size: 13px;
  }

  .col-type::before,
  .col-model::before,
  .col-time::before,
  .col-actions::before {
    content: attr(data-label);
    color: var(--text-secondary);
    font-size: 12px;
    font-weight: 600;
  }

  .col-actions {
    justify-content: flex-start;
    padding-top: 2px;
  }

  .col-actions::before {
    width: 100%;
  }

  .text-ellipsis {
    white-space: normal;
  }

  .action-content {
    gap: 10px;
    padding: 10px 14px;
  }
}
</style>
