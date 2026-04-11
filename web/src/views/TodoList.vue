<template>
  <div class="todo-page">
    <div class="todo-header">
      <PolicyTitle title="办事进度中心" />
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
        <div v-for="(todo, index) in filteredTodos" :key="todo.id" class="todo-item fade-in-up" :style="{ animationDelay: `${index * 50}ms` }" :class="{ done: todo.is_done }">
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
import PolicyTitle from '@/components/common/PolicyTitle.vue';
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
.todo-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 16px 20px 24px;
  height: 100%;
  box-sizing: border-box;
  overflow-y: auto;
}

.todo-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.add-btn {
  background: var(--color-primary);
  color: #fff;
  border: none;
  border-bottom: 3px solid var(--color-primary-dark);
  border-radius: 999px;
  padding: 7px 18px; font-size: 13px; font-weight: 600;
  cursor: pointer; transition: all 0.2s;
}
.add-btn:hover { background: var(--color-primary-light); border-bottom-color: var(--color-primary); }

/* 草稿区 */
.draft-section {
  background: color-mix(in srgb, var(--color-primary) 6%, var(--card-bg));
  border: 1px solid color-mix(in srgb, var(--color-primary) 12%, var(--border-color));
  border-left: 3px solid var(--color-primary);
  border-radius: 18px;
  padding: 16px 18px;
  box-shadow: 0 14px 28px color-mix(in srgb, var(--color-primary) 8%, transparent);
}
.section-label-row { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.section-label { font-size: 13px; font-weight: 700; color: var(--color-primary-dark); }
.draft-hint { font-size: 11px; color: var(--text-muted); }
.draft-list { display: flex; flex-direction: column; gap: 8px; }
.draft-card {
  display: flex; align-items: flex-start; justify-content: space-between;
  background: var(--card-bg);
  border: 1px solid color-mix(in srgb, var(--color-primary) 10%, var(--border-color));
  border-radius: 14px;
  padding: 12px 14px;
  gap: 12px;
}
.draft-info { display: flex; flex-direction: column; gap: 3px; flex: 1; }
.draft-title { font-size: 13px; font-weight: 600; color: var(--text-primary); }
.draft-deadline { font-size: 11px; color: var(--color-secondary); }
.draft-detail { font-size: 11px; color: var(--text-secondary); margin: 0; }
.draft-actions { display: flex; gap: 8px; flex-shrink: 0; }

/* 主列表 */
.todo-main {
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 18px;
  padding: 16px 18px 18px;
  box-shadow: 0 18px 32px color-mix(in srgb, var(--color-primary) 8%, transparent);
}
.todo-filters {
  display: inline-flex;
  gap: 6px;
  padding: 4px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-primary) 7%, var(--card-bg));
  border: 1px solid color-mix(in srgb, var(--color-primary) 12%, var(--border-color));
  align-self: flex-start;
}
.todo-filters button {
  background: transparent;
  border: none;
  border-radius: 999px;
  padding: 6px 14px;
  font-size: 12px;
  cursor: pointer;
  color: var(--text-secondary);
  transition: all 0.2s;
}
.todo-filters button.active { background: var(--color-primary); color: #fff; font-weight: 700; }
.todo-loading, .todo-empty { text-align: center; color: var(--text-secondary); font-size: 13px; padding: 30px 0; }
.todo-list { display: flex; flex-direction: column; gap: 6px; }
.todo-item {
  display: flex; align-items: flex-start; gap: 12px;
  background: color-mix(in srgb, var(--color-primary) 3%, var(--card-bg));
  border: 1px solid color-mix(in srgb, var(--color-primary) 10%, var(--border-color));
  border-left: 3px solid var(--color-primary);
  border-radius: 14px;
  padding: 12px 14px;
  transition: opacity 0.2s, transform 0.2s ease, box-shadow 0.2s ease;
  opacity: 0;
}

.todo-item:hover {
  transform: translateY(-1px);
  box-shadow: 0 14px 24px color-mix(in srgb, var(--color-primary) 8%, transparent);
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(16px); }
  to   { opacity: 1; transform: translateY(0); }
}

