<template>
  <div class="home-container">
    <div class="three-col-layout" :class="{ 'focus-mode': focusMode, 'right-collapsed': !rightDrawerOpen }">

      <!-- ── 左栏：历史抽屉 toggle ─────────────────────────────── -->
      <div class="left-stack">
        <!-- 历史抽屉 -->
        <div class="history-drawer" :class="{ open: historyDrawerOpen }">
          <div class="history-drawer-shell">
            <div class="drawer-tab" @click="historyDrawerOpen = !historyDrawerOpen">
              <span class="drawer-tab-text">{{ historyDrawerOpen ? '◀' : '▶' }} 最近解析</span>
            </div>
            <aside class="panel-card history-panel drawer-panel">
            <div class="panel-header">
              <span class="panel-dot dot-blue"></span>
              <h3 class="panel-title">最近解析</h3>
              <span class="panel-badge">历史</span>
            </div>
            <div class="history-section">
              <div class="history-header">
                <span class="history-title">最近解析</span>
                <button class="history-refresh capsule-btn" @click="fetchRecentHistory" :disabled="historyLoading">刷新</button>
              </div>
              <div v-if="!userStore.token" class="history-empty">登录后查看最近解析</div>
              <div v-else class="history-list">
                <div
                  v-for="item in recentMessages"
                  :key="item.id"
                  class="history-item"
                  :class="{ active: selectedHistoryId === item.id }"
                  @click="selectHistory(item)"
                >
                  <div class="history-main">
                    <span class="history-item-title">{{ getMessageTitle(item) }}</span>
                    <span class="history-item-date">{{ formatHistoryDate(item.created_time) }}</span>
                  </div>
                  <button
                    class="history-fav"
                    :class="{ active: isHistoryFavorited(item.id) }"
                    @click.stop="toggleHistoryFavorite(item)"
                    title="收藏"
                  >
                    <svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" :fill="isHistoryFavorited(item.id) ? '#f1c40f' : 'none'">
                      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
                    </svg>
                  </button>
                </div>
                <div v-if="historyLoading" class="loading-placeholder">
                  <div v-for="i in 3" :key="i" class="skeleton-line"></div>
                </div>
              </div>
              <div v-if="selectedHistoryDetail" class="history-detail">
                <div class="history-detail-title">{{ getMessageTitle(selectedHistoryDetail) }}</div>
                <p class="history-detail-text">{{ selectedHistoryDetail.original_text || '暂无详情' }}</p>
                <button class="history-restore-btn" @click="restoreHistory(selectedHistoryDetail)">恢复该解析</button>
              </div>
              <div v-else-if="userStore.token && !historyLoading" class="history-empty">暂无记录</div>
            </div>
            </aside>
          </div>
        </div>
      </div>

      <!-- ── 中栏：文件处理 ────────────────────────────────────── -->
      <main class="center-panel">
        <input ref="importInput" type="file" hidden accept=".json,application/json" @change="handleImportConversation" />

        <!-- 初始视图：上传区 -->
        <div v-if="!showResult" class="initial-view">
          <div class="scan-zone">
          <div
            class="upload-area"
            @click.self="triggerFileUpload"
            @dragover.prevent
            @drop.prevent="handleDrop"
            :class="{ 'disabled': loading }"
          >
            <!-- 卷轴装饰 -->
            <div class="scroll-decoration left-scroll"></div>
            <div class="scroll-decoration right-scroll"></div>

            <div class="upload-content">
              <PolicyTitle
                class="upload-title-block"
                title="看见政策"
                subtitle="多模态 · 可视化 · 富呈现"
              />
              <div class="upload-buttons">
                <button class="action-btn upload-round-btn" @click.stop="triggerFileUpload" :disabled="loading">本地上传</button>
                <button class="action-btn upload-round-btn" @click.stop="handleUrlUpload" :disabled="loading">URL上传</button>
                <button class="action-btn upload-round-btn" @click.stop="handleScreenshot" :disabled="loading">截图</button>
              </div>
              <p class="upload-hint">点击或拖拽上传 (支持文档、图片、PDF)</p>
            </div>

            <div v-if="showUrlInput" class="url-float" @click.stop>
              <div class="url-float-title">URL 上传</div>
              <input
                ref="urlInputRef"
                v-model="urlInputValue"
                class="url-float-input"
                type="text"
                placeholder="https://example.com/file.pdf"
                @keydown.enter.prevent="submitUrlUpload"
              />
              <div class="url-float-actions">
                <button class="url-float-btn primary" @click="submitUrlUpload">确定</button>
                <button class="url-float-btn" @click="cancelUrlUpload">取消</button>
              </div>
            </div>
            <input type="file" ref="fileInput" style="display:none" @change="handleFileUpload" accept=".txt,.pdf,.doc,.docx,.xls,.xlsx,image/jpeg,image/png,image/webp,image/bmp,image/tiff" />
            <input type="file" ref="screenshotInput" style="display:none" @change="handleScreenshotUpload" accept="image/jpeg,image/png,image/webp,image/bmp,image/tiff" />
          </div>

          <div v-if="loading" class="loading-banner">
            <div class="loading-banner-head">
              <div class="loading-copy">
                <span class="loading-kicker">智能解析任务</span>
                <span class="loading-title">正在智能解读中...</span>
              </div>
              <div class="loading-metrics">
                <span class="loading-percent">{{ Math.round(parseProgress) }}%</span>
                <span class="loading-elapsed">{{ parseElapsedSec }}s</span>
              </div>
            </div>
            <div class="loading-stage-row">
              <span class="loading-stage-dot"></span>
              <div class="loading-stage">{{ parseStageLabel }}</div>
            </div>
            <div class="loading-progress-track">
              <div class="loading-progress-fill" :style="{ width: `${parseProgress}%` }"></div>
            </div>
            <div class="loading-progress-meta">
              <span>任务持续推进中</span>
              <span>{{ parseProgress >= 96 ? '即将完成' : '请勿关闭当前页面' }}</span>
            </div>
          </div>
          </div>

          <!-- 示例区域 -->
          <div class="examples-section">
            <div class="examples-head">
              <h2 class="section-title">示例</h2>
              <div class="examples-nav" v-if="exampleChunks.length > 1">
                <button class="examples-nav-btn" @click="prevExamplePage">‹</button>
                <button class="examples-nav-btn" @click="nextExamplePage">›</button>
              </div>
            </div>
            <div class="examples-carousel" @mouseenter="stopExampleAutoplay" @mouseleave="startExampleAutoplay">
              <div class="examples-track" :style="exampleTrackStyle">
                <div
                  v-for="(group, groupIndex) in exampleChunks"
                  :key="`group-${groupIndex}`"
                  class="examples-page"
                >
                  <div class="examples-grid">
                    <div
                      v-for="(ex, index) in group"
                      :key="ex.id"
                      class="example-card"
                      :style="{ animationDelay: `${index * 0.12}s` }"
                      @click="handleExampleClick(ex)"
                    >
                      <div class="card-image-wrapper">
                        <div class="breakout-image">
                          <img :src="ex.image" alt="example document" />
                        </div>
                      </div>
                      <div class="card-content">
                        <h3 class="card-title">{{ ex.title }}</h3>
                        <div class="card-tags">
                          <span v-for="tag in ex.tags" :key="tag" class="tag">{{ tag }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div v-if="exampleChunks.length > 1" class="examples-dots">
              <button
                v-for="(_, idx) in exampleChunks"
                :key="`dot-${idx}`"
                class="examples-dot"
                :class="{ active: idx === examplePageIndex }"
                @click="goToExamplePage(idx)"
              ></button>
            </div>
          </div>

          <!-- 热点资讯图片横条 -->
          <!-- 当下热点栏已移除 -->
        </div>

        <!-- 结果视图 -->
        <div v-else class="result-view">
          <div class="result-header">
            <button @click="resetView" class="back-btn"><span class="icon">←</span> 返回</button>
            <h2>解读结果</h2>
            <div class="result-header-actions">
              <button class="result-header-btn" @click="triggerImportConversation">导入会话</button>
            </div>
          </div>
          <div class="response-section" v-if="aiResponse">
            <div class="fixed-result-header">
              <div class="header-top-row">
                <h3 class="result-title">{{ currentTitle }}</h3>
                <div class="tags-container">
                  <span class="highlight-tag" v-if="aiResponse.target_audience">{{ aiResponse.target_audience }}</span>
                  <span class="info-tag" v-if="aiResponse.chat_analysis?.notice_type">{{ aiResponse.chat_analysis.notice_type }}</span>
                </div>
                <div class="result-actions">
                  <button class="result-action-btn" @click="toggleTTS" :title="ttsActive ? '停止播报' : '语音播报'">
                    <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none">
                      <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                      <template v-if="!ttsActive">
                        <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path>
                      </template>
                      <template v-else>
                        <line x1="23" y1="9" x2="17" y2="15"></line>
                        <line x1="17" y1="9" x2="23" y2="15"></line>
                      </template>
                    </svg>
                    {{ ttsActive ? '停止' : '播报' }}
                  </button>
                  <button class="result-action-btn" @click="addFavorite" :title="isFavorited ? '已收藏' : '收藏'" :class="{ favorited: isFavorited }">
                    <svg viewBox="0 0 24 24" width="16" height="16" :stroke="isFavorited ? '#c0392b' : 'currentColor'" stroke-width="2" :fill="isFavorited ? '#c0392b' : 'none'"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>
                    {{ isFavorited ? '已收藏' : '收藏' }}
                  </button>
                  <button class="result-action-btn" @click="handleExportConversation" :disabled="!aiResponse?.id" title="导出会话 JSON">
                    <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                    导出
                  </button>
                </div>
              </div>
              <span
                v-if="aiResponse?.chat_analysis?.parse_mode"
                class="parse-mode-badge"
              >
                {{ String(aiResponse.chat_analysis.parse_mode).startsWith('fallback') ? '快速容错解析' : '自由结构解析' }}
              </span>
            </div>
            <div class="scrollable-content">
              <KnowledgeGraphPanel
                :content="kgPayload.content"
                :nodes="kgPayload.nodes"
                :links="kgPayload.links"
                :dynamic-payload="kgPayload.dynamicPayload"
                :analysis-payload="aiResponse?.chat_analysis || {}"
                :visual-config="kgPayload.visualConfig"
                :original-file-url="aiResponse?.file_url || ''"
                :rewrite-targets="REWRITE_TARGETS"
                :rewrite-loading="isRewriting"
                :rewrite-enabled="Boolean(aiResponse?.id)"
                @rewrite="rewriteTarget"
              />
            </div>
          </div>
        </div>
      </main>

      <!-- ── 右栏：红头文件 ─────────────────────────────────────── -->
      <div class="right-stack" :class="{ open: rightDrawerOpen }">
        <div class="right-drawer-shell">
          <div class="drawer-tab right-drawer-tab" @click="rightDrawerOpen = !rightDrawerOpen">
            <span class="drawer-tab-text">{{ rightDrawerOpen ? '▶' : '◀' }} 中央文件</span>
          </div>
          <aside class="right-panel-col panel-card">
        <div class="panel-header">
          <span class="panel-dot" :class="rightPanelMode === 'docs' ? 'dot-red' : 'dot-blue'"></span>
          <h3 class="panel-title">{{ rightPanelMode === 'docs' ? '中央文件' : '时事热点' }}</h3>
          <div class="right-panel-switch">
            <button class="switch-btn" :class="{ active: rightPanelMode === 'docs' }" @click="rightPanelMode = 'docs'">中央文件</button>
            <button class="switch-btn" :class="{ active: rightPanelMode === 'news' }" @click="rightPanelMode = 'news'">时事热点</button>
          </div>
        </div>

        <template v-if="rightPanelMode === 'docs'">
          <div class="doc-titles-scroll">
            <div
              v-for="(doc, idx) in centralDocs"
              :key="idx"
              class="doc-title-item"
              :class="{ active: selectedDocIdx === idx }"
              @click="selectedDocIdx = idx"
            >
              <span class="doc-index">{{ String(idx + 1).padStart(2, '0') }}</span>
              <span class="doc-title-text">{{ doc.title }}</span>
            </div>
            <div v-if="docsLoading" class="loading-placeholder">
              <div v-for="i in 3" :key="i" class="skeleton-line"></div>
            </div>
          </div>

          <div class="cloud-section">
            <div class="cloud-label">热点聚类分析</div>
            <div ref="wordCloudRef" class="word-cloud-chart"></div>
          </div>

          <div class="doc-content-section" v-if="centralDocs[selectedDocIdx]">
            <div class="doc-content-header">
              <div class="red-header-bar">
                <span class="red-star">★</span>
                <span>中华人民共和国国务院</span>
                <span class="red-star">★</span>
              </div>
              <h4 class="doc-content-title">{{ centralDocs[selectedDocIdx].title }}</h4>
              <span class="doc-date" v-if="centralDocs[selectedDocIdx].pubDate">{{ centralDocs[selectedDocIdx].pubDate }}</span>
            </div>
            <div class="doc-content-body">
              <span v-html="stripHtml(centralDocs[selectedDocIdx].description) || '暂无摘要内容'"></span>
              <a v-if="centralDocs[selectedDocIdx].link" :href="centralDocs[selectedDocIdx].link" target="_blank" class="doc-read-more">阅读全文 →</a>
            </div>
          </div>
        </template>

        <template v-else>
          <div class="carousel-wrap">
            <transition name="carousel-fade" mode="out-in">
              <div class="carousel-slide" :key="carouselIndex">
                <div class="carousel-content">
                  <span class="carousel-num">{{ String(carouselIndex + 1).padStart(2, '0') }}</span>
                  <p class="carousel-text">{{ hotNews[carouselIndex]?.title || '加载中...' }}</p>
                </div>
                <div class="carousel-dots">
                  <span
                    v-for="(_, i) in Math.min(hotNews.length, 5)"
                    :key="i"
                    class="dot"
                    :class="{ active: i === carouselIndex % Math.min(hotNews.length, 5) }"
                    @click="carouselIndex = i"
                  ></span>
                </div>
              </div>
            </transition>
          </div>
          <div class="news-list">
            <div
              v-for="(item, idx) in hotNews"
              :key="idx"
              class="news-item"
              @click="openLink(item.link)"
            >
              <span class="news-rank" :class="idx < 3 ? 'rank-top' : ''">{{ idx + 1 }}</span>
              <span class="news-title">{{ item.title }}</span>
              <svg class="news-arrow" viewBox="0 0 24 24" width="12" height="12" stroke="currentColor" stroke-width="2" fill="none"><polyline points="9 18 15 12 9 6"></polyline></svg>
            </div>
            <div v-if="newsLoading" class="loading-placeholder">
              <div v-for="i in 5" :key="i" class="skeleton-line"></div>
            </div>
          </div>
        </template>
          </aside>
        </div>
      </div>

    </div><!-- end three-col-layout -->

  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, computed, watch } from 'vue';
