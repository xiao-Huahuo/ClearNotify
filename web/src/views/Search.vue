<template>
  <div class="search-page">
    <PolicyTitle class="page-title" title="搜索中心" />

    <div class="search-bar-wrap">
      <UnifiedSearchBox
        v-model="inputVal"
        v-model:types="selectedTypes"
        size="header"
        source="search_page_dropdown"
        placeholder="搜索政策、文章、历史、智能体..."
        @submit="handleSearchSubmit"
      />

      <div class="hot-tags" v-if="!hasSearched">
        <span class="hot-label">热门：</span>
        <button
          v-for="tag in hotTags"
          :key="tag"
          type="button"
          class="hot-tag"
          @click="quickSearch(tag)"
        >
          {{ tag }}
        </button>
      </div>
    </div>

    <div class="results-area" v-if="hasSearched">
      <div class="results-meta">
        <span class="results-count" v-if="!searching">
          找到 <strong>{{ results.length }}</strong> 条结果
          <span v-if="currentQuery"> · "{{ currentQuery }}"</span>
        </span>
        <div class="filter-tabs">
          <button
            v-for="tab in filterTabs"
            :key="tab.key"
            type="button"
            :class="{ active: activeFilter === tab.key }"
            @click="activeFilter = tab.key"
          >
            {{ tab.label }}
          </button>
        </div>
      </div>

      <div v-if="searching" class="skeleton-list">
        <div v-for="i in 5" :key="i" class="skeleton-result">
          <div class="sk-type"></div>
          <div class="sk-body">
            <div class="sk-title"></div>
            <div class="sk-desc"></div>
          </div>
        </div>
      </div>

      <div v-else-if="filteredResults.length === 0" class="empty-state">
        <svg viewBox="0 0 24 24" width="48" height="48" stroke="#ccc" stroke-width="1.5" fill="none">
          <circle cx="11" cy="11" r="8"></circle>
          <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
        </svg>
        <p>未找到相关内容</p>
        <span>可以尝试别的关键词，或放宽搜索类型筛选。</span>
      </div>

      <div v-else class="result-list">
        <div
          v-for="(item, idx) in filteredResults"
          :key="`${item.source_type}-${item.subject_type}-${item.subject_id || idx}`"
          class="result-item"
          @click="openSearchResult(item)"
        >
          <div class="ri-left">
            <span class="ri-type" :class="getResultTypeClass(item)">
              {{ getResultTypeLabel(item) }}
            </span>
          </div>
          <div class="ri-body">
            <p class="ri-title" v-html="highlight(item.title)"></p>
            <p class="ri-desc" v-if="item.description" v-html="highlight(item.description)"></p>
            <div class="ri-meta">
              <span class="ri-date" v-if="item.published_at">{{ formatDate(item.published_at) }}</span>
              <span class="ri-source" v-if="item.external_url">{{ getDomain(item.external_url) }}</span>
              <span class="ri-source" v-else-if="item.subtitle">{{ item.subtitle }}</span>
            </div>
          </div>
          <div class="ri-right">
            <svg viewBox="0 0 24 24" width="14" height="14" stroke="#ccc" stroke-width="2" fill="none">
              <polyline points="9 18 15 12 9 6"></polyline>
            </svg>
          </div>
        </div>
      </div>
    </div>

    <div class="recommend-area" v-else>
      <div class="rec-section">
        <h3 class="rec-title">最新政策</h3>
        <div class="rec-list">
          <div
            v-for="(doc, idx) in recentDocs"
            :key="`doc-${idx}`"
            class="rec-item"
            @click="openRecommendPolicy(doc)"
          >
            <span class="rec-rank" :class="{ 'rank-top': idx < 3 }">{{ idx + 1 }}</span>
            <div class="rec-content">
              <p class="rec-text">{{ doc.title }}</p>
              <span class="rec-date">{{ formatDate(doc.pubDate) }}</span>
            </div>
          </div>
          <div v-if="docsLoading" class="loading-placeholder">
            <div v-for="i in 3" :key="`doc-loading-${i}`" class="skeleton-line"></div>
          </div>
        </div>
      </div>

      <div class="rec-section">
        <h3 class="rec-title">时事热点</h3>
        <div class="rec-list">
          <div
            v-for="(item, idx) in recentNews"
            :key="`news-${idx}`"
            class="rec-item"
            @click="openRecommendNews(item)"
          >
            <span class="rec-rank" :class="{ 'rank-top': idx < 3 }">{{ idx + 1 }}</span>
            <div class="rec-content">
              <p class="rec-text">{{ item.title }}</p>
              <span class="rec-date">{{ formatDate(item.pubDate) }}</span>
            </div>
          </div>
          <div v-if="newsLoading" class="loading-placeholder">
            <div v-for="i in 3" :key="`news-loading-${i}`" class="skeleton-line"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import PolicyTitle from '@/components/common/PolicyTitle.vue';
