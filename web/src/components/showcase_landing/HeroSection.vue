<template>
  <section class="hero-section" :class="{ ready }">
    <div class="hero-backdrop">
      <div class="hero-grid"></div>
      <span class="hero-orb orb-one"></span>
      <span class="hero-orb orb-two"></span>
      <span class="hero-orb orb-three"></span>
    </div>

    <div class="hero-shell">
      <div class="hero-copy">
        <div class="hero-badge">智能政策分析平台</div>
        <p class="hero-kicker">POLICY INTELLIGENCE · PUBLIC SIGNAL · AGENT WORKFLOW</p>
        <h1 class="hero-title">
          用企业级展示语言，
          <br />
          重构政策产品的第一印象
        </h1>
        <p class="hero-description">
          云上观策把政策发布、公众理解、智能解析和意见反馈压缩进一个整屏叙事首页，
          让“政务系统”第一次看起来像真正完成过品牌设计的产品。
        </p>

        <div class="hero-actions">
          <button class="hero-btn primary" @click="router.push('/')">立即体验</button>
          <button class="hero-btn ghost" @click="router.push('/showcase/discovery')">浏览政策广场</button>
        </div>

        <div class="hero-stats">
          <article v-for="(stat, index) in heroStats" :key="stat.label" class="stat-card" :style="{ '--delay': `${index * 90}ms` }">
            <span class="stat-label">{{ stat.label }}</span>
            <strong class="stat-value">{{ stat.value }}</strong>
            <span class="stat-note">{{ stat.note }}</span>
          </article>
        </div>
      </div>

      <div class="hero-visual">
        <div class="visual-frame">
          <div class="visual-topbar">
            <span class="signal-pill live">LIVE</span>
            <span class="signal-pill">{{ previewTitle }}</span>
            <span class="signal-pill subtle">SHOWCASE</span>
          </div>

          <div class="visual-main">
            <div class="visual-column focus">
              <div class="focus-card">
                <span class="focus-tag">政策脉冲</span>
                <h3>把复杂业务翻译成首页级叙事</h3>
                <p>数字指标、Agent 流程、内容广场与公众反馈在同一张画面里联动。</p>
                <div class="focus-wave">
                  <span v-for="bar in 18" :key="bar" :style="{ '--bar': bar }"></span>
                </div>
              </div>

              <div class="mini-matrix">
                <div v-for="signal in heroPreviewSignals" :key="signal.label" class="matrix-card">
                  <span class="matrix-dot" :style="{ background: signal.accent }"></span>
                  <div>
                    <strong>{{ signal.value }}</strong>
                    <p>{{ signal.label }}</p>
                  </div>
                </div>
              </div>
            </div>

            <div class="visual-column side">
              <div class="insight-card top">
                <span>01</span>
                <strong>可演示的品牌首页</strong>
              </div>
              <div class="insight-card middle">
                <span>02</span>
                <strong>真实接口接入的动态指标</strong>
              </div>
              <div class="insight-card bottom">
                <span>03</span>
                <strong>AI Agent 驱动的使用闭环</strong>
              </div>
            </div>
          </div>
        </div>

        <button class="scroll-hint" @click="handleNextSection">
          <span>继续向下</span>
          <i></i>
        </button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { apiClient, API_ROUTES } from '@/router/api_routes'
import { heroPreviewSignals } from './showcaseContent'
import { emitShowcaseGoto, showcaseSectionProps, useSectionReady } from './useShowcaseSection'

defineOptions({ name: 'HeroSection' })
defineProps(showcaseSectionProps)

const router = useRouter()
const ready = useSectionReady()
const previewTitle = ref('政策展示首页')
const heroStats = ref([
  { label: '已发布政策', value: '—', note: '公开可读的政策内容' },
  { label: '注册用户', value: '—', note: '平台累计接入账号' },
  { label: '智能解析', value: '—', note: '累计 AI 解析次数' },
  { label: '参与评议', value: '—', note: '群众反馈与讨论' },
])

const fallbackStats = {
  approved_docs: 128,
  total_users: 5200,
  total_messages: 18400,
  total_opinions: 860,
}

const numberWithSuffix = (value) => `${Number(value || 0).toLocaleString()}+`

const syncStats = (payload = fallbackStats) => {
  previewTitle.value = Number(payload.approved_docs || 0) > 999 ? '大规模政策触达' : '政策展示首页'
  heroStats.value = [
    { label: '已发布政策', value: numberWithSuffix(payload.approved_docs), note: '公开可读的政策内容' },
    { label: '注册用户', value: numberWithSuffix(payload.total_users), note: '平台累计接入账号' },
    { label: '智能解析', value: numberWithSuffix(payload.total_messages), note: '累计 AI 解析次数' },
    { label: '参与评议', value: numberWithSuffix(payload.total_opinions), note: '群众反馈与讨论' },
  ]
}