import * as echarts from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { useUserStore } from '@/stores/auth.js';
import { createChatMessage, createChatMessageWithFile, exportChatMessage, importChatMessage, uploadAndExtractDocument, rewriteChatMessage, getChatMessages, getChatMessage, startChatProgressTask } from '@/api/ai';
import { getHotNews, getCentralDocs, getHotKeywords, getNewsWithImages } from '@/api/news';
import { useRouter } from 'vue-router';
import { toggleSpeak, isSpeaking } from '@/utils/tts.js';
import { apiClient, API_ROUTES } from '@/router/api_routes.js';
import KnowledgeGraphPanel from '@/components/Home/KnowledgeGraphPanel.vue';
import PolicyTitle from '@/components/common/PolicyTitle.vue';


const userStore = useUserStore();
const router = useRouter();

// ── 文件处理状态 ──────────────────────────────────────────────────────────────
const inputText = ref('');
const aiResponse = ref(null);
const loading = ref(false);
const parseProgress = ref(0);
const parseStage = ref('');
const parseElapsedSec = ref(0);
const isRewriting = ref(false);
const showResult = ref(false);
const fileInput = ref(null);
const importInput = ref(null);
const showUrlInput = ref(false);
const urlInputValue = ref('');
const urlInputRef = ref(null);
const focusMode = computed(() => loading.value || showResult.value);
const parseStageLabel = computed(() => {
  if (parseStage.value) return parseStage.value;
  return '准备解析';
});

// ── 左栏：时事热点 ────────────────────────────────────────────────────────────
const hotNews = ref([]);
const newsLoading = ref(true);
const carouselIndex = ref(0);
let carouselTimer = null;
const rightPanelMode = ref('docs');
const rightDrawerOpen = ref(false);

// 最近解析记录
const recentMessages = ref([]);
const historyLoading = ref(false);
const selectedHistoryId = ref(null);
const selectedHistoryDetail = ref(null);
const favoritesMap = ref({});
const historyDrawerOpen = ref(false);

// ── 右栏：中央文件 ────────────────────────────────────────────────────────────
const centralDocs = ref([]);
const docsLoading = ref(true);
const selectedDocIdx = ref(0);
const wordCloudRef = ref(null);
let wordCloudChart = null;

// ── 热点资讯图片横条 ──────────────────────────────────────────────────────────
const newsImages = ref([]);
const isGenericTitle = (v) => /^(未知事项|未命名事项|unknown|payload|payload_root)$/i.test(String(v || '').trim());
const firstLine = (text) =>
  String(text || '')
    .split(/\r?\n/)
    .map((s) => s.trim())
    .find(Boolean) || '';
const normalizeGraphSourceText = (text) =>
  String(text || '')
    .replace(/\r\n/g, '\n')
    .replace(/\r/g, '\n')
    .replace(/[ \t]+/g, ' ')
    .trim();
const extractTitleFromPayload = (payload) => {
  const seen = new Set();
  const walk = (obj, depth = 0) => {
    if (!obj || depth > 4 || seen.has(obj)) return '';
    if (typeof obj === 'string') {
      const t = obj.trim();
      if (t && !isGenericTitle(t)) return t;
      return '';
    }
    if (Array.isArray(obj)) {
      for (const item of obj.slice(0, 20)) {
        const hit = walk(item, depth + 1);
        if (hit) return hit;
      }
      return '';
    }
    if (typeof obj === 'object') {
      seen.add(obj);
      for (const [, v] of Object.entries(obj).slice(0, 40)) {
        if (typeof v === 'string' && v.trim() && !isGenericTitle(v)) return v.trim();
        const hit = walk(v, depth + 1);
        if (hit) return hit;
      }
    }
    return '';
  };
  return walk(payload);
};
const getMessageTitle = (msg) => {
  if (!msg) return '未命名文档';
  if (msg.handling_matter && !isGenericTitle(msg.handling_matter)) return msg.handling_matter;
  const analysis = msg.chat_analysis || {};
  const nodes = msg.nodes || analysis.nodes || [];
  const focus = (msg.visual_config || analysis.visual_config || {}).focus_node;
  const root = nodes.find((n) => n?.id === focus) || [...nodes].sort((a, b) => Number(b?.importance || 0) - Number(a?.importance || 0))[0];
  if (root?.label && !isGenericTitle(root.label)) return root.label;
  const payload = msg.dynamic_payload || analysis.dynamic_payload || {};
  const p = extractTitleFromPayload(payload);
  if (p) return p.slice(0, 90);
  const content = msg.content || analysis.content || msg.original_text || '';
  const line = firstLine(content);
  return line ? line.slice(0, 90) : '未命名文档';
};
const kgPayload = computed(() => {
  const analysis = aiResponse.value?.chat_analysis || {};
  const visual = aiResponse.value?.visual_config || analysis.visual_config || {};
  const dynamicPayload = aiResponse.value?.dynamic_payload || analysis.dynamic_payload || {};
  const sourceText = normalizeGraphSourceText(
    aiResponse.value?.original_text || analysis.original_text || aiResponse.value?.content || analysis.content || ''
  );
  return {
    content: sourceText,
    nodes: aiResponse.value?.nodes || analysis.nodes || [],
    links: aiResponse.value?.links || analysis.links || [],
    dynamicPayload,
    visualConfig: visual,
  };
});
const currentTitle = computed(() => getMessageTitle(aiResponse.value));
const REWRITE_TARGETS = ['老人版', '学生版', '家属转述版', '极简版', '客服答复版'];

