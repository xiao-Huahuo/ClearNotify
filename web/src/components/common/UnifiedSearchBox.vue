<template>
  <div
    class="unified-search-box"
    :class="[`size-${size}`, { 'is-focused': searchFocused, 'is-expanded': showAdvancedOptionsPanel }]"
    @focusin="handleSearchFocus"
    @focusout="handleSearchBlur"
  >
    <div class="search-bar">
      <svg class="search-icon" viewBox="0 0 24 24" width="17" height="17" stroke="currentColor" stroke-width="2" fill="none">
        <circle cx="11" cy="11" r="8"></circle>
        <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
      </svg>

      <input
        :value="searchQuery"
        :placeholder="placeholder"
        type="text"
        @input="handleSearchInput"
        @keydown.down.prevent="moveSuggestion(1)"
        @keydown.up.prevent="moveSuggestion(-1)"
        @keyup.enter="handleSearchEnter"
        @keyup.esc="closeSearchDropdown"
      />

      <button
        v-if="searchQuery"
        class="search-clear"
        type="button"
        title="清空搜索"
        @click="clearSearchQuery"
      >
        <svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      </button>

      <button class="search-submit" type="button" :title="submitTitle" @click="submitSearch()">
        <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none">
          <circle cx="11" cy="11" r="8"></circle>
          <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
        </svg>
      </button>
    </div>

    <div v-if="showSearchDropdown" class="search-dropdown">
      <div v-if="showRecentSearchCapsules && recentSearchCapsules.length" class="dropdown-block">
        <div class="dropdown-head">
          <span>最近搜索</span>
          <span class="dropdown-meta">{{ recentSearchCapsules.length }}</span>
        </div>
        <div class="search-capsules">
          <button
            v-for="item in recentSearchCapsules"
            :key="getSuggestionKey('recent_search', item)"
            class="search-capsule"
            type="button"
            @mousedown.prevent="runRecentSearch(item)"
          >
            {{ item.title }}
          </button>
        </div>
      </div>

      <div v-if="showTypeFilters && showAdvancedOptionsPanel" class="dropdown-block">
        <div class="dropdown-head">
          <span>搜索范围</span>
          <button class="dropdown-link" type="button" @mousedown.prevent="selectAllTypes">全选</button>
        </div>
        <div class="type-filter-grid">
          <label v-for="option in typeOptions" :key="option.value" class="type-filter-item">
            <input
              type="checkbox"
              :checked="selectedTypeSet.has(option.value)"
              @change="toggleType(option.value)"
            />
            <span>{{ option.label }}</span>
          </label>
        </div>
        <p class="dropdown-hint">Trie 负责前缀联想，RAG 负责语义召回。</p>
      </div>

      <div v-if="remoteSearching && !visibleSuggestionSections.length" class="search-dropdown-empty">联想中...</div>

      <template v-for="section in visibleSuggestionSections" :key="section.key">
        <div class="dropdown-block">
          <div class="dropdown-head">
            <span>{{ section.title }}</span>
            <span v-if="section.total > section.items.length" class="dropdown-meta">
              +{{ section.total - section.items.length }}
            </span>
          </div>
          <button
            v-for="item in section.items"
            :key="getSuggestionKey(section.key, item)"
            class="search-dropdown-item"
            :class="{ 'is-active': activeSuggestionKey === getSuggestionKey(section.key, item) }"
            type="button"
            @mousedown.prevent="openSuggestion(item)"
            @mousemove="activeSuggestionKey = getSuggestionKey(section.key, item)"
          >
            <span class="dropdown-badge">{{ getSearchSourceLabel(item.source_type) }}</span>
            <span class="dropdown-main">
              <span class="dropdown-title">{{ item.title }}</span>
              <span class="dropdown-subtitle">{{ item.subtitle || item.description || section.fallback }}</span>
            </span>
            <span v-if="getMatchLabel(section.key, item)" class="dropdown-match">
              {{ getMatchLabel(section.key, item) }}
            </span>
          </button>
        </div>
      </template>

      <div
        v-if="!visibleSuggestionSections.length && !remoteSearching"
        class="search-dropdown-empty"
      >
        暂无匹配结果，回车进入搜索
      </div>

      <div class="dropdown-footer">
        <button class="dropdown-more" type="button" @mousedown.prevent="toggleAdvancedOptions">
          {{ showAdvancedOptionsPanel ? '收起更多搜索选项' : '更多搜索选项' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { getSearchSuggestIndex, getSearchSuggestions } from '@/api/search';
import { openUnifiedSearchResult } from '@/utils/searchActions';
import { buildSearchTrie, trieSearch } from '@/utils/searchTrie';
import {
  SEARCH_TYPE_OPTIONS,
  SEARCH_TYPE_VALUES,
  areSearchTypesEqual,
  getSearchSourceLabel,
  matchesSearchTypes,
  normalizeSearchTypes,
} from '@/utils/unifiedSearch';
import { useUserStore } from '@/stores/auth.js';

const props = defineProps({
  modelValue: { type: String, default: '' },
  types: { type: Array, default: () => [] },
  placeholder: { type: String, default: '搜索政策、文章、历史、智能体...' },
  source: { type: String, default: 'unified_search_box' },
  size: { type: String, default: 'default' },
  submitTitle: { type: String, default: '搜索' },
  collapsedResultLimit: { type: Number, default: 8 },
  expandedResultLimit: { type: Number, default: 18 },
  remoteLimit: { type: Number, default: 24 },
  showRecentSearchCapsules: { type: Boolean, default: true },
  showTypeFilters: { type: Boolean, default: true },
  autoloadIndex: { type: Boolean, default: true },
});

const emit = defineEmits(['update:modelValue', 'update:types', 'submit']);

const router = useRouter();
const userStore = useUserStore();

const searchQuery = ref(String(props.modelValue || ''));
const selectedTypes = ref(normalizeSearchTypes(props.types));
const searchFocused = ref(false);
const searchIndexItems = ref([]);
const searchTrieRoot = ref(null);
const localSuggestions = ref([]);
const remoteSuggestions = ref([]);
const remoteSearching = ref(false);
const activeSuggestionKey = ref('');
const keyboardSuggestionNavigation = ref(false);
const showAdvancedOptionsPanel = ref(false);

let searchBlurTimer = null;
let remoteSuggestTimer = null;
let remoteSuggestRequestId = 0;

const typeOptions = SEARCH_TYPE_OPTIONS;
const selectedTypeSet = computed(() => new Set(effectiveTypes.value));
const effectiveTypes = computed(() =>
  selectedTypes.value.length ? selectedTypes.value : [...SEARCH_TYPE_VALUES]
);

const recentSearchCapsules = computed(() => {
  const limit = showAdvancedOptionsPanel.value ? 10 : 6;
  return remoteSuggestions.value
    .filter((item) => item.group === 'recent_search')
    .slice(0, limit);
});

const suggestionSections = computed(() => {
  const query = searchQuery.value.trim();
  const sections = [];

  const trieItems = localSuggestions.value.filter((item) =>
    matchesSearchTypes(item, effectiveTypes.value, { keepSearchHistory: true })
  );
  if (query && trieItems.length) {
    sections.push({
      key: 'local_prefix',
      title: 'Trie 前缀联想',
      fallback: '前缀命中',
      items: trieItems,
      total: trieItems.length,
    });
  }

  const localKeys = new Set(trieItems.map((item) => buildSuggestionKey(item)));
  const groupedItems = new Map();

  remoteSuggestions.value.forEach((item) => {
    if (item.group === 'recent_search') return;
    if (!matchesSearchTypes(item, effectiveTypes.value)) return;

    const key = buildSuggestionKey(item);
    if (query && localKeys.has(key)) return;

    const group = item.group || 'semantic';
    if (!groupedItems.has(group)) groupedItems.set(group, []);
    groupedItems.get(group).push(item);
  });

  const groupOrder = query
    ? ['recent_history', 'semantic']
    : ['recent_history', 'quick_access'];

  groupOrder.forEach((group) => {
    const items = groupedItems.get(group) || [];
    if (!items.length) return;
    sections.push({
      key: group,
      title: getSuggestionSectionTitle(group),
      fallback: group === 'quick_access' ? '统一搜索入口' : '搜索建议',
      items,
      total: items.length,
    });
  });

  return sections;
});

const visibleSuggestionSections = computed(() => {
  const maxItems = showAdvancedOptionsPanel.value
    ? props.expandedResultLimit
    : props.collapsedResultLimit;
  let remaining = maxItems;

  return suggestionSections.value
    .map((section) => {
      if (remaining <= 0) return null;
      const sectionItems = section.items.slice(0, remaining);
      remaining -= sectionItems.length;
      return {
        ...section,
        items: sectionItems,
      };
    })
    .filter(Boolean);
});

const flattenedSuggestions = computed(() =>
  visibleSuggestionSections.value.flatMap((section) =>
    section.items.map((item) => ({
      key: getSuggestionKey(section.key, item),
      item,
    }))
  )
);

const showSearchDropdown = computed(() => {
  if (!searchFocused.value) return false;
  return Boolean(
    recentSearchCapsules.value.length ||
      visibleSuggestionSections.value.length ||
      remoteSearching.value ||
      showAdvancedOptionsPanel.value
  );
});

const emitQueryUpdate = (value) => {
  emit('update:modelValue', value);
};

const emitTypesUpdate = (value) => {
  emit('update:types', [...value]);
};

const syncActiveSuggestion = async () => {
  const [first] = flattenedSuggestions.value;
  const nextKey = first?.key || '';
  if (!nextKey) {
    activeSuggestionKey.value = '';
    return;
  }
  if (activeSuggestionKey.value === nextKey) return;
  activeSuggestionKey.value = nextKey;
  await nextTick();
};

const refreshLocalSuggestions = () => {
  const query = searchQuery.value.trim();
  if (!query) {
    localSuggestions.value = [];
    return;
  }
  localSuggestions.value = trieSearch(
    searchTrieRoot.value,
    searchIndexItems.value,
    query,
    12,
  );
};

const fetchSuggestionIndex = async () => {
  try {
    const res = await getSearchSuggestIndex();
    searchIndexItems.value = res.data?.items || [];
    searchTrieRoot.value = buildSearchTrie(searchIndexItems.value);
    refreshLocalSuggestions();
  } catch (error) {
    console.warn('搜索索引加载失败', error);
    searchIndexItems.value = [];
    searchTrieRoot.value = null;
  }
};

const fetchRemoteSuggestions = ({ immediate = false } = {}) => {
  clearTimeout(remoteSuggestTimer);
  const query = searchQuery.value.trim();

  if (query && query.length < 2) {
    remoteSearching.value = false;
    remoteSuggestions.value = [];
    return;
  }

  const run = async () => {
    const requestId = ++remoteSuggestRequestId;
    remoteSearching.value = true;
    try {
      const res = await getSearchSuggestions(query, props.remoteLimit, {
        types: effectiveTypes.value,
      });
      if (requestId !== remoteSuggestRequestId) return;
      remoteSuggestions.value = res.data?.items || [];
    } catch (error) {
      if (requestId !== remoteSuggestRequestId) return;
      console.warn('联想搜索失败', error);
      remoteSuggestions.value = [];
    } finally {
      if (requestId !== remoteSuggestRequestId) return;
      remoteSearching.value = false;
    }
  };

  if (immediate || !query) {
    void run();
    return;
  }

  remoteSuggestTimer = setTimeout(run, 180);
};

const closeSearchDropdown = () => {
  searchFocused.value = false;
  activeSuggestionKey.value = '';
  keyboardSuggestionNavigation.value = false;
};

const clearSearchQuery = () => {
  searchQuery.value = '';
  emitQueryUpdate('');
  localSuggestions.value = [];
  activeSuggestionKey.value = '';
  keyboardSuggestionNavigation.value = false;
  if (searchFocused.value) {
    fetchRemoteSuggestions({ immediate: true });
  } else {
    remoteSuggestions.value = [];
  }
};

const handleSearchInput = (event) => {
  const nextValue = String(event?.target?.value || '');
  searchQuery.value = nextValue;
  emitQueryUpdate(nextValue);
  keyboardSuggestionNavigation.value = false;
  refreshLocalSuggestions();
  fetchRemoteSuggestions();
};

const handleSearchFocus = () => {
  if (searchBlurTimer) {
    clearTimeout(searchBlurTimer);
    searchBlurTimer = null;
  }
  if (searchFocused.value) return;
  searchFocused.value = true;
  keyboardSuggestionNavigation.value = false;
  if (!searchIndexItems.value.length) {
    void fetchSuggestionIndex();
  }
  refreshLocalSuggestions();
  fetchRemoteSuggestions({ immediate: true });
  void syncActiveSuggestion();
};

const handleSearchBlur = () => {
  searchBlurTimer = setTimeout(() => {
    searchFocused.value = false;
    activeSuggestionKey.value = '';
    keyboardSuggestionNavigation.value = false;
  }, 120);
};

const submitSearch = (queryOverride = '') => {
  const query = String(queryOverride || searchQuery.value || '').trim();
  if (!query) return;
  searchQuery.value = query;
  emitQueryUpdate(query);
  closeSearchDropdown();
  emit('submit', {
    query,
    types: [...effectiveTypes.value],
  });
};

const runRecentSearch = (item) => {
  const nextQuery = String(item?.extra?.query || item?.title || '').trim();
  const nextTypes = normalizeSearchTypes(item?.extra?.types);
  if (nextTypes.length) {
    selectedTypes.value = nextTypes;
    emitTypesUpdate(nextTypes);
  }
  submitSearch(nextQuery);
};

const openSuggestion = async (item) => {
  if (!item) return;
  closeSearchDropdown();
  await openUnifiedSearchResult(router, item, {
    source: props.source,
    query: searchQuery.value.trim(),
    track: Boolean(userStore.token),
  });
};

const moveSuggestion = async (step) => {
  if (!showSearchDropdown.value) {
    handleSearchFocus();
    return;
  }

  const items = flattenedSuggestions.value;
  if (!items.length) return;

  keyboardSuggestionNavigation.value = true;
  const currentIndex = items.findIndex((entry) => entry.key === activeSuggestionKey.value);
  const nextIndex =
    currentIndex < 0
      ? (step > 0 ? 0 : items.length - 1)
      : (currentIndex + step + items.length) % items.length;

  activeSuggestionKey.value = items[nextIndex].key;
  await nextTick();
};

const handleSearchEnter = async () => {
  const activeItem = flattenedSuggestions.value.find((entry) => entry.key === activeSuggestionKey.value)?.item;
  if (showSearchDropdown.value && keyboardSuggestionNavigation.value && activeItem) {
    await openSuggestion(activeItem);
    return;
  }
  submitSearch();
};

const applyTypes = (nextTypes) => {
  const normalized = normalizeSearchTypes(nextTypes);
  selectedTypes.value = normalized.length ? normalized : [...SEARCH_TYPE_VALUES];
  emitTypesUpdate(selectedTypes.value);
};

const toggleType = (type) => {
  const exists = selectedTypeSet.value.has(type);
  const nextTypes = exists
    ? effectiveTypes.value.filter((item) => item !== type)
    : [...effectiveTypes.value, type];

  if (!nextTypes.length) return;
  applyTypes(nextTypes);
};

const selectAllTypes = () => {
  applyTypes(SEARCH_TYPE_VALUES);
};

const toggleAdvancedOptions = () => {
  showAdvancedOptionsPanel.value = !showAdvancedOptionsPanel.value;
};

const getMatchLabel = (sectionKey, item) => {
  if (sectionKey === 'local_prefix') return 'Trie';
  const matchedBy = item?.extra?.matched_by;
  if (matchedBy === 'semantic') return 'RAG';
  if (matchedBy === 'hybrid') return 'Trie+RAG';
  return '';
};

const buildSuggestionKey = (item) =>
  [
    item?.source_type || '',
    item?.subject_type || '',
    item?.subject_id || '',
    item?.title || '',
    item?.action_type || '',
    item?.route_path || '',
    item?.external_url || '',
  ].join('|');

const getSuggestionKey = (groupKey, item) => `${groupKey}-${buildSuggestionKey(item)}`;

const getSuggestionSectionTitle = (group) => {
  if (group === 'recent_history') return '最近历史';
  if (group === 'quick_access') return '快速入口';
  return '语义召回';
};

watch(
  () => props.modelValue,
  (value) => {
    const nextValue = String(value || '');
    if (nextValue === searchQuery.value) return;
    searchQuery.value = nextValue;
    refreshLocalSuggestions();
    if (searchFocused.value) fetchRemoteSuggestions({ immediate: true });
  }
);

watch(
  () => props.types,
  (value) => {
    const normalized = normalizeSearchTypes(value);
    const nextTypes = normalized.length ? normalized : [...SEARCH_TYPE_VALUES];
    if (areSearchTypesEqual(nextTypes, selectedTypes.value)) return;
    selectedTypes.value = nextTypes;
    refreshLocalSuggestions();
    if (searchFocused.value) fetchRemoteSuggestions({ immediate: true });
  },
  { deep: true }
);

watch(
  effectiveTypes,
  () => {
    keyboardSuggestionNavigation.value = false;
    refreshLocalSuggestions();
    if (searchFocused.value) fetchRemoteSuggestions({ immediate: true });
  },
  { deep: true }
);

watch(
  flattenedSuggestions,
  () => {
    if (!searchFocused.value) return;
    void syncActiveSuggestion();
  },
  { flush: 'post' }
);

watch(
  () => userStore.token,
  () => {
    if (!props.autoloadIndex) return;
    void fetchSuggestionIndex();
    if (searchFocused.value) fetchRemoteSuggestions({ immediate: true });
  }
);

onMounted(() => {
  if (!selectedTypes.value.length) {
    selectedTypes.value = [...SEARCH_TYPE_VALUES];
  }
  if (props.autoloadIndex) {
    void fetchSuggestionIndex();
  }
});

onBeforeUnmount(() => {
  if (searchBlurTimer) clearTimeout(searchBlurTimer);
  if (remoteSuggestTimer) clearTimeout(remoteSuggestTimer);
});
</script>

<style scoped>
.unified-search-box {
  position: relative;
  width: 100%;
}

.search-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  min-width: 0;
  padding: 8px 10px 8px 12px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-primary) 5%, var(--card-bg));
  border: 1px solid color-mix(in srgb, var(--color-primary) 14%, var(--border-color));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08);
  transition: border-color 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
}

