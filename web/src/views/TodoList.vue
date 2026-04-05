<template>
  <div class="todo-page">
    <div class="todo-header">
      <h1 class="page-title">办事进度中心</h1>
      <button class="add-btn" @click="showAdd = true">+ 新建待办</button>
    </div>

    <!-- 草稿待确认区 -->
    <div v-if="drafts.length" class="draft-section">
      <div class="section-label-row">
        <span class="section-label">待确认草稿</span>
        <span class="draft-hint">来自 AI 解析，请确认后保存</span>
      </div>
      <div class="draft-list">
        <div v-for="d in drafts" :key="d.id" class="draft-card">
          <div class="draft-info">
            <span class="draft-title">{{ d.title }}</span>
            <span v-if="d.deadline" class="draft-deadline">截止：{{ d.deadline }}</span>
            <p v-if="d.detail" class="draft-detail">{{ d.detail }}</p>
          </div>
          <div class="draft-actions">
            <button class="confirm-btn" @click="confirmDraft(d.id)">确认保存</button>
            <button class="discard-btn" @click="deleteTodo(d.id)">废弃</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 主 Todo 列表 -->
    <div class="todo-main">
      <div class="todo-filters">
        <button :class="{ active: filter === 'all' }" @click="filter = 'all'">全部</button>
        <button :class="{ active: filter === 'pending' }" @click="filter = 'pending'">待完成</button>
        <button :class="{ active: filter === 'done' }" @click="filter = 'done'">已完成</button>
      </div>
      <div v-if="loading" class="todo-loading">加载中...</div>
      <div v-else-if="filteredTodos.length === 0" class="todo-empty">暂无待办事项</div>
      <div v-else class="todo-list">
        <div v-for="todo in filteredTodos" :key="todo.id" class="todo-item" :class="{ done: todo.is_done }">
          <div class="todo-check" @click="toggleTodo(todo.id)">
            <svg v-if="todo.is_done" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="#c0392b" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
            <div v-else class="check-empty"></div>
          </div>
          <div class="todo-body">
            <span class="todo-title">{{ todo.title }}</span>
            <span v-if="todo.deadline" class="todo-deadline">{{ todo.deadline }}</span>
            <p v-if="todo.detail" class="todo-detail">{{ todo.detail }}</p>
          </div>
          <button class="todo-del" @click="deleteTodo(todo.id)">
            <svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        </div>
      </div>
    </div>

    <!-- 新建弹窗 -->
    <div v-if="showAdd" class="modal-overlay" @click.self="showAdd = false">
      <div class="modal">
        <h3>新建待办</h3>
        <input v-model="newTitle" placeholder="待办标题 *" class="modal-input" />
        <input v-model="newDeadline" placeholder="截止时间（如：2025-12-31）" class="modal-input" />
        <textarea v-model="newDetail" placeholder="详细说明（可选）" class="modal-textarea"></textarea>
        <div class="modal-actions">
          <button class="confirm-btn" @click="createTodo" :disabled="!newTitle.trim()">保存</button>
          <button class="discard-btn" @click="showAdd = false">取消</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { apiClient, API_ROUTES } from '@/router/api_routes.js';

const todos = ref([]);
const drafts = ref([]);
const loading = ref(true);
const filter = ref('all');
const showAdd = ref(false);
const newTitle = ref('');
const newDeadline = ref('');
const newDetail = ref('');

const filteredTodos = computed(() => {
  if (filter.value === 'pending') return todos.value.filter(t => !t.is_done);
  if (filter.value === 'done') return todos.value.filter(t => t.is_done);
  return todos.value;
});

onMounted(loadTodos);

async function loadTodos() {
  loading.value = true;
  try {
    const [confirmedRes, allRes] = await Promise.all([
      apiClient.get(API_ROUTES.TODO),
      apiClient.get(API_ROUTES.TODO + '?confirmed_only=false'),
    ]);
    todos.value = confirmedRes.data;
    drafts.value = allRes.data.filter(t => !t.is_confirmed);
  } catch (e) {
    console.warn('Todo 加载失败', e);
  } finally {
    loading.value = false;
  }
}

async function toggleTodo(id) {
  try {
    const res = await apiClient.patch(`/todo/${id}/toggle`);
    const idx = todos.value.findIndex(t => t.id === id);
    if (idx !== -1) todos.value[idx] = res.data;
  } catch (e) { console.warn(e); }
}

async function confirmDraft(id) {
  try {
    const res = await apiClient.patch(`/todo/${id}/confirm`);
    drafts.value = drafts.value.filter(d => d.id !== id);
    todos.value.unshift(res.data);
  } catch (e) { console.warn(e); }
}

async function deleteTodo(id) {
  try {
    await apiClient.delete(`/todo/${id}`);
    todos.value = todos.value.filter(t => t.id !== id);
    drafts.value = drafts.value.filter(d => d.id !== id);
  } catch (e) { console.warn(e); }
}

