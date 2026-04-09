<template>
  <div class="swipe-page">
    <div class="swipe-header">
      <PolicyTitle title="政策推荐阅读" />
      <p class="swipe-desc">根据您的职业和浏览偏好，为您推荐相关政策</p>
    </div>

    <div class="swipe-layout" :class="{ 'article-open': activeDoc }">
      <!-- 左侧：概览栏（初始）/ 文章内容（点击后） -->
      <div class="left-section" :class="{ 'show-article': activeDoc }">
        <!-- 概览面板 -->
        <div class="overview-panel" v-show="!activeDoc">
          <!-- 轮播图 -->
          <div class="carousel-section">
            <transition name="slide-fade" mode="out-in">
              <div class="carousel-slide" :key="slideIdx" :style="getCarouselStyle(carouselDocs[slideIdx])">
                <div class="slide-overlay"></div>
                <div class="slide-content">
                  <span class="slide-tag">{{ carouselDocs[slideIdx]?.category || '政策文件' }}</span>
                  <h3 class="slide-title">{{ carouselDocs[slideIdx]?.title || '加载中...' }}</h3>
                  <p class="slide-meta">浏览 {{ carouselDocs[slideIdx]?.view_count || 0 }} · 点赞 {{ carouselDocs[slideIdx]?.like_count || 0 }}</p>
                </div>
              </div>
            </transition>
            <div class="carousel-dots">
              <span v-for="(_, i) in carouselDocs" :key="i" class="dot" :class="{ active: i === slideIdx }" @click="slideIdx = i"></span>
            </div>
          </div>

          <!-- 概览列表 -->
          <div class="overview-list" ref="overviewRef" @scroll="onScroll">
            <div class="overview-header">
              <span class="overview-dot"></span>
              <span class="overview-title">政策概览</span>
            </div>
            <div v-for="doc in docs" :key="doc.id" class="overview-item"
              :class="{ active: activeId === doc.id }" @click="openDoc(doc)">
              <div class="ov-top">
                <span class="ov-cat" v-if="doc.category">{{ doc.category }}</span>
                <span class="ov-date">{{ formatDate(doc.created_time) }}</span>
              </div>
              <h3 class="ov-title">{{ doc.title }}</h3>
              <div class="ov-meta">
                <span class="ov-author">{{ doc.uploader_name || '认证主体' }}</span>
                <div class="ov-stats">
                  <span class="ov-stat">
                    <svg viewBox="0 0 24 24" width="11" height="11" stroke="currentColor" stroke-width="2" fill="none"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                    {{ doc.view_count }}
                  </span>
                  <span class="ov-stat">
                    <svg viewBox="0 0 24 24" width="11" height="11" stroke="currentColor" stroke-width="2" fill="none"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3H14z"/></svg>
                    {{ doc.like_count }}
                  </span>
                </div>
              </div>
            </div>
            <div v-if="loading" class="loading-more">
              <div class="spinner-sm"></div> 加载中...
            </div>
            <div v-if="!loading && !hasMore" class="no-more">已加载全部内容</div>
          </div>
        </div>

        <!-- 文章阅读面板 -->
        <div class="reader-panel" v-show="activeDoc">
          <template v-if="activeDoc">
            <div class="rp-header">
              <button class="rp-close" @click="activeDoc = null; activeId = null">✕</button>
              <div class="rp-tags">
                <span v-if="activeDoc.category" class="rp-cat">{{ activeDoc.category }}</span>
                <span v-for="tag in parsedTags" :key="tag" class="rp-tag">{{ tag }}</span>
              </div>
            </div>
            <h1 class="rp-title">{{ activeDoc.title }}</h1>
            <div class="rp-meta">
              <span>{{ activeDoc.uploader_name || '认证主体' }}</span>
              <span>{{ formatDate(activeDoc.created_time) }}</span>
              <span>{{ activeDoc.view_count }} 次浏览</span>
            </div>
            <div class="rp-body">{{ activeDoc.content }}</div>
            <div class="rp-actions">
              <button class="rp-like" @click="likeDoc(activeDoc)">
                <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3H14z"/></svg>
                {{ activeDoc.like_count }} 点赞
              </button>
            </div>
          </template>
        </div>
      </div>

      <!-- 右侧：中央文件栏（初始）/ 合并面板（点击后） -->
      <div class="right-section" :class="{ 'merged': activeDoc }">
        <!-- 面板头部（点击后显示切换开关） -->
        <div class="panel-header" v-if="activeDoc">
          <span class="panel-dot" :class="rightPanelMode === 'docs' ? 'dot-red' : 'dot-blue'"></span>
          <h3 class="panel-title">{{ rightPanelMode === 'docs' ? '中央文件' : '时事热点' }}</h3>
          <div class="right-panel-switch">
            <button class="switch-btn" :class="{ active: rightPanelMode === 'docs' }" @click="rightPanelMode = 'docs'">中央文件</button>
            <button class="switch-btn" :class="{ active: rightPanelMode === 'news' }" @click="rightPanelMode = 'news'">时事热点</button>
          </div>
        </div>

        <!-- 中央文件内容 -->
        <div class="docs-content" v-show="!activeDoc || rightPanelMode === 'docs'">
          <h3 class="section-title" v-if="!activeDoc">中央文件</h3>
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
        </div>

        <!-- 时事热点内容 -->
        <div class="news-content" v-show="!activeDoc || rightPanelMode === 'news'">
          <h3 class="section-title" v-if="!activeDoc">时事热点</h3>
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
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import PolicyTitle from '@/components/common/PolicyTitle.vue'
import { useUserStore } from '@/stores/auth.js'
import { apiClient, API_ROUTES } from '@/router/api_routes'
import { getHotNews, getCentralDocs } from '@/api/news'

