<template>
  <div class="history-page">
    <section class="history-hero">
      <div class="hero-copy">
        <PolicyTitle
          title="统一历史"
          subtitle="解析、搜索、政策、文章与智能体行为统一归档"
        />
        <p class="hero-desc">
          这里展示可恢复、可检索、可回看的历史事件流。现在历史页顶部搜索也接入了 Trie 前缀联想和 RAG 语义召回。
        </p>
      </div>

      <div class="hero-actions">
        <button class="capsule-btn primary" type="button" @click="triggerImport">
          导入解析
        </button>
        <button class="capsule-btn" type="button" :disabled="loading" @click="refreshAll">
          刷新
        </button>
        <input
          ref="importInput"
          type="file"
          accept=".json,application/json"
          hidden
          @change="handleImport"
        />
      </div>
    </section>

    <section v-if="!userStore.token" class="empty-shell">
      <div class="empty-card">
        <h3>登录后查看完整历史</h3>
        <p>统一历史依赖个人账户，用于恢复解析、回到智能体会话、回看政策与检索记录。</p>
      </div>
    </section>

    <template v-else>
      <section class="toolbar-card">
        <div class="search-box">
          <UnifiedSearchBox
            v-model="keyword"
            v-model:types="searchTypes"
            size="compact"
            source="history_search_dropdown"
            placeholder="搜索历史标题、摘要、政策、文章、智能体..."
            @submit="handleHistorySearchSubmit"
          />
        </div>

        <div class="toolbar-meta">
          <span>总计 {{ facetTotal }} 条</span>
          <span v-if="activeDomain !== 'all'">当前分类：{{ getDomainLabel(activeDomain) }}</span>
        </div>
      </section>

      <section class="facet-bar">
        <button
          type="button"
          class="facet-chip"
          :class="{ active: activeDomain === 'all' }"
          @click="setDomain('all')"
        >
          全部
          <span>{{ facetTotal }}</span>
        </button>
        <button
          v-for="facet in orderedFacets"
          :key="facet.domain"
          type="button"
          class="facet-chip"
          :class="{ active: activeDomain === facet.domain }"
          @click="setDomain(facet.domain)"
        >
          {{ getDomainLabel(facet.domain) }}
          <span>{{ facet.count }}</span>
        </button>
      </section>

      <section ref="scrollContainer" class="history-list" @scroll="handleScroll">
        <div v-if="loading && !events.length" class="empty-shell">
          <div class="empty-card">加载中...</div>
        </div>

        <div v-else-if="!events.length" class="empty-shell">
          <div class="empty-card">
            <h3>暂无符合条件的历史</h3>
            <p>可以尝试切换分类，或缩短检索关键词。</p>
          </div>
        </div>

        <article
          v-for="event in events"
          :key="event.id"
          class="history-card"
          @click="openEvent(event)"
        >
          <div class="card-head">
            <div class="chip-row">
              <span class="chip domain">{{ getDomainLabel(event.domain) }}</span>
              <span class="chip event">{{ getEventLabel(event.event_type) }}</span>
              <span v-if="event.status" class="chip status">{{ getStatusLabel(event.status) }}</span>
              <span v-if="event.is_restorable" class="chip restore">可恢复</span>
            </div>
            <time class="time-text">{{ formatDate(event.occurred_time || event.created_time) }}</time>
          </div>

          <h3 class="card-title">{{ event.title || '未命名历史事件' }}</h3>
          <p v-if="event.subtitle" class="card-subtitle">{{ event.subtitle }}</p>
          <p v-if="getSummaryText(event)" class="card-summary">
            {{ getSummaryText(event) }}
          </p>

          <div class="card-meta">
            <span v-if="event.external_url">{{ getDomainHost(event.external_url) }}</span>
            <span v-else-if="event.route_path">{{ event.route_path }}</span>
            <span v-if="event.extra?.query">检索词：{{ event.extra.query }}</span>
          </div>

          <div class="card-actions" @click.stop>
            <button class="action-btn primary" type="button" @click="openEvent(event)">
              {{ getPrimaryActionLabel(event) }}
            </button>
            <button
              v-if="canExportEvent(event)"
              class="action-btn"
              type="button"
              @click="exportEvent(event)"
            >
              导出 JSON
            </button>
            <button
              v-if="event.external_url"
              class="action-btn"
              type="button"
              @click="openExternal(event.external_url)"
            >
              打开来源
            </button>
          </div>
        </article>

        <div v-if="loadingMore" class="feed-status">加载更多...</div>
        <div v-else-if="!hasMore && events.length" class="feed-status">已加载全部历史</div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import PolicyTitle from '@/components/common/PolicyTitle.vue';