import UnifiedSearchBox from '@/components/common/UnifiedSearchBox.vue';
import { trackHistoryEvent } from '@/api/history';
import { getHotNews, getCentralDocs } from '@/api/news';
import { unifiedSearch } from '@/api/search';
import { useUserStore } from '@/stores/auth.js';
import { openUnifiedSearchResult } from '@/utils/searchActions';
import {
  buildSearchRouteQuery,
  normalizeSearchTypes,
  serializeSearchTypes,
} from '@/utils/unifiedSearch';

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();

const inputVal = ref('');
const currentQuery = ref('');
const results = ref([]);
const searching = ref(false);
const hasSearched = ref(false);
const activeFilter = ref('all');
const selectedTypes = ref(normalizeSearchTypes(route.query.types));

const recentDocs = ref([]);
const recentNews = ref([]);
const docsLoading = ref(true);
const newsLoading = ref(true);

const hotTags = ['改革', '政策', '乡村振兴', '营商环境', '医疗', '教育', '就业', '数字经济'];

const filterTabs = [
  { key: 'all', label: '全部' },
  { key: 'history', label: '历史' },
  { key: 'agent', label: '智能体' },
  { key: 'news', label: '时事' },
  { key: 'policy', label: '政策' },
];

const filteredResults = computed(() => {
  if (activeFilter.value === 'all') return results.value;
  return results.value.filter((item) => item.source_type === activeFilter.value);
});

const formatDate = (value) => {
  if (!value) return '';
  const text = String(value);
  return text.length > 10 ? text.slice(0, 10) : text;
};

const getDomain = (url) => {
  try {
    return new URL(url).hostname.replace('www.', '');
  } catch {
    return '';
  }
};

const getResultTypeLabel = (item) => {
  if (item.source_type === 'history') return '历史';
  if (item.source_type === 'agent') return '智能体';
  if (item.source_type === 'policy') return '政策';
  return '时事';
};

const getResultTypeClass = (item) => {
  if (item.source_type === 'history') return 'type-history';
  if (item.source_type === 'agent') return 'type-agent';
  if (item.source_type === 'policy') return 'type-policy';
  return 'type-news';
};

const highlight = (text) => {
  if (!currentQuery.value || !text) return text;
  const escaped = currentQuery.value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  return String(text).replace(new RegExp(escaped, 'gi'), (match) => `<mark>${match}</mark>`);
};

const loadRecommend = async () => {
  try {
    const res = await getCentralDocs(5);
    recentDocs.value = res.data.items || [];
  } catch (error) {
    console.warn(error);
  } finally {
    docsLoading.value = false;
  }

  try {
    const res = await getHotNews(5);
    recentNews.value = res.data.items || [];
  } catch (error) {
    console.warn(error);
  } finally {
    newsLoading.value = false;
  }
};

const performSearch = async (options = {}) => {
  const {
    query = inputVal.value,
    types = selectedTypes.value,
    track = false,
    syncRoute = true,
  } = options;

  const normalizedQuery = String(query || '').trim();
  if (!normalizedQuery) return;

  const normalizedTypes = normalizeSearchTypes(types);

  inputVal.value = normalizedQuery;
  currentQuery.value = normalizedQuery;
  selectedTypes.value = normalizedTypes;
  hasSearched.value = true;
  searching.value = true;
  activeFilter.value = 'all';

  if (syncRoute) {
    await router.replace({ query: buildSearchRouteQuery(normalizedQuery, normalizedTypes) });
  }

  try {
    const res = await unifiedSearch(normalizedQuery, 30, {
      track,
      types: normalizedTypes,
    });
    results.value = res.data.items || [];
  } catch (error) {
    console.warn('搜索失败', error);
    results.value = [];
  } finally {
    searching.value = false;
  }
};

