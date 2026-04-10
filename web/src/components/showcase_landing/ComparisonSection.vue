<template>
  <section class="comparison-section" :class="{ ready }">
    <div class="section-shell">
      <div class="heading-block">
        <span class="section-eyebrow">为什么选择我们</span>
        <h2>把传统政务站点的“功能堆砌感”，变成有记忆点的品牌首页</h2>
      </div>

      <div class="comparison-grid">
        <div class="comparison-column">
          <article
            v-for="(card, index) in advantageCards"
            :key="card.title"
            class="comparison-card advantage"
            :style="{ '--delay': `${index * 110}ms` }"
          >
            <div class="card-image">
              <img v-if="card.image" :src="card.image" :alt="card.title" loading="lazy" decoding="async" />
            </div>
            <div class="card-body">
              <span class="card-tag">优势</span>
              <h3>{{ card.title }}</h3>
              <p>{{ card.desc }}</p>
            </div>
          </article>
        </div>

        <div class="comparison-core">
          <span class="core-mark">VS</span>
          <p>从“看完就忘”的普通页面，升级成“看过就记住”的企业级展示系统。</p>
          <div class="core-notes">
            <div class="core-note">
              <span>旧方案</span>
              <strong>信息分散，品牌感弱</strong>
            </div>
            <div class="core-note">
              <span>新方案</span>
              <strong>整屏叙事，视觉统一</strong>
            </div>
          </div>
          <div class="core-placeholder">
            <span class="placeholder-label">待补主视觉</span>
            <strong>横向品牌 KV / 城市与人群结合画面</strong>
            <p>这块建议后面换成一张宽幅企业感图片，作为左右对比之间的视觉缓冲层。</p>
          </div>
        </div>

        <div class="comparison-column disadvantage-column">
          <article
            v-for="(card, index) in disadvantageCards"
            :key="card.title"
            class="comparison-card disadvantage"
            :style="{ '--delay': `${(index + advantageCards.length) * 110}ms` }"
          >
            <div class="card-image">
              <img v-if="card.image" :src="card.image" :alt="card.title" loading="lazy" decoding="async" />
            </div>
            <div class="card-body">
              <span class="card-tag">痛点</span>
              <h3>{{ card.title }}</h3>
              <p>{{ card.desc }}</p>
            </div>
          </article>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { advantageCards, disadvantageCards } from './showcaseContent'
import { showcaseSectionProps, useSectionReady } from './useShowcaseSection'

defineOptions({ name: 'ComparisonSection' })
defineProps(showcaseSectionProps)

const ready = useSectionReady()
</script>

<style scoped>
.comparison-section {
  width: 100%;
  height: 100%;
  background:
    radial-gradient(circle at left top, rgba(255, 156, 117, 0.18), transparent 24%),
    radial-gradient(circle at right bottom, rgba(76, 186, 255, 0.18), transparent 28%),
    linear-gradient(135deg, #120d14 0%, #251528 38%, #101d31 100%);
  color: #fff;
}

.section-shell {
  height: 100%;
  padding: 104px 6vw 48px;
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.heading-block,
.comparison-grid {
  opacity: 0;
  transform: translateY(30px);
  transition: opacity 0.8s var(--showcase-ease), transform 0.8s var(--showcase-ease);
}

.comparison-section.ready .heading-block,
.comparison-section.ready .comparison-grid {
  opacity: 1;
  transform: translateY(0);
}

.comparison-grid {
  transition-delay: 0.12s;
}

.section-eyebrow {
  display: inline-flex;
  padding: 8px 14px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.72);
  font-size: 12px;
  letter-spacing: 0.18em;
}

.heading-block h2 {
  max-width: 840px;
  margin: 18px 0 0;
  font-family: 'STZhongsong', 'Songti SC', 'Noto Serif SC', serif;
  font-size: clamp(32px, 3.3vw, 50px);
  line-height: 1.18;
}

.comparison-grid {
  flex: 1;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 180px minmax(0, 1fr);
  gap: 24px;
  align-items: center;
}

.comparison-column {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.disadvantage-column {
  padding-top: 60px;
}

.comparison-card {
  display: grid;
  grid-template-columns: 120px minmax(0, 1fr);
  gap: 20px;
  align-items: center;
  padding: 16px 18px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.92);
  color: #111;
  box-shadow: 0 22px 44px rgba(0, 0, 0, 0.16);
  opacity: 0;
  transition:
    opacity 0.65s ease,
    transform 0.65s var(--showcase-ease),
    box-shadow 0.25s ease;
  transition-delay: var(--delay);
}

.comparison-card.advantage {
  transform: translateX(-70px);
}

.comparison-card.disadvantage {
  transform: translateX(70px);
}

.comparison-section.ready .comparison-card {
  opacity: 1;
  transform: translateX(0);
}

.comparison-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 32px 66px rgba(0, 0, 0, 0.22);
}

