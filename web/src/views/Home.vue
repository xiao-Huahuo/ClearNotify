<template>
  <div class="home-container">
    <!-- ═══════════════════════════════════════════════════════════
         三栏布局：左(时事热点) | 中(文件处理) | 右(红头文件)
    ═══════════════════════════════════════════════════════════ -->
    <div class="three-col-layout">

      <!-- ── 左栏：时事热点 ─────────────────────────────────────── -->
      <aside class="left-panel panel-card">
        <div class="panel-header">
          <span class="panel-dot dot-blue"></span>
          <h3 class="panel-title">时事热点</h3>
          <span class="panel-badge">实时</span>
        </div>

        <!-- 轮播图 -->
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

        <!-- Top 10 列表 -->
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
      </aside>

      <!-- ── 中栏：文件处理（原有逻辑） ────────────────────────── -->
      <main class="center-panel">
        <!-- 标题区域 -->
        <div class="hero-section" v-if="!showResult">
          <h1 class="main-title">文档解析</h1>
          <p class="sub-title">全格式兼容 · 精准提取 · 详细输出</p>
        </div>

        <!-- 初始视图：上传区 -->
        <div v-if="!showResult" class="initial-view">
          <div
            class="upload-area"
            @click="triggerFileUpload"
            @dragover.prevent
            @drop.prevent="handleDrop"
            :class="{ 'disabled': loading }"
          >
            <div class="upload-buttons">
              <button class="action-btn" @click.stop="triggerFileUpload" :disabled="loading">本地上传</button>
              <button class="action-btn" @click.stop="handleUrlUpload" :disabled="loading">URL上传</button>
              <button class="action-btn" @click.stop="handleScreenshot" :disabled="loading">截图</button>
            </div>
            <p class="upload-hint">点击或拖拽上传 (支持 TXT, PDF, Word, Excel)</p>
            <input type="file" ref="fileInput" style="display:none" @change="handleFileUpload" accept=".txt,.pdf,.doc,.docx,.xls,.xlsx" />
            <input type="file" ref="screenshotInput" style="display:none" @change="handleScreenshotUpload" accept="image/jpeg,image/png,image/webp,application/pdf" />
          </div>

          <div v-if="loading" class="loading-banner"><span>正在智能解读中...</span></div>

          <!-- 示例区域 -->
          <div class="examples-section">
            <h2 class="section-title">示例</h2>
            <div class="examples-grid">
              <div v-for="(ex, index) in examples" :key="ex.id" class="example-card">
                <div class="card-image-wrapper">
                  <div class="breakout-image">
                    <img :src="getExampleImage(index + 1)" alt="example document" />
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

          <!-- 热点资讯图片横条 -->
          <div class="news-image-strip" v-if="newsImages.length > 0">
            <h2 class="section-title">当下热点</h2>
            <div class="news-image-list">
              <div
                v-for="(item, idx) in newsImages"
                :key="idx"
                class="news-image-item"
                @click="openLink(item.link)"
              >
                <div class="news-img-block" :style="{ background: item.image_color || '#c0392b' }">
                  <span class="news-img-label">{{ item.category || '时事' }}</span>
                </div>
                <div class="news-img-text">
                  <p class="news-img-title">{{ item.title }}</p>
                  <span class="news-img-date">{{ item.pubDate || '最新' }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 结果视图 -->
        <div v-else class="result-view">
          <div class="result-header">
            <button @click="resetView" class="back-btn"><span class="icon">←</span> 返回</button>
            <h2>解读结果</h2>
          </div>
          <div class="response-section" v-if="aiResponse">
            <div class="fixed-result-header">
              <div class="header-top-row">
                <h3 class="result-title">{{ aiResponse.handling_matter || '未知事项' }}</h3>
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
                </div>
              </div>
            </div>
            <div class="scrollable-content">
              <div class="result-grid">
                <div class="info-list">
                  <div class="info-item" v-if="aiResponse.time_deadline">
                    <div class="info-text"><strong>办理时间：</strong><p>{{ aiResponse.time_deadline }}</p></div>
                  </div>
                  <div class="info-item" v-if="aiResponse.location_entrance">
                    <div class="info-text"><strong>办理地点/入口：</strong><p>{{ aiResponse.location_entrance }}</p></div>
                  </div>
                  <div class="info-item" v-if="aiResponse.required_materials">
                    <div class="info-text"><strong>所需材料：</strong><p>{{ aiResponse.required_materials }}</p></div>
                  </div>
                  <div class="info-item" v-if="aiResponse.handling_process">
                    <div class="info-text"><strong>办理流程：</strong>
                      <div class="process-text">{{ aiResponse.handling_process }}</div>
                      <!-- 流程图 -->
                      <div class="process-flowchart" v-if="parseProcessSteps(aiResponse.handling_process).length > 1">
                        <div
                          v-for="(step, si) in parseProcessSteps(aiResponse.handling_process)"
                          :key="si"
                          class="flow-step-wrap"
                        >
                          <div class="flow-step">
                            <span class="flow-num">{{ si + 1 }}</span>
                            <span class="flow-text">{{ step }}</span>
                          </div>
                          <div class="flow-arrow" v-if="si < parseProcessSteps(aiResponse.handling_process).length - 1">▼</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="right-panel">
                  <div class="warning-panel">
                    <div class="warning-box" v-if="aiResponse.precautions"><h4>注意事项</h4><p>{{ aiResponse.precautions }}</p></div>
                    <div class="warning-box" v-if="aiResponse.risk_warnings"><h4>风险提醒</h4><p>{{ aiResponse.risk_warnings }}</p></div>
                  </div>
                  <div class="analysis-dashboard" v-if="aiResponse.chat_analysis">
                    <div class="dashboard-item"><span class="label">语言复杂度: </span><span class="value text-only" :class="getComplexityClass(aiResponse.chat_analysis.language_complexity)">{{ aiResponse.chat_analysis.language_complexity || '未知' }}</span></div>
                    <div class="dashboard-item"><span class="label">办理复杂度: </span><span class="value text-only" :class="getComplexityClass(aiResponse.chat_analysis.handling_complexity)">{{ aiResponse.chat_analysis.handling_complexity || '未知' }}</span></div>
                    <div class="dashboard-item"><span class="label">风险等级: </span><span class="value text-only" :class="getComplexityClass(aiResponse.chat_analysis.risk_level)">{{ aiResponse.chat_analysis.risk_level || '未知' }}</span></div>
                  </div>
                  <div class="rewrite-toolbar">
                    <span>切换改写版本：</span>
                    <div class="rewrite-buttons">
                      <button class="rewrite-btn" @click="rewriteTarget('老人版')" :disabled="isRewriting">老人版</button>
                      <button class="rewrite-btn" @click="rewriteTarget('学生版')" :disabled="isRewriting">学生版</button>
                      <button class="rewrite-btn" @click="rewriteTarget('家属转述版')" :disabled="isRewriting">家属转述版</button>
                      <button class="rewrite-btn" @click="rewriteTarget('极简版')" :disabled="isRewriting">极简版</button>
                      <button class="rewrite-btn" @click="rewriteTarget('客服答复版')" :disabled="isRewriting">客服答复版</button>
                    </div>
                    <span v-if="isRewriting" class="rewriting-status">正在生成...</span>
                  </div>
                  <div class="original-text-section" v-if="aiResponse.original_text">
                    <h4>原文</h4>
                    <div class="original-content">{{ aiResponse.original_text }}</div>
                  </div>
                  <div class="mapping-section" v-if="aiResponse.file_url">
                    <h4>原文件参考</h4>
                    <a :href="aiResponse.file_url" target="_blank" class="file-link">点击查看上传的原文件</a>
                  </div>
                  <div class="mapping-section" v-else-if="aiResponse.original_text_mapping">
                    <h4>对应位置参考</h4>
                    <p>{{ aiResponse.original_text_mapping }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      <!-- ── 右栏：红头文件 ─────────────────────────────────────── -->
      <aside class="right-panel-col panel-card">
        <div class="panel-header">
          <span class="panel-dot dot-red"></span>
          <h3 class="panel-title">中央文件</h3>
          <span class="panel-badge badge-red">最新</span>
        </div>

        <!-- 最新文件标题列表（卷轴顶部） -->
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

        <!-- 热点聚类点云图 -->
        <div class="cloud-section">
          <div class="cloud-label">热点聚类分析</div>
          <div ref="wordCloudRef" class="word-cloud-chart"></div>
        </div>

        <!-- 选中文件内容展示 -->
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
      </aside>

    </div><!-- end three-col-layout -->

    <!-- 登录弹窗 -->
    <Modal :isOpen="showModal" @close="closeModal">
      <div class="auth-modal-content">
        <div class="logo-area-transition">
          <h1 class="logo-text">ClearNotify</h1>
        </div>
        <div class="form-transition-container" :style="{ height: containerHeight + 'px' }">
          <transition name="form-slide" @before-enter="onBeforeEnter" @enter="onEnter" @after-enter="onAfterEnter" @leave="onLeave">
            <div v-if="currentForm === 'login'" class="form-wrapper login-wrapper-abs" key="login">
              <LoginForm @success="handleLoginSuccess" @switch-to-register="currentForm = 'register'" />
            </div>
            <div v-else-if="currentForm === 'register'" class="form-wrapper register-wrapper-abs" key="register">
              <RegisterForm @switch-to-login="currentForm = 'login'" @success="handleLoginSuccess" />
            </div>
          </transition>
        </div>
      </div>
    </Modal>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue';
import * as echarts from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { useUserStore } from '@/stores/user';
import { createChatMessage, createChatMessageWithFile, uploadAndExtractDocument, rewriteChatMessage } from '@/api/ai';
import { getHotNews, getCentralDocs, getHotKeywords, getNewsWithImages } from '@/api/news';
import { useRouter } from 'vue-router';
import Modal from '@/components/common/Modal.vue';
import LoginForm from '@/components/Home/LoginForm.vue';
import RegisterForm from '@/components/Home/RegisterForm.vue';
import { toggleSpeak, isSpeaking } from '@/utils/tts.js';
import { apiClient, API_ROUTES } from '@/router/api_routes.js';

import ex1 from '@/assets/photos/main-examples/example1.png';
import ex2 from '@/assets/photos/main-examples/example2.jpeg';
import ex3 from '@/assets/photos/main-examples/example3.png';

const userStore = useUserStore();
const router = useRouter();

// ── 文件处理状态 ──────────────────────────────────────────────────────────────
const inputText = ref('');
const aiResponse = ref(null);
const loading = ref(false);
const isRewriting = ref(false);
const showResult = ref(false);
const fileInput = ref(null);

// ── 登录弹窗 ──────────────────────────────────────────────────────────────────
const showModal = ref(false);
const currentForm = ref('login');
const containerHeight = ref(350);

// ── 左栏：时事热点 ────────────────────────────────────────────────────────────
const hotNews = ref([]);
const newsLoading = ref(true);
const carouselIndex = ref(0);
let carouselTimer = null;

// ── 右栏：中央文件 ────────────────────────────────────────────────────────────
const centralDocs = ref([]);
const docsLoading = ref(true);
const selectedDocIdx = ref(0);
const wordCloudRef = ref(null);
let wordCloudChart = null;

// ── 热点资讯图片横条 ──────────────────────────────────────────────────────────
const newsImages = ref([]);

// ── 示例数据 ──────────────────────────────────────────────────────────────────
const examples = ref([
  { id: 1, title: '社区通知', tags: ['通知', '民生', '公告'] },
  { id: 2, title: '政务文件', tags: ['政策', '解读', '官方'] },
  { id: 3, title: '学校通知', tags: ['教育', '学生', '家长'] },
]);

const getExampleImage = (num) => {
  if (num === 1) return ex1;
  if (num === 2) return ex2;
  if (num === 3) return ex3;
  return ex1;
};

// ── 生命周期 ──────────────────────────────────────────────────────────────────
onMounted(async () => {
  if (userStore.token) userStore.fetchUser();
  window.addEventListener('open-login-modal', openLoginModal);

  // 并行加载新闻和文件
  await Promise.all([loadHotNews(), loadCentralDocs(), loadNewsImages()]);

  // 启动轮播
  carouselTimer = setInterval(() => {
    if (hotNews.value.length > 0) {
      carouselIndex.value = (carouselIndex.value + 1) % Math.min(hotNews.value.length, 5);
    }
  }, 3500);

  // 初始化词云
  await nextTick();
  initWordCloud();
});

onUnmounted(() => {
  clearInterval(carouselTimer);
  wordCloudChart?.dispose();
  window.removeEventListener('open-login-modal', openLoginModal);
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

// ── 登录弹窗逻辑 ──────────────────────────────────────────────────────────────
const onBeforeEnter = (el) => { el.style.opacity = 0; };
const onEnter = (el, done) => {
  nextTick(() => { containerHeight.value = el.offsetHeight; el.style.opacity = 1; done(); });
};
const onAfterEnter = (el) => { el.style.opacity = ''; };
const onLeave = (el, done) => { el.style.opacity = 0; setTimeout(done, 400); };

const openLoginModal = () => { currentForm.value = 'login'; containerHeight.value = 350; showModal.value = true; };
const closeModal = () => { showModal.value = false; };
const handleLoginSuccess = () => closeModal();

// ── 文件处理逻辑 ──────────────────────────────────────────────────────────────
const triggerFileUpload = () => {
  if (loading.value) return;
  if (!userStore.token) { openLoginModal(); return; }
  fileInput.value.click();
};

const handleFileUpload = (event) => processFile(event.target.files[0]);

const handleDrop = (event) => {
  if (loading.value) return;
  if (!userStore.token) { openLoginModal(); return; }
  processFile(event.dataTransfer.files[0]);
};

const processFile = async (file) => {
  if (!file) return;
  loading.value = true;
  aiResponse.value = null;
  try {
    const uploadRes = await uploadAndExtractDocument(file);
    const { extracted_text, file_url } = uploadRes.data;
    const chatRes = await createChatMessageWithFile(extracted_text, file_url);
    aiResponse.value = chatRes.data;
    showResult.value = true;
  } catch (error) {
    if (error.response?.status === 401) { userStore.logout(); openLoginModal(); }
    else alert('文件处理失败: ' + (error.response?.data?.detail || error.message));
  } finally {
    loading.value = false;
    if (fileInput.value) fileInput.value.value = '';
  }
};

const handleUrlUpload = () => {
  if (loading.value) return;
  if (!userStore.token) { openLoginModal(); return; }
  const url = prompt('请输入 URL:');
  if (url) { inputText.value = `URL: ${url}`; submitToAI(); }
};

const handleScreenshot = () => {
  if (!userStore.token) { openLoginModal(); return; }
  // 触发隐藏的图片文件选择器
  screenshotInput.value?.click();
};

const screenshotInput = ref(null);

const handleScreenshotUpload = async (event) => {
  const file = event.target.files?.[0];
  if (!file) return;
  loading.value = true;
  aiResponse.value = null;
  try {
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
    const response = await createChatMessage(extractedText);
    aiResponse.value = { ...response.data, file_url: ocrRes.data.file_url };
    showResult.value = true;
  } catch (error) {
    console.error('截图OCR失败:', error);
    alert('截图识别失败，请重试。');
  } finally {
    loading.value = false;
    event.target.value = '';
  }
};

const submitToAI = async () => {
  if (!userStore.token) { openLoginModal(); return; }
  if (!inputText.value.trim()) return;
  loading.value = true;
  aiResponse.value = null;
  try {
    const response = await createChatMessage(inputText.value);
    aiResponse.value = response.data;
    showResult.value = true;
  } catch (error) {
    if (error.response?.status === 401) { userStore.logout(); openLoginModal(); }
    else alert('解析失败: ' + (error.response?.data?.detail || error.message));
  } finally {
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
  if (fileInput.value) fileInput.value.value = '';
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
    await apiClient.post(API_ROUTES.FAVORITE + '?chat_message_id=' + aiResponse.value.id);
    isFavorited.value = true;
  } catch (e) { console.warn('收藏失败', e); }
}

const parseProcessSteps = (text) => {
  if (!text) return [];
  // 尝试按数字序号、换行、分号等分割
  const byNum = text.split(/\d+[.、。）)]\s*/);
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
  grid-template-columns: 260px 1fr 260px;
  gap: 16px;
  padding: 16px;
  flex: 1;
  overflow: hidden;
  min-height: 0;
}

/* ── 通用面板卡片 ─────────────────────────────────────────────────────────── */
.panel-card {
  background: #fff;
  border-radius: 16px;
  border: 1px solid #eee;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px 10px;
  background: linear-gradient(90deg, #7f8c8d 0%, #95a5a6 100%);
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
.main-title {
  font-size: 28px;
  font-weight: 800;
  color: #000;
  margin: 0 0 4px;
  letter-spacing: 2px;
}
.sub-title {
  font-size: 14px;
  color: #999;
  margin: 0;
}

.initial-view {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.upload-area {
  background: #fff;
  border: 2px dashed #e0e0e0;
  border-radius: 0;
  border-left: 4px solid #c0392b;
  padding: 28px 40px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 16px;
  flex-shrink: 0;
}
.upload-area:hover { border-color: #c0392b; background: #fdf5f5; }
.upload-area.disabled { opacity: 0.6; cursor: not-allowed; pointer-events: none; }

.upload-buttons {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-bottom: 14px;
}
.action-btn {
  background: #c0392b;
  border: none;
  border-radius: 0;
  padding: 8px 18px;
  font-size: 13px;
  font-weight: bold;
  color: #fff;
  cursor: pointer;
  transition: all 0.2s;
}
.action-btn:hover { background: #e74c3c; }
.upload-hint { font-size: 13px; color: #999; margin: 0; }

.loading-banner {
  background: #fff0f0;
  color: #c0392b;
  padding: 10px;
  border-left: 3px solid #c0392b;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
  font-weight: bold;
  font-size: 14px;
  animation: fadeIn 0.5s;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-8px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* 示例区域 */
.examples-section { margin-top: 12px; }
.section-title { font-size: 14px; color: #000; margin-bottom: 14px; font-weight: bold; }
.examples-grid { display: flex; gap: 16px; flex-wrap: wrap; }
.example-card {
  flex: 1;
  min-width: 160px;
  max-width: 260px;
  background: #fff;
  border-radius: 0;
  border: 1px solid #e8e8e8;
  border-top: 3px solid #c0392b;
  display: flex;
  flex-direction: column;
  cursor: pointer;
  transition: box-shadow 0.2s;
}
.example-card:hover { box-shadow: 0 4px 16px rgba(192,57,43,0.12); }
.example-card:hover .breakout-image {
  transform: translateY(-20px) rotate(0deg);
  box-shadow: 0 16px 30px rgba(0,0,0,0.18);
}
.card-image-wrapper {
  height: 120px;
  background: linear-gradient(135deg, #fdf5f5, #f5e6e6);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}
.breakout-image {
  position: absolute;
  bottom: -30px;
  right: 12px;
  width: 140px;
  border-radius: 0;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  transform: translateY(0) rotate(3deg);
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  z-index: 10;
}
.breakout-image img { width: 100%; height: auto; display: block; }
.card-content {
  padding: 10px 12px;
  background: #fff;
  flex: 1;
  z-index: 1;
  position: relative;
  margin-top: 20px;
}
.card-title { font-size: 13px; margin: 0 0 6px; color: #222; font-weight: 600; }
.card-tags { display: flex; gap: 6px; flex-wrap: wrap; }
.tag { background: #fff0f0; padding: 2px 8px; border-radius: 0; font-size: 11px; color: #c0392b; border: 1px solid #f5c6c6; }

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
.fixed-result-header { padding: 16px 24px; border-bottom: 1px solid #eee; flex-shrink: 0; }
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

.rewrite-toolbar { display: flex; flex-direction: column; gap: 8px; }
.rewrite-toolbar span { color: #000; font-weight: bold; font-size: 13px; }
.rewrite-buttons { display: flex; flex-wrap: wrap; gap: 8px; }
.rewrite-btn { background: #fff; border: 1px solid #000; color: #000; padding: 5px 12px; border-radius: 20px; cursor: pointer; transition: all 0.2s; font-size: 12px; font-weight: 500; }
.rewrite-btn:hover:not(:disabled) { background: var(--color-primary, #ffe066); border-color: var(--color-primary, #ffe066); }
.rewrite-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.rewriting-status { font-size: 12px; color: #999; font-style: italic; font-weight: normal !important; }

.original-text-section { flex: 1; display: flex; flex-direction: column; min-height: 150px; }
.original-text-section h4 { margin: 0 0 8px; font-size: 14px; font-weight: bold; color: #000; }
.original-content { flex: 1; background: #fafafa; border: 1px solid #eee; border-radius: 8px; padding: 12px; color: #666; font-size: 13px; line-height: 1.6; white-space: pre-wrap; overflow-y: auto; max-height: 300px; }

.mapping-section { padding-top: 12px; }
.mapping-section h4 { margin: 0 0 6px; font-size: 13px; font-weight: bold; color: #000; }
.mapping-section p { margin: 0; font-size: 12px; line-height: 1.5; color: #666; }
.file-link { color: #00a8ff; text-decoration: underline; }

/* ── 右栏：中央文件 ──────────────────────────────────────────────────────── */
.right-panel-col {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 文件标题列表 */
.doc-titles-scroll {
  flex-shrink: 0;
  max-height: 140px;
  overflow-y: auto;
  padding: 6px 0;
  border-bottom: 1px solid #f0f0f0;
}

.doc-title-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 7px 14px;
  cursor: pointer;
  border-radius: 8px;
  margin: 2px 6px;
  transition: background 0.2s;
}
.doc-title-item:hover { background: #fef9f9; }
.doc-title-item.active { background: #fff0f0; }

.doc-index {
  font-size: 11px;
  font-weight: 700;
  color: #c0392b;
  flex-shrink: 0;
  margin-top: 1px;
}

.doc-title-text {
  font-size: 12px;
  color: #333;
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
  border-bottom: 1px solid #f0f0f0;
}
.cloud-label {
  font-size: 11px;
  color: #999;
  margin-bottom: 6px;
  font-weight: 600;
  letter-spacing: 0.5px;
}
.word-cloud-chart {
  width: 100%;
  height: 160px;
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
  background: #c0392b;
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
  color: #111;
  line-height: 1.5;
  text-align: center;
}

.doc-date {
  font-size: 11px;
  color: #999;
  text-align: center;
}

.doc-content-body {
  font-size: 12px;
  color: #444;
  line-height: 1.8;
  text-indent: 2em;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.doc-read-more {
  color: #c0392b;
  font-size: 12px;
  text-decoration: none;
  font-weight: 600;
  text-indent: 0;
  align-self: flex-end;
}
.doc-read-more:hover { text-decoration: underline; }

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

/* ── 登录弹窗 ─────────────────────────────────────────────────────────────── */
.auth-modal-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 0 0;
  background: linear-gradient(45deg, skyblue, darkblue);
  border-radius: 20px;
  width: 480px;
  min-height: 450px;
  overflow: hidden;
  transition: height 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}
.logo-area-transition { display: flex; flex-direction: column; align-items: center; gap: 10px; margin-bottom: 20px; }
.auth-modal-content .logo-text { color: #fff; font-size: 28px; font-weight: 800; margin: 0; letter-spacing: 1px; }
.form-transition-container { width: 100%; position: relative; transition: height 0.4s cubic-bezier(0.4, 0, 0.2, 1); }
.form-wrapper { width: 100%; display: flex; justify-content: center; }
.login-wrapper-abs, .register-wrapper-abs { position: absolute; top: 0; left: 0; }
.form-slide-enter-active, .form-slide-leave-active { transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1); }
.form-slide-enter-from { opacity: 0; transform: translateY(30px); }
.form-slide-leave-to { opacity: 0; transform: translateY(-30px); }
</style>