// ── 示例数据 ──────────────────────────────────────────────────────────────────
const EXAMPLE_META_MAP = {
  'AI回答截图': { title: 'AI回答截图', tags: ['AI问答', '结果核验', '答复对比'] },
  'git使用说明书': { title: 'Git使用说明书', tags: ['开发工具', '命令手册', '协作规范'] },
  '国际赛事章程': { title: '国际赛事章程', tags: ['赛事规则', '条款解析', '制度文本'] },
  '复杂系统设计规范': { title: '复杂系统设计规范', tags: ['系统设计', '工程规范', '架构约束'] },
  '扫描件': { title: '扫描件', tags: ['OCR识别', '纸质文档', '文本提取'] },
  '拍照扫描件': { title: '拍照扫描件', tags: ['移动拍照', '图像增强', '识别纠错'] },
  '物理模拟准则': { title: '物理模拟准则', tags: ['科研方法', '仿真参数', '实验规范'] },
  '科研论文解读': { title: '科研论文解读', tags: ['学术阅读', '关键结论', '结构化摘要'] },
  '繁杂笔记': { title: '繁杂笔记', tags: ['笔记整理', '知识归纳', '重点提炼'] },
  '计算机语言学习': { title: '计算机语言学习', tags: ['编程学习', '语法要点', '知识卡片'] },
};
const exampleImageModules = import.meta.glob('/src/assets/photos/main-examples/*.png', { eager: true });
const exampleImageEntries = Object.entries(exampleImageModules).sort(([a], [b]) => a.localeCompare(b, 'zh-CN'));
const examples = ref(
  exampleImageEntries.slice(0, 10).map(([path, mod], idx) => {
    const fileName = path.split('/').pop()?.replace(/\.[^.]+$/, '') || `example-${idx + 1}`;
    const meta = EXAMPLE_META_MAP[fileName];
    return {
      id: idx + 1,
      title: meta?.title || fileName,
      tags: meta?.tags || ['示例文档', '智能解析', '知识图谱'],
      image: mod.default,
    };
  })
);
const EXAMPLES_PER_PAGE = 3;
const examplePageIndex = ref(0);
let exampleAutoTimer = null;
const exampleChunks = computed(() => {
  const groups = [];
  for (let i = 0; i < examples.value.length; i += EXAMPLES_PER_PAGE) {
    groups.push(examples.value.slice(i, i + EXAMPLES_PER_PAGE));
  }
  return groups;
});
const exampleTrackStyle = computed(() => ({
  transform: `translateX(-${examplePageIndex.value * 100}%)`
}));

const goToExamplePage = (idx) => {
  const total = exampleChunks.value.length;
  if (!total) return;
  examplePageIndex.value = ((idx % total) + total) % total;
};
const nextExamplePage = () => goToExamplePage(examplePageIndex.value + 1);
const prevExamplePage = () => goToExamplePage(examplePageIndex.value - 1);
const startExampleAutoplay = () => {
  stopExampleAutoplay();
  if (exampleChunks.value.length <= 1) return;
  exampleAutoTimer = setInterval(() => {
    nextExamplePage();
  }, 3600);
};
const stopExampleAutoplay = () => {
  if (!exampleAutoTimer) return;
  clearInterval(exampleAutoTimer);
  exampleAutoTimer = null;
};

// ── 生命周期 ──────────────────────────────────────────────────────────────────
onMounted(async () => {
  if (userStore.token) userStore.fetchUser();

  // 并行加载新闻和文件
  await Promise.all([loadHotNews(), loadCentralDocs(), loadNewsImages()]);
  await fetchRecentHistory();
  await fetchFavorites();

  // 启动轮播
  carouselTimer = setInterval(() => {
    if (hotNews.value.length > 0) {
      carouselIndex.value = (carouselIndex.value + 1) % Math.min(hotNews.value.length, 5);
    }
  }, 3500);

  // 初始化词云
  await nextTick();
  initWordCloud();
  startExampleAutoplay();

   const restoredMessage = sessionStorage.getItem('restoredChatMessage');
   if (restoredMessage) {
     try {
       aiResponse.value = JSON.parse(restoredMessage);
       showResult.value = true;
     } catch (error) {
       console.warn('恢复会话失败', error);
     } finally {
       sessionStorage.removeItem('restoredChatMessage');
     }
   }
});

onUnmounted(() => {
  clearInterval(carouselTimer);
  stopExampleAutoplay();
  stopParseProgress();
  wordCloudChart?.dispose();
});

watch(() => userStore.token, async (val) => {
  if (val) {
    await fetchRecentHistory();
    await fetchFavorites();
  } else {
    recentMessages.value = [];
    selectedHistoryId.value = null;
    selectedHistoryDetail.value = null;
    favoritesMap.value = {};
  }
});

// ── 数据加载 ──────────────────────────────────────────────────────────────────
async function loadHotNews() {
  try {
    const res = await getHotNews(10);
    hotNews.value = res.data.items || [];
  } catch (e) {
    console.warn('热点新闻加载失败', e);
  } finally {
    newsLoading.value = false;
  }
}

async function loadCentralDocs() {
  try {
    const res = await getCentralDocs(5);
    centralDocs.value = res.data.items || [];
  } catch (e) {
    console.warn('中央文件加载失败', e);
  } finally {
    docsLoading.value = false;
  }
}

async function loadNewsImages() {
  try {
    const res = await getNewsWithImages(5);
    newsImages.value = res.data.items || [];
  } catch (e) {
    console.warn('热点图片加载失败', e);
  }
}

async function initWordCloud() {
  if (!wordCloudRef.value) return;
  try {
    await import('echarts-wordcloud');
    echarts.use([CanvasRenderer]);
    const res = await getHotKeywords();
    const keywords = res.data.items || [];
    wordCloudChart = echarts.init(wordCloudRef.value);
    wordCloudChart.setOption({
      backgroundColor: 'transparent',
      series: [{
        type: 'wordCloud',
        shape: 'circle',
        left: 'center',
        top: 'center',
        width: '90%',
        height: '90%',
        sizeRange: [10, 28],
        rotationRange: [-45, 45],
        rotationStep: 45,
        gridSize: 6,
        drawOutOfBound: false,
        textStyle: {
          fontFamily: 'sans-serif',
          fontWeight: 'bold',
          color() {
            const colors = ['#c0392b', '#e74c3c', '#e67e22', '#d35400', '#8e44ad', '#2980b9', '#16a085', '#27ae60'];
            return colors[Math.floor(Math.random() * colors.length)];
          },
        },
        emphasis: { focus: 'self', textStyle: { shadowBlur: 10, shadowColor: '#333' } },
        data: keywords,
      }],
    });
    wordCloudChart.on('click', (params) => {
      if (params.name) {
        window.open(`https://www.baidu.com/s?wd=${encodeURIComponent(params.name)}`, '_blank');
      }
    });
  } catch (e) {
    console.warn('词云加载失败', e);
  }
}

// ── 工具函数 ──────────────────────────────────────────────────────────────────
const openLink = (url) => { if (url) window.open(url, '_blank'); };
const stripHtml = (html) => {
  if (!html) return '';
  return html.replace(/<[^>]*>/g, '').replace(/&nbsp;/g, ' ').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').trim();
};

const formatHistoryDate = (value) => {
  if (!value) return '';
  const dt = new Date(value);
  if (Number.isNaN(dt.getTime())) return '';
  return dt.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
};

const fetchRecentHistory = async () => {
  if (!userStore.token) {
    recentMessages.value = [];
    selectedHistoryId.value = null;
    selectedHistoryDetail.value = null;
    return;
  }
  historyLoading.value = true;
  try {
    const res = await getChatMessages({ limit: 15, sort_by: 'created_time', sort_order: 'desc' });
    recentMessages.value = res.data || [];
    if (recentMessages.value.length === 0) {
      selectedHistoryId.value = null;
      selectedHistoryDetail.value = null;
    } else if (!selectedHistoryId.value) {
      await selectHistory(recentMessages.value[0]);
    }
  } catch (error) {
    console.warn('加载历史记录失败', error);
  } finally {
    historyLoading.value = false;
  }
};

const selectHistory = async (item) => {
  if (!item?.id) return;
  selectedHistoryId.value = item.id;
  try {
    const res = await getChatMessage(item.id);
    selectedHistoryDetail.value = res.data;
  } catch (error) {
    selectedHistoryDetail.value = item;
  }
};

const restoreHistory = (item) => {
  if (!item) return;
  aiResponse.value = item;
  showResult.value = true;
  isFavorited.value = Boolean(favoritesMap.value[item.id]);
};

const fetchFavorites = async () => {
  if (!userStore.token) {
    favoritesMap.value = {};
    return;
  }
  try {
    const res = await apiClient.get(API_ROUTES.FAVORITE);
    const map = {};
    (res.data || []).forEach((fav) => {
      map[fav.chat_message_id] = fav;
    });
    favoritesMap.value = map;
    if (aiResponse.value?.id) {
      isFavorited.value = Boolean(map[aiResponse.value.id]);
    }
  } catch (error) {
    console.warn('加载收藏失败', error);
  }
};