.card-image {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  overflow: hidden;
  background: rgba(17, 17, 17, 0.08);
}

.card-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.card-body {
  min-width: 0;
}

.card-tag {
  display: inline-flex;
  padding: 6px 12px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
}

.advantage .card-tag {
  background: rgba(108, 224, 162, 0.18);
  color: #13895b;
}

.disadvantage .card-tag {
  background: rgba(255, 122, 111, 0.18);
  color: #c54e43;
}

.card-body h3 {
  margin: 12px 0 8px;
  font-size: 22px;
  line-height: 1.2;
}

.card-body p {
  margin: 0;
  color: #586173;
  line-height: 1.72;
}

.comparison-core {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
  text-align: center;
  color: rgba(255, 255, 255, 0.7);
}

.core-mark {
  display: grid;
  place-items: center;
  width: 96px;
  height: 96px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.18), rgba(255, 255, 255, 0.04));
  border: 1px solid rgba(255, 255, 255, 0.14);
  font-family: 'Bahnschrift', 'DIN Alternate', sans-serif;
  font-size: 30px;
  color: #fff;
  box-shadow: 0 0 36px rgba(255, 154, 127, 0.22);
}

.comparison-core p {
  margin: 0;
  line-height: 1.84;
}

.core-notes {
  display: grid;
  gap: 12px;
  width: 100%;
}

.core-note {
  width: 100%;
  padding: 14px 16px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.core-note span,
.core-note strong {
  display: block;
}

.core-note span {
  color: rgba(255, 255, 255, 0.46);
  font-size: 11px;
  letter-spacing: 0.16em;
}

.core-note strong {
  margin-top: 8px;
  font-size: 14px;
  line-height: 1.6;
  color: #fff;
}

.core-placeholder {
  width: 100%;
  padding: 18px;
  border-radius: 24px;
  border: 1px dashed rgba(255, 255, 255, 0.18);
  background:
    linear-gradient(135deg, rgba(255, 158, 120, 0.12), transparent 38%, rgba(88, 202, 255, 0.12)),
    rgba(255, 255, 255, 0.04);
}

.placeholder-label {
  display: inline-flex;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  font-size: 11px;
  letter-spacing: 0.14em;
}

.core-placeholder strong {
  display: block;
  margin-top: 12px;
  font-size: 16px;
  line-height: 1.55;
}

.core-placeholder p {
  margin: 10px 0 0;
  color: rgba(255, 255, 255, 0.62);
  line-height: 1.72;
  font-size: 13px;
}

@media (max-width: 1180px) {
  .comparison-grid {
    grid-template-columns: 1fr;
  }

  .comparison-core {
    order: -1;
  }

  .disadvantage-column {
    padding-top: 0;
  }
}

@media (max-width: 768px) {
  .section-shell {
    padding: 88px 20px 28px;
  }

  .comparison-card {
    grid-template-columns: 86px minmax(0, 1fr);
    border-radius: 28px;
  }

  .card-image {
    width: 86px;
    height: 86px;
  }
}

@media (max-width: 640px) {
  .comparison-card {
    grid-template-columns: 1fr;
    text-align: center;
    justify-items: center;
  }
}
</style>
