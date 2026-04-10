<template>
  <section class="philosophy-section" :class="{ ready }">
    <div class="section-shell">
      <span class="section-eyebrow">设计理念</span>

      <div class="philosophy-words">
        <span
          v-for="(char, index) in philosophyCharacters"
          :key="`${char}-${index}`"
          class="philosophy-char"
          :class="{ muted: punctuation.includes(char) }"
          :style="{ '--delay': `${index * 45}ms`, '--char-color': palette[index % palette.length] }"
        >
          {{ char }}
        </span>
      </div>

      <div class="philosophy-notes">
        <p v-for="note in philosophyNotes" :key="note">{{ note }}</p>
      </div>

      <div class="philosophy-grid">
        <article v-for="item in philosophyPillars" :key="item.title" class="philosophy-card" :class="{ placeholder: item.placeholder }">
          <span class="card-kicker">{{ item.kicker }}</span>
          <h3>{{ item.title }}</h3>
          <p>{{ item.desc }}</p>
        </article>
      </div>
    </div>
  </section>
</template>

<script setup>
import { philosophyNotes, philosophyText } from './showcaseContent'
import { showcaseSectionProps, useSectionReady } from './useShowcaseSection'

defineOptions({ name: 'DesignPhilosophySection' })
defineProps(showcaseSectionProps)

const ready = useSectionReady()
const philosophyCharacters = philosophyText.split('')
const punctuation = ['，', '。']
const palette = ['#ff9f7f', '#ffd166', '#7ee5ff', '#8bf1c6', '#c9a8ff', '#ff8bd2']
const philosophyPillars = [
  {
    kicker: 'Information Order',
    title: '让复杂信息先被看懂，再被记住',
    desc: '不是把内容堆满，而是用标题、节奏和层级把用户一步步带进业务核心。',
    placeholder: false,
  },
  {
    kicker: 'Brand Emotion',
    title: '让政务产品也拥有情绪和气场',
    desc: '通过艺术字、发光、渐层和镜面质感，建立不同于后台系统的第一眼记忆。',
    placeholder: false,
  },
  {
    kicker: 'Visual Placeholder',
    title: '这里可补一张理念主视觉',
    desc: '建议后续换成抽象人群、城市轮廓或装置感海报，让这页在超宽屏下更饱满。',
    placeholder: true,
  },
]
</script>

<style scoped>
.philosophy-section {
  width: 100%;
  height: 100%;
  background:
    radial-gradient(circle at center, rgba(255, 184, 102, 0.12), transparent 22%),
    linear-gradient(180deg, rgba(245, 246, 255, 0.98), rgba(254, 246, 250, 0.98));
}

[data-theme='dark'] .philosophy-section {
  background:
    radial-gradient(circle at center, rgba(255, 184, 102, 0.1), transparent 22%),
    linear-gradient(180deg, rgba(10, 15, 24, 0.98), rgba(15, 12, 22, 0.98));
}

.section-shell {
  height: 100%;
  padding: 110px 7vw 56px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 34px;
  text-align: center;
}

.section-eyebrow,
.philosophy-words,
.philosophy-notes {
  opacity: 0;
  transform: translateY(24px);
  transition: opacity 0.8s var(--showcase-ease), transform 0.8s var(--showcase-ease);
}

.philosophy-section.ready .section-eyebrow,
.philosophy-section.ready .philosophy-words,
.philosophy-section.ready .philosophy-notes {
  opacity: 1;
  transform: translateY(0);
}

.philosophy-words {
  transition-delay: 0.1s;
}

.philosophy-notes {
  transition-delay: 0.18s;
}

.section-eyebrow {
  align-self: center;
  display: inline-flex;
  padding: 8px 14px;
  border-radius: 999px;
  background: rgba(255, 138, 114, 0.12);
  color: #ba5237;
  letter-spacing: 0.2em;
  font-size: 12px;
}

.philosophy-words {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 10px 8px;
  max-width: 1100px;
  margin: 0 auto;
}

.philosophy-char {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 1.1em;
  font-family: 'STZhongsong', 'Songti SC', 'Noto Serif SC', serif;
  font-size: clamp(36px, 5.8vw, 90px);
  line-height: 1.15;
  color: var(--char-color);
  text-shadow: 0 0 20px color-mix(in srgb, var(--char-color) 45%, transparent);
  opacity: 0;
  transform: translateY(40px) scale(0.88);
  animation: char-pop 0.82s var(--showcase-ease) forwards;
  animation-delay: var(--delay);
}

.philosophy-section:not(.ready) .philosophy-char {
  animation: none;
}

.philosophy-char.muted {
  color: rgba(120, 128, 142, 0.54);
  text-shadow: none;
}

.philosophy-notes {
  display: grid;
  gap: 12px;
}

.philosophy-notes p {
  max-width: 860px;
  margin: 0 auto;
  color: var(--text-secondary, #666);
  line-height: 1.88;
  font-size: 16px;
}

.philosophy-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
}

.philosophy-card {
  padding: 22px 20px 24px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.62);
  border: 1px solid rgba(17, 17, 17, 0.08);
  text-align: left;
  box-shadow: 0 18px 44px rgba(31, 35, 64, 0.08);
}

[data-theme='dark'] .philosophy-card {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.08);
  box-shadow: 0 18px 44px rgba(0, 0, 0, 0.24);
}

.philosophy-card.placeholder {
  border-style: dashed;
  background:
    linear-gradient(135deg, rgba(255, 157, 127, 0.1), transparent 40%, rgba(126, 229, 255, 0.1)),
    rgba(255, 255, 255, 0.62);
}

[data-theme='dark'] .philosophy-card.placeholder {
  background:
    linear-gradient(135deg, rgba(255, 157, 127, 0.12), transparent 40%, rgba(126, 229, 255, 0.12)),
    rgba(255, 255, 255, 0.04);
}

.card-kicker {
  display: inline-flex;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(17, 17, 17, 0.06);
  color: var(--text-secondary, #666);
  font-size: 11px;
  letter-spacing: 0.14em;
}

[data-theme='dark'] .card-kicker {
  background: rgba(255, 255, 255, 0.08);
}

.philosophy-card h3 {
  margin: 14px 0 10px;
  font-size: 22px;
  line-height: 1.35;
}

.philosophy-card p {
  margin: 0;
  color: var(--text-secondary, #666);
  line-height: 1.78;
}

@keyframes char-pop {
  0% {
    opacity: 0;
    transform: translateY(40px) scale(0.94);
  }
  100% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@media (max-width: 768px) {
  .section-shell {
    padding: 88px 20px 36px;
  }

  .philosophy-char {
    font-size: clamp(28px, 9vw, 52px);
  }

  .philosophy-notes p {
    font-size: 15px;
  }

  .philosophy-grid {
    grid-template-columns: 1fr;
  }
}
</style>
