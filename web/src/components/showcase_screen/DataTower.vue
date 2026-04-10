<template>
  <article class="data-tower" :style="{ '--tower-a': colorA, '--tower-b': colorB }">
    <div class="tower-perspective">
      <div class="tower-ring main">
        <div class="tower-cut" v-for="cut in 5" :key="cut"></div>
      </div>
      <div class="tower-ring second"></div>
      <div class="tower-ring third"></div>
      <div class="tower-ring base">
        <div class="tower-base-cut" v-for="cut in 8" :key="cut"></div>
      </div>
      <div class="tower-core"></div>
      <div class="tower-text">
        <strong>{{ value }}</strong>
        <span>{{ suffix }}</span>
      </div>
    </div>
    <div class="tower-meta">
      <span class="tower-label">{{ label }}</span>
      <span class="tower-note">{{ note }}</span>
    </div>
  </article>
</template>

<script setup>
defineOptions({ name: 'DataTower' })

defineProps({
  value: {
    type: String,
    required: true,
  },
  label: {
    type: String,
    required: true,
  },
  note: {
    type: String,
    default: '',
  },
  suffix: {
    type: String,
    default: '',
  },
  colorA: {
    type: String,
    default: '#58cbff',
  },
  colorB: {
    type: String,
    default: '#ff8f7a',
  },
})
</script>

<style scoped>
.data-tower {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.tower-perspective {
  position: relative;
  width: 180px;
  height: 230px;
  perspective: 640px;
  transform-style: preserve-3d;
}

.tower-ring,
.tower-core {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  border-radius: 50%;
}

.tower-ring.main {
  top: 18px;
  width: 138px;
  height: 138px;
  background: rgba(2, 6, 12, 0.96);
  box-shadow:
    0 0 0 18px rgba(2, 12, 24, 0.94),
    inset 0 0 18px rgba(255, 255, 255, 0.04);
}

.tower-ring.main::before {
  content: '';
  position: absolute;
  inset: -18px;
  border-radius: 50%;
  background: conic-gradient(var(--tower-a), var(--tower-a) 58%, rgba(9, 21, 40, 0.95) 58%);
  z-index: -1;
  animation: ring-rotate 5s linear infinite;
}

.tower-ring.main::after {
  content: '';
  position: absolute;
  inset: -42px;
  border-radius: 50%;
  border: 10px solid rgba(11, 26, 50, 0.95);
  box-shadow:
    0 0 16px color-mix(in srgb, var(--tower-a) 28%, transparent),
    inset 0 0 18px rgba(255, 255, 255, 0.03);
}

.tower-cut {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 6px;
  height: 100px;
  background: rgba(4, 10, 20, 0.95);
  transform-origin: bottom center;
  transform: translate(-50%, -100%) rotate(calc((var(--i, 0)) * 72deg));
}

.tower-cut:nth-child(1) { transform: translate(-50%, -100%) rotate(0deg); }
.tower-cut:nth-child(2) { transform: translate(-50%, -100%) rotate(72deg); }
.tower-cut:nth-child(3) { transform: translate(-50%, -100%) rotate(144deg); }
.tower-cut:nth-child(4) { transform: translate(-50%, -100%) rotate(216deg); }
.tower-cut:nth-child(5) { transform: translate(-50%, -100%) rotate(288deg); }

.tower-ring.second {
  width: 112px;
  height: 112px;
  bottom: 28px;
  border: 5px solid transparent;
  border-top-color: color-mix(in srgb, var(--tower-a) 50%, transparent);
  border-left-color: color-mix(in srgb, var(--tower-a) 50%, transparent);
  border-right-color: color-mix(in srgb, var(--tower-a) 50%, transparent);
  border-bottom-color: rgba(11, 26, 50, 0.92);
  transform: translateX(-50%) rotateX(60deg);
  animation: float-second 3s ease-in-out infinite;
}

.tower-ring.third {
  width: 66px;
  height: 66px;
  bottom: 6px;
  border: 3px solid var(--tower-a);
  transform: translateX(-50%) rotateX(60deg);
  animation: float-third 3s ease-in-out infinite 0.25s;
}

.tower-ring.base {
  width: 110px;
  height: 110px;
  bottom: -24px;
  border: 26px solid color-mix(in srgb, var(--tower-a) 10%, transparent);
  transform: translateX(-50%) rotateX(60deg);
  animation: float-base 3s ease-in-out infinite 0.45s;
}

.tower-base-cut {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 3px;
  height: 56px;
  background: rgba(4, 10, 20, 0.9);
  transform-origin: bottom center;
}

.tower-base-cut:nth-child(1) { transform: translate(-50%, -100%) rotate(0deg); }
.tower-base-cut:nth-child(2) { transform: translate(-50%, -100%) rotate(45deg); }
.tower-base-cut:nth-child(3) { transform: translate(-50%, -100%) rotate(90deg); }
.tower-base-cut:nth-child(4) { transform: translate(-50%, -100%) rotate(135deg); }
.tower-base-cut:nth-child(5) { transform: translate(-50%, -100%) rotate(180deg); }
.tower-base-cut:nth-child(6) { transform: translate(-50%, -100%) rotate(225deg); }
.tower-base-cut:nth-child(7) { transform: translate(-50%, -100%) rotate(270deg); }
.tower-base-cut:nth-child(8) { transform: translate(-50%, -100%) rotate(315deg); }

.tower-core {
  left: 50%;
  top: 32px;
  width: 48px;
  height: 48px;
  transform: translateX(-50%);
  background: conic-gradient(var(--tower-a), var(--tower-b), var(--tower-a));
  box-shadow:
    0 0 18px color-mix(in srgb, var(--tower-a) 55%, transparent),
    0 0 28px color-mix(in srgb, var(--tower-b) 24%, transparent);
}

.tower-core::after {
  content: '';
  position: absolute;
  inset: 14px;
  border-radius: 50%;
  background: rgba(4, 10, 20, 0.95);
}

.tower-text {
  position: absolute;
  top: 74px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 112px;
  padding: 10px 10px 8px;
  color: #f8fbff;
  background: linear-gradient(180deg, rgba(3, 8, 14, 0.64), rgba(3, 8, 14, 0.16));
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 999px;
  text-shadow:
    0 0 18px color-mix(in srgb, var(--tower-a) 42%, transparent),
    0 6px 16px rgba(0, 0, 0, 0.7);
  box-shadow:
    inset 0 0 16px rgba(255, 255, 255, 0.04),
    0 0 24px rgba(0, 0, 0, 0.28);
}

.tower-text strong {
  font-family: 'Bahnschrift', 'DIN Alternate', sans-serif;
  font-size: 48px;
  line-height: 1;
  letter-spacing: 0.02em;
  -webkit-text-stroke: 1px rgba(4, 10, 18, 0.82);
}

.tower-text span {
  margin-top: 6px;
  font-size: 10px;
  letter-spacing: 0.18em;
  color: color-mix(in srgb, var(--tower-a) 74%, white);
}

.tower-meta {
  text-align: center;
}

.tower-label,
.tower-note {
  display: block;
}

.tower-label {
  font-size: 14px;
  color: #f4f7ff;
}

.tower-note {
  margin-top: 4px;
  color: rgba(255, 255, 255, 0.5);
  font-size: 11px;
}

@keyframes ring-rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes float-second {
  0%, 100% { bottom: 28px; }
  50% { bottom: 18px; }
}

@keyframes float-third {
  0%, 100% { bottom: 6px; }
  50% { bottom: -4px; }
}

@keyframes float-base {
  0%, 100% { bottom: -24px; }
  50% { bottom: -34px; }
}
</style>