const loadStats = async () => {
  try {
    const { data } = await apiClient.get(API_ROUTES.SHOWCASE_PUBLIC_STATS)
    syncStats(data)
  } catch (error) {
    console.warn('首页公开统计加载失败，使用兜底数据。', error)
    syncStats(fallbackStats)
  }
}

const handleNextSection = () => {
  emitShowcaseGoto(1)
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.hero-section {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
  background:
    radial-gradient(circle at 18% 22%, rgba(255, 183, 111, 0.24), transparent 28%),
    radial-gradient(circle at 82% 18%, rgba(94, 197, 255, 0.22), transparent 30%),
    linear-gradient(135deg, #140c12 0%, #512334 38%, #15233f 72%, #09131f 100%);
  color: #fff;
}

.hero-backdrop,
.hero-grid {
  position: absolute;
  inset: 0;
}

.hero-grid {
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.06) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.06) 1px, transparent 1px);
  background-size: 120px 120px;
  mask-image: radial-gradient(circle at center, black 38%, transparent 95%);
  opacity: 0.22;
}

.hero-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(10px);
  animation: drift 12s ease-in-out infinite;
}

.orb-one {
  inset: 10% auto auto 60%;
  width: 320px;
  height: 320px;
  background: radial-gradient(circle, rgba(92, 219, 255, 0.42), transparent 68%);
}

.orb-two {
  inset: auto auto 8% 10%;
  width: 420px;
  height: 420px;
  background: radial-gradient(circle, rgba(255, 115, 115, 0.26), transparent 68%);
  animation-delay: -4s;
}

.orb-three {
  inset: 24% auto auto 20%;
  width: 180px;
  height: 180px;
  background: radial-gradient(circle, rgba(255, 219, 100, 0.26), transparent 65%);
  animation-delay: -8s;
}

.hero-shell {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(360px, 0.95fr);
  gap: 48px;
  align-items: center;
  height: 100%;
  padding: 108px 6vw 72px;
}

.hero-copy,
.hero-visual {
  opacity: 0;
  transform: translateY(42px);
  transition: opacity 0.9s var(--showcase-ease), transform 0.9s var(--showcase-ease);
}

.hero-section.ready .hero-copy,
.hero-section.ready .hero-visual {
  opacity: 1;
  transform: translateY(0);
}

.hero-visual {
  transition-delay: 0.14s;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.18);
  box-shadow: 0 0 24px rgba(255, 144, 101, 0.18);
  font-size: 13px;
  letter-spacing: 0.14em;
}

.hero-kicker {
  margin: 18px 0 14px;
  color: rgba(255, 255, 255, 0.68);
  font-size: 12px;
  letter-spacing: 0.36em;
}

.hero-title {
  margin: 0;
  font-family: 'STZhongsong', 'Songti SC', 'Noto Serif SC', serif;
  font-size: clamp(40px, 5vw, 72px);
  line-height: 1.06;
  letter-spacing: 0.02em;
  text-shadow: 0 16px 40px rgba(0, 0, 0, 0.26);
}

.hero-description {
  max-width: 640px;
  margin: 24px 0 0;
  color: rgba(255, 255, 255, 0.78);
  font-size: 17px;
  line-height: 1.82;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  margin-top: 32px;
}

.hero-btn {
  height: 50px;
  padding: 0 26px;
  border-radius: 999px;
  border: 1px solid transparent;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition:
    transform 0.3s var(--showcase-ease),
    box-shadow 0.3s ease,
    background 0.3s ease,
    border-color 0.3s ease;
}

.hero-btn:hover {
  transform: translateY(-3px);
}

.hero-btn.primary {
  background: linear-gradient(135deg, #fff4e4 0%, #ffd5c0 100%);
  color: #5f2030;
  box-shadow: 0 18px 42px rgba(255, 160, 112, 0.24);
}

.hero-btn.ghost {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
  border-color: rgba(255, 255, 255, 0.16);
  backdrop-filter: blur(18px);
}

.hero-stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin-top: 42px;
}

.stat-card {
  position: relative;
  padding: 18px 18px 20px;
  border-radius: 22px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.13), rgba(255, 255, 255, 0.06));
  border: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08);
  opacity: 0;
  transform: translateY(22px);
  transition:
    opacity 0.7s ease,
    transform 0.7s var(--showcase-ease),
    border-color 0.3s ease;
  transition-delay: var(--delay);
}

.hero-section.ready .stat-card {
  opacity: 1;
  transform: translateY(0);
}

.stat-card:hover {
  border-color: rgba(255, 255, 255, 0.26);
}

.stat-label,
.stat-note {
  display: block;
}

.stat-label {
  color: rgba(255, 255, 255, 0.64);
  font-size: 12px;
  letter-spacing: 0.14em;
}