import UnifiedSearchBox from '@/components/common/UnifiedSearchBox.vue';
import { useUserStore } from '@/stores/auth.js';
import { exportChatMessage, getChatMessage, importChatMessage } from '@/api/ai';
import { getHistoryFacets, getHistoryFeed } from '@/api/history';

const router = useRouter();
const userStore = useUserStore();

const PAGE_SIZE = 20;

const events = ref([]);
const loading = ref(false);
const loadingMore = ref(false);
const hasMore = ref(true);
const skip = ref(0);
const keyword = ref('');
const searchTypes = ref([]);
const activeDomain = ref('all');
const scrollContainer = ref(null);
const importInput = ref(null);
const facetState = ref({ total: 0, items: [] });

const DOMAIN_LABELS = {
  all: '全部',
  document_parse: '解析记录',
  agent_chat: '智能体对话',
  policy_publish: '政策发布',
  policy_browse: '政策浏览',
  article_browse: '文章浏览',
  search: '搜索记录',
  favorite: '收藏记录',
  todo: '待办记录',
};

const EVENT_LABELS = {
  created: '创建',
  imported: '导入',
  updated: '更新',
  rewritten: '改写',
  deleted: '删除',
  batch_deleted: '批量删除',
  exported: '导出',
  continued: '继续对话',
  viewed: '浏览',
  searched: '搜索',
  approved: '已通过',
  rejected: '已驳回',
  added: '加入',
  removed: '移除',
  confirmed: '确认',
  completed: '完成',
  reopened: '重开',
  opened_external: '外链打开',
  result_clicked: '点击结果',
};

const STATUS_LABELS = {
  approved: '已通过',
  rejected: '已驳回',
  pending: '待审核',
  done: '已完成',
  confirmed: '已确认',
  draft: '草稿',
};

const facetTotal = computed(() => facetState.value.total || 0);
const orderedFacets = computed(() => facetState.value.items || []);

const getDomainLabel = (domain) => DOMAIN_LABELS[domain] || domain || '未分类';
const getEventLabel = (eventType) => EVENT_LABELS[eventType] || eventType || '事件';
const getStatusLabel = (status) => STATUS_LABELS[status] || status;

const formatDate = (value) => {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
};

const getSummaryText = (event) => event.summary || event.content_excerpt || '';

