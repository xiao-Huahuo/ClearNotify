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

@keyframes char-pop {
  0% {
    opacity: 0;
    transform: translateY(40px) scale(0.88);
  }
  65% {
    opacity: 1;
    transform: translateY(-10px) scale(1.02);
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
}
</style>