const isHistoryFavorited = (id) => Boolean(favoritesMap.value[id]);

const toggleHistoryFavorite = async (item) => {
  if (!item?.id) return;
  const existing = favoritesMap.value[item.id];
  try {
    if (existing) {
      await apiClient.delete(`${API_ROUTES.FAVORITE}${existing.id}`);
      const nextMap = { ...favoritesMap.value };
      delete nextMap[item.id];
      favoritesMap.value = nextMap;
      if (aiResponse.value?.id === item.id) isFavorited.value = false;
    } else {
      const res = await apiClient.post(`${API_ROUTES.FAVORITE}?chat_message_id=${item.id}`);
      favoritesMap.value = { ...favoritesMap.value, [item.id]: res.data };
      if (aiResponse.value?.id === item.id) isFavorited.value = true;
    }
  } catch (error) {
    console.warn('收藏操作失败', error);
  }
};

const requestLoginModal = () => {
  window.dispatchEvent(new CustomEvent('open-login-modal'));
};

let parseTicker = null;
let parseStartedAt = 0;
let parseEventSource = null;

const stopParseProgress = () => {
  if (parseTicker) {
    clearInterval(parseTicker);
    parseTicker = null;
  }
  if (parseEventSource) {
    parseEventSource.close();
    parseEventSource = null;
  }
};

const startParseProgress = () => {
  stopParseProgress();
  parseStartedAt = Date.now();
  parseProgress.value = 4;
  parseElapsedSec.value = 0;
  parseStage.value = '初始化任务';
  parseTicker = setInterval(() => {
    parseElapsedSec.value = Math.max(0, Math.floor((Date.now() - parseStartedAt) / 1000));
    const cap = 92;
    if (parseProgress.value < cap) {
      parseProgress.value += parseProgress.value < 40 ? 2 : 1;
    }
  }, 450);
};

const markParseStage = (label, targetProgress) => {
  parseStage.value = label;
  parseProgress.value = Math.max(parseProgress.value, Math.min(targetProgress, 96));
};

const finishParseProgress = () => {
  parseProgress.value = 100;
  stopParseProgress();
};

const startRealParseProgress = async () => {
  if (!userStore.token) return null;
  try {
    const startRes = await startChatProgressTask();
    const taskId = startRes?.data?.task_id;
    if (!taskId) return null;
    const streamUrl = `/api${API_ROUTES.CHAT_PROGRESS_STREAM}?task_id=${encodeURIComponent(taskId)}&token=${encodeURIComponent(userStore.token)}`;
    parseEventSource = new EventSource(streamUrl);
    parseEventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data || '{}');
        if (typeof data.progress === 'number') {
          parseProgress.value = Math.max(parseProgress.value, Math.min(100, data.progress));
        }
        if (data.stage) parseStage.value = data.stage;
        if (data.status === 'completed' || data.status === 'failed' || data.status === 'not_found') {
          parseEventSource?.close();
          parseEventSource = null;
        }
      } catch (_) {
        // ignore malformed SSE payload
      }
    };
    parseEventSource.onerror = () => {
      parseEventSource?.close();
      parseEventSource = null;
    };
    return taskId;
  } catch (_) {
    return null;
  }
};

// ── 文件处理逻辑 ──────────────────────────────────────────────────────────────
const triggerFileUpload = () => {
  if (loading.value) return;
  if (!userStore.token) { requestLoginModal(); return; }
  if (fileInput.value) {
    fileInput.value.value = '';
    fileInput.value.click();
  }
};

const handleExampleClick = async (example) => {
  if (loading.value) return;
  if (!userStore.token) { requestLoginModal(); return; }

  // 将示例图片转换为文件并处理
  try {
    const response = await fetch(example.image);
    const blob = await response.blob();
    const file = new File([blob], `${example.title}.png`, { type: 'image/png' });
    await processFile(file);
  } catch (error) {
    console.error('处理示例失败:', error);
  }
};

const triggerImportConversation = () => {
  if (!userStore.token) { requestLoginModal(); return; }
  importInput.value?.click();
};

const handleFileUpload = (event) => processFile(event.target.files[0]);

const handleDrop = (event) => {
  if (loading.value) return;
  if (!userStore.token) { requestLoginModal(); return; }
  processFile(event.dataTransfer.files[0]);
};

const isImageFile = (file) => {
  const type = String(file?.type || '').toLowerCase();
  if (type.startsWith('image/')) return true;
  const filename = String(file?.name || '').toLowerCase();
  return /\.(png|jpe?g|webp|gif|bmp|tiff?)$/.test(filename);
};

