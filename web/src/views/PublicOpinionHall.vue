<template>
  <div class="opinion-hall">
    <div class="hall-header">
      <PolicyTitle title="民生评议大厅" />
      <p class="hall-desc">全站用户对各项政策的落地评价、智能解析纠错和办事留言公开展示</p>
    </div>

    <!-- 顶部区域：轮播图(左2/3) + 热门政策Top5(右1/3) -->
    <div class="top-section">
      <div class="carousel-area">
        <transition name="slide-fade" mode="out-in">
          <div class="carousel-slide" :key="slideIdx" :style="getCarouselStyle(topDocs[slideIdx])">
            <div class="slide-overlay"></div>
            <div class="slide-inner">
              <span class="slide-tag">{{ topDocs[slideIdx]?.category || '政务文件' }}</span>
              <h2 class="slide-title">{{ topDocs[slideIdx]?.title || '加载中...' }}</h2>
              <p class="slide-desc">浏览 {{ topDocs[slideIdx]?.view_count || 0 }} · 点赞 {{ topDocs[slideIdx]?.like_count || 0 }}</p>
              <button class="slide-btn" @click="openDoc(topDocs[slideIdx])">查看详情</button>
            </div>
          </div>
        </transition>
        <div class="slide-dots">
          <span v-for="(_, i) in topDocs" :key="i" class="sdot" :class="{ active: i === slideIdx }" @click="slideIdx = i"></span>
        </div>
        <button class="arrow-btn left-btn" @click="prevSlide">
          <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2.5" fill="none"><polyline points="15 18 9 12 15 6"></polyline></svg>
        </button>
        <button class="arrow-btn right-btn" @click="nextSlide">
          <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2.5" fill="none"><polyline points="9 18 15 12 9 6"></polyline></svg>
        </button>
      </div>

      <!-- 热门政策 Top5 -->
      <div class="hot-docs-panel">
        <div class="panel-header">
          <span class="panel-dot"></span>
          <span>热门政策 Top5</span>
          <router-link to="/discovery-home" class="panel-more">查看全部 →</router-link>
        </div>
        <div v-for="(doc, i) in hotDocs" :key="doc.id" class="hot-doc-item" @click="openDoc(doc)">
          <span class="hot-rank" :class="{ top3: i < 3 }">{{ i + 1 }}</span>
          <div class="hot-doc-info">
            <span class="hot-doc-title">{{ doc.title }}</span>
            <span class="hot-doc-meta">{{ doc.view_count }} 浏览 · {{ doc.like_count }} 点赞</span>
          </div>
        </div>
        <div v-if="!hotDocs.length" class="empty-tip">暂无数据</div>
      </div>
    </div>

    <!-- 词云气泡区域 -->
    <div class="wordcloud-section">
      <div class="wordcloud-container" ref="wordcloudRef">
        <div
          v-for="word in cloudWords" :key="word.text"
          class="bubble-word"
          :style="word.bubbleStyle"
          @click="searchByWord(word.text)"
        >{{ word.text }}</div>
      </div>
    </div>

    <!-- 认证主体专属视图 -->
    <div v-if="userStore.isCertified || userStore.isAdmin" class="certified-section">
      <div class="section-header">
        <span class="section-dot"></span>
        <span>我的政策反馈（认证主体专属）</span>
      </div>
      <div v-if="myOpinions.length" class="opinion-list">
        <div v-for="op in myOpinions" :key="op.id" class="opinion-card certified-card">
          <div class="op-meta">
            <span class="op-type-badge" :class="op.opinion_type">{{ opTypeLabel(op.opinion_type) }}</span>
            <span class="op-user">{{ op.user_name }}</span>
            <span class="op-time">{{ formatTime(op.created_time) }}</span>
          </div>
          <p class="op-content">{{ op.content }}</p>
          <div v-if="op.rating" class="op-rating">
            <span v-for="n in 5" :key="n" class="star" :class="{ filled: n <= op.rating }">★</span>
          </div>
        </div>
      </div>
      <div v-else class="empty-tip">暂无用户对您的政策提交评议</div>
    </div>

    <!-- 实时信息流 -->
    <div class="feed-section">
      <div class="feed-header">
        <div class="section-header">
          <span class="section-dot"></span>
          <span>实时评议信息流</span>
        </div>
        <div class="feed-controls">
          <button class="mode-btn" :class="{ active: viewMode === 'list' }" @click="viewMode = 'list'">
            <svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line></svg>
            条形
          </button>
          <button class="mode-btn" :class="{ active: viewMode === 'grid' }" @click="viewMode = 'grid'">
            <svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>
            砖块
          </button>
          <button class="refresh-btn" @click="refreshFeed">
            <svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none"><polyline points="23 4 23 10 17 10"></polyline><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path></svg>
            刷新
          </button>
        </div>
      </div>

      <div class="opinion-list" :class="viewMode">
        <div v-for="op in feedOpinions" :key="op.id" class="opinion-card">
          <div class="op-meta">
            <span class="op-type-badge" :class="op.opinion_type">{{ opTypeLabel(op.opinion_type) }}</span>
            <span class="op-user">{{ op.user_name }}</span>
            <span class="op-time">{{ formatTime(op.created_time) }}</span>
          </div>
          <p class="op-content">{{ op.content }}</p>
          <div v-if="op.rating" class="op-rating">
            <span v-for="n in 5" :key="n" class="star" :class="{ filled: n <= op.rating }">★</span>
          </div>
          <div class="op-actions">
            <button class="like-btn" @click="likeOpinion(op)">
              <svg viewBox="0 0 24 24" width="12" height="12" stroke="currentColor" stroke-width="2" fill="none"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3H14z"></path><path d="M7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path></svg>
              {{ op.like_count }}
            </button>
          </div>
        </div>
      </div>

      <div v-if="feedLoading" class="loading-tip">加载中...</div>
      <div v-else-if="!feedHasMore" class="end-tip">— 已到底部 —</div>
      <div ref="loadMoreRef" class="load-more-trigger"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import PolicyTitle from '@/components/common/PolicyTitle.vue'
