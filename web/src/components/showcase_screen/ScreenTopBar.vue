<template>
  <header class="screen-topbar">
    <div class="topbar-title-block">
      <span class="topbar-eyebrow">PUBLIC GOVERNANCE DATA SCREEN</span>
      <h1 class="topbar-title">云上观策 · 公共数据分析大屏</h1>
      <p class="topbar-sub">珊瑚暖光与冷青信号共同驱动的展示型分析舞台</p>
    </div>

    <div class="topbar-center">
      <div class="status-chip">
        <span class="status-dot live"></span>
        <strong>LIVE STREAM</strong>
      </div>
      <div class="status-chip">
        <span class="status-dot sync"></span>
        <strong>{{ activeUsers }} 活跃用户</strong>
      </div>
    </div>

    <div class="topbar-right">
      <div class="time-block">
        <span class="time-label">数据时钟</span>
        <strong class="time-value">{{ currentTime }}</strong>
      </div>
    </div>
  </header>
</template>

<script setup>
defineOptions({ name: 'ScreenTopBar' })

defineProps({
  currentTime: {
    type: String,
    default: '',
  },
  activeUsers: {
    type: [String, Number],
    default: '—',
  },
})
</script>

<style scoped>
.screen-topbar {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(540px, auto) minmax(0, 1fr);
  align-items: center;
  gap: 18px;
  padding: 0 0 18px;
}

.screen-topbar::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255, 143, 122, 0.4), rgba(88, 203, 255, 0.45), transparent);
}

.topbar-title-block {
  grid-column: 2;
  justify-self: center;
  text-align: center;
}

.topbar-eyebrow {
  display: inline-flex;
  color: rgba(255, 255, 255, 0.54);
  font-size: 11px;
  letter-spacing: 0.28em;
}

.topbar-title {
  margin: 10px 0 8px;
  font-family: 'STZhongsong', 'Songti SC', 'Noto Serif SC', serif;
  font-size: clamp(28px, 3vw, 42px);
  line-height: 1.15;
  color: #fff;
  text-shadow:
    0 0 22px rgba(255, 143, 122, 0.18),
    0 0 28px rgba(88, 203, 255, 0.14);
}

.topbar-sub {
  margin: 0;
  color: rgba(255, 255, 255, 0.62);
  font-size: 13px;
  letter-spacing: 0.08em;
}

.topbar-center {
  grid-column: 1;
  justify-self: start;
  display: flex;
  gap: 10px;
  align-items: center;
}

.status-chip {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  height: 40px;
  padding: 0 14px;
  clip-path: polygon(0 8px, 8px 0, calc(100% - 12px) 0, 100% 12px, 100% 100%, 0 100%);
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.74);
  font-size: 12px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot.live {
  background: #ff8f7a;
  box-shadow: 0 0 12px #ff8f7a;
}

.status-dot.sync {
  background: #58cbff;
  box-shadow: 0 0 12px #58cbff;
}

.topbar-right {
  grid-column: 3;
  justify-self: end;
}

.time-block {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
}

.time-label {
  color: rgba(255, 255, 255, 0.46);
  font-size: 11px;
  letter-spacing: 0.16em;
}

.time-value {
  color: #f4f7ff;
  font-family: 'Bahnschrift', 'Segoe UI', sans-serif;
  font-size: 20px;
}

@media (max-width: 1200px) {
  .screen-topbar {
    grid-template-columns: 1fr;
  }

  .topbar-title-block,
  .topbar-center,
  .topbar-right {
    grid-column: auto;
    justify-self: start;
    text-align: left;
  }

  .topbar-center,
  .time-block {
    justify-self: start;
    align-items: flex-start;
  }

  .topbar-center {
    flex-wrap: wrap;
  }
}
</style>
