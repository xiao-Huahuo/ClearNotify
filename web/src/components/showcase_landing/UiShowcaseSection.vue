<template>
  <section class="ui-showcase-section" :class="{ ready }">
    <div class="section-shell">
      <div class="section-copy">
        <span class="section-eyebrow">UI 概览</span>
        <h2>用轮播式组件展台，把产品能力拍成一支品牌短片</h2>
        <p>
          左侧集中展示 5 组关键界面，右侧保留叙事和说明文本。
          每一次切换都像在浏览一套完成过美术调性的产品展示页，而不是普通后台截图。
        </p>
      </div>

      <div class="showcase-layout">
        <div class="showcase-stage">
          <div class="stage-frame">
            <div class="stage-chrome">
              <span></span>
              <span></span>
              <span></span>
            </div>

            <div class="stage-window">
              <article
                v-for="(slide, index) in uiSlides"
                :key="slide.title"
                class="stage-slide"
                :class="{ active: activeIndex === index }"
              >
                <div class="slide-grid">
                  <div class="slide-hero-shot">
                    <img :src="slide.images[0]" :alt="slide.title" loading="lazy" decoding="async" />
                  </div>
                  <div class="slide-side-shot top">
                    <img :src="slide.images[1]" :alt="`${slide.title} 细节 1`" loading="lazy" decoding="async" />
                  </div>
                  <div class="slide-side-shot bottom">
                    <img :src="slide.images[2]" :alt="`${slide.title} 细节 2`" loading="lazy" decoding="async" />
                  </div>
                </div>

                <div class="slide-overlay">
                  <span class="overlay-tag">{{ slide.eyebrow }}</span>
                  <strong>{{ slide.subtitle }}</strong>
                </div>
              </article>
            </div>
          </div>

          <div class="stage-indicators">
            <button
              v-for="(slide, index) in uiSlides"
              :key="slide.title"
              class="indicator"
              :class="{ active: activeIndex === index }"
              :aria-label="slide.title"
              @click="setActive(index)"
            ></button>
          </div>
        </div>

        <aside class="showcase-aside">
          <span class="aside-index">0{{ activeIndex + 1 }}</span>
          <span class="aside-tag">{{ currentSlide.eyebrow }}</span>
          <h3>{{ currentSlide.title }}</h3>
          <p class="aside-description">{{ currentSlide.description }}</p>

          <div class="aside-meta">
            <div v-for="fact in asideFacts" :key="fact.label" class="meta-card">
              <span class="meta-label">{{ fact.label }}</span>
              <strong class="meta-value">{{ fact.value }}</strong>
            </div>
          </div>

          <div class="aside-bullets">
            <div v-for="bullet in currentSlide.bullets" :key="bullet" class="bullet-item">
              <i :style="{ background: currentSlide.accent }"></i>
              <span>{{ bullet }}</span>
            </div>
          </div>

          <div class="placeholder-panel">
            <span class="placeholder-tag">可继续补图</span>
            <strong>{{ currentSlide.eyebrow }}主题特写图 / 局部品牌细节图</strong>
            <p>这里预留给你后面补一张更统一的 UI 宣传图，用来压住右侧的信息密度，让画面更满、更高级。</p>
          </div>
        </aside>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { uiSlides } from './showcaseContent'
import { showcaseSectionProps, useSectionReady } from './useShowcaseSection'

defineOptions({ name: 'UiShowcaseSection' })
defineProps(showcaseSectionProps)

const ready = useSectionReady()
const activeIndex = ref(0)
const currentSlide = computed(() => uiSlides[activeIndex.value])
const asideFacts = computed(() => [
  { label: '切换节奏', value: '4.2s Auto' },
  { label: '编排比例', value: '2 / 3 + 1 / 3' },
  { label: '当前主题', value: currentSlide.value.eyebrow },
])

let timer = null

const startAutoPlay = () => {
  timer = window.setInterval(() => {
    activeIndex.value = (activeIndex.value + 1) % uiSlides.length
  }, 4200)
}

const setActive = (index) => {
  activeIndex.value = index
  if (timer) {
    window.clearInterval(timer)
  }
  startAutoPlay()
}

onMounted(() => {
  startAutoPlay()
})

onUnmounted(() => {
  if (timer) {
    window.clearInterval(timer)
  }
})
</script>