const processFile = async (file) => {
  if (!file) return;
  loading.value = true;
  startParseProgress();
  aiResponse.value = null;
  const taskId = await startRealParseProgress();
  try {
    let extractedText = '';
    let fileUrl = '';

    if (isImageFile(file)) {
      markParseStage('图片上传与OCR识别', 30);
      const formData = new FormData();
      formData.append('file', file);
      const ocrRes = await apiClient.post(API_ROUTES.UPLOAD_OCR, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      extractedText = ocrRes.data?.extracted_text || '';
      fileUrl = ocrRes.data?.file_url || '';
      if (!extractedText.trim()) {
        alert('未能识别出文字，请尝试更清晰的图片。');
        return;
      }
      markParseStage('LLM 自由解析中', 70);
    } else {
      markParseStage('上传与文本提取中', 26);
      const uploadRes = await uploadAndExtractDocument(file);
      extractedText = uploadRes.data?.extracted_text || '';
      fileUrl = uploadRes.data?.file_url || '';
      markParseStage('LLM 自由解析中', 68);
    }

    const chatRes = await createChatMessageWithFile(extractedText, fileUrl, taskId);
    aiResponse.value = chatRes.data;
    markParseStage('图谱构建与结果整理', 94);
    showResult.value = true;
    await fetchRecentHistory();
    await fetchFavorites();
  } catch (error) {
    if (error.response?.status === 401) { userStore.logout(); requestLoginModal(); }
    else alert('文件处理失败: ' + (error.response?.data?.detail || error.message));
  } finally {
    finishParseProgress();
    loading.value = false;
    if (fileInput.value) fileInput.value.value = '';
  }
};

const handleUrlUpload = () => {
  if (loading.value) return;
  if (!userStore.token) { requestLoginModal(); return; }
  showUrlInput.value = true;
  nextTick(() => urlInputRef.value?.focus());
};

const submitUrlUpload = () => {
  const url = urlInputValue.value.trim();
  if (!url) {
    showUrlInput.value = false;
    return;
  }
  inputText.value = `URL: ${url}`;
  showUrlInput.value = false;
  urlInputValue.value = '';
  submitToAI();
};

const cancelUrlUpload = () => {
  showUrlInput.value = false;
  urlInputValue.value = '';
};

const handleScreenshot = () => {
  if (loading.value) return;
  if (!userStore.token) { requestLoginModal(); return; }
  if (screenshotInput.value) {
    screenshotInput.value.value = '';
    screenshotInput.value.click();
  }
};

const screenshotInput = ref(null);

const handleScreenshotUpload = async (event) => {
  const file = event.target.files?.[0];
  if (!file) return;
  if (!file.type.startsWith('image/')) {
    alert('截图仅支持图片格式');
    event.target.value = '';
    return;
  }
  loading.value = true;
  startParseProgress();
  aiResponse.value = null;
  const taskId = await startRealParseProgress();
  try {
    markParseStage('截图上传与OCR识别', 30);
    const formData = new FormData();
    formData.append('file', file);
    const ocrRes = await apiClient.post(API_ROUTES.UPLOAD_OCR, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    const extractedText = ocrRes.data.extracted_text;
    if (!extractedText || !extractedText.trim()) {
      alert('未能识别出文字，请尝试更清晰的图片。');
      return;
    }
    markParseStage('LLM 自由解析中', 70);
    const response = await createChatMessageWithFile(extractedText, ocrRes.data.file_url, taskId);
    aiResponse.value = response.data;
    markParseStage('图谱构建与结果整理', 94);
    showResult.value = true;
    await fetchRecentHistory();
    await fetchFavorites();
  } catch (error) {
    console.error('截图OCR失败:', error);
    alert('截图识别失败，请重试。');
  } finally {
    finishParseProgress();
    loading.value = false;
    event.target.value = '';
  }
};

const handleImportConversation = async (event) => {
  const file = event.target.files?.[0];
  if (!file) return;
  loading.value = true;
  startParseProgress();
  try {
    markParseStage('导入会话与结构恢复', 80);
    const res = await importChatMessage(file);
    aiResponse.value = res.data;
    showResult.value = true;
    isFavorited.value = false;
    await fetchRecentHistory();
    await fetchFavorites();
  } catch (error) {
    alert(error.response?.data?.detail || '导入会话失败');
  } finally {
    finishParseProgress();
    loading.value = false;
    event.target.value = '';
  }
};

const submitToAI = async () => {
  if (!userStore.token) { requestLoginModal(); return; }
  if (!inputText.value.trim()) return;
  loading.value = true;
  startParseProgress();
  aiResponse.value = null;
  const taskId = await startRealParseProgress();
  try {
    markParseStage('LLM 自由解析中', 72);
    const response = await createChatMessage(inputText.value, taskId);
    aiResponse.value = response.data;
    markParseStage('图谱构建与结果整理', 94);
    showResult.value = true;
    await fetchRecentHistory();
    await fetchFavorites();
  } catch (error) {
    if (error.response?.status === 401) { userStore.logout(); requestLoginModal(); }
    else alert('解析失败: ' + (error.response?.data?.detail || error.message));
  } finally {
    finishParseProgress();
    loading.value = false;
  }
};

const rewriteTarget = async (target) => {
  if (!aiResponse.value?.id) return;
  isRewriting.value = true;
  try {
    const response = await rewriteChatMessage(aiResponse.value.id, target);
    aiResponse.value = response.data;
  } catch (error) {
    alert('改写失败: ' + (error.response?.data?.detail || error.message));
  } finally {
    isRewriting.value = false;
  }
};

const resetView = () => {
  inputText.value = '';
  aiResponse.value = null;
  showResult.value = false;
  isFavorited.value = false;
  showUrlInput.value = false;
  urlInputValue.value = '';
  if (fileInput.value) fileInput.value.value = '';
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

const handleExportConversation = async () => {
  if (!aiResponse.value?.id) return;
  try {
    const res = await exportChatMessage(aiResponse.value.id);
    downloadBlob(res.data, `chat_${aiResponse.value.id}.json`);
  } catch (error) {
    alert(error.response?.data?.detail || '导出失败');
  }
};

// ── TTS ──────────────────────────────────────────────────────────────────────
const ttsActive = isSpeaking;
function buildTTSText(r) {
  const parts = [];
  if (r.handling_matter) parts.push('办理事项：' + r.handling_matter);
  if (r.target_audience) parts.push('适用对象：' + r.target_audience);
  if (r.time_deadline) parts.push('办理时间：' + r.time_deadline);
  if (r.location_entrance) parts.push('办理地点：' + r.location_entrance);
  if (r.required_materials) parts.push('所需材料：' + r.required_materials);
  if (r.precautions) parts.push('注意事项：' + r.precautions);
  return parts.join('。');
}
function toggleTTS() {
  if (!aiResponse.value) return;
  toggleSpeak(buildTTSText(aiResponse.value));
}

// ── 收藏 ──────────────────────────────────────────────────────────────────────
const isFavorited = ref(false);
async function addFavorite() {
  if (!aiResponse.value?.id || isFavorited.value) return;
  try {
    const res = await apiClient.post(API_ROUTES.FAVORITE + '?chat_message_id=' + aiResponse.value.id);
    isFavorited.value = true;
    if (res?.data) {
      favoritesMap.value = { ...favoritesMap.value, [aiResponse.value.id]: res.data };
    }
  } catch (e) { console.warn('收藏失败', e); }
}

const parseProcessSteps = (text) => {
  if (!text) return [];
  // 尝试按数字序号、换行、分号等分割
  const byNum = text.split(/\d+[.、。)\]]\s*/);
  if (byNum.length > 2) return byNum.filter(s => s.trim()).map(s => s.trim());
  const byNewline = text.split(/[\n；;]+/);
  if (byNewline.length > 1) return byNewline.filter(s => s.trim()).map(s => s.trim());
  return [text.trim()];
};

const getComplexityClass = (level) => {  if (level === '高') return 'level-high';
  if (level === '中') return 'level-medium';
  if (level === '低') return 'level-low';
  return '';
};
</script>

<style scoped>
/* ── 整体容器 ─────────────────────────────────────────────────────────────── */
.home-container {
  height: 100vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: var(--content-bg, #f5f7fa);
}

.three-col-layout {
  display: grid;
  grid-template-columns: 40px 1fr 300px;
  gap: 16px;
  padding: 16px;
  flex: 1;
  overflow: hidden;
  min-height: 0;
  transition: grid-template-columns 0.4s ease, gap 0.4s ease, padding 0.4s ease;
}

.three-col-layout.right-collapsed {
  grid-template-columns: 40px 1fr 40px;
}

.three-col-layout.focus-mode {
  grid-template-columns: 0 1fr 0;
  gap: 0;
  padding: 0;
}

.left-panel,
.right-stack {
  transition: transform 0.4s ease, opacity 0.4s ease;
}

.left-stack {
  transition: transform 0.4s ease, opacity 0.4s ease;
  position: relative;
}

.three-col-layout.focus-mode .left-stack {
  transform: translateX(-120%);
  opacity: 0;
  pointer-events: none;
}

.three-col-layout.focus-mode .right-stack {
  transform: translateX(120%);
  opacity: 0;
  pointer-events: none;
}

.three-col-layout.focus-mode .center-panel {
  padding: 16px;
}

/* ── 通用面板卡片 ─────────────────────────────────────────────────────────── */
.panel-card {
  background: var(--card-bg);
  border-radius: 16px;
  border: 1px solid color-mix(in srgb, var(--color-primary) 10%, var(--border-color));
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
  box-shadow: 0 18px 32px color-mix(in srgb, var(--color-primary) 10%, transparent);
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px 10px;
  background:
    linear-gradient(
      90deg,
      color-mix(in srgb, var(--color-primary-dark) 72%, #516070) 0%,
      color-mix(in srgb, var(--color-primary) 64%, var(--color-secondary) 36%) 100%
    );
  flex-shrink: 0;
  border-radius: 12px 12px 0 0;
}

.panel-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.dot-blue { background: rgba(255,255,255,0.7); }
.dot-red  { background: rgba(255,255,255,0.7); }

.panel-title {
  margin: 0;
  font-size: 14px;
  font-weight: 700;
  color: #fff;
  flex: 1;
}

.panel-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 20px;
  background: rgba(255,255,255,0.2);
  color: #fff;
  font-weight: 600;
}
.badge-red {
  background: rgba(192,57,43,0.3);
  color: #fff;
}

.right-panel-switch {
  display: flex;
  gap: 6px;
}

.switch-btn {
  border: 1px solid rgba(255, 255, 255, 0.35);
  background: transparent;
  color: rgba(255, 255, 255, 0.9);
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 9px;
  cursor: pointer;
  transition: all 0.2s;
}

.switch-btn.active {
  background: rgba(255, 255, 255, 0.22);
  border-color: rgba(255, 255, 255, 0.7);
  color: #fff;
}

.left-stack {
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: visible;
  position: relative;
  z-index: 30;
}

/* ── 历史抽屉 ─────────────────────────────────────────────── */
.history-drawer {
  position: relative;
  height: 100%;
  overflow: visible;
}

.history-drawer-shell {
  position: absolute;
  left: 0;
  top: 0;
  width: 260px;
  height: 100%;
  transform: translateX(calc(-100% + 20px));
  transition: transform 0.35s cubic-bezier(0.4,0,0.2,1);
  z-index: 31;
}

.history-drawer.open .history-drawer-shell {
  transform: translateX(0);
}

.drawer-tab {
  position: absolute;
  left: calc(100% - 40px);
  top: 50%;
  transform: translateY(-50%);
  width: 40px;
  background:
    linear-gradient(
      180deg,
      var(--color-primary-dark) 0%,
      var(--color-primary) 58%,
      var(--color-secondary) 100%
    );
  color: #fff;
  border-radius: 0 8px 8px 0;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 20;
  padding: 12px 0;
  writing-mode: vertical-rl;
  user-select: none;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 1px;
  box-shadow: 2px 0 10px color-mix(in srgb, var(--color-primary) 24%, transparent);
  transition: filter 0.2s ease, transform 0.2s ease;
}
.drawer-tab:hover {
  filter: brightness(1.05);
  transform: translateY(-50%) translateX(1px);
}

.drawer-tab-text {
  writing-mode: vertical-rl;
  text-orientation: mixed;
  font-size: 11px;
}

.drawer-panel {
  position: absolute;
  left: 0;
  top: 0;
  width: calc(100% - 40px);
  height: 100%;
  z-index: 15;
  box-shadow: 6px 0 22px color-mix(in srgb, var(--color-primary) 12%, transparent);
}

.history-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px 12px 12px;
  min-height: 0;
}

.history-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.history-title {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-primary);
}

.history-refresh {
  border: none;
  background: var(--color-primary);
  font-size: 11px;
  padding: 3px 10px;
  cursor: pointer;
  color: #fff;
  border-radius: 999px;
  box-shadow: 0 6px 14px color-mix(in srgb, var(--color-primary) 18%, transparent);
  font-weight: bold;
  transition: transform 0.2s ease, filter 0.2s ease;
}

.history-refresh:hover:not(:disabled) {
  filter: brightness(1.04);
  transform: translateY(-1px);
}

.history-refresh:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  overflow-y: auto;
  flex: 1;
  max-height: 600px;
}

.history-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  padding: 6px 8px;
  background: color-mix(in srgb, var(--color-primary) 5%, var(--card-bg));
  border: 1px solid color-mix(in srgb, var(--color-primary) 10%, var(--border-color));
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}

.history-item:hover {
  background: color-mix(in srgb, var(--color-primary) 8%, var(--card-bg));
  border-color: color-mix(in srgb, var(--color-primary) 24%, var(--border-color));
  box-shadow: 0 10px 18px color-mix(in srgb, var(--color-primary) 10%, transparent);
}

.history-item.active {
  background: color-mix(in srgb, var(--color-primary) 12%, var(--card-bg));
  border-color: color-mix(in srgb, var(--color-primary) 34%, var(--border-color));
}

.history-main {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  flex: 1;
}

.history-item-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.history-item-date {
  font-size: 10px;
  color: var(--text-muted);
}