const handleSearchSubmit = ({ query, types }) =>
  performSearch({
    query,
    types,
    track: true,
    syncRoute: true,
  });

const quickSearch = (tag) =>
  performSearch({
    query: tag,
    types: selectedTypes.value,
    track: true,
    syncRoute: true,
  });

const clearSearch = async () => {
  inputVal.value = '';
  currentQuery.value = '';
  selectedTypes.value = [];
  hasSearched.value = false;
  results.value = [];
  activeFilter.value = 'all';
  await router.replace({ query: {} });
};

const trackExternalBrowse = (payload) => {
  if (!userStore.token) return;
  trackHistoryEvent(payload).catch(() => {});
};

const openExternalLink = (url) => {
  if (url) window.open(url, '_blank');
};

const openSearchResult = (item) => {
  if (!item) return;
  const originRoute = `/search?${new URLSearchParams(
    buildSearchRouteQuery(currentQuery.value || inputVal.value.trim(), selectedTypes.value),
  ).toString()}`;

  openUnifiedSearchResult(router, item, {
    source: 'search_results',
    query: currentQuery.value || inputVal.value.trim(),
    originRoute,
    track: Boolean(userStore.token),
  }).catch((error) => {
    console.warn('打开搜索结果失败', error);
  });
};

const openRecommendPolicy = (doc) => {
  if (!doc?.link) return;
  trackExternalBrowse({
    domain: 'policy_browse',
    event_type: 'opened_external',
    subject_type: 'external_policy_article',
    title: doc.title || '最新政策',
    summary: doc.description || null,
    route_path: '/search',
    external_url: doc.link,
    icon: 'policy',
    search_text: [doc.title, doc.description].filter(Boolean).join('\n'),
    extra: {
      source: 'search_recommend_policy',
      pub_date: doc.pubDate || null,
    },
  });
  openExternalLink(doc.link);
};

const openRecommendNews = (item) => {
  if (!item?.link) return;
  trackExternalBrowse({
    domain: 'article_browse',
    event_type: 'opened_external',
    subject_type: 'news_article',
    title: item.title || '时事热点',
    summary: item.description || null,
    route_path: '/search',
    external_url: item.link,
    icon: 'news',
    search_text: [item.title, item.description].filter(Boolean).join('\n'),
    extra: {
      source: 'search_recommend_news',
      pub_date: item.pubDate || null,
    },
  });
  openExternalLink(item.link);
};

watch(
  () => [route.query.q, route.query.types],
  async ([queryValue, typeValue]) => {
    const normalizedQuery = String(queryValue || '').trim();
    const normalizedTypes = normalizeSearchTypes(typeValue);
    const routeTypeKey = serializeSearchTypes(normalizedTypes);
    const localTypeKey = serializeSearchTypes(selectedTypes.value);

    if (!normalizedQuery) {
      if (currentQuery.value || hasSearched.value) {
        await clearSearch();
      }
      return;
    }

    if (normalizedQuery === currentQuery.value && routeTypeKey === localTypeKey) {
      inputVal.value = normalizedQuery;
      return;
    }

    await performSearch({
      query: normalizedQuery,
      types: normalizedTypes,
      track: false,
      syncRoute: false,
    });
  },
);

onMounted(async () => {
  await loadRecommend();

  const initialQuery = String(route.query.q || '').trim();
  if (!initialQuery) return;

  await performSearch({
    query: initialQuery,
    types: normalizeSearchTypes(route.query.types),
    track: false,
    syncRoute: false,
  });
});
</script>