import { useUserStore } from '@/stores/auth.js'
import { useRouter } from 'vue-router'
import { apiClient, API_ROUTES } from '@/router/api_routes'

const userStore = useUserStore()
const router = useRouter()

const slideIdx = ref(0)
const topDocs = ref([])
const hotDocs = ref([])
const cloudWords = ref([])
const feedOpinions = ref([])
const myOpinions = ref([])
const feedLoading = ref(false)
const feedHasMore = ref(true)
const feedSkip = ref(0)
const viewMode = ref('list')
const wordcloudRef = ref(null)
const loadMoreRef = ref(null)

const SLIDE_COLORS = ['#c0392b', '#2980b9', '#27ae60', '#8e44ad', '#e67e22']
const carouselImageModules = import.meta.glob('/src/assets/photos/opinion-carousel/*.{jpg,jpeg,png,webp}', { eager: true })
const carouselImages = Object.entries(carouselImageModules)
  .sort(([a], [b]) => a.localeCompare(b, 'zh-CN'))
  .map(([, mod]) => mod.default)

let slideTimer = null
let observer = null

const prevSlide = () => { slideIdx.value = (slideIdx.value - 1 + topDocs.value.length) % topDocs.value.length }
const nextSlide = () => { slideIdx.value = (slideIdx.value + 1) % topDocs.value.length }
const getCarouselStyle = (doc) => {
  const style = { background: doc?.bg || '#c0392b' }
  if (doc?.bgImage) {
    style.backgroundImage = `url(${doc.bgImage})`
    style.backgroundSize = 'cover'
    style.backgroundPosition = 'center'
  }
  return style
}

const opTypeLabel = (t) => ({ review: '落地评价', correction: '解析纠错', message: '办事留言' }[t] || t)