.history-fav {
  border: none;
  background: transparent;
  cursor: pointer;
  color: #bbb;
  padding: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.history-fav.active {
  color: #f1c40f;
}

.history-detail {
  border-top: 1px dashed color-mix(in srgb, var(--color-primary) 16%, var(--border-color));
  padding-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.history-detail-title {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-primary);
}

.history-detail-text {
  font-size: 11px;
  color: var(--text-secondary);
  line-height: 1.5;
  max-height: 72px;
  overflow: hidden;
}

.history-restore-btn {
  align-self: flex-start;
  background:
    linear-gradient(
      135deg,
      var(--color-primary-dark) 0%,
      var(--color-primary) 62%,
      var(--color-secondary) 100%
    );
  color: #fff;
  border: none;
  padding: 4px 10px;
  font-size: 11px;
  cursor: pointer;
  border-radius: 999px;
  box-shadow: 0 10px 18px color-mix(in srgb, var(--color-primary) 18%, transparent);
  transition: filter 0.2s ease, transform 0.2s ease;
}

.history-restore-btn:hover {
  filter: brightness(1.04);
  transform: translateY(-1px);
}

.history-empty {
  font-size: 11px;
  color: var(--text-muted);
  padding: 6px 0;
}


/* ── 左栏：轮播 ──────────────────────────────────────────────────────────── */
.carousel-wrap {
  flex-shrink: 0;
  height: 100px;
  background: linear-gradient(135deg, #c0392b 0%, #922b21 100%);
  position: relative;
  overflow: hidden;
}

.carousel-slide {
  position: absolute;
  inset: 0;
  padding: 14px 16px 10px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.carousel-content {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.carousel-num {
  font-size: 28px;
  font-weight: 900;
  color: rgba(255,255,255,0.15);
  line-height: 1;
  flex-shrink: 0;
}

.carousel-text {
  margin: 0;
  font-size: 13px;
  color: #fff;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.carousel-dots {
  display: flex;
  gap: 5px;
}
.carousel-dots .dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: rgba(255,255,255,0.3);
  cursor: pointer;
  transition: background 0.3s;
}
.carousel-dots .dot.active {
  background: #fff;
  width: 14px;
  border-radius: 3px;
}

.carousel-fade-enter-active,
.carousel-fade-leave-active { transition: opacity 0.5s; }
.carousel-fade-enter-from,
.carousel-fade-leave-to { opacity: 0; }

/* ── 左栏：新闻列表 ──────────────────────────────────────────────────────── */
.news-list {
  flex: 1;
  overflow-y: auto;
  padding: 6px 0;
}

.news-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  cursor: pointer;
  transition: background 0.2s;
  border-radius: 8px;
  margin: 2px 6px;
}
.news-item:hover {
  background: #f5f7fa;
}

.news-rank {
  font-size: 13px;
  font-weight: 700;
  color: #ccc;
  width: 18px;
  flex-shrink: 0;
  text-align: center;
}
.news-rank.rank-top { color: #e74c3c; }

.news-title {
  flex: 1;
  font-size: 12px;
  color: #333;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.news-arrow {
  color: #ccc;
  flex-shrink: 0;
}

/* ── 中栏 ─────────────────────────────────────────────────────────────────── */
.center-panel {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
}

.hero-section {
  padding: 20px 0 12px;
  flex-shrink: 0;
}
.hero-header-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}
.hero-actions {
  display: flex;
  gap: 10px;
}
.hero-action-btn,
.result-header-btn {
  background: #fff;
  border: 1px solid #ddd;
  color: #333;
  padding: 8px 14px;
  cursor: pointer;
  transition: all 0.2s;
}
.hero-action-btn:hover,
.result-header-btn:hover {
  border-color: #c0392b;
  color: #c0392b;
}
.main-title {
  font-size: 36px;
  font-weight: 900;
  color: #c0392b;
  margin: 0 0 4px;
  letter-spacing: 4px;
  text-align: center;
  font-family: 'Noto Serif SC', 'SimSun', Georgia, serif;
}
.sub-title {
  font-size: 14px;
  color: #999;
  margin: 0;
  text-align: center;
}

.hero-title-block {
  flex: 1;
  text-align: center;
  display: flex;
  justify-content: center;
}

.initial-view {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  align-items: stretch;
}

.scan-zone {
  min-height: 44vh;
  width: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.upload-area {
  background: var(--home-upload-surface);
  border: 2px dashed var(--home-upload-border);
  border-radius: 12px;
  padding: 48px 60px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  margin: 0 auto 8px;
  width: 50%;
  min-width: 600px;
  max-width: 800px;
  flex-shrink: 0;
  position: relative;
  overflow: hidden;
}
.upload-area:hover { border-color: var(--home-upload-border-hover); background: var(--home-upload-surface-hover); }
.upload-area.disabled { opacity: 0.6; cursor: not-allowed; pointer-events: none; }

/* 卷轴装饰 */
.scroll-decoration {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 40px;
  background: var(--home-upload-scroll-gradient);
  box-shadow: inset 0 0 12px rgba(8, 14, 24, 0.18), 0 0 18px var(--home-upload-button-glow);
  z-index: 1;
  transition: background 0.35s ease, box-shadow 0.35s ease;
}
.left-scroll {
  left: 0;
  animation: scrollUnrollLeft 1.2s cubic-bezier(0.34, 1.56, 0.64, 1) both;
  transform-origin: left center;
}
.right-scroll {
  right: 0;
  animation: scrollUnrollRight 1.2s cubic-bezier(0.34, 1.56, 0.64, 1) both;
  transform-origin: right center;
}

@keyframes scrollUnrollLeft {
  from { transform: scaleX(0); }
  to { transform: scaleX(1); }
}
@keyframes scrollUnrollRight {
  from { transform: scaleX(0); }
  to { transform: scaleX(1); }
}

.upload-content {
  position: relative;
  z-index: 2;
}

.upload-title-block {
  margin-bottom: 24px;
}

/* 打字机效果 */
.upload-title-block :deep(.policy-title) {
  overflow: hidden;
  border-right: 2px solid var(--home-upload-border-hover);
  white-space: nowrap;
  animation: typing 1.5s steps(4) 0.3s both, blink 0.75s step-end infinite;
}

.upload-title-block :deep(.policy-subtitle) {
  overflow: hidden;
  white-space: nowrap;
  animation: typing 2s steps(12) 1.8s both;
}

@keyframes typing {
  from { width: 0; }
  to { width: 100%; }
}

@keyframes blink {
  50% { border-color: transparent; }
}

.upload-buttons {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-bottom: 14px;
}

@keyframes fadeInLeft {
  from { opacity: 0; transform: translateX(-20px); }
  to   { opacity: 1; transform: translateX(0); }
}
.upload-round-btn:nth-child(1) { animation: fadeInLeft 0.4s ease 0.05s both; }
.upload-round-btn:nth-child(2) { animation: fadeInLeft 0.4s ease 0.15s both; }
.upload-round-btn:nth-child(3) { animation: fadeInLeft 0.4s ease 0.25s both; }
.action-btn {
  background: var(--upload-round-btn-bg, var(--home-upload-button-bg));
  border: none;
  border-radius: 0;
  padding: 8px 18px;
  font-size: 13px;
  font-weight: bold;
  color: var(--upload-round-btn-text, #fff);
  cursor: pointer;
  transition: background 0.25s ease, transform 0.2s ease, box-shadow 0.25s ease;
}
.action-btn:hover {
  background: var(--upload-round-btn-hover-bg, var(--home-upload-button-hover-bg));
  transform: translateY(-1px);
}

.upload-round-btn {
  --upload-round-btn-bg: var(--home-upload-button-solid-bg);
  --upload-round-btn-hover-bg: var(--home-upload-button-solid-hover-bg);
  --upload-round-btn-shadow: var(--home-upload-button-solid-shadow);
  --upload-round-btn-glow: var(--home-upload-button-solid-glow);
  --upload-round-btn-text: var(--home-upload-button-solid-text);
  width: 98px;
  height: 98px;
  border-radius: 50% !important;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow:
    0 4px 0 var(--upload-round-btn-shadow, var(--home-upload-button-shadow)),
    0 14px 28px var(--upload-round-btn-glow, var(--home-upload-button-glow));
  padding: 0 !important;
}

/* Capsule button style (shared) */
.capsule-btn {
  border-radius: 999px !important;
  background: #c0392b !important;
  color: #fff !important;
  border: none !important;
  box-shadow: 0 3px 0 #922b21 !important;
  padding: 7px 18px !important;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.15s;
}
.capsule-btn:hover { background: #e74c3c !important; box-shadow: 0 2px 0 #922b21 !important; transform: translateY(1px); }
.capsule-btn:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
.upload-hint { font-size: 13px; color: var(--home-upload-hint-color); margin: 0; }

.url-float {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 260px;
  background: #fff;
  border: 1px solid #e5e5e5;
  box-shadow: 0 8px 24px rgba(0,0,0,0.12);
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  z-index: 5;
}

.url-float-title {
  font-size: 12px;
  font-weight: 700;
  color: #333;
  text-align: left;
}

.url-float-input {
  border: 1px solid #ddd;
  padding: 6px 8px;
  font-size: 12px;
  outline: none;
}

.url-float-input:focus {
  border-color: #c0392b;
}

.url-float-actions {
  display: flex;
  justify-content: flex-end;
  gap: 6px;
}

.url-float-btn {
  border: 1px solid #ddd;
  background: #fff;
  padding: 4px 10px;
  font-size: 11px;
  cursor: pointer;
}

.url-float-btn.primary {
  background: #c0392b;
  border-color: #c0392b;
  color: #fff;
}

.loading-banner {
  background:
    radial-gradient(circle at top right, color-mix(in srgb, var(--color-accent-cool) 12%, transparent), transparent 38%),
    linear-gradient(155deg, color-mix(in srgb, var(--color-primary) 7%, var(--card-bg)), var(--card-bg));
  color: var(--text-primary);
  padding: 16px 18px 14px;
  border: 1px solid color-mix(in srgb, var(--color-primary) 14%, var(--border-color));
  border-radius: 18px;
  margin: 0 auto 16px;
  width: min(800px, calc(100vw - 32px));
  box-sizing: border-box;
  box-shadow: 0 18px 34px color-mix(in srgb, var(--color-primary) 12%, transparent);
  display: flex;
  font-size: 14px;
  animation: fadeIn 0.5s;
  gap: 10px;
  flex-direction: column;
  align-items: stretch;
  position: relative;
  overflow: hidden;
}

.loading-banner::after {
  content: '';
  position: absolute;
  inset: auto -30% 0 auto;
  width: 180px;
  height: 180px;
  border-radius: 50%;
  background: color-mix(in srgb, var(--color-primary) 8%, transparent);
  filter: blur(12px);
  pointer-events: none;
}

.loading-banner-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
}

.loading-copy {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.loading-kicker {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-secondary);
}

.loading-title {
  font-weight: 800;
  font-size: 15px;
  color: var(--text-primary);
}

.loading-metrics {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.loading-percent {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 58px;
  padding: 5px 10px;
  border-radius: 999px;
  background: var(--color-primary);
  color: #fff;
  font-size: 12px;
  font-weight: 800;
  box-shadow: 0 10px 18px color-mix(in srgb, var(--color-primary) 18%, transparent);
}

.loading-elapsed {
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 700;
}

.loading-stage-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.loading-stage-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--color-primary), var(--color-secondary));
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--color-primary) 12%, transparent);
  animation: pulseDot 1.4s ease-in-out infinite;
}