.unified-search-box.is-focused .search-bar {
  background: color-mix(in srgb, var(--color-primary) 7%, var(--card-bg));
  border-color: color-mix(in srgb, var(--color-primary) 48%, var(--border-color));
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--color-primary) 10%, transparent);
}

.search-icon {
  flex-shrink: 0;
  color: var(--text-secondary);
}

.search-bar input {
  flex: 1;
  min-width: 0;
  border: none;
  outline: none;
  background: transparent;
  color: var(--text-primary);
  font-size: 14px;
}

.search-bar input::placeholder {
  color: var(--text-muted);
}

.search-clear,
.search-submit,
.dropdown-link,
.dropdown-more {
  border: none;
  background: none;
  cursor: pointer;
}

.search-clear {
  width: 28px;
  height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  border-radius: 999px;
  transition: background 0.18s ease, color 0.18s ease;
}

.search-clear:hover {
  background: color-mix(in srgb, var(--color-primary) 8%, transparent);
  color: var(--text-primary);
}

.search-submit {
  width: 34px;
  height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border-radius: 999px;
  background: var(--color-primary);
  color: #fff;
  box-shadow: 0 12px 24px color-mix(in srgb, var(--color-primary) 24%, transparent);
  transition: transform 0.18s ease, filter 0.18s ease;
}