const getDomainHost = (url) => {
  try {
    return new URL(url).hostname.replace('www.', '');
  } catch {
    return '';
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

const loadFacets = async () => {
  if (!userStore.token) {
    facetState.value = { total: 0, items: [] };
    return;
  }

  try {
    const res = await getHistoryFacets();
    facetState.value = res.data || { total: 0, items: [] };
  } catch (error) {
    console.warn('加载历史分面失败', error);
    facetState.value = { total: 0, items: [] };
  }
};

const loadFeed = async (reset = true) => {
  if (!userStore.token) {
    events.value = [];
    hasMore.value = false;
    return;
  }

  if (reset) {
    loading.value = true;
    hasMore.value = true;
    skip.value = 0;
  } else {
    if (loading.value || loadingMore.value || !hasMore.value) return;
    loadingMore.value = true;
  }

  const nextSkip = reset ? 0 : skip.value;

  try {
    const res = await getHistoryFeed({
      domain: activeDomain.value,
      q: keyword.value.trim(),
      skip: nextSkip,
      limit: PAGE_SIZE,
    });
    const items = res.data || [];
    events.value = reset ? items : [...events.value, ...items];
    skip.value = nextSkip + items.length;
    hasMore.value = items.length === PAGE_SIZE;
  } catch (error) {
    console.warn('加载历史列表失败', error);
    if (reset) events.value = [];
    hasMore.value = false;
  } finally {
    loading.value = false;
    loadingMore.value = false;
  }
};

const refreshFeed = async () => {
  if (scrollContainer.value) scrollContainer.value.scrollTop = 0;
  await loadFeed(true);
};

const refreshAll = async () => {
  await Promise.all([loadFacets(), refreshFeed()]);
};

const handleHistorySearchSubmit = async ({ query, types }) => {
  keyword.value = query;
  searchTypes.value = types || [];
  await refreshFeed();
};

const setDomain = async (domain) => {
  if (activeDomain.value === domain) return;
  activeDomain.value = domain;
  await refreshFeed();
};

const handleScroll = () => {
  const el = scrollContainer.value;
  if (!el) return;
  if (el.scrollTop + el.clientHeight >= el.scrollHeight - 160) {
    void loadFeed(false);
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
    await refreshAll();
    router.push('/home');
  } catch (error) {
    alert(error.response?.data?.detail || '导入失败');
  } finally {
    event.target.value = '';
  }
};

const restoreChatMessage = async (messageId) => {
  const res = await getChatMessage(messageId);
  sessionStorage.setItem('restoredChatMessage', JSON.stringify(res.data));
  await router.push('/home');
};

const openExternal = (url) => {
  if (url) window.open(url, '_blank');
};

const getPrimaryActionLabel = (event) => {
  if (event.subject_type === 'chat_message') return '恢复解析';
  if (event.subject_type === 'agent_conversation') return '进入对话';
  if (event.subject_type === 'policy_document') return '查看政策';
  if (event.subject_type === 'search_query') return '重新搜索';
  if (event.subject_type === 'todo') return '查看待办';
  if (event.subject_type === 'favorite') return '查看收藏';
  if (event.external_url) return '打开来源';
  return '打开';
};

const canExportEvent = (event) =>
  event.subject_type === 'chat_message' && Boolean(event.subject_id);

const exportEvent = async (event) => {
  if (!event.subject_id) return;
  try {
    const res = await exportChatMessage(event.subject_id);
    downloadBlob(res.data, `chat_${event.subject_id}.json`);
  } catch (error) {
    alert(error.response?.data?.detail || '导出失败');
  }
};

const openEvent = async (event) => {
  try {
    if (event.subject_type === 'chat_message' && event.subject_id) {
      await restoreChatMessage(event.subject_id);
      return;
    }

    if (event.subject_type === 'agent_conversation') {
      const conversationId = event.subject_id || event.extra?.conversation_id;
      if (!conversationId) return;
      await router.push({ path: '/agent', query: { conversation_id: String(conversationId) } });
      return;
    }

    if (event.subject_type === 'policy_document') {
      const docId = event.subject_id || event.extra?.policy_document_id;
      if (!docId) return;
      await router.push({ path: '/policy-swipe', query: { doc_id: String(docId) } });
      return;
    }

    if (event.subject_type === 'search_query') {
      const query = event.extra?.query || event.title;
      const types = Array.isArray(event.extra?.types) && event.extra.types.length
        ? { types: event.extra.types.join(',') }
        : {};
      await router.push({ path: '/search', query: { q: query, ...types } });
      return;
    }

    if (event.subject_type === 'todo') {
      await router.push('/todo');
      return;
    }

    if (event.subject_type === 'favorite') {
      await router.push('/favorites');
      return;
    }

    if (event.route_path) {
      await router.push(event.route_path);
      return;
    }

    if (event.external_url) {
      openExternal(event.external_url);
    }
  } catch (error) {
    alert(error.response?.data?.detail || '打开历史失败');
  }
};

watch(
  () => userStore.token,
  async (token) => {
    if (!token) {
      events.value = [];
      facetState.value = { total: 0, items: [] };
      hasMore.value = false;
      return;
    }
    await refreshAll();
  }
);

onMounted(async () => {
  if (userStore.token) {
    await refreshAll();
  }
});
</script>

<style scoped>
.history-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 16px;
  padding: 18px 20px 20px;
  background: var(--content-bg);
}

.history-hero,
.toolbar-card,
.facet-bar,
.history-list {
  border-radius: 22px;
}

.history-hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  padding: 22px 24px;
  background:
    radial-gradient(circle at top right, color-mix(in srgb, var(--color-accent-cool) 14%, transparent), transparent 42%),
    linear-gradient(155deg, color-mix(in srgb, var(--color-primary) 9%, var(--card-bg)), var(--card-bg));
  border: 1px solid color-mix(in srgb, var(--color-primary) 14%, var(--border-color));
  box-shadow: 0 18px 36px color-mix(in srgb, var(--color-primary) 10%, transparent);
}

