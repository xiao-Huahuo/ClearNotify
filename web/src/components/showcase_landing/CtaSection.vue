<template>
  <section class="cta-section" :class="{ ready }">
    <div class="section-shell">
      <div class="cta-panel">
        <span class="section-eyebrow">免费注册</span>
        <h2>立即加入云上观策</h2>
        <p>用一套真正有气场的首页，承接你的政策内容、分析能力和品牌表达。</p>

        <div class="cta-metrics">
          <div v-for="metric in ctaMetrics" :key="metric.label" class="metric-card">
            <span class="metric-value">{{ metric.value }}</span>
            <span class="metric-label">{{ metric.label }}</span>
          </div>
        </div>

        <div class="cta-actions">
          <button class="cta-btn primary" @click="router.push('/register')">免费注册</button>
          <button class="cta-btn ghost" @click="router.push('/')">进入系统</button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { ctaMetrics } from './showcaseContent'
import { showcaseSectionProps, useSectionReady } from './useShowcaseSection'

defineOptions({ name: 'CtaSection' })
defineProps(showcaseSectionProps)

const router = useRouter()
const ready = useSectionReady()
</script>

<style scoped>
.cta-section {
  width: 100%;
  height: 100%;
  background:
    radial-gradient(circle at center, rgba(255, 208, 146, 0.2), transparent 24%),
    linear-gradient(135deg, #160d14 0%, #3f2238 45%, #13243d 100%);
  color: #fff;
}

.section-shell {
  height: 100%;
  padding: 112px 6vw 56px;
  display: grid;
  place-items: center;
}

.cta-panel {
  width: min(960px, 100%);
  padding: 48px;
  border-radius: 36px;
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.14), rgba(255, 255, 255, 0.06)),
    linear-gradient(135deg, rgba(255, 165, 109, 0.18), transparent 45%, rgba(91, 207, 255, 0.12));
  border: 1px solid rgba(255, 255, 255, 0.16);
  box-shadow: 0 42px 110px rgba(0, 0, 0, 0.34);
  text-align: center;
  opacity: 0;
  transform: translateY(28px) scale(0.98);
  transition: opacity 0.82s var(--showcase-ease), transform 0.82s var(--showcase-ease);
}

.cta-section.ready .cta-panel {
  opacity: 1;
  transform: translateY(0) scale(1);
}

.section-eyebrow {
  display: inline-flex;
  padding: 8px 14px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.12);
  color: rgba(255, 255, 255, 0.78);
  font-size: 12px;
  letter-spacing: 0.2em;
}

.cta-panel h2 {
  margin: 20px 0 12px;
  font-family: 'STZhongsong', 'Songti SC', 'Noto Serif SC', serif;
  font-size: clamp(36px, 4vw, 58px);
  line-height: 1.1;
}

.cta-panel p {
  max-width: 620px;
  margin: 0 auto;
  color: rgba(255, 255, 255, 0.72);
  line-height: 1.84;
}

.cta-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  margin-top: 30px;
}

.metric-card {
  padding: 22px 18px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.metric-value,
.metric-label {
  display: block;
}

.metric-value {
  font-family: 'Bahnschrift', 'DIN Alternate', sans-serif;
  font-size: 30px;
}

.metric-label {
  margin-top: 8px;
  color: rgba(255, 255, 255, 0.58);
  font-size: 12px;
  letter-spacing: 0.12em;
}

.cta-actions {
  display: flex;
  justify-content: center;
  gap: 14px;
  flex-wrap: wrap;
  margin-top: 32px;
}

.cta-btn {
  min-width: 160px;
  height: 50px;
  border-radius: 999px;
  border: 1px solid transparent;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: transform 0.3s var(--showcase-ease), box-shadow 0.3s ease;
}

.cta-btn:hover {
  transform: translateY(-3px);
}

.cta-btn.primary {
  background: linear-gradient(135deg, #ffe7d6, #ffc7b3);
  color: #6c2637;
  box-shadow: 0 18px 42px rgba(255, 160, 112, 0.24);
}

.cta-btn.ghost {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.16);
  color: #fff;
}

@media (max-width: 768px) {
  .section-shell {
    padding: 88px 20px 32px;
  }

  .cta-panel {
    padding: 32px 22px;
  }

  .cta-metrics {
    grid-template-columns: 1fr;
  }
}
</style>
