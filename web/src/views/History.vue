<template>
  <div class="history-container">
    <!-- 固定的头部和控制栏 -->
    <div class="fixed-header-area">
      <div class="header-section">
        <h1 class="page-title">会话历史</h1>
      </div>

      <!-- 顶部操作栏与过滤区 -->
      <div class="top-bar">
        <div class="filter-section">
          <span class="filter-label">排序方式:</span>
          <div class="tags-group">
            <span class="sort-tag active">按时间降序</span>
            <span class="sort-tag">按复杂度</span>
            <span class="sort-tag">仅看办理类</span>
          </div>
        </div>

        <!-- 多选操作组 -->
        <div class="multi-select-actions">
          <button class="batch-action-btn" @click="toggleSelectMode" :class="{ 'active': isSelectMode }">
            <svg v-if="!isSelectMode" viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" class="css-i6dzq1"><polyline points="9 11 12 14 22 4"></polyline><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path></svg>
            <span v-if="!isSelectMode">多选</span>
            <span v-else>取消多选</span>
          </button>
        </div>
      </div>

      <!-- 固定的表头 -->
      <div class="table-header">
        <div class="col-checkbox" v-show="isSelectMode">
          <div class="custom-checkbox" :class="{ 'checked': isAllSelected }" @click="toggleSelectAll">
            <svg v-if="isAllSelected" viewBox="0 0 24 24" width="12" height="12" stroke="currentColor" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
          </div>
        </div>
        <div class="col-name">任务名称</div>
        <div class="col-type">类型</div>
        <div class="col-model">模型</div>
        <div class="col-time">创建时间</div>
        <div class="col-actions">操作</div>
      </div>
    </div>

    <!-- 可滚动的列表区 -->
    <div class="table-container scrollable-area">
      <!-- 当没有记录或加载中时，这个绝对居中的块会显示 -->
      <div v-if="loading" class="empty-state-centered">
        <span>加载中...</span>
      </div>
      <div v-else-if="messages.length === 0" class="empty-state-centered">
        <span>无记录</span>
      </div>

      <div v-else class="table-body">
        <div v-for="msg in messages" :key="msg.id" class="table-row" :class="{ 'row-selected': selectedIds.includes(msg.id) }" @click="handleRowClick(msg.id)">
          <div class="col-checkbox" v-show="isSelectMode">
            <div class="custom-checkbox" :class="{ 'checked': selectedIds.includes(msg.id) }">
              <svg v-if="selectedIds.includes(msg.id)" viewBox="0 0 24 24" width="12" height="12" stroke="currentColor" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
            </div>
          </div>
          <div class="col-name text-ellipsis" :title="msg.original_text">
            {{ formatName(msg.original_text) }}
          </div>
          <div class="col-type">
            <span class="type-text">文档</span>
          </div>
          <div class="col-model">
            <span class="model-badge">MOONSHOT</span>
          </div>
          <div class="col-time">{{ formatDate(msg.created_time) }}</div>
          <div class="col-actions" @click.stop>
            <button class="icon-btn" title="打开原文件" @click="handleOpenFolder(msg.id)">
              <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>
            </button>
            <button class="icon-btn delete-btn" title="删除记录" @click="handleDelete(msg.id)">
              <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 悬浮批量操作栏 -->
    <div class="floating-action-bar" :class="{ 'show': isSelectMode && selectedIds.length > 0 }">
      <div class="action-content">
        <span class="selected-count">已选择 {{ selectedIds.length }} 项</span>
        <span class="divider">|</span>
        <button class="icon-btn batch-delete-btn" title="批量删除" @click="handleBatchDelete">
          <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
        </button>
        <button class="icon-btn close-action-btn" title="取消选择" @click="clearSelection">
          <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { getChatMessages, deleteChatMessage, batchDeleteChatMessages } from '@/api/ai';

const messages = ref([]);
const loading = ref(false);

// 多选状态
const isSelectMode = ref(false);
const selectedIds = ref([]);

// 计算属性：是否全选
const isAllSelected = computed(() => {
  return messages.value.length > 0 && selectedIds.value.length === messages.value.length;
});

// 格式化名称：取原文前 20 个字符，不使用省略号
const formatName = (text) => {
  if (!text) return '未命名文档';
  const cleanText = text.replace(/\s+/g, ' ');
  return cleanText.length > 20 ? cleanText.substring(0, 20) : cleanText;
};

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
};

const fetchMessages = async () => {
  loading.value = true;
  try {
    const res = await getChatMessages();
    messages.value = res.data.sort((a, b) => new Date(b.created_time) - new Date(a.created_time));
  } catch (error) {
    console.error('获取历史记录失败:', error);
  } finally {
    loading.value = false;
  }
};

// --- 操作逻辑 ---

const handleOpenFolder = (id) => {
  alert(`占位功能：准备打开记录 ID ${id} 对应的文件或详情`);
};