const formatTime = (t) => {
  if (!t) return ''
  const d = new Date(t)
  return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`
}

const openDoc = (doc) => {
  if (!doc) return
  router.push({ name: 'discovery-home' })
}

const searchByWord = (word) => {
  router.push({ name: 'search', query: { q: word } })
}

const buildWordCloud = (opinions) => {
  const freq = {}
  opinions.forEach(op => {
    op.content.split(/[\s，。！？、,.!?]+/).filter(w => w.length >= 2).forEach(w => {
      freq[w] = (freq[w] || 0) + 1
    })
  })
  const sorted = Object.entries(freq).sort((a, b) => b[1] - a[1]).slice(0, 28)
  const max = sorted[0]?.[1] || 1
  cloudWords.value = sorted.map(([text, count], i) => {
    const ratio = count / max
    const size = 10 + ratio * 12
    const dim = size * text.length * 0.52 + 14
    return {
      text,
      bubbleStyle: {
        '--bubble-color': SLIDE_COLORS[i % SLIDE_COLORS.length],
        '--float-dur': `${3.5 + (i % 5) * 0.7}s`,
        '--float-delay': `${(i * 0.4) % 4}s`,
        fontSize: `${size}px`,
        width: `${dim}px`,
        height: `${dim}px`,
        opacity: 0.72 + ratio * 0.28,
      }
    }
  })
}

const loadFeed = async () => {
  if (feedLoading.value || !feedHasMore.value) return
  feedLoading.value = true
  try {
    const res = await apiClient.get(API_ROUTES.OPINIONS_FEED, { params: { skip: feedSkip.value, limit: 20 } })
    const items = res.data
    feedOpinions.value.push(...items)
    feedSkip.value += items.length
    if (items.length < 20) feedHasMore.value = false
    buildWordCloud(feedOpinions.value)
  } catch (e) {
    console.error(e)
  } finally {
    feedLoading.value = false
  }
}

const refreshFeed = () => {
  feedOpinions.value = []
  feedSkip.value = 0
  feedHasMore.value = true
  loadFeed()
}

const likeOpinion = async (op) => {
  try {
    const res = await apiClient.post(API_ROUTES.OPINION_LIKE(op.id))
    op.like_count = res.data.like_count
  } catch (e) { console.error(e) }
}

onMounted(async () => {
  // 加载已审核政务文件
  try {
    const res = await apiClient.get(API_ROUTES.POLICY_DOCS_APPROVED, { params: { limit: 10 } })
    const docs = res.data.map((d, i) => ({
      ...d,
      bg: SLIDE_COLORS[i % SLIDE_COLORS.length],
      bgImage: carouselImages.length ? carouselImages[i % carouselImages.length] : ''
    }))
    topDocs.value = docs.slice(0, 5)
    hotDocs.value = [...docs].sort((a, b) => (b.view_count + b.like_count) - (a.view_count + a.like_count)).slice(0, 5)
  } catch (e) {
    topDocs.value = [{ title: '暂无政策文件', bg: '#c0392b', bgImage: carouselImages[0] || '', view_count: 0, like_count: 0 }]
  }

  // 认证主体加载自己的评议
  if (userStore.isCertified || userStore.isAdmin) {
    try {
      const res = await apiClient.get(API_ROUTES.OPINIONS_MINE)
      myOpinions.value = res.data
    } catch (e) { console.error(e) }
  }

  await loadFeed()

  // 轮播定时器
  slideTimer = setInterval(nextSlide, 4000)

  // 无限滚动
  observer = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting) loadFeed()
  }, { threshold: 0.1 })
  if (loadMoreRef.value) observer.observe(loadMoreRef.value)
})

onUnmounted(() => {
  clearInterval(slideTimer)
  observer?.disconnect()
})
</script>

<style scoped>
.opinion-hall {
  padding: 20px 18px;
  max-width: none;
  margin: 0;
}

.hall-header { margin-bottom: 24px; }
.hall-desc { color: var(--color-text-muted, #666); font-size: 14px; margin: 6px 0 0; }

/* 顶部区域 */
.top-section {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;
  margin-bottom: 24px;
  height: 280px;
}

.carousel-area {
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  height: 100%;
}

.carousel-slide {
  width: 100%; height: 100%;
  display: flex; align-items: center;
  position: relative;
}

.slide-overlay {
  position: absolute; inset: 0;
  background: rgba(0,0,0,0.35);
}

.slide-inner {
  position: relative; z-index: 1;
  padding: 32px;
  color: #fff;
}

.slide-tag {
  background: rgba(255,255,255,0.2);
  padding: 3px 10px; border-radius: 12px;
  font-size: 12px; margin-bottom: 10px; display: inline-block;
}

.slide-title { font-size: 22px; font-weight: 800; margin: 8px 0; line-height: 1.3; }
.slide-desc { font-size: 13px; opacity: 0.85; margin-bottom: 16px; }

.slide-btn {
  background: #fff; color: #c0392b;
  border: none; padding: 8px 20px;
  border-radius: 20px; font-weight: bold;
  cursor: pointer; font-size: 13px;
}

.slide-dots {
  position: absolute; bottom: 12px; left: 50%;
  transform: translateX(-50%);
  display: flex; gap: 6px; z-index: 2;
}

.sdot {
  width: 6px; height: 6px; border-radius: 50%;
  background: rgba(255,255,255,0.5); cursor: pointer; transition: all 0.3s;
}
.sdot.active { background: #fff; width: 18px; border-radius: 3px; }

.arrow-btn {
  position: absolute; top: 50%; transform: translateY(-50%);
  background: rgba(255,255,255,0.2); border: none;
  width: 32px; height: 32px; border-radius: 50%;
  cursor: pointer; color: #fff; display: flex;
  align-items: center; justify-content: center; z-index: 2;
  transition: background 0.2s;
}
.arrow-btn:hover { background: rgba(255,255,255,0.4); }
.left-btn { left: 12px; }
.right-btn { right: 12px; }

/* 热门政策面板 */
.hot-docs-panel {
  background: var(--color-bg-card, #fff);
  border: 1px solid var(--color-border, #e8e8e8);
  border-left: 3px solid #c0392b;
  border-radius: 4px;
  padding: 16px;
  overflow-y: auto;
}

.panel-header {
  display: flex; align-items: center; gap: 8px;
  margin-bottom: 12px; font-weight: bold; font-size: 14px;
}
.panel-dot { width: 8px; height: 8px; border-radius: 50%; background: #c0392b; }
.panel-more { margin-left: auto; font-size: 12px; color: #c0392b; text-decoration: none; }

.hot-doc-item {
  display: flex; align-items: flex-start; gap: 10px;
  padding: 8px 0; border-bottom: 1px solid var(--color-border, #f0f0f0);
  cursor: pointer; transition: opacity 0.2s;
}
.hot-doc-item:hover { opacity: 0.7; }
.hot-doc-item:last-child { border-bottom: none; }

.hot-rank {
  width: 20px; height: 20px; border-radius: 4px;
  background: #f0f0f0; color: #999;
  font-size: 12px; font-weight: bold;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.hot-rank.top3 { background: #c0392b; color: #fff; }

.hot-doc-info { display: flex; flex-direction: column; gap: 3px; }
.hot-doc-title { font-size: 13px; font-weight: 500; line-height: 1.4; }
.hot-doc-meta { font-size: 11px; color: #999; }

/* 词云气泡 */
.wordcloud-section {
  background: var(--color-bg-card, #fff);
  border: 1px solid var(--color-border, #e8e8e8);
  border-radius: 0;
  padding: 14px 24px;
  margin-left: -18px;
  margin-right: -18px;
  margin-bottom: 24px;
  min-height: 140px;
}

.wordcloud-container {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.bubble-word {
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: color-mix(in srgb, var(--bubble-color) 15%, white);
  border: 1px solid color-mix(in srgb, var(--bubble-color) 40%, white);
  color: var(--bubble-color);
  font-weight: 700;
  cursor: pointer;
  user-select: none;
  animation: bubbleFloat var(--float-dur, 4s) ease-in-out infinite;
  animation-delay: var(--float-delay, 0s);
  transition: transform 0.2s, box-shadow 0.2s;
  text-align: center;
  padding: 2px;
  box-shadow: 0 2px 8px color-mix(in srgb, var(--bubble-color) 20%, transparent);
}

:global([data-theme="dark"]) .bubble-word {
  background: transparent;
  border: 1px solid color-mix(in srgb, var(--bubble-color) 60%, transparent);
}

.bubble-word:hover {
  transform: scale(1.18);
  box-shadow: 0 6px 20px color-mix(in srgb, var(--bubble-color) 35%, transparent);
  z-index: 1;
}

@keyframes bubbleFloat {
  0%, 100% { transform: translateY(0) rotate(-1deg); }
  33%       { transform: translateY(-8px) rotate(1deg); }
  66%       { transform: translateY(-4px) rotate(-0.5deg); }
}

/* 认证主体专属 */
.certified-section {
  margin-bottom: 24px;
  background: var(--color-bg-card, #fff);
  border: 1px solid var(--color-border, #e8e8e8);
  border-left: 3px solid #1a56db;
  padding: 20px;
}

:global([data-theme="dark"]) .certified-section {
  background: var(--card-bg);
  border-color: rgba(255,255,255,0.1);
}

/* 信息流 */
.feed-section {
  background: var(--color-bg-card, #fff);
  border: 1px solid var(--color-border, #e8e8e8);
  padding: 20px;
}

:global([data-theme="dark"]) .feed-section {
  background: var(--card-bg);
  border-color: rgba(255,255,255,0.1);
}

.feed-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 16px;
}

.feed-controls { display: flex; gap: 8px; }

.mode-btn, .refresh-btn {
  display: flex; align-items: center; gap: 4px;
  background: none; border: 1px solid var(--color-border, #e8e8e8);
  padding: 5px 10px; border-radius: 4px;
  font-size: 12px; cursor: pointer; color: #666;
  transition: all 0.2s;
}
.mode-btn.active, .mode-btn:hover, .refresh-btn:hover {
  background: #c0392b; color: #fff; border-color: #c0392b;
}

.section-header {
  display: flex; align-items: center; gap: 8px;
  font-weight: bold; font-size: 14px;
}
.section-dot { width: 8px; height: 8px; border-radius: 50%; background: #c0392b; }

/* 评议卡片 */
.opinion-list { display: flex; flex-direction: column; gap: 12px; }
.opinion-list.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
}

.opinion-card {
  border: 1px solid var(--color-border, #e8e8e8);
  border-left: 3px solid #c0392b;
  padding: 14px 16px;
  transition: box-shadow 0.2s;
}
.opinion-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.06); }

:global([data-theme="dark"]) .opinion-card {
  border-color: rgba(255,255,255,0.1);
}
:global([data-theme="dark"]) .opinion-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.3); }

.certified-card { border-left-color: #1a56db; }

.op-meta {
  display: flex; align-items: center; gap: 8px;
  margin-bottom: 8px; flex-wrap: wrap;
}

.op-type-badge {
  font-size: 11px; padding: 2px 8px; border-radius: 10px; font-weight: bold;
}
.op-type-badge.review { background: #fce4e4; color: #c0392b; }
.op-type-badge.correction { background: #e8f0fe; color: #1a56db; }
.op-type-badge.message { background: #e8f5e9; color: #2e7d32; }

.op-user { font-size: 12px; font-weight: 600; }
.op-time { font-size: 11px; color: #999; margin-left: auto; }

:global([data-theme="dark"]) .op-user { color: #e2e8f0; }
:global([data-theme="dark"]) .op-time { color: #94a3b8; }

.op-content { font-size: 14px; line-height: 1.6; margin: 0 0 8px; color: var(--color-text, #333); }

:global([data-theme="dark"]) .op-content { color: #cbd5e1; }

.op-rating { display: flex; gap: 2px; margin-bottom: 8px; }
.star { color: #ddd; font-size: 14px; }
.star.filled { color: #f39c12; }

.op-actions { display: flex; gap: 8px; }
.like-btn {
  display: flex; align-items: center; gap: 4px;
  background: none; border: 1px solid var(--color-border, #e8e8e8);
  padding: 3px 8px; border-radius: 12px;
  font-size: 12px; cursor: pointer; color: #666;
  transition: all 0.2s;
}
.like-btn:hover { color: #c0392b; border-color: #c0392b; }

.loading-tip, .end-tip, .empty-tip {
  text-align: center; color: #999; font-size: 13px; padding: 20px;
}

.load-more-trigger { height: 20px; }

.slide-fade-enter-active, .slide-fade-leave-active { transition: opacity 0.4s; }
.slide-fade-enter-from, .slide-fade-leave-to { opacity: 0; }
</style>