<style scoped>
.ui-showcase-section {
  width: 100%;
  height: 100%;
  background:
    radial-gradient(circle at right top, rgba(78, 170, 255, 0.18), transparent 28%),
    linear-gradient(180deg, rgba(255, 247, 240, 0.98), rgba(248, 244, 255, 0.96));
  color: var(--text-primary, #111);
}

[data-theme='dark'] .ui-showcase-section {
  background:
    radial-gradient(circle at right top, rgba(86, 180, 255, 0.14), transparent 28%),
    linear-gradient(180deg, rgba(15, 18, 26, 0.98), rgba(10, 13, 22, 0.98));
  color: var(--text-primary, #f4f4f4);
}

.section-shell {
  height: 100%;
  padding: 104px 6vw 52px;
  display: flex;
  flex-direction: column;
  gap: 28px;
}

.section-copy,
.showcase-layout {
  opacity: 0;
  transform: translateY(28px);
  transition: opacity 0.8s var(--showcase-ease), transform 0.8s var(--showcase-ease);
}

.ui-showcase-section.ready .section-copy,
.ui-showcase-section.ready .showcase-layout {
  opacity: 1;
  transform: translateY(0);
}

.showcase-layout {
  transition-delay: 0.12s;
  display: grid;
  grid-template-columns: minmax(0, 1.7fr) minmax(280px, 0.9fr);
  gap: 24px;
  align-items: stretch;
  flex: 1;
}

.section-eyebrow {
  display: inline-flex;
  padding: 8px 14px;
  border-radius: 999px;
  background: rgba(255, 122, 73, 0.12);
  color: #b14b2f;
  font-size: 12px;
  letter-spacing: 0.2em;
}

[data-theme='dark'] .section-eyebrow {
  background: rgba(255, 122, 73, 0.16);
  color: #ffd8c8;
}

.section-copy h2 {
  margin: 18px 0 12px;
  font-family: 'STZhongsong', 'Songti SC', 'Noto Serif SC', serif;
  font-size: clamp(32px, 3.4vw, 52px);
  line-height: 1.15;
}

.section-copy p {
  margin: 0;
  max-width: 760px;
  color: var(--text-secondary, #5f6472);
  line-height: 1.8;
}

.showcase-stage {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 18px;
}

.stage-frame {
  position: relative;
  min-height: 0;
  flex: 1;
  border-radius: 32px;
  padding: 18px;
  background: rgba(255, 255, 255, 0.76);
  border: 1px solid rgba(18, 25, 37, 0.08);
  box-shadow: 0 30px 80px rgba(34, 40, 72, 0.16);
  overflow: hidden;
}

[data-theme='dark'] .stage-frame {
  background: rgba(255, 255, 255, 0.03);
  border-color: rgba(255, 255, 255, 0.08);
  box-shadow: 0 30px 80px rgba(0, 0, 0, 0.4);
}

.stage-frame::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(255, 126, 91, 0.1), transparent 34%, rgba(71, 181, 255, 0.08));
  pointer-events: none;
}

.stage-chrome {
  display: flex;
  gap: 8px;
  margin-bottom: 14px;
}

.stage-chrome span {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: rgba(18, 25, 37, 0.14);
}

[data-theme='dark'] .stage-chrome span {
  background: rgba(255, 255, 255, 0.18);
}

.stage-window {
  position: relative;
  height: calc(100% - 26px);
  min-height: 430px;
  border-radius: 24px;
  overflow: hidden;
}

.stage-slide {
  position: absolute;
  inset: 0;
  opacity: 0;
  transform: translateX(8%);
  transition:
    opacity 0.8s ease,
    transform 0.8s var(--showcase-ease);
  pointer-events: none;
}

.stage-slide.active {
  opacity: 1;
  transform: translateX(0);
  pointer-events: auto;
}

.slide-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(220px, 0.65fr);
  grid-template-rows: repeat(2, minmax(0, 1fr));
  gap: 14px;
  height: 100%;
}

.slide-hero-shot,
.slide-side-shot {
  position: relative;
  border-radius: 24px;
  overflow: hidden;
  background: rgba(17, 17, 17, 0.08);
}

.slide-hero-shot {
  grid-row: 1 / span 2;
}

.slide-hero-shot img,
.slide-side-shot img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.slide-overlay {
  position: absolute;
  left: 24px;
  right: 24px;
  bottom: 22px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 18px;
  border-radius: 20px;
  background: rgba(12, 16, 26, 0.74);
  color: #fff;
  backdrop-filter: blur(18px);
}

.overlay-tag {
  display: inline-flex;
  padding: 7px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.12);
  font-size: 11px;
  letter-spacing: 0.16em;
}

.slide-overlay strong {
  font-size: 14px;
  font-weight: 600;
}

