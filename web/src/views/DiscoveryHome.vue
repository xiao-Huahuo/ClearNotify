<template>
  <div class="discover-page" ref="pageScrollRef" @scroll="handleNewsScroll">

    <!-- ══ 顶部区域：轮播 + 内嵌搜索 + 内嵌概况卡 ══ -->
    <div class="top-section">
      <div class="panorama-hero">
        <transition name="hero-fade" mode="out-in">
          <div
            :key="slides[slideIdx].title"
            class="hero-slide"
            :style="slides[slideIdx].img ? { backgroundImage: `url(${slides[slideIdx].img})` } : { background: slides[slideIdx].bg }"
            @click="slides[slideIdx].action && slides[slideIdx].action()"
          >
            <div class="hero-overlay"></div>
            <div class="hero-content">
              <span class="panorama-tag">{{ slides[slideIdx].tag }}</span>
              <p class="panorama-title">{{ slides[slideIdx].title }}</p>
              <p class="hero-desc">{{ slides[slideIdx].desc }}</p>
            </div>
          </div>
        </transition>

        <button class="hero-arrow left" @click.stop="prevSlide">
          <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2.2" fill="none"><polyline points="15 18 9 12 15 6"></polyline></svg>
        </button>
        <button class="hero-arrow right" @click.stop="nextSlide">
          <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2.2" fill="none"><polyline points="9 18 15 12 9 6"></polyline></svg>
        </button>

        <div class="hero-dots">
          <span
            v-for="(_, idx) in slides"
            :key="idx"
            class="hero-dot"
            :class="{ active: idx === slideIdx }"
            @click.stop="slideIdx = idx"
          ></span>
        </div>

        <div class="tsb-input-wrap" @focusin="searchFocused = true" @focusout="handleSearchBlur">
          <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
          <input v-model="searchInput" placeholder="搜索政策文件、时事热点..." @keydown.enter="goSearch" />
          <button v-if="searchInput" @click="searchInput = ''" class="tsb-clear">
            <svg viewBox="0 0 24 24" width="12" height="12" stroke="currentColor" stroke-width="2.5" fill="none"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
          <button class="tsb-btn" @click="goSearch">搜索</button>

          <div v-if="searchFocused" class="search-popover">
            <template v-if="!searchInput.trim()">
              <div class="pop-section">
                <span class="pop-title">热门</span>
                <div class="rec-tags">
                  <span v-for="tag in hotTags" :key="tag" class="rec-tag" @mousedown.prevent="quickSearch(tag)">{{ tag }}</span>
                </div>
              </div>
              <div class="pop-section">
                <span class="pop-title">最新政策</span>
                <div class="pop-list">
                  <span v-for="(doc, i) in recentDocs.slice(0, 5)" :key="i" class="pop-item" @mousedown.prevent="openLink(doc.link)">{{ doc.title }}</span>
                </div>
              </div>
            </template>
            <template v-else>
              <div v-if="searchLoading" class="pop-empty">检索中...</div>
              <div v-else-if="searchResults.length" class="pop-list">
                <span
                  v-for="(item, i) in searchResults"
                  :key="`${item.source_type || 'unknown'}-${i}`"
                  class="pop-item"
                  @mousedown.prevent="openSearchItem(item)"
                >
                  <span class="pop-item-type">{{ item.source_type === 'policy' ? '政策' : '时事' }}</span>
                  <span class="pop-item-text">{{ item.title }}</span>
                </span>
              </div>
              <div v-else class="pop-empty">未找到相关内容，回车可进入完整检索</div>
            </template>
          </div>
        </div>

        <div class="gov-summary-card">
          <div class="summary-header">
            <span class="summary-dot"></span>
            <span class="summary-title">今日政务概况</span>
            <span class="summary-time">{{ summaryData.update_time || '--:--' }} 更新</span>
          </div>
          <div class="summary-body" v-if="!summaryLoading">
            <div class="summary-stat">
              <span class="stat-num">{{ summaryData.news_count || 0 }}</span>
              <span class="stat-label">条时事热点</span>
            </div>
            <div class="summary-stat">
              <span class="stat-num">{{ summaryData.doc_count || 0 }}</span>
              <span class="stat-label">份中央文件</span>
            </div>
            <div class="summary-divider"></div>
            <div class="summary-item">
              <span class="si-label">热点头条</span>
              <p class="si-text">{{ summaryData.top_news || '加载中...' }}</p>
            </div>
            <div class="summary-item">
              <span class="si-label">最新政策</span>
              <p class="si-text">{{ summaryData.top_doc || '加载中...' }}</p>
            </div>
          </div>
          <div v-else class="summary-loading">
            <div v-for="i in 4" :key="i" class="skeleton-line"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- ══ 中部：砖块墙 ══ -->
    <div class="bricks-section">
      <h3 class="section-label">功能中心</h3>
      <div class="masonry-wall">
        <div
          v-for="brick in bricks" :key="brick.id"
          class="brick-item"
          :class="[brick.size, brick.disabled ? 'disabled' : '']"
          :style="{ '--brick-color': brick.color, gridColumn: `span ${brick.colSpan}`, gridRow: `span ${brick.rowSpan}` }"
          @click="!brick.disabled && brick.action && brick.action()"
        >
          <div class="brick-shine"></div>
          <div class="brick-edge"></div>
          <div class="brick-icon">
            <component :is="'svg'" v-bind="brick.iconProps" v-html="brick.iconPath"></component>
          </div>
          <div class="brick-info">
            <span class="brick-name">{{ brick.name }}</span>
            <span class="brick-desc">{{ brick.desc }}</span>
          </div>
          <span v-if="brick.disabled" class="brick-badge">即将上线</span>
          <span v-if="brick.hot" class="brick-badge hot">热门</span>
        </div>
      </div>
    </div>

    <!-- ══ 下部：新闻列表 + 右侧热点文件 ══ -->
    <div class="bottom-section">
      <!-- 新闻列表 -->
      <div class="news-section">
        <div class="news-header">
          <h3 class="section-label" style="margin:0">资讯列表</h3>
          <div class="view-toggle">
            <button :class="{ active: viewMode === 'list' }" @click="viewMode = 'list'">
              <svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line></svg>
              列表
            </button>
            <button :class="{ active: viewMode === 'card' }" @click="viewMode = 'card'">
              <svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>
              卡片
            </button>
          </div>
        </div>

        <!-- 列表模式 -->
        <div
          v-if="viewMode === 'list'"
          ref="newsScrollRef"
          class="news-list-view"
          @scroll="handleNewsScroll"
        >
          <div v-if="newsLoading" class="news-skeleton">
            <div v-for="i in 5" :key="i" class="skeleton-row">
              <div class="sk-tag"></div>
              <div class="sk-title"></div>
              <div class="sk-meta"></div>
            </div>
          </div>
          <div
            v-else
            v-for="(item, idx) in newsList"
            :key="idx"
            class="news-list-item"
            @click="openLink(item.link)"
          >
            <div class="nl-thumb" :style="getNewsThumbStyle(idx)">
              <img
                v-if="getNewsCover(idx)"
                :src="getNewsCover(idx)"
                :alt="item.title || 'news cover'"
                loading="lazy"
                decoding="async"
                fetchpriority="low"
              />
            </div>
            <span class="nl-type" :class="item.source_type === 'policy' ? 'type-policy' : 'type-news'">
              {{ item.source_type === 'policy' ? '政策' : '时事' }}
            </span>
            <div class="nl-content">
              <p class="nl-title">{{ item.title }}</p>
              <p class="nl-desc" v-if="item.description">{{ stripHtml(item.description) }}</p>
            </div>
            <div class="nl-right">
              <span class="complexity-badge" :class="getComplexityClass(item)">
                AI复杂度 {{ getComplexityScore(item) }}
              </span>
              <span class="nl-date">{{ formatDate(item.pubDate) }}</span>
            </div>
          </div>
        </div>

        <!-- 卡片模式 -->
        <div
          v-else
          ref="newsScrollRef"
          class="news-card-view"
          @scroll="handleNewsScroll"
        >
          <div v-if="newsLoading" class="news-skeleton card-skeleton">
            <div v-for="i in 6" :key="i" class="skeleton-card"></div>
          </div>
          <div
            v-else
            v-for="(item, idx) in newsList"
            :key="idx"
            class="news-card"
            @click="openLink(item.link)"
          >
            <div class="nc-header" :style="getNewsCardHeaderStyle(idx)">
              <img
                v-if="getNewsCover(idx)"
                class="nc-cover"
                :src="getNewsCover(idx)"
                :alt="item.title || 'news cover'"
                loading="lazy"
                decoding="async"
                fetchpriority="low"
              />
              <span class="nc-header-mask"></span>
              <span class="nc-type">{{ item.source_type === 'policy' ? '政策' : '时事' }}</span>
            </div>
            <div class="nc-body">
              <p class="nc-title">{{ item.title }}</p>
              <p class="nc-desc" v-if="item.description">{{ stripHtml(item.description) }}</p>
            </div>
            <div class="nc-footer">
              <span class="complexity-badge" :class="getComplexityClass(item)">
                AI复杂度 {{ getComplexityScore(item) }}
              </span>
              <span class="nc-date">{{ formatDate(item.pubDate) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧热点文件 -->
      <div class="hot-docs-panel">
        <div class="hdp-header">
          <span class="hdp-dot"></span>
          <span class="hdp-title">热点文件 Top 5</span>
        </div>
        <div class="hdp-list">
          <div
            v-for="(doc, idx) in hotDocs"
            :key="idx"
            class="hdp-item"
            @click="openLink(doc.link)"
          >
            <span class="hdp-rank" :class="idx < 3 ? 'rank-top' : ''">{{ idx + 1 }}</span>
            <div class="hdp-content">
              <p class="hdp-text">{{ doc.title }}</p>
              <span class="hdp-date">{{ formatDate(doc.pubDate) }}</span>
            </div>
          </div>
          <div v-if="docsLoading" class="loading-placeholder">
            <div v-for="i in 3" :key="i" class="skeleton-line"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- ══ 全景政策广场：认证主体上传的真实政务文件 ══ -->
    <div class="policy-square">
      <div class="ps-header">
        <div class="ps-title-row">
          <span class="ps-dot"></span>
          <h3 class="section-label" style="margin:0">全景政策广场</h3>
          <span class="ps-sub">认证主体发布的最新政务文件</span>
        </div>
        <div class="ps-controls">
          <button class="ps-mode-btn" :class="{ active: policyDocViewMode === 'list' }" @click="policyDocViewMode = 'list'">
            <svg viewBox="0 0 24 24" width="13" height="13" stroke="currentColor" stroke-width="2" fill="none"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line></svg>
            条形
          </button>
          <button class="ps-mode-btn" :class="{ active: policyDocViewMode === 'grid' }" @click="policyDocViewMode = 'grid'">
            <svg viewBox="0 0 24 24" width="13" height="13" stroke="currentColor" stroke-width="2" fill="none"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>
            砖块
          </button>
          <router-link to="/public-opinion-hall" class="ps-hall-link">民意评议大厅 →</router-link>
        </div>
      </div>

      <div v-if="policyDocsLoading" class="ps-skeleton">
        <div v-for="i in 4" :key="i" class="skeleton-card"></div>
      </div>
      <div v-else-if="!policyDocs.length" class="ps-empty">
        暂无已审核的政务文件，认证主体上传后经管理员审核即可展示
      </div>
      <div v-else class="ps-list" :class="policyDocViewMode">
        <div v-for="(doc, i) in policyDocs" :key="doc.id" class="ps-card">
          <div class="ps-card-accent" :style="{ background: POLICY_COLORS[i % POLICY_COLORS.length] }"></div>
          <div class="ps-card-body">
            <div class="ps-card-meta">
              <span class="ps-category" v-if="doc.category">{{ doc.category }}</span>
              <span class="ps-uploader">{{ doc.uploader_name }}</span>
              <span class="ps-date">{{ formatDate(doc.created_time) }}</span>
            </div>
            <p class="ps-card-title">{{ doc.title }}</p>
            <p class="ps-card-content">{{ doc.content?.slice(0, 80) }}{{ doc.content?.length > 80 ? '...' : '' }}</p>
            <div class="ps-card-tags" v-if="doc.tags">
              <span v-for="tag in doc.tags.split(',')" :key="tag" class="ps-tag">{{ tag.trim() }}</span>
            </div>
          </div>
          <div class="ps-card-footer">
            <span class="ps-stat">
              <svg viewBox="0 0 24 24" width="12" height="12" stroke="currentColor" stroke-width="2" fill="none"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
              {{ doc.view_count }}
            </span>
            <button class="ps-like-btn" @click.stop="likeDoc(doc)">
              <svg viewBox="0 0 24 24" width="12" height="12" stroke="currentColor" stroke-width="2" fill="none"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3H14z"></path><path d="M7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path></svg>
              {{ doc.like_count }}
            </button>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { getHotNews, getCentralDocs, getDailySummary, searchNews } from '@/api/news';
import { apiClient, API_ROUTES } from '@/router/api_routes';
import { useUserStore } from '@/stores/auth.js';

const router = useRouter();
const userStore = useUserStore();
let slideTimer = null;
let searchDebounceTimer = null;
// ── 轮播 ──────────────────────────────────────────────────────────────────────
const slideIdx = ref(0);
const discoverSlideModules = import.meta.glob('/src/assets/photos/discover/*.jpg', { eager: true });
const discoverSlideImages = Object.entries(discoverSlideModules)
  .sort(([a], [b]) => a.localeCompare(b, 'zh-CN'))
  .map(([, mod]) => mod.default);

const slideMetaPool = [
  {
    tag: '智能解析',
    title: '极速识别文件',
    desc: '上传通知、政策文件，AI 秒级提取关键信息',
    bg: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
    action: () => router.push('/'),
  },
  {
    tag: '多版本改写',
    title: '适配不同人群',
    desc: '老人版、学生版、极简版，一键切换表达风格',
    bg: 'linear-gradient(135deg, #c0392b 0%, #8e44ad 100%)',
    action: () => router.push('/rewrite'),
  },
  {
    tag: '数据分析',
    title: '可视化政务数据',
    desc: '多维度图表，直观呈现文件处理统计',
    bg: 'linear-gradient(135deg, #16a085 0%, #2980b9 100%)',
    action: () => router.push('/feature-b'),
  },
  {
    tag: '政策广场',
    title: '文件与情报统一检索',
    desc: '从热点问题到政策文件，快速定位关键信息',
    bg: 'linear-gradient(135deg, #1f6feb 0%, #0ea5e9 100%)',
    action: () => router.push('/search'),
  },
  {
    tag: '效能数据',
    title: '监测与趋势可视化',
    desc: '联通政务场景与访问数据，支持决策分析',
    bg: 'linear-gradient(135deg, #e67e22 0%, #f39c12 100%)',
    action: () => router.push('/data-analysis-and-visualization'),
  },
];

const slides = (discoverSlideImages.length ? discoverSlideImages : ['']).map((img, idx) => {
  const meta = slideMetaPool[idx % slideMetaPool.length];
  return { ...meta, img };
});

const discoverNewsModules = import.meta.glob('/src/assets/photos/discover/news/*.{jpg,jpeg,png,webp}', { eager: true });
const discoverNewsImages = Object.entries(discoverNewsModules)
  .sort(([a], [b]) => a.localeCompare(b, 'zh-CN'))
  .map(([, mod]) => mod.default);

const getNewsCover = (idx) => {
  if (!discoverNewsImages.length) return '';
  return discoverNewsImages[idx % discoverNewsImages.length];
};

const getNewsCardHeaderStyle = (idx) => {
  return { background: cardColors[idx % cardColors.length] };
};

const getNewsThumbStyle = (idx) => {
  return { background: cardColors[idx % cardColors.length] };
};
const prewarmNewsCovers = () => {
  if (!discoverNewsImages.length) return;
  const run = () => {
    discoverNewsImages.forEach((src) => {
      const img = new Image();
      img.decoding = 'async';
      img.src = src;
      if (img.decode) img.decode().catch(() => {});
    });
  };
  if (typeof window !== 'undefined' && 'requestIdleCallback' in window) {
    window.requestIdleCallback(run, { timeout: 1200 });
  } else {
    setTimeout(run, 160);
  }
};
// ── 传送带 ────────────────────────────────────────────────────────────────────
// 使用 CSS animation，无需 JS timer

// ── 顶部搜索框 ────────────────────────────────────────────────────────────────
const searchInput = ref('');
const searchFocused = ref(false);
const searchResults = ref([]);
const searchLoading = ref(false);
const hotTags = ['改革', '政策', '乡村振兴', '营商环境', '医疗', '教育', '就业', '数字经济'];
const recentDocs = ref([]);
const recentNews = ref([]);
const nextSlide = () => { slideIdx.value = (slideIdx.value + 1) % slides.length; };
const prevSlide = () => { slideIdx.value = (slideIdx.value - 1 + slides.length) % slides.length; };

// ── 今日政务概况 ──────────────────────────────────────────────────────────────
const summaryData = ref({});
const summaryLoading = ref(true);

// ── 砖块功能 ──────────────────────────────────────────────────────────────────
const bricks = [
  { id: 1, name: '极速识别', desc: '上传文件即时解析', size: 'brick-lg', color: '#1565c0', hot: true, colSpan: 5, rowSpan: 4,
    iconProps: { viewBox: '0 0 24 24', width: '28', height: '28', stroke: '#fff', 'stroke-width': '2', fill: 'none' },
    iconPath: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line>',
    action: () => router.push('/'),
  },
  { id: 2, name: '多版本改写', desc: '一键适配不同人群', size: 'brick-md', color: '#2e7d32', hot: true, colSpan: 3, rowSpan: 4,
    iconProps: { viewBox: '0 0 24 24', width: '24', height: '24', stroke: '#fff', 'stroke-width': '2', fill: 'none' },
    iconPath: '<path d="M12 20h9"></path><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path>',
    action: () => router.push('/rewrite'),
  },
  { id: 3, name: '数据分析看板', desc: '查看可视化统计图表', size: 'brick-md', color: '#8e44ad', hot: true, colSpan: 4, rowSpan: 4,
    iconProps: { viewBox: '0 0 24 24', width: '24', height: '24', stroke: '#fff', 'stroke-width': '2', fill: 'none' },
    iconPath: '<line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line>',
    action: () => router.push('/data-analysis-and-visualization'),
  },
  { id: 4, name: '待办清单', desc: '管理办事任务进度', size: 'brick-md', color: '#1565c0', colSpan: 4, rowSpan: 4,
    iconProps: { viewBox: '0 0 24 24', width: '24', height: '24', stroke: '#fff', 'stroke-width': '2', fill: 'none' },
    iconPath: '<path d="M9 11l3 3L22 4"></path><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path>',
    action: () => router.push('/todo'),
  },
  { id: 5, name: '政策发布中心', desc: '认证主体发布与管理政策', size: 'brick-md', color: '#00695c', colSpan: 4, rowSpan: 4,
    iconProps: { viewBox: '0 0 24 24', width: '24', height: '24', stroke: '#fff', 'stroke-width': '2', fill: 'none' },
    iconPath: '<rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line>',
    action: () => router.push('/policy-publish-center'),
  },
  { id: 6, name: '民意评议大厅', desc: '查看实时评议与反馈', size: 'brick-md', color: '#e65100', colSpan: 4, rowSpan: 4,
    iconProps: { viewBox: '0 0 24 24', width: '24', height: '24', stroke: '#fff', 'stroke-width': '2', fill: 'none' },
    iconPath: '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>',
    action: () => router.push('/public-opinion-hall'),
  },
  { id: 7, name: '政策检索', desc: '关键词搜索政策与时事', size: 'brick-sm', color: '#0277bd', hot: true, colSpan: 3, rowSpan: 2,
    iconProps: { viewBox: '0 0 24 24', width: '20', height: '20', stroke: '#fff', 'stroke-width': '2', fill: 'none' },
    iconPath: '<circle cx="11" cy="11" r="7"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line>',
    action: () => router.push('/search'),
  },
  { id: 11, name: '政策速览', desc: '卡片滑动浏览政策', size: 'brick-sm', color: '#0d9488', colSpan: 3, rowSpan: 2,
    iconProps: { viewBox: '0 0 24 24', width: '20', height: '20', stroke: '#fff', 'stroke-width': '2', fill: 'none' },
    iconPath: '<rect x="3" y="5" width="18" height="14" rx="2"></rect><line x1="8" y1="9" x2="16" y2="9"></line><line x1="8" y1="13" x2="13" y2="13"></line>',
    action: () => router.push('/policy-swipe'),
  },
  { id: 8, name: '智能体助手', desc: '与政策智能体对话', size: 'brick-sm', color: '#37474f', colSpan: 3, rowSpan: 4,
    iconProps: { viewBox: '0 0 24 24', width: '20', height: '20', stroke: '#fff', 'stroke-width': '2', fill: 'none' },
    iconPath: '<rect x="3" y="3" width="18" height="14" rx="2"></rect><path d="M8 21h8"></path><path d="M12 17v4"></path>',
    action: () => router.push('/agent'),
  },
  { id: 9, name: '会话历史', desc: '查看历史解析记录', size: 'brick-sm', color: '#455a64', colSpan: 6, rowSpan: 2,
    iconProps: { viewBox: '0 0 24 24', width: '20', height: '20', stroke: '#fff', 'stroke-width': '2', fill: 'none' },
    iconPath: '<circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline>',
    action: () => router.push('/history'),
  },
  { id: 10, name: '收藏夹', desc: '收藏的重要解析记录', size: 'brick-sm', color: '#5d4037', colSpan: 3, rowSpan: 4,
    iconProps: { viewBox: '0 0 24 24', width: '20', height: '20', stroke: '#fff', 'stroke-width': '2', fill: 'none' },
    iconPath: '<path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path>',
    action: () => router.push('/favorites'),
  },
];

// ── 全景政策广场（认证主体上传的真实政务文件）────────────────────────────────
const policyDocs = ref([]);
const policyDocsLoading = ref(true);
const policyDocViewMode = ref('list');
const POLICY_COLORS = ['#c0392b', '#2980b9', '#27ae60', '#8e44ad', '#e67e22'];

async function loadPolicyDocs() {
  try {
    const res = await apiClient.get(API_ROUTES.POLICY_DOCS_APPROVED, { params: { limit: 20 } });
    policyDocs.value = res.data;
  } catch (e) {
    console.warn('政务文件加载失败', e);
  } finally {
    policyDocsLoading.value = false;
  }
}

const likeDoc = async (doc) => {
  try {
    const res = await apiClient.post(API_ROUTES.POLICY_DOC_LIKE(doc.id));
    doc.like_count = res.data.like_count;
  } catch (e) { console.error(e); }
};

// ── 新闻列表 ──────────────────────────────────────────────────────────────────
const newsList = ref([]);
const newsLoading = ref(true);
const viewMode = ref('card');
const cardColors = ['#c0392b', '#2980b9', '#27ae60', '#e67e22', '#8e44ad', '#16a085'];
const newsScrollRef = ref(null);
const pageScrollRef = ref(null);

// ── 热点文件 ──────────────────────────────────────────────────────────────────
const hotDocs = ref([]);
const allHotDocs = ref([]);
const docsLoading = ref(true);
const HOT_DOCS_BASE_COUNT = 5;

// ── 生命周期 ──────────────────────────────────────────────────────────────────
onMounted(() => {
  slideTimer = setInterval(nextSlide, 4000);
  prewarmNewsCovers();
  loadSummary();
  loadNews();
  loadDocs();
  loadPolicyDocs();
});

onUnmounted(() => {
  clearInterval(slideTimer);
  clearTimeout(searchDebounceTimer);
});

async function loadSummary() {
  try {
    const res = await getDailySummary();
    summaryData.value = res.data;
  } catch (e) {
    console.warn('政务概况加载失败', e);
  } finally {
    summaryLoading.value = false;
  }
}

async function loadNews() {
  try {
    const newsRes = await getHotNews(16);
    const news = (newsRes.data.items || []).map(i => ({ ...i, source_type: 'news' }));
    newsList.value = news;
    recentNews.value = news.slice(0, 3);
    await nextTick();
    syncHotDocsByNewsScroll();
  } catch (e) {
    console.warn('新闻加载失败', e);
  } finally {
    newsLoading.value = false;
  }
}

async function loadDocs() {
  try {
    const [docsRes, hotNewsRes] = await Promise.all([
      getCentralDocs(50),
      getHotNews(50),
    ]);
    const docs = docsRes.data.items || [];
    const hotNews = hotNewsRes.data.items || [];
    const merged = [...docs, ...hotNews];
    const dedup = [];
    const seen = new Set();
    for (const item of merged) {
      const key = item.link || item.title;
      if (!key || seen.has(key)) continue;
      seen.add(key);
      dedup.push(item);
    }
    allHotDocs.value = dedup;
    hotDocs.value = allHotDocs.value.slice(0, HOT_DOCS_BASE_COUNT);
    recentDocs.value = docs.slice(0, HOT_DOCS_BASE_COUNT);
    // 合并政策文件到新闻列表
    const policyDocsForNews = recentDocs.value.map(i => ({ ...i, source_type: 'policy' }));
    newsList.value = [...newsList.value, ...policyDocsForNews];
    await nextTick();
    syncHotDocsByNewsScroll();
  } catch (e) {
    console.warn('热点文件加载失败', e);
  } finally {
    docsLoading.value = false;
  }
}

const syncHotDocsByNewsScroll = () => {
  if (!allHotDocs.value.length) return;
  const getProgress = () => {
    const leftEl = newsScrollRef.value;
    if (leftEl) {
      const leftMax = leftEl.scrollHeight - leftEl.clientHeight;
      if (leftMax > 8) {
        return Math.min(1, Math.max(0, leftEl.scrollTop / leftMax));
      }
    }
    const pageEl = pageScrollRef.value;
    if (pageEl) {
      const pageMax = pageEl.scrollHeight - pageEl.clientHeight;
      if (pageMax > 8) {
        return Math.min(1, Math.max(0, pageEl.scrollTop / pageMax));
      }
    }
    return 0;
  };

  const progress = getProgress();
  const maxByNews = newsList.value.length ? Math.min(allHotDocs.value.length, newsList.value.length) : allHotDocs.value.length;
  const extra = Math.ceil((maxByNews - HOT_DOCS_BASE_COUNT) * progress);
  const target = HOT_DOCS_BASE_COUNT + extra;
  hotDocs.value = allHotDocs.value.slice(0, Math.max(HOT_DOCS_BASE_COUNT, target));
};

const handleNewsScroll = () => {
  syncHotDocsByNewsScroll();
};

const openLink = (url) => { if (url) window.open(url, '_blank'); };
const goSearch = () => { if (searchInput.value.trim()) router.push({ path: '/search', query: { q: searchInput.value } }); };
const quickSearch = (tag) => { router.push({ path: '/search', query: { q: tag } }); };
const handleSearchBlur = () => {
  setTimeout(() => {
    searchFocused.value = false;
  }, 120);
};
const openSearchItem = (item) => {
  if (!item) return;
  if (item.link) {
    openLink(item.link);
    return;
  }
  quickSearch(item.title || searchInput.value);
};

watch(searchInput, (val) => {
  clearTimeout(searchDebounceTimer);
  const keyword = val.trim();
  if (!keyword) {
    searchResults.value = [];
    searchLoading.value = false;
    return;
  }
  searchDebounceTimer = setTimeout(async () => {
    searchLoading.value = true;
    try {
      const res = await searchNews(keyword, 10);
      const items = res.data?.items || [];
      const lower = keyword.toLowerCase();
      const prefix = items.filter(item => (item.title || '').toLowerCase().startsWith(lower));
      const rest = items.filter(item => !(item.title || '').toLowerCase().startsWith(lower));
      searchResults.value = [...prefix, ...rest].slice(0, 8);
    } catch (e) {
      console.warn('前缀搜索失败', e);
      searchResults.value = [];
    } finally {
      searchLoading.value = false;
    }
  }, 220);
});

watch(viewMode, async () => {
  await nextTick();
  syncHotDocsByNewsScroll();
});
const stripHtml = (html) => {
  if (!html) return '';
  return html.replace(/<[^>]*>/g, '').replace(/&nbsp;/g, ' ').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').trim();
};

const formatDate = (d) => {
  if (!d) return '';
  const s = String(d);
  return s.length > 10 ? s.slice(0, 10) : s;
};

const getComplexityScore = (item) => {
  const title = item.title || '';
  const complexWords = ['改革', '政策', '规定', '条例', '办法', '意见', '通知', '决定'];
  let score = Math.min(title.length / 5, 5);
  complexWords.forEach(w => { if (title.includes(w)) score += 0.5; });
  return Math.min(Math.round(score * 10) / 10, 9.9).toFixed(1);
};

const getComplexityClass = (item) => {
  const s = parseFloat(getComplexityScore(item));
  if (s >= 7) return 'cx-high';
  if (s >= 4) return 'cx-mid';
  return 'cx-low';
};
</script>

<style scoped>
/* ── 全景政策广场 ── */
.policy-square {
  background: var(--color-bg-card, #fff);
  border: 1px solid var(--color-border, #e8e8e8);
  border-radius: 4px;
  padding: 20px;
  margin-bottom: 20px;
}
.ps-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.ps-title-row { display: flex; align-items: center; gap: 8px; }
.policy-square .section-label { color: #111; }
.ps-dot { width: 8px; height: 8px; border-radius: 50%; background: #c0392b; }
.ps-sub { font-size: 12px; color: #999; }
.ps-controls { display: flex; align-items: center; gap: 8px; }
.ps-mode-btn {
  display: flex; align-items: center; gap: 4px;
  background: none; border: 1px solid var(--color-border, #e8e8e8);
  padding: 4px 10px; border-radius: 4px; font-size: 12px; cursor: pointer; color: #666;
  transition: all 0.2s;
}
.ps-mode-btn.active, .ps-mode-btn:hover { background: #c0392b; color: #fff; border-color: #c0392b; }
.ps-hall-link { font-size: 12px; color: #c0392b; text-decoration: none; white-space: nowrap; }
.ps-empty { text-align: center; color: #999; font-size: 13px; padding: 30px; }
.ps-skeleton { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }

.ps-list { display: flex; flex-direction: column; gap: 10px; }
.ps-list.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); }

.ps-card {
  display: flex; border: 1px solid var(--color-border, #e8e8e8);
  border-radius: 4px; overflow: hidden; transition: box-shadow 0.2s;
}
.ps-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.07); }
.ps-list.grid .ps-card { flex-direction: column; }

.ps-card-accent { width: 4px; flex-shrink: 0; }
.ps-list.grid .ps-card-accent { width: 100%; height: 4px; }

.ps-card-body { flex: 1; padding: 12px 14px; }
.ps-card-meta { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; flex-wrap: wrap; }
.ps-category { font-size: 11px; background: #f0f0f0; padding: 2px 8px; border-radius: 10px; }
.ps-uploader { font-size: 12px; font-weight: 600; }
.ps-date { font-size: 11px; color: #999; margin-left: auto; }
.ps-card-title { font-size: 14px; font-weight: 700; margin: 0 0 6px; line-height: 1.4; }
.ps-card-content { font-size: 13px; color: #666; margin: 0 0 8px; line-height: 1.5; }
.ps-card-tags { display: flex; flex-wrap: wrap; gap: 4px; }
.ps-tag { font-size: 11px; background: #fce4e4; color: #c0392b; padding: 2px 7px; border-radius: 10px; }

.ps-card-footer {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 14px; border-top: 1px solid var(--color-border, #f0f0f0);
  font-size: 12px; color: #999;
}
.ps-stat { display: flex; align-items: center; gap: 4px; }
.ps-like-btn {
  display: flex; align-items: center; gap: 4px;
  background: none; border: none; cursor: pointer; color: #999; font-size: 12px;
  transition: color 0.2s;
}
.ps-like-btn:hover { color: #c0392b; }

.discover-page {
  height: 100%;
  overflow-y: auto;
  padding: 16px 20px;
  background: linear-gradient(135deg, #1a0a09 0%, #c0392b 40%, #2980b9 100%);
  display: flex;
  flex-direction: column;
  gap: 14px;
}

/* ── 顶部区域布局 ─────────────────────────────────────────────────────────── */
.top-section {
  flex-shrink: 0;
  margin-left: -20px;
  margin-right: -20px;
}
.panorama-hero {
  position: relative;
  border-radius: 18px;
  overflow: hidden;
  height: clamp(260px, 33vh, 420px);
  border: 1px solid rgba(255,255,255,0.2);
  box-shadow: 0 16px 40px rgba(0,0,0,0.25);
}
.hero-slide {
  width: 100%;
  height: 100%;
  background-size: cover;
  background-position: center;
  position: relative;
  cursor: pointer;
}
.hero-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(145deg, rgba(0,0,0,0.5) 0%, rgba(0,0,0,0.18) 45%, rgba(0,0,0,0.4) 100%);
}
.hero-content {
  position: absolute;
  left: 26px;
  bottom: 28px;
  color: #fff;
  z-index: 2;
  max-width: 45%;
}
.hero-desc {
  margin: 8px 0 0;
  font-size: 13px;
  line-height: 1.6;
  color: rgba(255,255,255,0.85);
}
.hero-arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(15, 23, 42, 0.45);
  color: #fff;
  cursor: pointer;
  z-index: 3;
}
.hero-arrow.left { left: 14px; }
.hero-arrow.right { left: calc(100% - 14px - 36px - 300px); }
.hero-arrow:hover { background: rgba(15, 23, 42, 0.7); }
.hero-dots {
  position: absolute;
  left: 24px;
  bottom: 16px;
  display: flex;
  gap: 6px;
  z-index: 3;
}
.hero-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: rgba(255,255,255,0.35);
  cursor: pointer;
  transition: all 0.2s;
}
.hero-dot.active { width: 22px; background: #fff; }

/* 搜索框 */
.tsb-input-wrap {
  position: absolute;
  top: 16px;
  left: 16px;
  width: clamp(240px, 25vw, 460px);
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(112, 116, 124, 0.46);
  border: 1px solid rgba(255,255,255,0.35);
  border-radius: 999px;
  padding: 8px 10px 8px 12px;
  color: rgba(255,255,255,0.85);
  transition: border-color 0.2s, background 0.2s;
  z-index: 4;
}
.tsb-input-wrap:focus-within { border-color: rgba(255,255,255,0.75); background: rgba(80, 84, 91, 0.58); }
.tsb-input-wrap input {
  border: none; outline: none; flex: 1;
  font-size: 13px; color: #fff; background: transparent;
}
.tsb-input-wrap input::placeholder { color: rgba(255,255,255,0.72); }
.tsb-clear {
  background: none; border: none; cursor: pointer; color: rgba(255,255,255,0.8); padding: 0; display: flex;
}
.tsb-btn {
  background: rgba(255,255,255,0.94); color: #2c3e50; border: none;
  border-radius: 999px; padding: 5px 12px;
  font-size: 12px; font-weight: 600; cursor: pointer; white-space: nowrap; transition: all 0.2s;
}
.tsb-btn:hover { background: #fff; }

.search-popover {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  width: 100%;
  background: rgba(255,255,255,0.96);
  border: 1px solid rgba(0,0,0,0.06);
  border-radius: 14px;
  box-shadow: 0 12px 32px rgba(0,0,0,0.18);
  padding: 10px;
  z-index: 6;
}

:global([data-theme="dark"]) .search-popover {
  background: rgba(30,30,30,0.96);
  border: 1px solid rgba(255,255,255,0.1);
}
.pop-section { display: flex; flex-direction: column; gap: 8px; }
.pop-section + .pop-section { margin-top: 10px; }
.pop-title { font-size: 11px; font-weight: 700; color: #475569; letter-spacing: 0.4px; }

:global([data-theme="dark"]) .pop-title { color: #cbd5e1; }

.rec-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.rec-tag {
  font-size: 11px; background: #f8fafc; color: #334155;
  border: 1px solid #d6dbe3; padding: 4px 10px;
  border-radius: 999px; cursor: pointer; transition: all 0.2s;
}
.rec-tag:hover { background: #e2e8f0; }

:global([data-theme="dark"]) .rec-tag {
  background: rgba(255,255,255,0.1);
  color: #e2e8f0;
  border: 1px solid rgba(255,255,255,0.15);
}
:global([data-theme="dark"]) .rec-tag:hover { background: rgba(255,255,255,0.15); }

.pop-list { display: flex; flex-direction: column; gap: 6px; }
.pop-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 8px;
  cursor: pointer;
}
.pop-item:hover { background: #f1f5f9; }

:global([data-theme="dark"]) .pop-item:hover { background: rgba(255,255,255,0.08); }

.pop-item-type {
  font-size: 10px;
  color: #334155;
  background: #e2e8f0;
  border-radius: 10px;
  padding: 2px 7px;
}

:global([data-theme="dark"]) .pop-item-type {
  color: #e2e8f0;
  background: rgba(255,255,255,0.15);
}

.pop-item-text {
  flex: 1;
  min-width: 0;
  font-size: 12px;
  color: #1f2937;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

:global([data-theme="dark"]) .pop-item-text { color: #e2e8f0; }

.pop-empty { font-size: 12px; color: #64748b; padding: 6px 2px; }

:global([data-theme="dark"]) .pop-empty { color: #94a3b8; }

@keyframes heroFade {
  from { opacity: 0.4; transform: scale(1.01); }
  to { opacity: 1; transform: scale(1); }
}
.hero-fade-enter-active, .hero-fade-leave-active { transition: opacity 0.35s ease; }
.hero-fade-enter-from, .hero-fade-leave-to { opacity: 0; }

.panorama-tag {
  font-size: 10px; color: rgba(255,255,255,0.85);
  background: rgba(255,255,255,0.15); padding: 2px 8px;
  border-radius: 10px; align-self: flex-start; margin-bottom: 6px;
}
.panorama-title {
  margin: 0; font-size: 15px; font-weight: 700; color: #fff;
  text-shadow: 0 1px 4px rgba(0,0,0,0.4);
}
/* 今日政务概况 */
.gov-summary-card {
  position: absolute;
  right: 14px;
  top: 14px;
  bottom: 14px;
  width: 280px;
  background: rgba(111, 115, 123, 0.42);
  border-radius: 14px;
  border: 1px solid rgba(255,255,255,0.26);
  backdrop-filter: blur(3px);
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  z-index: 2;
}
.summary-header {
  display: flex;
  align-items: center;
  gap: 8px;
}
.summary-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: #f59e0b;
  flex-shrink: 0;
}
.summary-title { font-size: 13px; font-weight: 700; color: #f8fafc; flex: 1; }
.summary-time { font-size: 11px; color: rgba(255,255,255,0.72); }
.summary-body { display: flex; flex-direction: column; gap: 10px; }
.summary-stat { display: flex; align-items: baseline; gap: 6px; }
.stat-num { font-size: 26px; font-weight: 800; color: #fff; line-height: 1; }
.stat-label { font-size: 12px; color: rgba(255,255,255,0.78); }
.summary-divider { height: 1px; background: rgba(255,255,255,0.25); }
.summary-item { display: flex; flex-direction: column; gap: 4px; }
.si-label { font-size: 11px; color: rgba(255,255,255,0.76); font-weight: 600; letter-spacing: 0.5px; }
.si-text {
  margin: 0;
  font-size: 12px;
  color: rgba(255,255,255,0.94);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.summary-loading { display: flex; flex-direction: column; gap: 10px; }

/* ── 砖块功能 ─────────────────────────────────────────────────────────────── */
.bricks-section { flex-shrink: 0; }
.section-label {
  font-size: 14px;
  font-weight: 700;
  color: rgba(255,255,255,0.9);
  margin: 0 0 8px;
}

/* 砖块墙 */
.masonry-wall {
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  grid-auto-rows: 34px;
  grid-auto-flow: dense;
  gap: 6px;
}

.brick-item {
  background: linear-gradient(
    135deg,
    color-mix(in srgb, var(--brick-color, #1565c0) 78%, #000 22%) 0%,
    var(--brick-color, #1565c0) 48%,
    color-mix(in srgb, var(--brick-color, #1565c0) 72%, #fff 28%) 100%
  );
  border-radius: 0;
  box-sizing: border-box;
  padding: 12px 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
  position: relative;
  overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s;
  min-height: 100%;
  border: 1px solid rgba(255,255,255,0.15);
  box-shadow: 0 2px 8px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.15);
}
.brick-item.brick-lg { padding: 16px 18px; }
.brick-item.brick-sm { padding: 10px 14px; }

.brick-item:not(.disabled):hover {
  transform: translateY(-3px) scale(1.02);
  box-shadow: 0 8px 24px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.25);
}
.brick-item.disabled { opacity: 0.55; cursor: not-allowed; }

/* 反光效果 */
.brick-shine {
  position: absolute;
  top: 0; left: -60%;
  width: 40%;
  height: 100%;
  background: linear-gradient(105deg, transparent 40%, rgba(255,255,255,0.18) 50%, transparent 60%);
  pointer-events: none;
  transition: left 0.4s ease;
}
.brick-item:not(.disabled):hover .brick-shine { left: 120%; }

/* 边缘高光 */
.brick-edge {
  position: absolute;
  inset: 0;
  border-radius: 0;
  border: 1px solid rgba(255,255,255,0.2);
  pointer-events: none;
}
.brick-icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}
.brick-info { display: flex; flex-direction: column; gap: 2px; }
.brick-name { font-size: 13px; font-weight: 700; color: #fff; white-space: nowrap; }
.brick-desc { font-size: 10px; color: rgba(255,255,255,0.65); white-space: nowrap; }
.brick-badge {
  position: absolute;
  top: 6px;
  right: 6px;
  font-size: 9px;
  background: rgba(255,255,255,0.2);
  color: #fff;
  padding: 1px 6px;
  border-radius: 0;
  font-weight: 600;
}
.brick-badge.hot { background: #e74c3c; }

/* ── 下部区域 ─────────────────────────────────────────────────────────────── */
.bottom-section {
  display: grid;
  grid-template-columns: 1fr 240px;
  gap: 16px;
  flex: 1;
  min-height: 0;
}

/* 新闻列表 */
.news-section {
  background: transparent;
  border-radius: 16px;
  border: none;
  box-shadow: none;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.news-header {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  position: relative;
  padding: 10px 16px 8px;
  background: transparent;
  border-radius: 0;
  flex-shrink: 0;
}
.news-header .section-label {
  color: #fff;
  margin: 0;
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}
.view-toggle {
  display: flex;
  gap: 4px;
  background: rgba(255,255,255,0.15);
  border-radius: 8px;
  padding: 3px;
}
.view-toggle button {
  display: flex;
  align-items: center;
  gap: 4px;
  background: none;
  border: none;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  color: #666;
  cursor: pointer;
  transition: all 0.2s;
}
.view-toggle button.active { background: #fff; color: #000; font-weight: 600; }

/* 列表视图 */
.news-list-view { flex: 1; overflow-y: auto; }
.news-list-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 16px;
  background: #fff;
  border-bottom: 1px solid #f5f5f5;
  cursor: pointer;
  transition: background 0.15s;
}
.news-list-item:hover { background: #fafafa; }
.nl-thumb {
  width: 92px;
  height: 60px;
  border-radius: 8px;
  overflow: hidden;
  position: relative;
  flex-shrink: 0;
}
.nl-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.nl-type {
  flex-shrink: 0;
  font-size: 10px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 10px;
  margin-top: 2px;
}
.type-news { background: #e6f7ff; color: #0077cc; }
.type-policy { background: #fff0f0; color: #c0392b; }
.nl-content { flex: 1; min-width: 0; }
.nl-title {
  margin: 0 0 3px;
  font-size: 13px;
  font-weight: 600;
  color: #111;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.nl-desc {
  margin: 0;
  font-size: 11px;
  color: #888;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.nl-right { flex-shrink: 0; display: flex; flex-direction: column; align-items: flex-end; gap: 4px; }
.nl-date { font-size: 11px; color: #bbb; }

/* 卡片视图 */
.news-card-view {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  align-content: start;
}
.news-card {
  border-radius: 10px;
  border: none;
  background: #fff;
  overflow: hidden;
  cursor: pointer;
  transition: box-shadow 0.2s;
  display: flex;
  flex-direction: column;
}
.news-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.1); }
.nc-header {
  position: relative;
  height: 240px;
  display: flex;
  align-items: flex-end;
  padding: 8px 10px;
  overflow: hidden;
}
.nc-cover {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.nc-header-mask {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(0,0,0,0.05) 0%, rgba(0,0,0,0.45) 100%);
}
.nc-type {
  position: relative;
  z-index: 1;
  font-size: 10px;
  color: rgba(255,255,255,0.9);
  font-weight: 700;
}
.nc-body { padding: 10px; flex: 1; }
.nc-title { margin: 0 0 4px; font-size: 12px; font-weight: 600; color: #111; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.nc-desc { margin: 0; font-size: 11px; color: #888; line-height: 1.3; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.nc-footer { padding: 8px 10px; border-top: 1px solid #f5f5f5; display: flex; align-items: center; justify-content: space-between; }
.nc-date { font-size: 10px; color: #bbb; }

/* AI 复杂度 */
.complexity-badge {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 10px;
}
.cx-high { background: #fff0f0; color: #c0392b; }
.cx-mid  { background: #fff8e6; color: #e67e22; }
.cx-low  { background: #f0fff4; color: #27ae60; }

/* 骨架屏 */
.news-skeleton { padding: 12px 16px; display: flex; flex-direction: column; gap: 12px; }
.skeleton-row { display: flex; align-items: center; gap: 10px; }
.sk-tag { width: 36px; height: 18px; border-radius: 10px; background: #f0f0f0; flex-shrink: 0; }
.sk-title { flex: 1; height: 14px; border-radius: 6px; background: #f0f0f0; }
.sk-meta { width: 60px; height: 12px; border-radius: 6px; background: #f0f0f0; }
.card-skeleton { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
.skeleton-card { height: 140px; border-radius: 10px; background: linear-gradient(90deg, #f0f0f0 25%, #e8e8e8 50%, #f0f0f0 75%); background-size: 200% 100%; animation: shimmer 1.5s infinite; }

/* 热点文件面板 */
.hot-docs-panel {
  background: #fff;
  border-radius: 16px;
  border: 1px solid #eee;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  align-self: start;
}
.hdp-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 14px 10px;
  border-bottom: 1px solid #f0f0f0;
  flex-shrink: 0;
}
.hdp-dot { width: 8px; height: 8px; border-radius: 50%; background: #c0392b; flex-shrink: 0; }
.hdp-title { font-size: 13px; font-weight: 700; color: #111; }
.hdp-list { flex: none; overflow: visible; padding: 6px 0; }
.hdp-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 9px 12px;
  cursor: pointer;
  transition: background 0.15s;
  border-radius: 8px;
  margin: 2px 6px;
}
.hdp-item:hover { background: #fef9f9; }
.hdp-rank { font-size: 13px; font-weight: 700; color: #ccc; width: 16px; flex-shrink: 0; text-align: center; }
.hdp-rank.rank-top { color: #c0392b; }
.hdp-content { flex: 1; min-width: 0; }
.hdp-text { margin: 0 0 3px; font-size: 12px; color: #333; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.hdp-date { font-size: 10px; color: #bbb; }

/* 通用骨架 */
.loading-placeholder { padding: 8px 12px; }
.skeleton-line {
  height: 12px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 6px;
  margin-bottom: 10px;
}
@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

@media (max-width: 1024px) {
  .hero-content { max-width: 52%; }
  .gov-summary-card {
    position: static;
    width: auto;
    margin: 10px;
    background: rgba(255,255,255,0.18);
  }
  .hero-arrow.right { left: auto; right: 14px; }
  .hero-dots { left: 50%; transform: translateX(-50%); }
  .bottom-section { grid-template-columns: 1fr; }
  .masonry-wall { grid-template-columns: repeat(6, minmax(0, 1fr)); }
  .news-card-view { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .card-skeleton { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

@media (max-width: 768px) {
  .discover-page { padding: 12px; }
  .top-section { margin-left: -12px; margin-right: -12px; }
  .panorama-hero { height: auto; min-height: 250px; }
  .hero-content {
    max-width: calc(100% - 24px);
    left: 12px;
    right: 12px;
    bottom: 14px;
  }
  .tsb-input-wrap {
    position: relative;
    top: auto;
    left: auto;
    margin: 12px;
    width: calc(100% - 24px);
  }
  .search-popover { left: 0; width: 100%; }
  .masonry-wall { grid-template-columns: repeat(4, minmax(0, 1fr)); }
  .brick-item { grid-column: span 4 !important; grid-row: span 2 !important; }
  .news-card-view { grid-template-columns: 1fr; }
  .card-skeleton { grid-template-columns: 1fr; }
  .hero-arrow { width: 32px; height: 32px; }
  .hero-arrow.left { left: 8px; }
  .hero-arrow.right { right: 8px; }
}
</style>
