<template>
  <section class="flow-section" :class="{ ready }">
    <div class="section-shell">
      <div class="heading-block">
        <span class="section-eyebrow">使用流程</span>
        <h2>三步开始智能政策分析</h2>
      </div>

      <div class="flow-grid">
        <article
          v-for="(step, index) in flowSteps"
          :key="step.title"
          class="flow-card"
          :style="{ '--delay': `${index * 120}ms` }"
        >
          <span class="step-index">0{{ index + 1 }}</span>
          <h3>{{ step.title }}</h3>
          <p>{{ step.desc }}</p>
          <span class="step-tip">{{ step.tip }}</span>
          <div v-if="index < flowSteps.length - 1" class="step-connector">→</div>
        </article>
      </div>
    </div>
  </section>
</template>

<script setup>
import { flowSteps } from './showcaseContent'
import { showcaseSectionProps, useSectionReady } from './useShowcaseSection'

defineOptions({ name: 'FlowSection' })
defineProps(showcaseSectionProps)

const ready = useSectionReady()
</script>

<style scoped>
.flow-section {
  width: 100%;
  height: 100%;
  background:
    radial-gradient(circle at right top, rgba(82, 190, 255, 0.14), transparent 26%),
    linear-gradient(180deg, rgba(248, 250, 255, 0.98), rgba(243, 246, 252, 0.98));
}

[data-theme='dark'] .flow-section {
  background:
    radial-gradient(circle at right top, rgba(82, 190, 255, 0.12), transparent 26%),
    linear-gradient(180deg, rgba(12, 16, 24, 0.98), rgba(10, 14, 22, 0.98));
}

.section-shell {
  height: 100%;
  padding: 104px 6vw 48px;
  display: flex;
  flex-direction: column;
  gap: 28px;
}

.heading-block,
.flow-grid {
  opacity: 0;
  transform: translateY(24px);
  transition: opacity 0.8s var(--showcase-ease), transform 0.8s var(--showcase-ease);
}

.flow-section.ready .heading-block,
.flow-section.ready .flow-grid {
  opacity: 1;
  transform: translateY(0);
}

.flow-grid {
  transition-delay: 0.14s;
}

.section-eyebrow {
  display: inline-flex;
  padding: 8px 14px;
  border-radius: 999px;
  background: rgba(82, 190, 255, 0.12);
  color: #2e6f98;
  font-size: 12px;
  letter-spacing: 0.2em;
}

.heading-block h2 {
  margin: 18px 0 0;
  font-family: 'STZhongsong', 'Songti SC', 'Noto Serif SC', serif;
  font-size: clamp(32px, 3.4vw, 52px);
}

.flow-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 20px;
  align-items: stretch;
  flex: 1;
}

.flow-card {
  position: relative;
  padding: 28px;
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(18, 25, 37, 0.08);
  box-shadow: 0 24px 56px rgba(26, 31, 57, 0.1);
  opacity: 0;
  transform: translateY(24px);
  transition:
    opacity 0.68s ease,
    transform 0.68s var(--showcase-ease),
    box-shadow 0.3s ease;
  transition-delay: var(--delay);
}

[data-theme='dark'] .flow-card {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.08);
  box-shadow: 0 24px 56px rgba(0, 0, 0, 0.34);
}

.flow-section.ready .flow-card {
  opacity: 1;
  transform: translateY(0);
}

.flow-card:hover {
  transform: translateY(-8px);
}

.step-index {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 58px;
  height: 58px;
  border-radius: 18px;
  background: linear-gradient(135deg, #ff8f72, #5dcfff);
  color: #fff;
  font-family: 'Bahnschrift', 'DIN Alternate', sans-serif;
  font-size: 20px;
}

.flow-card h3 {
  margin: 22px 0 10px;
  font-size: 28px;
  line-height: 1.18;
}

.flow-card p {
  margin: 0;
  color: var(--text-secondary, #666);
  line-height: 1.84;
}

.step-tip {
  display: inline-flex;
  margin-top: 24px;
  padding: 8px 14px;
  border-radius: 999px;
  background: rgba(17, 17, 17, 0.05);
  color: var(--text-primary, #111);
  font-size: 12px;
}

[data-theme='dark'] .step-tip {
  background: rgba(255, 255, 255, 0.07);
  color: #fff;
}

.step-connector {
  position: absolute;
  top: 50%;
  right: -18px;
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.12);
  color: #5dcfff;
  font-size: 18px;
}

@media (max-width: 1080px) {
  .flow-grid {
    grid-template-columns: 1fr;
  }

  .step-connector {
    top: auto;
    right: 50%;
    bottom: -18px;
    transform: translateX(50%) rotate(90deg);
  }
}

@media (max-width: 768px) {
  .section-shell {
    padding: 88px 20px 32px;
  }

  .flow-card h3 {
    font-size: 24px;
  }
}
</style>