.stage-indicators {
  display: flex;
  justify-content: center;
  gap: 12px;
}

.indicator {
  width: 48px;
  height: 6px;
  border-radius: 999px;
  border: none;
  background: rgba(18, 25, 37, 0.12);
  cursor: pointer;
  transition: all 0.3s ease;
}

[data-theme='dark'] .indicator {
  background: rgba(255, 255, 255, 0.12);
}

.indicator.active {
  width: 72px;
  background: linear-gradient(90deg, #ff7a18, #5bcfff);
  box-shadow: 0 0 16px rgba(91, 207, 255, 0.4);
}

.showcase-aside {
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 32px 30px;
  border-radius: 30px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(18, 25, 37, 0.08);
  box-shadow: 0 20px 48px rgba(26, 31, 57, 0.12);
}

[data-theme='dark'] .showcase-aside {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.08);
}

.aside-index {
  font-family: 'Bahnschrift', 'DIN Alternate', sans-serif;
  color: rgba(17, 17, 17, 0.28);
  font-size: 52px;
  line-height: 1;
}

[data-theme='dark'] .aside-index {
  color: rgba(255, 255, 255, 0.18);
}

.aside-tag {
  margin-top: 18px;
  color: var(--color-primary, #c0392b);
  letter-spacing: 0.22em;
  font-size: 12px;
}

.showcase-aside h3 {
  margin: 16px 0 12px;
  font-size: 30px;
  line-height: 1.2;
}

.aside-description {
  margin: 0;
  color: var(--text-secondary, #666);
  line-height: 1.84;
}

.aside-bullets {
  display: grid;
  gap: 14px;
  margin-top: 28px;
}

.aside-meta {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-top: 22px;
}

.meta-card {
  padding: 12px 12px 14px;
  border-radius: 18px;
  background: rgba(17, 17, 17, 0.04);
}

[data-theme='dark'] .meta-card {
  background: rgba(255, 255, 255, 0.05);
}

.meta-label,
.meta-value {
  display: block;
}

.meta-label {
  color: var(--text-secondary, #666);
  font-size: 11px;
  letter-spacing: 0.12em;
}

.meta-value {
  margin-top: 8px;
  font-size: 15px;
  line-height: 1.4;
}

.bullet-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(17, 17, 17, 0.04);
}

[data-theme='dark'] .bullet-item {
  background: rgba(255, 255, 255, 0.05);
}

.bullet-item i {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  box-shadow: 0 0 12px currentColor;
}

.placeholder-panel {
  margin-top: 18px;
  padding: 18px 18px 20px;
  border-radius: 22px;
  border: 1px dashed rgba(17, 17, 17, 0.16);
  background:
    linear-gradient(135deg, rgba(255, 122, 24, 0.08), transparent 40%, rgba(91, 207, 255, 0.08)),
    rgba(255, 255, 255, 0.55);
}

[data-theme='dark'] .placeholder-panel {
  border-color: rgba(255, 255, 255, 0.14);
  background:
    linear-gradient(135deg, rgba(255, 122, 24, 0.12), transparent 40%, rgba(91, 207, 255, 0.12)),
    rgba(255, 255, 255, 0.03);
}

.placeholder-tag {
  display: inline-flex;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(17, 17, 17, 0.08);
  font-size: 11px;
  letter-spacing: 0.14em;
}

[data-theme='dark'] .placeholder-tag {
  background: rgba(255, 255, 255, 0.08);
}

.placeholder-panel strong {
  display: block;
  margin-top: 12px;
  font-size: 16px;
  line-height: 1.55;
}

.placeholder-panel p {
  margin: 10px 0 0;
  color: var(--text-secondary, #666);
  line-height: 1.72;
  font-size: 13px;
}

@media (max-width: 1080px) {
  .showcase-layout {
    grid-template-columns: 1fr;
  }

  .showcase-aside {
    padding: 24px;
  }
}

@media (max-width: 768px) {
  .section-shell {
    padding: 88px 20px 32px;
  }

  .slide-grid {
    grid-template-columns: 1fr;
    grid-template-rows: 1.2fr repeat(2, 0.7fr);
  }

  .slide-hero-shot {
    grid-row: auto;
  }

  .stage-window {
    min-height: 520px;
  }

  .slide-overlay {
    flex-direction: column;
    align-items: flex-start;
  }

  .aside-meta {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .showcase-aside h3 {
    font-size: 24px;
  }

  .indicator {
    width: 28px;
  }

  .indicator.active {
    width: 44px;
  }
}
</style>
