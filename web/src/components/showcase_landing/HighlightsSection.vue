<template>
  <section class="highlights-section" :class="{ ready }">
    <div class="section-shell">
      <div class="chain-marquee">
        <div class="chain-track">
          <template v-for="repeat in 2" :key="repeat">
            <template v-for="item in highlightCards" :key="`${repeat}-${item.title}`">
              <span class="chain-node">{{ item.tag }}</span>
              <span class="chain-arrow">→</span>
            </template>
          </template>
        </div>
      </div>

      <div class="heading-block">
        <span class="section-eyebrow">亮点速览</span>
        <h2>{{ typedTitle }}</h2>
      </div>

      <div class="cards-grid">
        <article
          v-for="(item, index) in highlightCards"
          :key="item.title"
          class="highlight-card"
          :style="{ '--delay': `${index * 90}ms`, '--card-gradient': item.gradient }"
        >
          <span class="card-tag">{{ item.tag }}</span>
          <h3>{{ item.title }}</h3>
          <p>{{ item.description }}</p>
          <button class="card-link" @click="router.push(item.route)">进入体验</button>
        </article>
      </div>
    </div>
  </section>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { highlightCards } from './showcaseContent'
import { showcaseSectionProps, useSectionReady, useTypewriter } from './useShowcaseSection'

defineOptions({ name: 'HighlightsSection' })
defineProps(showcaseSectionProps)

const router = useRouter()
const ready = useSectionReady()
const typedTitle = useTypewriter('亮点速览 / Showcase Highlights', 60, 180)
</script>

<style scoped>
.highlights-section {
  width: 100%;
  height: 100%;
  background:
    radial-gradient(circle at 12% 18%, rgba(255, 138, 116, 0.18), transparent 24%),
    linear-gradient(180deg, rgba(16, 18, 30, 0.98), rgba(11, 14, 22, 0.98));
  color: #fff;
}

.section-shell {
  height: 100%;
  padding: 104px 6vw 52px;
  display: flex;
  flex-direction: column;
  gap: 28px;
}

.chain-marquee,
.heading-block,
.cards-grid {
  opacity: 0;
  transform: translateY(24px);
  transition: opacity 0.8s var(--showcase-ease), transform 0.8s var(--showcase-ease);
}

.highlights-section.ready .chain-marquee,
.highlights-section.ready .heading-block,
.highlights-section.ready .cards-grid {
  opacity: 1;
  transform: translateY(0);
}

.heading-block {
  transition-delay: 0.1s;
}

.cards-grid {
  transition-delay: 0.16s;
}

.chain-marquee {
  overflow: hidden;
  padding: 10px 0;
}

.chain-track {
  display: flex;
  align-items: center;
  gap: 16px;
  width: max-content;
  animation: marquee 24s linear infinite;
}

.chain-node {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0 18px;
  height: 42px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: rgba(255, 255, 255, 0.72);
  font-size: 12px;
  letter-spacing: 0.12em;
}

.chain-arrow {
  color: rgba(255, 255, 255, 0.34);
  font-size: 22px;
}

.section-eyebrow {
  display: inline-flex;
  padding: 8px 14px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.74);
  font-size: 12px;
  letter-spacing: 0.2em;
}

.heading-block h2 {
  margin: 18px 0 0;
  min-height: 1.3em;
  font-family: 'Bahnschrift', 'Segoe UI', 'PingFang SC', sans-serif;
  font-size: clamp(30px, 3.8vw, 54px);
  letter-spacing: 0.03em;
}

.cards-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 20px;
  flex: 1;
}

.highlight-card {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 24px;
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  overflow: hidden;
  opacity: 0;
  transform: translateY(24px);
  transition:
    opacity 0.65s ease,
    transform 0.65s var(--showcase-ease),
    border-color 0.3s ease,
    box-shadow 0.3s ease;
  transition-delay: var(--delay);
}

.highlights-section.ready .highlight-card {
  opacity: 1;
  transform: translateY(0);
}

.highlight-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background: var(--card-gradient);
  opacity: 0.22;
}

.highlight-card::after {
  content: '';
  position: absolute;
  inset: 1px;
  border-radius: 27px;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.highlight-card:hover {
  transform: translateY(-8px);
  border-color: rgba(255, 255, 255, 0.18);
  box-shadow: 0 24px 56px rgba(0, 0, 0, 0.28);
}

.card-tag,
.highlight-card h3,
.highlight-card p,
.card-link {
  position: relative;
  z-index: 1;
}

.card-tag {
  display: inline-flex;
  align-self: flex-start;
  padding: 7px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.16);
  font-size: 11px;
  letter-spacing: 0.14em;
}

.highlight-card h3 {
  margin: 18px 0 10px;
  font-size: 28px;
  line-height: 1.16;
}

.highlight-card p {
  margin: 0 0 28px;
  color: rgba(255, 255, 255, 0.76);
  line-height: 1.82;
}

.card-link {
  height: 46px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.18);
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
  font-weight: 700;
  cursor: pointer;
  transition: transform 0.3s var(--showcase-ease), background 0.3s ease;
}

.card-link:hover {
  transform: translateY(-2px);
  background: rgba(255, 255, 255, 0.14);
}

@keyframes marquee {
  from {
    transform: translateX(0);
  }
  to {
    transform: translateX(-50%);
  }
}

@media (max-width: 1180px) {
  .cards-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .section-shell {
    padding: 88px 20px 32px;
  }
}

@media (max-width: 640px) {
  .cards-grid {
    grid-template-columns: 1fr;
  }

  .highlight-card h3 {
    font-size: 24px;
  }
}
</style>