.stat-value {
  display: block;
  margin-top: 10px;
  font-family: 'Bahnschrift', 'DIN Alternate', 'Segoe UI', sans-serif;
  font-size: clamp(24px, 2vw, 32px);
  letter-spacing: 0.02em;
}

.stat-note {
  margin-top: 8px;
  color: rgba(255, 255, 255, 0.48);
  font-size: 11px;
}

.visual-frame {
  position: relative;
  padding: 22px;
  border-radius: 30px;
  background:
    linear-gradient(180deg, rgba(14, 19, 30, 0.86), rgba(8, 12, 20, 0.96)),
    linear-gradient(135deg, rgba(255, 255, 255, 0.08), transparent);
  border: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow:
    0 40px 90px rgba(0, 0, 0, 0.36),
    inset 0 1px 0 rgba(255, 255, 255, 0.08);
}

.visual-frame::after {
  content: '';
  position: absolute;
  inset: 16px;
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  pointer-events: none;
}

.visual-topbar {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 18px;
}

.signal-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 7px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.72);
  font-size: 11px;
  letter-spacing: 0.12em;
}

.signal-pill.live {
  background: rgba(255, 120, 102, 0.16);
  color: #ffd7d1;
}

.signal-pill.subtle {
  margin-left: auto;
}

.visual-main {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) 180px;
  gap: 16px;
}

.visual-column {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.focus-card,
.matrix-card,
.insight-card {
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.focus-card {
  padding: 24px;
}

.focus-tag {
  display: inline-flex;
  padding: 7px 12px;
  border-radius: 999px;
  background: rgba(255, 206, 168, 0.12);
  color: #ffd0bc;
  font-size: 11px;
  letter-spacing: 0.12em;
}

.focus-card h3 {
  margin: 18px 0 10px;
  font-size: 26px;
  line-height: 1.2;
}

.focus-card p {
  margin: 0;
  color: rgba(255, 255, 255, 0.66);
  line-height: 1.74;
}

.focus-wave {
  display: grid;
  grid-template-columns: repeat(18, 1fr);
  gap: 6px;
  align-items: end;
  height: 110px;
  margin-top: 22px;
}

.focus-wave span {
  display: block;
  border-radius: 999px 999px 4px 4px;
  background: linear-gradient(180deg, rgba(255, 143, 122, 0.98), rgba(88, 203, 255, 0.28));
  height: calc(18px + (var(--bar) * 4px));
  animation: pulse-bar 2.8s ease-in-out infinite;
  animation-delay: calc(var(--bar) * 0.08s);
}

.mini-matrix {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.matrix-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px;
}

.matrix-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  box-shadow: 0 0 14px currentColor;
}

.matrix-card strong {
  display: block;
  font-size: 13px;
}

.matrix-card p {
  margin: 4px 0 0;
  color: rgba(255, 255, 255, 0.54);
  font-size: 11px;
}

.insight-card {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 118px;
  padding: 18px;
}

.insight-card span {
  color: rgba(255, 255, 255, 0.42);
  font-size: 12px;
}

.insight-card strong {
  font-size: 16px;
  line-height: 1.5;
}

.insight-card.top {
  background: linear-gradient(135deg, rgba(255, 123, 123, 0.18), rgba(255, 255, 255, 0.04));
}

.insight-card.middle {
  background: linear-gradient(135deg, rgba(95, 212, 255, 0.18), rgba(255, 255, 255, 0.04));
}

.insight-card.bottom {
  background: linear-gradient(135deg, rgba(128, 250, 176, 0.16), rgba(255, 255, 255, 0.04));
}

.scroll-hint {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  margin-top: 18px;
  padding: 0;
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.74);
  font-size: 13px;
  cursor: pointer;
}

.scroll-hint i {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.22);
  position: relative;
}

.scroll-hint i::before {
  content: '';
  position: absolute;
  inset: 8px;
  border-right: 1px solid currentColor;
  border-bottom: 1px solid currentColor;
  transform: rotate(45deg);
}

@keyframes pulse-bar {
  0%,
  100% {
    transform: scaleY(0.82);
    opacity: 0.62;
  }
  50% {
    transform: scaleY(1.08);
    opacity: 1;
  }
}

@keyframes drift {
  0%,
  100% {
    transform: translate3d(0, 0, 0);
  }
  50% {
    transform: translate3d(18px, -16px, 0);
  }
}

@media (max-width: 1180px) {
  .hero-shell {
    grid-template-columns: 1fr;
    gap: 28px;
    padding-top: 96px;
  }

  .hero-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .hero-shell {
    padding: 88px 20px 36px;
  }

  .hero-description {
    font-size: 15px;
  }

  .hero-stats {
    gap: 10px;
  }

  .visual-main,
  .mini-matrix {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .hero-title {
    font-size: clamp(34px, 12vw, 56px);
  }

  .hero-stats {
    grid-template-columns: 1fr;
  }

  .focus-card h3 {
    font-size: 22px;
  }
}
</style>