const userStore = useUserStore()
const docs = ref([])
const loading = ref(false)
const hasMore = ref(true)
const skip = ref(0)
const LIMIT = 10
const activeDoc = ref(null)
const activeId = ref(null)
const overviewRef = ref(null)
const slideIdx = ref(0)
const carouselDocs = ref([])
let carouselTimer = null

// 中央文件和热点新闻
const centralDocs = ref([])
const hotNews = ref([])
const docsLoading = ref(true)
const newsLoading = ref(true)
const selectedDocIdx = ref(0)
const rightPanelMode = ref('docs')

const parsedTags = computed(() => {
  if (!activeDoc.value?.tags) return []
  return activeDoc.value.tags.split(',').map(t => t.trim()).filter(Boolean)
})

const formatDate = (t) => t ? new Date(t).toLocaleDateString('zh-CN') : ''

const stripHtml = (html) => {
  if (!html) return ''
  return String(html).replace(/<[^>]*>/g, '')
}

const getCarouselStyle = (doc) => {
  if (!doc) return {}
  const colors = ['linear-gradient(135deg, #667eea 0%, #764ba2 100%)', 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)']
  return { background: colors[slideIdx.value % colors.length] }
}

const loadMore = async () => {
  if (loading.value || !hasMore.value) return
  loading.value = true
  try {
    const route = userStore.token ? API_ROUTES.POLICY_DOC_RECOMMEND_ME : API_ROUTES.POLICY_DOC_RECOMMEND
    const res = await apiClient.get(route, { params: { skip: skip.value, limit: LIMIT } })
    const items = res.data
    docs.value.push(...items)
    skip.value += items.length
    if (items.length < LIMIT) hasMore.value = false

    // 初始化轮播图数据
    if (carouselDocs.value.length === 0 && items.length > 0) {
      carouselDocs.value = items.slice(0, 3)
    }
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

const loadCentralDocs = async () => {
  try {
    const res = await getCentralDocs(5)
    centralDocs.value = res.data.items || []
  } catch (e) {
    console.warn('中央文件加载失败', e)
  } finally {
    docsLoading.value = false
  }
}

const loadHotNews = async () => {
  try {
    const res = await getHotNews(10)
    hotNews.value = res.data.items || []
  } catch (e) {
    console.warn('热点新闻加载失败', e)
  } finally {
    newsLoading.value = false
  }
}

const onScroll = () => {
  const el = overviewRef.value
  if (!el) return
  if (el.scrollTop + el.clientHeight >= el.scrollHeight - 100) loadMore()
}

const openDoc = async (doc) => {
  activeDoc.value = doc
  activeId.value = doc.id
  apiClient.post(API_ROUTES.POLICY_DOC_VIEW(doc.id)).catch(() => {})
}

const likeDoc = async (doc) => {
  try {
    const res = await apiClient.post(API_ROUTES.POLICY_DOC_LIKE(doc.id))
    doc.like_count = res.data.like_count
  } catch (e) { console.error(e) }
}

const openLink = (url) => {
  if (url) window.open(url, '_blank')
}

const startCarousel = () => {
  carouselTimer = setInterval(() => {
    slideIdx.value = (slideIdx.value + 1) % carouselDocs.value.length
  }, 4000)
}

onMounted(() => {
  loadMore()
  loadCentralDocs()
  loadHotNews()
  startCarousel()
})

onBeforeUnmount(() => {
  if (carouselTimer) clearInterval(carouselTimer)
})
</script>

<style scoped>
.swipe-page { padding: 24px; max-width: 1600px; margin: 0 auto; height: calc(100vh - 80px); display: flex; flex-direction: column; }
.swipe-header { margin-bottom: 20px; }
.swipe-desc { color: var(--text-secondary, #666); font-size: 14px; margin: 4px 0 0; }

.swipe-layout {
  display: grid;
  grid-template-columns: 380px 1fr;
  gap: 20px;
  flex: 1;
  min-height: 0;
  transition: grid-template-columns 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.swipe-layout.article-open {
  grid-template-columns: 1fr 400px;
}

/* 左侧区域 */
.left-section {
  position: relative;
  overflow: hidden;
}

.overview-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: 100%;
  transition: opacity 0.3s, transform 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.left-section.show-article .overview-panel {
  opacity: 0;
  transform: translateX(-30px);
  pointer-events: none;
}

.reader-panel {
  position: absolute;
  inset: 0;
  background: var(--card-bg, #fff);
  border: 1px solid var(--border-color, #e8e8e8);
  overflow-y: auto;
  padding: 24px;
  opacity: 0;
  transform: translateX(30px);
  pointer-events: none;
  transition: opacity 0.3s, transform 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.left-section.show-article .reader-panel {
  opacity: 1;
  transform: translateX(0);
  pointer-events: auto;
}

/* 右侧区域 */
.right-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: var(--card-bg, #fff);
  border: 1px solid var(--border-color, #e8e8e8);
  padding: 20px;
  overflow-y: auto;
  transition: all 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.section-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary, #111);
  margin: 0 0 16px;
  padding-bottom: 12px;
  border-bottom: 2px solid var(--color-primary, #c0392b);
}

/* 面板头部 */
.panel-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-color, #e8e8e8);
  margin-bottom: 16px;
}

.panel-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}
.dot-red { background: #c0392b; }
.dot-blue { background: #3498db; }

.panel-title {
  font-size: 16px;
  font-weight: 700;
  margin: 0;
  color: var(--text-primary, #111);
}

.right-panel-switch {
  display: flex;
  gap: 8px;
  margin-left: auto;
}

.switch-btn {
  background: transparent;
  border: 1px solid var(--border-color, #ddd);
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
  color: var(--text-secondary, #666);
}

.switch-btn.active {
  background: var(--color-primary, #c0392b);
  border-color: var(--color-primary, #c0392b);
  color: #fff;
}

/* 轮播图 */
.carousel-section {
  position: relative;
  height: 200px;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
.carousel-slide {
  position: relative;
  width: 100%;
  height: 100%;
  background-size: cover;
  background-position: center;
  cursor: pointer;
  transition: transform 0.3s;
}
.slide-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(to bottom, rgba(0,0,0,0.2), rgba(0,0,0,0.6));
}
.slide-content {
  position: relative;
  z-index: 1;
  padding: 20px;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  color: #fff;
}
.slide-tag {
  font-size: 11px;
  background: rgba(255,255,255,0.25);
  padding: 3px 10px;
  border-radius: 10px;
  width: fit-content;
  margin-bottom: 8px;
}
.slide-title {
  font-size: 16px;
  font-weight: 700;
  margin: 0 0 6px;
  line-height: 1.4;
}
.slide-meta {
  font-size: 12px;
  opacity: 0.9;
  margin: 0;
}
.carousel-dots {
  position: absolute;
  bottom: 12px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 6px;
  z-index: 2;
}
.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: rgba(255,255,255,0.5);
  cursor: pointer;
  transition: all 0.3s;
}
.dot.active {
  width: 20px;
  border-radius: 3px;
  background: #fff;
}

/* 概览列表 */
.overview-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-right: 4px;
}
.overview-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  padding: 0 4px;
}
.overview-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-primary, #c0392b);
}
.overview-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary, #111);
}
.overview-item {
  background: var(--card-bg, #fff);
  border: 1px solid var(--border-color, #e8e8e8);
  border-left: 3px solid transparent;
  padding: 12px 14px;
  cursor: pointer;
  transition: all 0.2s;
  border-radius: 6px;
}
.overview-item:hover {
  border-left-color: var(--color-primary, #c0392b);
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.overview-item.active {
  border-left-color: var(--color-primary, #c0392b);
  background: rgba(192,57,43,0.03);
}
.ov-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}
.ov-cat {
  font-size: 10px;
  background: rgba(192,57,43,0.1);
  color: #c0392b;
  padding: 2px 7px;
  border-radius: 8px;
}
.ov-date {
  font-size: 10px;
  color: #999;
}
.ov-title {
  font-size: 13px;
  font-weight: 600;
  margin: 0 0 8px;
  line-height: 1.4;
  color: var(--text-primary, #111);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.ov-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.ov-author {
  font-size: 11px;
  color: #999;
}
.ov-stats {
  display: flex;
  gap: 8px;
}
.ov-stat {
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: 11px;
  color: #bbb;
}

/* 阅读面板样式 */
.rp-header { display: flex; align-items: flex-start; gap: 12px; margin-bottom: 16px; }
.rp-close { background: none; border: 1px solid var(--border-color, #eee); width: 28px; height: 28px; border-radius: 50%; cursor: pointer; font-size: 12px; color: #999; flex-shrink: 0; transition: all 0.2s; }
.rp-close:hover { background: #f0f0f0; color: #333; }
.rp-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.rp-cat { font-size: 11px; background: rgba(192,57,43,0.1); color: #c0392b; padding: 2px 10px; border-radius: 10px; }
.rp-tag { font-size: 11px; background: var(--content-bg, #f4f5f7); color: #666; padding: 2px 10px; border-radius: 10px; }
.rp-title { font-size: 20px; font-weight: 800; margin: 0 0 12px; line-height: 1.4; color: var(--text-primary, #111); }
.rp-meta { display: flex; gap: 16px; font-size: 12px; color: #999; margin-bottom: 20px; flex-wrap: wrap; }
.rp-body { font-size: 15px; line-height: 1.9; color: var(--text-primary, #333); white-space: pre-wrap; }
.rp-actions { margin-top: 24px; padding-top: 16px; border-top: 1px solid var(--border-color, #eee); }
.rp-like { display: flex; align-items: center; gap: 6px; background: none; border: 1px solid var(--border-color, #eee); padding: 8px 20px; border-radius: 20px; cursor: pointer; font-size: 13px; color: #666; transition: all 0.2s; }
.rp-like:hover { border-color: #c0392b; color: #c0392b; }

/* 中央文件样式 */
.doc-titles-scroll {
  max-height: 200px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.doc-title-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: var(--content-bg, #f9f9f9);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.doc-title-item:hover {
  background: rgba(192,57,43,0.05);
}

.doc-title-item.active {
  background: rgba(192,57,43,0.1);
  border-left: 3px solid #c0392b;
}

.doc-index {
  font-size: 14px;
  font-weight: 700;
  color: #c0392b;
  flex-shrink: 0;
}

.doc-title-text {
  font-size: 13px;
  color: var(--text-primary, #333);
  line-height: 1.4;
  flex: 1;
}

.doc-content-section {
  background: var(--content-bg, #fafafa);
  padding: 16px;
  border-radius: 8px;
}

.doc-content-header {
  text-align: center;
  margin-bottom: 16px;
}

.red-header-bar {
  background: linear-gradient(90deg, #c0392b 0%, #e74c3c 100%);
  color: #fff;
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 12px;
}

.red-star {
  font-size: 16px;
}

.doc-content-title {
  font-size: 15px;
  font-weight: 700;
  margin: 0 0 8px;
  color: var(--text-primary, #111);
}

.doc-date {
  font-size: 11px;
  color: #999;
}

.doc-content-body {
  font-size: 13px;
  line-height: 1.8;
  color: var(--text-secondary, #666);
}

.doc-read-more {
  display: inline-block;
  margin-top: 12px;
  color: #c0392b;
  text-decoration: none;
  font-size: 13px;
  font-weight: 600;
}

.doc-read-more:hover {
  text-decoration: underline;
}

/* 时事热点样式 */
.news-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.news-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: var(--content-bg, #f9f9f9);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.news-item:hover {
  background: rgba(192,57,43,0.05);
}

.news-rank {
  font-size: 14px;
  font-weight: 700;
  color: #999;
  flex-shrink: 0;
  width: 24px;
  text-align: center;
}

.news-rank.rank-top {
  color: #c0392b;
}

.news-title {
  flex: 1;
  font-size: 13px;
  color: var(--text-primary, #333);
  line-height: 1.4;
}

.news-arrow {
  flex-shrink: 0;
  color: #ccc;
}

.loading-more { display: flex; align-items: center; justify-content: center; gap: 8px; padding: 16px; color: #999; font-size: 13px; }
.spinner-sm { width: 14px; height: 14px; border: 2px solid #eee; border-top-color: #c0392b; border-radius: 50%; animation: spin 0.7s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.no-more { text-align: center; padding: 16px; color: #ccc; font-size: 12px; }

.loading-placeholder {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.skeleton-line {
  height: 12px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.slide-fade-enter-active, .slide-fade-leave-active { transition: opacity 0.4s; }
.slide-fade-enter-from, .slide-fade-leave-to { opacity: 0; }
</style>
