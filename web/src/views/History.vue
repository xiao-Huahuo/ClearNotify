<template>
  <div class="history-container">
    <div class="fixed-header-area">
      <div class="header-section">
        <h1 class="page-title">会话历史</h1>
        <div class="header-actions">
          <button class="import-btn" @click="triggerImport">导入会话</button>
          <input ref="importInput" type="file" accept=".json,application/json" hidden @change="handleImport" />
        </div>
      </div>

      <div class="top-bar">
        <div class="filter-section">
          <span class="filter-label">排序方式:</span>
          <div class="tags-group">
            <span class="sort-tag" :class="{ active: sortBy === 'created_time' && sortOrder === 'desc' }" @click="applySort('created_time', 'desc')">按时间降序</span>
            <span class="sort-tag" :class="{ active: sortBy === 'difficulty' }" @click="applySort('difficulty', sortOrder === 'asc' ? 'desc' : 'asc')">按复杂度</span>
            <span class="sort-tag" :class="{ active: handlingOnly }" @click="toggleHandlingOnly">仅看办理类</span>
          </div>
        </div>

        <div class="multi-select-actions">
          <button class="batch-action-btn" @click="toggleSelectMode" :class="{ active: isSelectMode }">
            <span v-if="!isSelectMode">多选</span>
            <span v-else>取消多选</span>
          </button>
        </div>
      </div>

      <div class="table-header">
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
    </div>

    <div class="table-container scrollable-area">
      <div v-if="loading" class="empty-state-centered">
        <span>加载中...</span>
      </div>
      <div v-else-if="messages.length === 0" class="empty-state-centered">
        <span>无记录</span>
      </div>

      <div v-else class="table-body">
        <div
          v-for="msg in messages"
          :key="msg.id"
          class="table-row"
          :class="{ 'row-selected': selectedIds.includes(msg.id) }"
          @click="handleRowClick(msg.id)"
        >
          <div class="col-checkbox" v-show="isSelectMode">
            <div class="custom-checkbox" :class="{ checked: selectedIds.includes(msg.id) }">
              <svg v-if="selectedIds.includes(msg.id)" viewBox="0 0 24 24" width="12" height="12" stroke="currentColor" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
            </div>
          </div>
          <div class="col-name text-ellipsis" :title="msg.original_text">
            {{ formatName(msg.original_text) }}
          </div>
          <div class="col-type">
            <span class="type-text">{{ msg.chat_analysis?.notice_type || '文档' }}</span>
          </div>
          <div class="col-model">
            <span class="model-badge">{{ getDifficultyLabel(msg) }}</span>
          </div>
          <div class="col-time">{{ formatDate(msg.created_time) }}</div>
          <div class="col-actions" @click.stop>
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
    </div>

    <div class="floating-action-bar" :class="{ show: isSelectMode && selectedIds.length > 0 }">
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
const isSelectMode = ref(false);
const selectedIds = ref([]);
const sortBy = ref('created_time');
const sortOrder = ref('desc');
const handlingOnly = ref(false);
const importInput = ref(null);
const favoritesMap = ref({});

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

const fetchMessages = async () => {
  loading.value = true;
  try {
    const res = await getChatMessages({
      sort_by: sortBy.value,
      sort_order: sortOrder.value,
      handling_only: handlingOnly.value,
    });
    messages.value = res.data;
  } catch (error) {
    console.error('获取历史记录失败:', error);
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
  fetchMessages();
};

const toggleHandlingOnly = () => {
  handlingOnly.value = !handlingOnly.value;
  fetchMessages();
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
    router.push('/');
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
    router.push('/');
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
}

.fixed-header-area {
  padding: 30px 30px 0 30px;
  background-color: var(--content-bg);
  z-index: 10;
  flex-shrink: 0;
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
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
  border: 1px solid #ddd;
  background: #fff;
  color: #333;
  padding: 8px 14px;
  cursor: pointer;
}

.import-btn:hover {
  border-color: #c0392b;
  color: #c0392b;
}

.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.filter-section {
  display: flex;
  align-items: center;
  gap: 15px;
}

.filter-label {
  font-size: 14px;
  color: #666;
  font-weight: bold;
}

.tags-group {
  display: flex;
  gap: 10px;
}

.sort-tag {
  background-color: #f5f5f5;
  color: #666;
  padding: 6px 16px;
  border-radius: var(--border-radius-pill);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.sort-tag.active {
  background: #c0392b;
  color: #fff;
  font-weight: bold;
}

.batch-action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background-color: #f5f5f5;
  color: #666;
  border: none;
  padding: 8px 16px;
  border-radius: var(--border-radius-pill);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.batch-action-btn.active {
  background-color: #000;
  color: #fff;
}

.table-header {
  display: flex;
  padding: 15px 0;
  border-bottom: 1px solid #eee;
  font-weight: bold;
  color: #999;
  font-size: 14px;
  align-items: center;
}

.table-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}

.scrollable-area {
  overflow-y: auto;
  padding: 0 30px 100px 30px;
}

.table-row {
  display: flex;
  padding: 15px 0;
  border-bottom: 1px solid #eee;
  align-items: center;
  font-size: 15px;
  transition: background-color 0.2s;
  background-color: var(--content-bg);
  cursor: pointer;
}

.table-row.row-selected {
  background-color: #f8f9fa;
}

.table-row:hover {
  background-color: #fafafa;
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
  border: 1px solid #ccc;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  color: transparent;
}

.custom-checkbox.checked {
  background-color: #c0392b;
  border-color: #c0392b;
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
  color: #666;
  font-size: 14px;
}
.col-actions {
  flex: 1.4;
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.text-ellipsis {
  white-space: nowrap;
  overflow: hidden;
  color: #000;
  font-weight: bold;
}

.type-text {
  color: #555;
}

.model-badge {
  background-color: #000;
  color: #fff;
  padding: 4px 12px;
  border-radius: var(--border-radius-pill);
  font-size: 12px;
  font-weight: bold;
}

.icon-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: transform 0.2s, color 0.2s;
  color: #999;
}

.icon-btn:hover {
  transform: scale(1.05);
  color: #000;
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
  background-color: #fff;
  border-radius: 30px;
  padding: 10px 20px;
  display: flex;
  align-items: center;
  gap: 15px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  border: 1px solid #f0f0f0;
}

.selected-count {
  font-size: 14px;
  font-weight: bold;
  color: #000;
}

.divider {
  color: #ddd;
  font-size: 16px;
}

.empty-state-centered {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: #999;
  font-size: 14px;
}
</style>
