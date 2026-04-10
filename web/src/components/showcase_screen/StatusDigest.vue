<template>
  <LuminousFrame
    title="文件与反馈态势"
    eyebrow="Status Digest"
    subtitle="用更厚重的结构填满右下区域，并持续给出综合判断"
    :accent-start="accentStart"
    :accent-end="accentEnd"
    compact
  >
    <div class="digest-hero">
      <div class="hero-head">
        <span class="hero-label">公开展示完成度</span>
        <strong class="hero-value">{{ approvalRate }}%</strong>
      </div>
      <div class="hero-track">
        <div class="hero-fill" :style="{ width: `${approvalRate}%` }"></div>
      </div>
    </div>

    <div class="digest-grid">
      <article v-for="metric in metrics" :key="metric.label" class="digest-card">
        <span class="card-label">{{ metric.label }}</span>
        <strong class="card-value">{{ metric.value }}</strong>
        <p class="card-note">{{ metric.note }}</p>
      </article>
    </div>

    <div class="digest-notes">
      <div v-for="note in notes" :key="note" class="note-row">
        <span class="note-dot"></span>
        <span>{{ note }}</span>
      </div>
    </div>
  </LuminousFrame>
</template>

<script setup>
import LuminousFrame from './LuminousFrame.vue'

defineOptions({ name: 'StatusDigest' })

defineProps({
  metrics: {
    type: Array,
    default: () => [],
  },
  approvalRate: {
    type: Number,
    default: 0,
  },
  notes: {
    type: Array,
    default: () => [],
  },
  accentStart: {
    type: String,
    default: '#80fab0',
  },
  accentEnd: {
    type: String,
    default: '#58cbff',
  },
})
</script>

<style scoped>
.digest-hero {
  position: relative;
  padding: 16px 16px 18px;
  background:
    linear-gradient(120deg, rgba(128, 250, 176, 0.12), rgba(88, 203, 255, 0.08) 44%, transparent 70%),
    rgba(255, 255, 255, 0.03);
  clip-path: polygon(0 10px, 10px 0, calc(100% - 14px) 0, 100% 14px, 100% 100%, 0 100%);
  overflow: hidden;
}

.digest-hero::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.14), transparent);
  transform: translateX(-100%);
  animation: hero-scan 5s linear infinite;
}

.hero-head {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 12px;
}

.hero-label {
  color: rgba(255, 255, 255, 0.56);
  font-size: 11px;
  letter-spacing: 0.14em;
}

.hero-value {
  color: #fff;
  font-family: 'Bahnschrift', 'DIN Alternate', sans-serif;
  font-size: 32px;
  line-height: 1;
  text-shadow: 0 0 22px rgba(88, 203, 255, 0.2);
}

.hero-track {
  position: relative;
  height: 10px;
  margin-top: 16px;
  background: rgba(255, 255, 255, 0.08);
  clip-path: polygon(0 0, 100% 0, calc(100% - 8px) 100%, 0 100%);
}

.hero-fill {
  height: 100%;
  background: linear-gradient(90deg, #80fab0, #58cbff);
  box-shadow: 0 0 18px rgba(88, 203, 255, 0.35);
}

.digest-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 14px;
}

.digest-card {
  padding: 14px 14px 16px;
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.05), transparent 48%, rgba(88, 203, 255, 0.06)),
    rgba(255, 255, 255, 0.02);
  clip-path: polygon(0 8px, 8px 0, 100% 0, 100% calc(100% - 8px), calc(100% - 8px) 100%, 0 100%);
  border: 1px solid rgba(255, 255, 255, 0.07);
}

.card-label {
  display: block;
  color: rgba(255, 255, 255, 0.54);
  font-size: 11px;
  letter-spacing: 0.12em;
}

.card-value {
  display: block;
  margin-top: 10px;
  color: #fff;
  font-family: 'Bahnschrift', 'DIN Alternate', sans-serif;
  font-size: 24px;
  line-height: 1;
}

.card-note {
  margin: 10px 0 0;
  color: rgba(255, 255, 255, 0.58);
  font-size: 12px;
  line-height: 1.65;
}

.digest-notes {
  display: grid;
  gap: 10px;
  margin-top: 14px;
}

.note-row {
  display: grid;
  grid-template-columns: 10px minmax(0, 1fr);
  gap: 10px;
  align-items: start;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.03);
  clip-path: polygon(0 8px, 8px 0, 100% 0, 100% 100%, 0 100%);
  color: rgba(255, 255, 255, 0.66);
  font-size: 12px;
  line-height: 1.7;
}

.note-dot {
  width: 6px;
  height: 6px;
  margin-top: 7px;
  border-radius: 50%;
  background: linear-gradient(180deg, #80fab0, #58cbff);
  box-shadow: 0 0 12px rgba(88, 203, 255, 0.42);
}

@keyframes hero-scan {
  from {
    transform: translateX(-100%);
  }
  to {
    transform: translateX(100%);
  }
}

@media (max-width: 640px) {
  .digest-grid {
    grid-template-columns: 1fr;
  }
}
</style>