.hero-copy {
  min-width: 0;
}

.hero-desc {
  margin: 10px 0 0;
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.7;
}

.hero-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.capsule-btn,
.action-btn,
.facet-chip {
  border: 1px solid color-mix(in srgb, var(--color-primary) 12%, var(--border-color));
  background: color-mix(in srgb, var(--color-primary) 6%, var(--card-bg));
  color: var(--text-primary);
  border-radius: 999px;
  cursor: pointer;
  transition: transform 0.18s ease, border-color 0.18s ease, background 0.18s ease;
}

.capsule-btn:hover,
.action-btn:hover,
.facet-chip:hover {
  transform: translateY(-1px);
  border-color: var(--color-primary);
}

.capsule-btn {
  padding: 10px 16px;
  font-size: 13px;
  font-weight: 700;
}

.capsule-btn.primary,
.action-btn.primary,
.facet-chip.active {
  background: var(--color-primary);
  color: #fff;
  border-color: var(--color-primary);
}

.toolbar-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 16px 18px;
  background: var(--card-bg);
  border: 1px solid var(--border-color);
}

.search-box {
  flex: 1;
  min-width: 0;
}

.toolbar-meta {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
  color: var(--text-secondary);
  font-size: 13px;
}

.facet-bar {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.facet-chip {
  padding: 8px 14px;
  font-size: 13px;
  font-weight: 600;
}

.facet-chip span {
  margin-left: 6px;
  opacity: 0.82;
}

.history-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding-right: 2px;
}

.history-card,
.empty-card {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 20px;
  padding: 18px 20px;
  box-shadow: 0 14px 30px color-mix(in srgb, var(--color-primary) 8%, transparent);
}

.history-card {
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.history-card:hover {
  transform: translateY(-2px);
  border-color: color-mix(in srgb, var(--color-primary) 26%, var(--border-color));
  box-shadow: 0 20px 36px color-mix(in srgb, var(--color-primary) 12%, transparent);
}

.card-head,
.card-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chip {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
}

.chip.domain {
  background: color-mix(in srgb, var(--color-primary) 12%, var(--card-bg));
  color: var(--color-primary-dark);
}

.chip.event {
  background: color-mix(in srgb, var(--color-accent-cool) 12%, var(--card-bg));
  color: var(--color-accent-cool);
}

.chip.status {
  background: color-mix(in srgb, #2e8b57 12%, var(--card-bg));
  color: #2e8b57;
}

.chip.restore {
  background: color-mix(in srgb, #8e44ad 12%, var(--card-bg));
  color: #8e44ad;
}

.time-text {
  color: var(--text-muted);
  font-size: 12px;
  white-space: nowrap;
}

.card-title {
  margin: 14px 0 6px;
  color: var(--text-primary);
  font-size: 20px;
  line-height: 1.4;
}

.card-subtitle {
  margin: 0 0 8px;
  color: var(--text-secondary);
  font-size: 13px;
}

.card-summary {
  margin: 0;
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.8;
  white-space: pre-wrap;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-meta {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
  margin-top: 14px;
  color: var(--text-muted);
  font-size: 12px;
}

.card-actions {
  margin-top: 16px;
  justify-content: flex-start;
  flex-wrap: wrap;
}

.action-btn {
  padding: 8px 14px;
  font-size: 12px;
  font-weight: 700;
}

.empty-shell {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-card {
  max-width: 520px;
  text-align: center;
}

.empty-card h3 {
  margin: 0 0 10px;
  font-size: 20px;
  color: var(--text-primary);
}

.empty-card p {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.8;
}

.feed-status {
  padding: 8px 0 4px;
  text-align: center;
  color: var(--text-muted);
  font-size: 13px;
}

@media (max-width: 900px) {
  .history-page {
    padding: 14px;
  }

  .history-hero,
  .toolbar-card,
  .history-card,
  .empty-card {
    padding: 16px;
  }

  .history-hero,
  .toolbar-card,
  .card-head {
    flex-direction: column;
    align-items: stretch;
  }

  .hero-actions,
  .toolbar-meta {
    justify-content: flex-start;
  }

  .time-text {
    white-space: normal;
  }

  .card-title {
    font-size: 18px;
  }
}
</style>