.loading-stage {
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 600;
}

.loading-progress-track {
  width: 100%;
  height: 12px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-primary) 10%, var(--border-color));
  overflow: hidden;
  position: relative;
}

.loading-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--color-primary-dark) 0%, var(--color-primary) 54%, var(--color-secondary) 100%);
  border-radius: 999px;
  transition: width 0.35s ease;
  position: relative;
}

.loading-progress-fill::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(110deg, transparent 0%, rgba(255,255,255,0.18) 35%, rgba(255,255,255,0.42) 50%, transparent 65%);
  transform: translateX(-100%);
  animation: progressShine 1.5s linear infinite;
}

.loading-progress-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-size: 11px;
  color: var(--text-muted);
  font-weight: 600;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-8px); }
  to   { opacity: 1; transform: translateY(0); }
}

@keyframes progressShine {
  to { transform: translateX(100%); }
}

@keyframes pulseDot {
  0%, 100% { transform: scale(1); opacity: 0.85; }
  50% { transform: scale(1.18); opacity: 1; }
}

/* 示例区域 */
.examples-section {
  margin-top: 4px;
  width: min(100%, 64vw, 1200px);
  max-width: 1200px;
  margin-left: auto;
  margin-right: auto;
}
.examples-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.section-title {
  font-size: 14px;
  color: var(--text-primary);
  margin-bottom: 14px;
  font-weight: bold;
}
.examples-nav {
  display: flex;
  gap: 8px;
}
.examples-nav-btn {
  border: 1px solid color-mix(in srgb, var(--color-primary) 18%, var(--border-color));
  background: var(--card-bg);
  color: var(--color-primary-dark);
  width: 30px;
  height: 30px;
  border-radius: 999px;
  cursor: pointer;
  font-size: 18px;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 16px color-mix(in srgb, var(--color-primary) 8%, transparent);
  transition: background 0.2s ease, color 0.2s ease, border-color 0.2s ease, transform 0.2s ease;
}
.examples-nav-btn:hover {
  background: color-mix(in srgb, var(--color-primary) 10%, var(--card-bg));
  border-color: color-mix(in srgb, var(--color-primary) 34%, var(--border-color));
  color: var(--color-primary);
  transform: translateY(-1px);
}
.examples-carousel {
  overflow: hidden;
  padding-top: 0;
  margin-top: 0;
}
.examples-track {
  display: flex;
  transition: transform 0.45s ease;
  will-change: transform;
}
.examples-page {
  min-width: 100%;
  width: 100%;
  padding-top: 56px;
  box-sizing: border-box;
}
.examples-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 20px;
}
.example-card {
  background: var(--card-bg);
  border-radius: 14px;
  border: 1px solid color-mix(in srgb, var(--color-primary) 10%, var(--border-color));
  display: flex;
  flex-direction: column;
  cursor: pointer;
  transition: all 0.3s;
  opacity: 0;
  animation: exampleFadeIn 0.6s ease forwards, exampleShake 0.5s ease forwards;
  position: relative;
  overflow: visible;
}