<style scoped>
.search-page {
  height: 100%;
  overflow-y: auto;
  padding: 24px 32px;
  background: var(--content-bg, #f5f7fa);
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.search-bar-wrap {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-width: 720px;
  margin: 0 auto;
  width: 100%;
}

.hot-tags {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.hot-label {
  font-size: 12px;
  color: var(--text-muted, #999);
}

.hot-tag {
  border: 1px solid var(--border-color, #e0e0e0);
  background: var(--card-bg, #fff);
  color: var(--text-secondary, #555);
  border-radius: 999px;
  padding: 5px 12px;
  font-size: 12px;
  cursor: pointer;
  transition: border-color 0.2s ease, background 0.2s ease, color 0.2s ease;
}

.hot-tag:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
  background: color-mix(in srgb, var(--color-primary) 8%, var(--card-bg));
}

.results-area {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.results-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.results-count {
  font-size: 13px;
  color: var(--text-secondary, #666);
}

.results-count strong {
  color: var(--text-primary, #111);
}

.filter-tabs {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.filter-tabs button {
  background: var(--card-bg, #fff);
  border: 1px solid var(--border-color, #e0e0e0);
  color: var(--text-secondary, #666);
  padding: 5px 14px;
  border-radius: 20px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.filter-tabs button.active {
  background: var(--text-primary, #111);
  color: #fff;
  border-color: var(--text-primary, #111);
  font-weight: 600;
}

.skeleton-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.skeleton-result {
  display: flex;
  gap: 12px;
  background: var(--card-bg, #fff);
  border-radius: 12px;
  padding: 16px;
  border: 1px solid var(--border-color, #eee);
}

.sk-type {
  width: 40px;
  height: 20px;
  border-radius: 10px;
  background: #f0f0f0;
  flex-shrink: 0;
}

.sk-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.sk-title,
.sk-desc,
.skeleton-line {
  background: linear-gradient(90deg, #f0f0f0 25%, #e8e8e8 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

.sk-title {
  height: 16px;
  border-radius: 6px;
}

.sk-desc {
  width: 70%;
  height: 12px;
  border-radius: 6px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 60px 0;
  color: #aaa;
}

.empty-state p {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #666;
}

.empty-state span {
  font-size: 13px;
}

.result-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.result-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  background: var(--card-bg, #fff);
  border-radius: 12px;
  border: 1px solid var(--border-color, #eee);
  padding: 14px 16px;
  cursor: pointer;
  transition: box-shadow 0.2s ease, border-color 0.2s ease;
}

.result-item:hover {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  border-color: color-mix(in srgb, var(--color-primary) 24%, var(--border-color));
}

.ri-left {
  flex-shrink: 0;
  padding-top: 2px;
}

.ri-type {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 10px;
}

.type-history {
  background: #f4eefb;
  color: #7d3c98;
}

.type-agent {
  background: #e9f7ef;
  color: #1e8449;
}

.type-news {
  background: #e6f7ff;
  color: #0077cc;
}

.type-policy {
  background: #fff0f0;
  color: #c0392b;
}

.ri-body {
  flex: 1;
  min-width: 0;
}

.ri-title {
  margin: 0 0 5px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary, #111);
  line-height: 1.5;
}

.ri-title :deep(mark),
.ri-desc :deep(mark) {
  background: #fff3cd;
  color: #111;
  border-radius: 2px;
  padding: 0 1px;
}

.ri-desc {
  margin: 0 0 6px;
  font-size: 12px;
  color: var(--text-secondary, #666);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.ri-meta {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.ri-date {
  font-size: 11px;
  color: #bbb;
}

.ri-source {
  font-size: 11px;
  color: var(--color-primary);
}

.ri-right {
  flex-shrink: 0;
  padding-top: 4px;
}

.recommend-area {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.rec-section {
  background: var(--card-bg, #fff);
  border-radius: 16px;
  border: 1px solid var(--border-color, #eee);
  padding: 16px;
}

.rec-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary, #111);
  margin: 0 0 12px;
}

.rec-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.rec-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 9px 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s ease;
}

.rec-item:hover {
  background: var(--content-bg, #f5f7fa);
}

.rec-rank {
  font-size: 13px;
  font-weight: 700;
  color: #ccc;
  width: 18px;
  flex-shrink: 0;
  text-align: center;
}

.rec-rank.rank-top {
  color: var(--color-primary);
}

.rec-content {
  flex: 1;
  min-width: 0;
}

.rec-text {
  margin: 0 0 3px;
  font-size: 13px;
  color: var(--text-primary, #222);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.rec-date {
  font-size: 11px;
  color: #bbb;
}

.loading-placeholder {
  padding: 4px 0;
}

.skeleton-line {
  height: 12px;
  border-radius: 6px;
  margin-bottom: 10px;
}

@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }

  100% {
    background-position: -200% 0;
  }
}

@media (max-width: 900px) {
  .search-page {
    padding: 18px 16px;
  }

  .results-meta {
    flex-direction: column;
    align-items: flex-start;
  }

  .recommend-area {
    grid-template-columns: 1fr;
  }
}
</style>