const handleDelete = async (id) => {
  try {
    await deleteChatMessage(id);
    messages.value = messages.value.filter(msg => msg.id !== id);
    // 如果该项被选中，从选中列表中移除
    selectedIds.value = selectedIds.value.filter(selectedId => selectedId !== id);
  } catch (error) {
    console.error('删除失败:', error);
    alert('删除失败');
  }
};

// --- 多选逻辑 ---

const toggleSelectMode = () => {
  isSelectMode.value = !isSelectMode.value;
  if (!isSelectMode.value) {
    clearSelection();
  }
};

const toggleSelectAll = () => {
  if (isAllSelected.value) {
    selectedIds.value = [];
  } else {
    selectedIds.value = messages.value.map(msg => msg.id);
  }
};

const handleRowClick = (id) => {
  if (!isSelectMode.value) return;

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
    // 从前端列表中移除已删除的项
    messages.value = messages.value.filter(msg => !selectedIds.value.includes(msg.id));
    clearSelection();
    isSelectMode.value = false;
  } catch (error) {
    console.error('批量删除失败:', error);
    alert('批量删除失败');
  }
};

onMounted(() => {
  fetchMessages();
});
</script>

<style scoped>
.history-container {
  display: flex;
  flex-direction: column;
  height: 100%; /* 占满父容器高度 */
  background-color: var(--content-bg);
  position: relative;
}

/* 固定头部区域 */
.fixed-header-area {
  padding: 30px 30px 0 30px; /* 顶部和左右内边距，底部无 */
  background-color: var(--content-bg); /* 确保背景色覆盖可能出现的滚动内容 */
  z-index: 10; /* 保证在滚动内容之上 */
  flex-shrink: 0; /* 防止被挤压 */
}

.page-title {
  font-size: 28px;
  font-weight: bold;
  margin-bottom: 20px;
  color: var(--color-text-dark);
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

.sort-tag:hover {
  opacity: 0.8;
}

.sort-tag.active {
  font-weight: bold;
}

/* 多选按钮 */
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

.batch-action-btn:hover {
  background-color: #eee;
}

.batch-action-btn.active {
  background-color: #000;
  color: #fff;
}

/* 固定的表头 */
.table-header {
  display: flex;
  padding: 15px 0;
  border-bottom: 1px solid #eee;
  font-weight: bold;
  color: #999;
  font-size: 14px;
  align-items: center;
}

/* 表格主体及可滚动区域 */
.table-container {
  flex: 1; /* 占据剩余所有空间 */
  display: flex;
  flex-direction: column;
  position: relative; /* 为居中提供上下文 */
  overflow: hidden; /* 隐藏容器溢出，让子元素滚动 */
}

.scrollable-area {
  overflow-y: auto; /* 仅在此区域垂直滚动 */
  padding: 0 30px 100px 30px; /* 恢复左右内边距，底部留出空间给悬浮栏 */
}

.table-row {
  display: flex;
  padding: 15px 0;
  border-bottom: 1px solid #eee;
  align-items: center;
  font-size: 15px;
  transition: background-color 0.2s;
  background-color: var(--content-bg);
  cursor: default;
}

.table-row.row-selected {
  background-color: #f8f9fa; /* 选中时稍微给点底色区分 */
}

.table-row:last-child {
  border-bottom: none;
}

.table-row:hover {
  background-color: #fafafa;
}

/* 列宽分配 */
.col-checkbox {
  width: 40px; /* 固定宽度 */
  display: flex;
  justify-content: center;
  align-items: center;
  flex-shrink: 0;
}

/* 自定义复选框 UI */
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
  color: transparent; /* 默认不显示 SVG 颜色 */
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
.col-type {
  flex: 1;
}
.col-model {
  flex: 1;
}
.col-time {
  flex: 1.5;
  color: #666;
  font-size: 14px;
}
.col-actions {
  flex: 1;
  display: flex;
  gap: 15px;
  justify-content: flex-end;
}

/* 文本截断 */
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

/* 简约线条风操作按钮 */
.icon-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: transform 0.2s, color 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999; /* 默认浅灰色线条 */
}

.icon-btn:hover {
  transform: scale(1.1);
  color: #000; /* hover 变黑 */
}

.delete-btn:hover {
  color: #f44336; /* 删除按钮 hover 变红 */
}

/* 悬浮批量操作栏 */
.floating-action-bar {
  position: absolute; /* 改为基于父容器(history-container)定位 */
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
  border-radius: 30px; /* 胶囊形状 */
  padding: 10px 20px;
  display: flex;
  align-items: center;
  gap: 15px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15); /* 明确要求白色阴影悬浮胶囊 */
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

.batch-delete-btn {
  color: #666;
}
.batch-delete-btn:hover {
  color: #f44336;
}

.close-action-btn {
  color: #999;
}
.close-action-btn:hover {
  color: #000;
}

/* 空状态绝对居中 */
.empty-state-centered {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: #999;
  font-size: 14px;
}
</style>