@keyframes exampleFadeIn {
  from {
    opacity: 0;
    transform: translateY(30px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes exampleShake {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  25% { transform: translateY(-3px) rotate(-2deg); }
  50% { transform: translateY(0) rotate(0deg); }
  75% { transform: translateY(-3px) rotate(2deg); }
}

.example-card:hover {
  box-shadow: 0 18px 30px color-mix(in srgb, var(--color-primary) 12%, transparent);
  transform: translateY(-4px);
}
.example-card:hover .breakout-image {
  transform: translateX(-50%) translateY(-14px) rotate(0deg) scale(1.03);
  box-shadow: none;
}
.card-image-wrapper {
  height: 140px;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: visible;
  border-radius: 14px 14px 0 0;
  z-index: 1;
}
.breakout-image {
  position: absolute;
  bottom: -16px;
  left: 50%;
  transform: translateX(-50%) translateY(-14px) rotate(2deg);
  width: 78%;
  max-width: 230px;
  border-radius: 4px;
  box-shadow: none;
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  z-index: 3;
  background: transparent;
  padding: 0;
}
.breakout-image img {
  width: auto;
  max-width: 100%;
  max-height: 180px;
  height: auto;
  display: block;
  border-radius: 2px;
  margin: 0 auto;
}
.card-content {
  padding: 40px 16px 16px;
  background: var(--card-bg, #fff);
  flex: 1;
  z-index: 4;
  position: relative;
  border-radius: 0 0 14px 14px;
}
.card-title {
  font-size: 16px;
  margin: 0 0 8px;
  color: var(--text-primary);
  font-weight: 600;
  line-height: 1.4;
  min-height: 36px;
}
.card-tags { display: flex; gap: 6px; flex-wrap: wrap; }
.tag {
  background: color-mix(in srgb, var(--color-primary) 10%, var(--card-bg));
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 11px;
  color: var(--color-primary-dark);
  border: 1px solid color-mix(in srgb, var(--color-primary) 18%, var(--border-color));
}
.examples-dots {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-top: 14px;
}
.examples-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  border: none;
  background: color-mix(in srgb, var(--color-primary) 22%, var(--border-color));
  cursor: pointer;
  transition: all 0.25s ease;
}
.examples-dot.active {
  width: 22px;
  background: linear-gradient(90deg, var(--color-primary-dark), var(--color-primary));
}

:global([data-theme="dark"]) .example-card {
  background: var(--card-bg);
  border-color: rgba(255,255,255,0.1);
}

:global([data-theme="dark"]) .card-content {
  background: var(--card-bg);
}

:global([data-theme="dark"]) .card-title {
  color: #e2e8f0;
}

:global([data-theme="dark"]) .tag {
  background: rgba(192,57,43,0.2);
  border-color: rgba(192,57,43,0.4);
}

:global([data-theme="dark"]) .loading-banner {
  background:
    radial-gradient(circle at top right, color-mix(in srgb, var(--color-accent-cool) 12%, transparent), transparent 40%),
    linear-gradient(155deg, color-mix(in srgb, var(--color-primary) 12%, var(--card-bg)), var(--card-bg));
  border-color: color-mix(in srgb, var(--color-primary) 18%, var(--border-color));
}

:global([data-theme="dark"]) .loading-kicker,
:global([data-theme="dark"]) .loading-elapsed,
:global([data-theme="dark"]) .loading-stage {
  color: var(--text-secondary);
}

:global([data-theme="dark"]) .loading-progress-meta {
  color: var(--text-muted);
}

:global([data-theme="dark"]) .loading-progress-track {
  background: color-mix(in srgb, var(--color-primary) 14%, var(--border-color));
}

:global([data-theme="dark"]) .loading-progress-fill {
  background: linear-gradient(90deg, var(--color-primary-dark) 0%, var(--color-primary) 52%, var(--color-secondary) 100%);
}

@media (max-width: 1360px) {
  .three-col-layout {
    gap: 12px;
    padding: 12px;
  }

  .examples-section {
    width: min(100%, 72vw, 1040px);
  }

  .examples-grid {
    gap: 18px;
  }
}

@media (max-width: 1180px) {
  .three-col-layout,
  .three-col-layout.right-collapsed {
    grid-template-columns: 32px 1fr 32px;
    gap: 10px;
    padding: 10px;
  }

  .history-drawer-shell {
    width: min(248px, calc(100vw - 72px));
  }

  .right-drawer-shell {
    width: min(292px, calc(100vw - 72px));
  }

  .history-section {
    padding: 10px 10px 12px;
  }

  .doc-titles-scroll {
    max-height: 132px;
  }

  .cloud-section,
  .doc-content-section {
    padding-left: 12px;
    padding-right: 12px;
  }

  .examples-section {
    width: 100%;
  }

  .examples-page {
    padding-top: 46px;
  }

  .examples-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 16px;
  }
}

@media (max-width: 768px) {
  .three-col-layout,
  .three-col-layout.right-collapsed {
    grid-template-columns: 24px 1fr 24px;
    gap: 8px;
    padding: 8px;
  }

  .history-drawer-shell {
    width: min(236px, calc(100vw - 48px));
  }

  .right-drawer-shell {
    width: min(272px, calc(100vw - 48px));
  }

  .panel-header {
    padding: 10px 12px 9px;
  }

  .panel-title {
    font-size: 13px;
  }

  .panel-badge,
  .switch-btn {
    font-size: 10px;
  }

  .history-item,
  .doc-title-item {
    padding: 6px 10px;
  }

  .history-item-title,
  .doc-title-text {
    font-size: 11px;
  }

  .history-detail-title,
  .doc-content-title {
    font-size: 12px;
  }

  .doc-content-body {
    font-size: 11.5px;
    line-height: 1.7;
  }

  .examples-section {
    margin-top: 8px;
  }

  .examples-head {
    gap: 10px;
  }

  .section-title {
    margin-bottom: 10px;
  }

  .examples-page {
    padding-top: 36px;
  }

  .examples-grid {
    grid-template-columns: 1fr;
    gap: 14px;
  }

  .card-image-wrapper {
    height: 126px;
  }

  .breakout-image {
    width: 74%;
    max-width: 210px;
  }

  .card-content {
    padding: 36px 14px 14px;
  }

  .card-title {
    font-size: 15px;
    min-height: 0;
  }

  .examples-nav-btn {
    width: 28px;
    height: 28px;
    font-size: 16px;
  }

  .tag {
    font-size: 10px;
  }

  .loading-banner {
    width: calc(100vw - 28px);
    padding: 14px 14px 12px;
    border-radius: 16px;
  }

  .loading-banner-head,
  .loading-progress-meta {
    flex-direction: column;
    align-items: stretch;
  }

  .loading-metrics {
    justify-content: space-between;
  }
}

/* 热点资讯图片横条 */
.news-image-strip { margin-top: 20px; }
.news-image-list { display: flex; flex-direction: column; gap: 8px; }
.news-image-item {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #fff;
  border-radius: 0;
  border: 1px solid #e8e8e8;
  border-left: 3px solid #c0392b;
  padding: 10px;
  cursor: pointer;
  transition: background 0.2s;
}
.news-image-item:hover { background: #fdf5f5; }
.news-img-block {
  width: 72px;
  height: 52px;
  border-radius: 8px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}
.news-img-label {
  font-size: 11px;
  color: rgba(255,255,255,0.9);
  font-weight: 700;
  letter-spacing: 1px;
}
.news-img-text { flex: 1; min-width: 0; }
.news-img-title {
  margin: 0 0 4px;
  font-size: 13px;
  color: #222;
  font-weight: 600;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.news-img-date { font-size: 11px; color: #aaa; }

/* 结果视图 */
.result-view {
  animation: fadeIn 0.5s;
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
}
.result-header {
  display: flex;
  align-items: center;
  margin-bottom: 14px;
  flex-shrink: 0;
}
.result-header-actions {
  margin-left: auto;
}
.back-btn {
  background: none;
  border: 1px solid #ccc;
  padding: 6px 14px;
  border-radius: 20px;
  cursor: pointer;
  margin-right: 16px;
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 13px;
  transition: all 0.2s;
  color: #000;
}
.back-btn:hover { background: #f0f0f0; }
.result-header h2 { margin: 0; font-size: 18px; }

.response-section {
  background: #fff;
  border-radius: 12px;
  border: 1px solid #e0e0e0;
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
}
.fixed-result-header { padding: 16px 24px; border-bottom: 1px solid #eee; flex-shrink: 0; position: relative; }
.parse-mode-badge {
  position: absolute;
  right: 16px;
  bottom: 6px;
  font-size: 10px;
  color: #888;
  opacity: 0.7;
}
.header-top-row { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
.result-title { margin: 0; font-size: 20px; color: #000; font-weight: bold; }
.tags-container { display: flex; gap: 8px; flex: 1; }
.result-actions { display: flex; gap: 8px; margin-left: auto; }
.result-action-btn {
  display: flex; align-items: center; gap: 4px;
  background: #f5f5f5; border: 1px solid #e0e0e0;
  padding: 5px 12px; font-size: 12px; cursor: pointer;
  color: #444; transition: all 0.2s;
}
.result-action-btn:hover { border-color: #c0392b; color: #c0392b; background: #fff0f0; }
.result-action-btn.favorited { color: #c0392b; border-color: #c0392b; background: #fff0f0; }
.highlight-tag { background: #000; color: #fff; padding: 4px 14px; border-radius: 20px; font-size: 12px; font-weight: bold; }
.info-tag { background: var(--color-primary, #ffe066); color: #000; padding: 4px 14px; border-radius: 20px; font-size: 12px; font-weight: bold; }

.scrollable-content { padding: 24px; overflow-y: auto; flex: 1; }
.result-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }

.info-list { display: flex; flex-direction: column; gap: 20px; }
.info-item { display: flex; align-items: flex-start; }
.info-text strong { display: block; margin-bottom: 6px; color: #000; font-size: 14px; }
.info-text p { margin: 0; color: #333; line-height: 1.6; font-size: 14px; }
.process-text { white-space: pre-wrap; color: #333; line-height: 1.6; background: var(--content-bg, #f5f7fa); padding: 12px; border-radius: 8px; border: 1px solid #eee; font-size: 14px; }

.process-flowchart { margin-top: 12px; display: flex; flex-direction: column; align-items: flex-start; gap: 0; }
.flow-step-wrap { display: flex; flex-direction: column; align-items: flex-start; width: 100%; }
.flow-step {
  display: flex; align-items: center; gap: 10px;
  background: #fff; border: 1px solid #e0e0e0; border-left: 3px solid #c0392b;
  padding: 8px 14px; border-radius: 4px; width: 100%; box-sizing: border-box;
}
.flow-num {
  width: 22px; height: 22px; border-radius: 50%;
  background: #c0392b; color: #fff; font-size: 11px; font-weight: 700;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.flow-text { font-size: 13px; color: #333; line-height: 1.4; }
.flow-arrow { font-size: 12px; color: #c0392b; padding: 2px 0 2px 12px; }

.right-panel { display: flex; flex-direction: column; gap: 20px; }
.warning-panel { display: flex; flex-direction: column; gap: 12px; }
.warning-box { padding: 12px; border-radius: 8px; background: #fff; color: #666; border: 1px solid #eee; }
.warning-box h4 { margin: 0 0 6px; font-size: 13px; font-weight: bold; color: #000; }
.warning-box p { margin: 0; font-size: 12px; line-height: 1.6; }

.analysis-dashboard { display: flex; gap: 16px; padding: 12px 0; border-top: 1px dashed #eee; border-bottom: 1px dashed #eee; }
.dashboard-item { display: flex; align-items: center; gap: 6px; }
.dashboard-item .label { color: #666; font-size: 13px; }
.dashboard-item .value.text-only { font-weight: bold; font-size: 13px; }
.level-high { color: #e53935 !important; }
.level-medium { color: #f57c00 !important; }
.level-low { color: #43a047 !important; }

/* ── 右栏：中央文件 ──────────────────────────────────────────────────────── */
.right-panel-col {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.right-stack {
  position: relative;
  height: 100%;
  overflow: visible;
  z-index: 40;
  isolation: isolate;
}

.right-drawer-shell {
  position: absolute;
  right: 0;
  top: 0;
  width: 300px;
  height: 100%;
  transform: translateX(0);
  transition: transform 0.35s cubic-bezier(0.4,0,0.2,1);
  z-index: 41;
}

.right-stack:not(.open) .right-drawer-shell {
  transform: translateX(calc(100% - 40px));
}

.right-drawer-tab {
  left: -40px;
  border-radius: 8px 0 0 8px;
  box-shadow: -2px 0 10px color-mix(in srgb, var(--color-primary) 24%, transparent);
  z-index: 42;
}

/* 文件标题列表 */
.doc-titles-scroll {
  flex-shrink: 0;
  max-height: 140px;
  overflow-y: auto;
  padding: 6px 0;
  border-bottom: 1px solid color-mix(in srgb, var(--color-primary) 10%, var(--border-color));
}

.doc-title-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 7px 14px;
  cursor: pointer;
  border-radius: 8px;
  margin: 2px 6px;
  background: color-mix(in srgb, var(--color-primary) 4%, var(--card-bg));
  border: 1px solid transparent;
  transition: background 0.2s ease, border-color 0.2s ease, transform 0.2s ease;
}
.doc-title-item:hover {
  background: color-mix(in srgb, var(--color-primary) 8%, var(--card-bg));
  border-color: color-mix(in srgb, var(--color-primary) 20%, var(--border-color));
}
.doc-title-item.active {
  background: color-mix(in srgb, var(--color-primary) 12%, var(--card-bg));
  border-color: color-mix(in srgb, var(--color-primary) 32%, var(--border-color));
  transform: translateX(-1px);
}

.doc-index {
  font-size: 11px;
  font-weight: 700;
  color: var(--color-primary-dark);
  flex-shrink: 0;
  margin-top: 1px;
}

.doc-title-text {
  font-size: 12px;
  color: var(--text-primary);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 词云区域 */
.cloud-section {
  flex-shrink: 0;
  padding: 10px 14px 6px;
  border-bottom: 1px solid color-mix(in srgb, var(--color-primary) 10%, var(--border-color));
}
.cloud-label {
  font-size: 11px;
  color: var(--text-secondary);
  margin-bottom: 6px;
  font-weight: 600;
  letter-spacing: 0.5px;
}
.word-cloud-chart {
  width: 100%;
  height: 160px;
  border-radius: 12px;
  background: linear-gradient(180deg, color-mix(in srgb, var(--color-primary) 5%, var(--card-bg)), var(--card-bg));
  border: 1px solid color-mix(in srgb, var(--color-primary) 10%, var(--border-color));
}

/* 文件内容展示 */
.doc-content-section {
  flex: 1;
  overflow-y: auto;
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.doc-content-header {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.red-header-bar {
  background:
    linear-gradient(
      90deg,
      var(--color-primary-dark) 0%,
      var(--color-primary) 54%,
      var(--color-secondary) 100%
    );
  color: #fff;
  text-align: center;
  padding: 6px 10px;
  font-size: 11px;
  font-weight: 700;
  border-radius: 4px;
  letter-spacing: 1px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}
.red-star { font-size: 10px; }

.doc-content-title {
  margin: 0;
  font-size: 13px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.5;
  text-align: center;
}

.doc-date {
  font-size: 11px;
  color: var(--text-muted);
  text-align: center;
}

.doc-content-body {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.8;
  text-indent: 2em;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.doc-read-more {
  color: var(--color-primary-dark);
  font-size: 12px;
  text-decoration: none;
  font-weight: 600;
  text-indent: 0;
  align-self: flex-end;
}
.doc-read-more:hover {
  color: var(--color-primary);
  text-decoration: underline;
}

/* ── 骨架屏 ──────────────────────────────────────────────────────────────── */
.loading-placeholder { padding: 8px 14px; }
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
</style>