.search-submit:hover {
  transform: translateY(-1px);
  filter: brightness(1.03);
}

.search-dropdown {
  position: absolute;
  top: calc(100% + 10px);
  left: 50%;
  transform: translateX(-50%);
  width: min(calc(100vw - 24px), max(100%, 560px));
  max-height: min(72vh, 540px);
  overflow-y: auto;
  padding: 12px;
  border-radius: 24px;
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--card-bg) 94%, white), var(--card-bg));
  border: 1px solid color-mix(in srgb, var(--color-primary) 14%, var(--border-color));
  box-shadow:
    0 28px 54px rgba(10, 17, 28, 0.18),
    0 8px 20px color-mix(in srgb, var(--color-primary) 10%, transparent);
  z-index: 80;
}

.dropdown-block + .dropdown-block {
  margin-top: 10px;
}

.dropdown-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 2px 6px 8px;
  color: var(--text-secondary);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.dropdown-meta {
  color: var(--text-muted);
  letter-spacing: normal;
}

.dropdown-link {
  padding: 0;
  color: var(--color-primary);
  font-size: 11px;
  font-weight: 700;
}

.search-capsules {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.search-capsule {
  padding: 6px 11px;
  border-radius: 999px;
  border: 1px solid color-mix(in srgb, var(--color-primary) 16%, var(--border-color));
  background: color-mix(in srgb, var(--color-primary) 7%, var(--card-bg));
  color: var(--text-primary);
  font-size: 12px;
  cursor: pointer;
  transition: transform 0.16s ease, border-color 0.16s ease, background 0.16s ease;
}

.search-capsule:hover {
  transform: translateY(-1px);
  border-color: color-mix(in srgb, var(--color-primary) 42%, var(--border-color));
  background: color-mix(in srgb, var(--color-primary) 10%, var(--card-bg));
}

.type-filter-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.type-filter-item {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  padding: 8px 10px;
  border-radius: 14px;
  background: color-mix(in srgb, var(--content-bg) 78%, var(--card-bg));
  border: 1px solid color-mix(in srgb, var(--color-primary) 10%, var(--border-color));
  color: var(--text-primary);
  font-size: 12px;
  cursor: pointer;
}

.type-filter-item input {
  margin: 0;
  accent-color: var(--color-primary);
}

.dropdown-hint {
  margin: 8px 2px 0;
  color: var(--text-muted);
  font-size: 11px;
  line-height: 1.5;
}

.search-dropdown-item {
  width: 100%;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
  padding: 8px 8px;
  border: none;
  background: transparent;
  border-radius: 14px;
  color: var(--text-primary);
  cursor: pointer;
  text-align: left;
  transition: background 0.16s ease;
}

.search-dropdown-item:hover,
.search-dropdown-item.is-active {
  background: color-mix(in srgb, var(--color-primary) 8%, var(--card-bg));
}

.dropdown-badge {
  flex-shrink: 0;
  padding: 3px 8px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-primary) 12%, var(--card-bg));
  color: var(--color-primary-dark);
  font-size: 10px;
  font-weight: 700;
}