.fade-in-up {
  animation: fadeInUp 0.35s ease both;
}
.todo-item.done { opacity: 0.7; border-left-color: color-mix(in srgb, var(--text-muted) 54%, var(--border-color)); }
.todo-check { cursor: pointer; flex-shrink: 0; margin-top: 2px; }
.check-empty {
  width: 18px; height: 18px; border: 2px solid color-mix(in srgb, var(--border-color) 80%, var(--text-muted));
  border-radius: 2px; transition: border-color 0.2s;
}
.todo-check:hover .check-empty { border-color: var(--color-primary); }
.todo-body { flex: 1; display: flex; flex-direction: column; gap: 3px; }
.todo-title { font-size: 13px; font-weight: 600; color: var(--text-primary); }
.todo-item.done .todo-title { text-decoration: line-through; color: var(--text-muted); }
.todo-deadline { font-size: 11px; color: var(--color-secondary); }
.todo-detail { font-size: 11px; color: var(--text-secondary); margin: 0; }
.todo-del {
  background: none; border: none; cursor: pointer;
  color: var(--text-muted); padding: 2px; flex-shrink: 0; transition: color 0.2s;
}
.todo-del:hover { color: var(--color-primary); }

/* 按钮 */
.confirm-btn {
  background: var(--color-primary); color: #fff; border: none;
  border-radius: 999px;
  padding: 7px 12px; font-size: 12px; cursor: pointer; transition: background 0.2s, transform 0.2s ease;
}
.confirm-btn:hover { background: var(--color-primary-light); transform: translateY(-1px); }
.confirm-btn:disabled { background: #ccc; cursor: not-allowed; }
.discard-btn {
  background: color-mix(in srgb, var(--border-color) 42%, var(--card-bg));
  color: var(--text-secondary);
  border: none;
  border-radius: 999px;
  padding: 7px 12px;
  font-size: 12px;
  cursor: pointer;
  transition: background 0.2s;
}
.discard-btn:hover { background: color-mix(in srgb, var(--border-color) 62%, var(--card-bg)); }

/* 弹窗 */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.3);
  display: flex; align-items: center; justify-content: center; z-index: 1000;
}
.modal {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 20px;
  box-shadow: 0 28px 54px rgba(0,0,0,0.24);
  padding: 24px; width: min(380px, calc(100vw - 28px));
  display: flex; flex-direction: column; gap: 12px;
}
.modal h3 { margin: 0; font-size: 16px; font-weight: 700; color: var(--text-primary); }
.modal-input, .modal-textarea {
  border: 1px solid var(--border-color); padding: 8px 12px;
  border-radius: 12px;
  background: color-mix(in srgb, var(--color-primary) 4%, var(--card-bg));
  font-size: 13px; outline: none; width: 100%; box-sizing: border-box;
  transition: border-color 0.2s;
  color: var(--text-primary);
}
.modal-input:focus, .modal-textarea:focus { border-color: var(--color-primary); }
.modal-textarea { height: 80px; resize: vertical; }
.modal-actions { display: flex; gap: 8px; justify-content: flex-end; }

@media (max-width: 768px) {
  .todo-page {
    padding: 14px 14px 24px;
  }

  .todo-header,
  .section-label-row,
  .draft-card {
    flex-direction: column;
    align-items: stretch;
  }

  .add-btn,
  .draft-actions,
  .modal-actions {
    width: 100%;
  }

  .draft-actions,
  .modal-actions {
    justify-content: stretch;
  }

  .draft-actions > button,
  .modal-actions > button {
    flex: 1 1 0;
  }

  .todo-main,
  .draft-section {
    padding: 16px;
  }

  .todo-filters {
    width: 100%;
    justify-content: space-between;
  }

  .todo-filters button {
    flex: 1 1 0;
    text-align: center;
  }

  .todo-item {
    gap: 10px;
  }
}
</style>
