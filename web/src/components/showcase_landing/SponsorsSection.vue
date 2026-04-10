<template>
  <section class="sponsors-section" :class="{ ready }">
    <div class="section-shell">
      <div class="heading-block">
        <span class="section-eyebrow">合作伙伴与技术生态</span>
        <h2>让品牌层、工程层与 AI 能力共用一套语言</h2>
      </div>

      <div class="logo-marquee">
        <div class="logo-track">
          <article v-for="(sponsor, index) in [...sponsors, ...sponsors]" :key="`${sponsor.name}-${index}`" class="logo-card">
            <div class="logo-box">
              <img v-if="sponsor.logo" :src="sponsor.logo" :alt="sponsor.name" loading="lazy" decoding="async" />
              <span v-else>{{ sponsor.name.charAt(0) }}</span>
            </div>
            <span class="logo-name">{{ sponsor.name }}</span>
          </article>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { sponsors } from './showcaseContent'
import { showcaseSectionProps, useSectionReady } from './useShowcaseSection'

defineOptions({ name: 'SponsorsSection' })
defineProps(showcaseSectionProps)

const ready = useSectionReady()
</script>

<style scoped>
.sponsors-section {
  width: 100%;
  height: 100%;
  background:
    radial-gradient(circle at center, rgba(94, 198, 255, 0.12), transparent 28%),
    linear-gradient(180deg, rgba(8, 12, 20, 0.98), rgba(11, 14, 22, 0.98));
  color: #fff;
}

.section-shell {
  height: 100%;
  padding: 104px 6vw 52px;
  display: flex;
  flex-direction: column;
  gap: 34px;
  justify-content: center;
}

.heading-block,
.logo-marquee {
  opacity: 0;
  transform: translateY(24px);
  transition: opacity 0.8s var(--showcase-ease), transform 0.8s var(--showcase-ease);
}

.sponsors-section.ready .heading-block,
.sponsors-section.ready .logo-marquee {
  opacity: 1;
  transform: translateY(0);
}

.logo-marquee {
  transition-delay: 0.14s;
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
  font-family: 'STZhongsong', 'Songti SC', 'Noto Serif SC', serif;
  font-size: clamp(30px, 3.5vw, 50px);
}

.logo-marquee {
  position: relative;
  overflow: hidden;
  padding: 12px 0;
}

.logo-marquee::before,
.logo-marquee::after {
  content: '';
  position: absolute;
  top: 0;
  bottom: 0;
  width: 120px;
  z-index: 2;
  pointer-events: none;
}

.logo-marquee::before {
  left: 0;
  background: linear-gradient(90deg, rgba(8, 12, 20, 1), transparent);
}

.logo-marquee::after {
  right: 0;
  background: linear-gradient(270deg, rgba(8, 12, 20, 1), transparent);
}

.logo-track {
  display: flex;
  gap: 18px;
  width: max-content;
  animation: sponsor-scroll 26s linear infinite;
}

.logo-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  min-width: 134px;
  padding: 18px 14px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.logo-box {
  width: 64px;
  height: 64px;
  display: grid;
  place-items: center;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.08);
}

.logo-box img {
  width: 42px;
  height: 42px;
  object-fit: contain;
}

.logo-box span {
  font-family: 'Bahnschrift', 'DIN Alternate', sans-serif;
  font-size: 28px;
}

.logo-name {
  color: rgba(255, 255, 255, 0.72);
  font-size: 12px;
  letter-spacing: 0.08em;
}

@keyframes sponsor-scroll {
  from {
    transform: translateX(0);
  }
  to {
    transform: translateX(-50%);
  }
}

@media (max-width: 768px) {
  .section-shell {
    padding: 88px 20px 32px;
  }

  .logo-card {
    min-width: 108px;
  }
}
</style>