.dropdown-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.dropdown-title {
  color: var(--text-primary);
  font-size: 13px;
  font-weight: 700;
  line-height: 1.35;
}

.dropdown-subtitle {
  color: var(--text-secondary);
  font-size: 11px;
  line-height: 1.45;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.dropdown-match {
  padding: 3px 7px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-accent-cool) 12%, var(--card-bg));
  color: var(--color-accent-cool);
  font-size: 10px;
  font-weight: 700;
}

.search-dropdown-empty {
  padding: 14px 8px 8px;
  color: var(--text-secondary);
  font-size: 12px;
}

.dropdown-footer {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid color-mix(in srgb, var(--color-primary) 10%, var(--border-color));
}

.dropdown-more {
  width: 100%;
  min-height: 38px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-primary) 6%, var(--card-bg));
  border: 1px solid color-mix(in srgb, var(--color-primary) 12%, var(--border-color));
  color: var(--text-primary);
  font-size: 12px;
  font-weight: 700;
  transition: transform 0.16s ease, border-color 0.16s ease;
}

.dropdown-more:hover {
  transform: translateY(-1px);
  border-color: color-mix(in srgb, var(--color-primary) 42%, var(--border-color));
}

.size-compact .search-bar {
  padding: 5px 8px 5px 10px;
}

.size-header .search-bar {
  padding: 5px 9px 5px 11px;
}

.size-header .search-bar input {
  font-size: 13px;
}

.size-header .search-submit {
  width: 30px;
  height: 30px;
}

.size-header .search-clear {
  width: 24px;
  height: 24px;
}

.size-compact .search-bar input {
  font-size: 13px;
}

.size-compact .search-submit {
  width: 30px;
  height: 30px;
}

.size-compact .search-clear {
  width: 24px;
  height: 24px;
}

@media (max-width: 720px) {
  .search-dropdown {
    width: min(calc(100vw - 16px), 100%);
    max-height: min(68vh, 500px);
    border-radius: 20px;
    padding: 10px;
  }

  .type-filter-grid {
    grid-template-columns: 1fr;
  }
}
</style>
