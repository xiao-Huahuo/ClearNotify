<template>
  <section class="features-section" :class="{ ready }">
    <div class="section-shell">
      <div class="heading-block">
        <span class="section-eyebrow">核心功能</span>
        <h2>一站式政策智能服务</h2>
        <p>
          用统一的视觉结构串起政策搜索、广场浏览、民意反馈、数据展示与云小圆 AI Agent，
          让首页不仅负责“介绍”，也负责展示真正的产品能力。
        </p>
      </div>

      <div class="features-grid">
        <article
          v-for="(feature, index) in features"
          :key="feature.title"
          class="feature-card"
          :style="{ '--feature-color': feature.color, '--delay': `${index * 80}ms` }"
        >
          <div class="feature-icon">
            <svg viewBox="0 0 24 24" width="22" height="22" stroke="currentColor" stroke-width="1.8" fill="none" v-html="feature.icon"></svg>
          </div>
          <div class="feature-order">0{{ index + 1 }}</div>
          <h3>{{ feature.title }}</h3>
          <p>{{ feature.desc }}</p>
        </article>
      </div>
    </div>
  </section>
</template>

<script setup>
import { features } from './showcaseContent'
import { showcaseSectionProps, useSectionReady } from './useShowcaseSection'

defineOptions({ name: 'FeaturesSection' })
defineProps(showcaseSectionProps)

const ready = useSectionReady()
</script>

<style scoped>
.features-section {
  width: 100%;
  height: 100%;
  background:
    radial-gradient(circle at 16% 18%, rgba(255, 168, 125, 0.18), transparent 26%),
    linear-gradient(180deg, rgba(255, 251, 247, 0.98), rgba(244, 246, 252, 0.98));
}

[data-theme='dark'] .features-section {
  background:
    radial-gradient(circle at 16% 18%, rgba(255, 168, 125, 0.12), transparent 26%),
    linear-gradient(180deg, rgba(13, 17, 27, 0.98), rgba(10, 13, 21, 0.98));
}

.section-shell {
  height: 100%;
  padding: 104px 6vw 56px;
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.heading-block,
.features-grid {
  opacity: 0;
  transform: translateY(26px);
  transition: opacity 0.8s var(--showcase-ease), transform 0.8s var(--showcase-ease);
}

.features-section.ready .heading-block,
.features-section.ready .features-grid {
  opacity: 1;
  transform: translateY(0);
}

.features-grid {
  transition-delay: 0.12s;
}

.section-eyebrow {
  display: inline-flex;
  padding: 8px 14px;
  border-radius: 999px;
  background: rgba(255, 135, 91, 0.12);
  color: #b1492e;
  font-size: 12px;
  letter-spacing: 0.2em;
}

.heading-block h2 {
  margin: 18px 0 12px;
  font-family: 'STZhongsong', 'Songti SC', 'Noto Serif SC', serif;
  font-size: clamp(34px, 3.6vw, 54px);
  line-height: 1.14;
}

.heading-block p {
  max-width: 820px;
  margin: 0;
  color: var(--text-secondary, #666);
  line-height: 1.8;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 20px;
  flex: 1;
}

.feature-card {
  position: relative;
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: 28px 26px;
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(19, 26, 38, 0.08);
  box-shadow: 0 24px 52px rgba(27, 34, 63, 0.1);
  overflow: hidden;
  opacity: 0;
  transform: translateY(24px);
  transition:
    transform 0.6s var(--showcase-ease),
    opacity 0.6s ease,
    box-shadow 0.3s ease,
    border-color 0.3s ease;
  transition-delay: var(--delay);
}

[data-theme='dark'] .feature-card {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.08);
  box-shadow: 0 24px 52px rgba(0, 0, 0, 0.32);
}

.features-section.ready .feature-card {
  opacity: 1;
  transform: translateY(0);
}

.feature-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, color-mix(in srgb, var(--feature-color) 20%, transparent), transparent 62%);
  opacity: 0.75;
}

.feature-card::after {
  content: '';
  position: absolute;
  inset: auto -40px -60px auto;
  width: 160px;
  height: 160px;
  border-radius: 50%;
  background: color-mix(in srgb, var(--feature-color) 28%, transparent);
  filter: blur(24px);
}

.feature-card:hover {
  transform: translateY(-8px);
  border-color: color-mix(in srgb, var(--feature-color) 36%, rgba(19, 26, 38, 0.12));
  box-shadow: 0 32px 70px rgba(22, 29, 52, 0.16);
}

.feature-icon,
.feature-order,
.feature-card h3,
.feature-card p {
  position: relative;
  z-index: 1;
}

.feature-icon {
  width: 50px;
  height: 50px;
  display: grid;
  place-items: center;
  border-radius: 16px;
  background: color-mix(in srgb, var(--feature-color) 18%, rgba(255, 255, 255, 0.65));
  color: var(--feature-color);
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--feature-color) 24%, transparent);
}

.feature-order {
  margin-top: 22px;
  color: color-mix(in srgb, var(--feature-color) 72%, #fff);
  font-family: 'Bahnschrift', 'DIN Alternate', sans-serif;
  font-size: 12px;
  letter-spacing: 0.3em;
}

.feature-card h3 {
  margin: 16px 0 12px;
  font-size: 24px;
}

.feature-card p {
  margin: 0;
  color: var(--text-secondary, #666);
  line-height: 1.84;
}

@media (max-width: 1080px) {
  .features-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .section-shell {
    padding: 88px 20px 32px;
  }
}

@media (max-width: 640px) {
  .features-grid {
    grid-template-columns: 1fr;
  }

  .feature-card h3 {
    font-size: 22px;
  }
}
</style>