async function createTodo() {
  if (!newTitle.value.trim()) return;
  try {
    const params = new URLSearchParams({ title: newTitle.value });
    if (newDeadline.value) params.append('deadline', newDeadline.value);
    if (newDetail.value) params.append('detail', newDetail.value);
    const res = await apiClient.post(API_ROUTES.TODO + '?' + params.toString());
    todos.value.unshift(res.data);
    showAdd.value = false;
    newTitle.value = ''; newDeadline.value = ''; newDetail.value = '';
  } catch (e) { console.warn(e); }
}
</script>

<style scoped>
.todo-page { display: flex; flex-direction: column; gap: 16px; }
.todo-header { display: flex; align-items: center; justify-content: space-between; }
.page-title { font-size: 20px; font-weight: 800; color: #111; margin: 0; }
.add-btn {
  background: #c0392b; color: #fff; border: none;
  border-bottom: 3px solid #922b21; border-radius: 999px;
  padding: 7px 18px; font-size: 13px; font-weight: 600;
  cursor: pointer; transition: all 0.2s;
}
.add-btn:hover { background: #e74c3c; border-bottom-color: #c0392b; }

/* 草稿区 */
.draft-section { background: #fff8f8; border-left: 3px solid #e74c3c; padding: 12px 16px; }
.section-label-row { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.section-label { font-size: 13px; font-weight: 700; color: #c0392b; }
.draft-hint { font-size: 11px; color: #aaa; }
.draft-list { display: flex; flex-direction: column; gap: 8px; }
.draft-card {
  display: flex; align-items: flex-start; justify-content: space-between;
  background: #fff; border: 1px solid #f5c6c6; padding: 10px 14px; gap: 12px;
}
.draft-info { display: flex; flex-direction: column; gap: 3px; flex: 1; }
.draft-title { font-size: 13px; font-weight: 600; color: #222; }
.draft-deadline { font-size: 11px; color: #e67e22; }
.draft-detail { font-size: 11px; color: #888; margin: 0; }
.draft-actions { display: flex; gap: 8px; flex-shrink: 0; }

/* 主列表 */
.todo-main { display: flex; flex-direction: column; gap: 10px; }
.todo-filters { display: flex; gap: 6px; }
.todo-filters button {
  background: #fff; border: 2px solid #c0392b; border-radius: 999px;
  padding: 5px 14px; font-size: 12px; cursor: pointer; color: #c0392b; transition: all 0.2s;
}
.todo-filters button.active { background: #c0392b; color: #fff; }
.todo-loading, .todo-empty { text-align: center; color: #aaa; font-size: 13px; padding: 30px 0; }
.todo-list { display: flex; flex-direction: column; gap: 6px; }
.todo-item {
  display: flex; align-items: flex-start; gap: 12px;
  background: #fff; border: 1px solid #eee; border-left: 3px solid #c0392b;
  padding: 10px 14px; transition: opacity 0.2s;
}
.todo-item.done { opacity: 0.5; border-left-color: #bbb; }
.todo-check { cursor: pointer; flex-shrink: 0; margin-top: 2px; }
.check-empty {
  width: 18px; height: 18px; border: 2px solid #ddd;
  border-radius: 2px; transition: border-color 0.2s;
}
.todo-check:hover .check-empty { border-color: #c0392b; }
.todo-body { flex: 1; display: flex; flex-direction: column; gap: 3px; }
.todo-title { font-size: 13px; font-weight: 600; color: #222; }
.todo-item.done .todo-title { text-decoration: line-through; color: #aaa; }
.todo-deadline { font-size: 11px; color: #e67e22; }
.todo-detail { font-size: 11px; color: #888; margin: 0; }
.todo-del {
  background: none; border: none; cursor: pointer;
  color: #ccc; padding: 2px; flex-shrink: 0; transition: color 0.2s;
}
.todo-del:hover { color: #c0392b; }

/* 按钮 */
.confirm-btn {
  background: #c0392b; color: #fff; border: none;
  padding: 5px 12px; font-size: 12px; cursor: pointer; transition: background 0.2s;
}
.confirm-btn:hover { background: #e74c3c; }
.confirm-btn:disabled { background: #ccc; cursor: not-allowed; }
.discard-btn {
  background: #f5f5f5; color: #666; border: none;
  padding: 5px 12px; font-size: 12px; cursor: pointer; transition: background 0.2s;
}
.discard-btn:hover { background: #eee; }

/* 弹窗 */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.3);
  display: flex; align-items: center; justify-content: center; z-index: 1000;
}
.modal {
  background: #fff; padding: 24px; width: 380px;
  display: flex; flex-direction: column; gap: 12px;
}
.modal h3 { margin: 0; font-size: 16px; font-weight: 700; color: #111; }
.modal-input, .modal-textarea {
  border: 1px solid #e0e0e0; padding: 8px 12px;
  font-size: 13px; outline: none; width: 100%; box-sizing: border-box;
  transition: border-color 0.2s;
}
.modal-input:focus, .modal-textarea:focus { border-color: #c0392b; }
.modal-textarea { height: 80px; resize: vertical; }
.modal-actions { display: flex; gap: 8px; justify-content: flex-end; }
</style>
