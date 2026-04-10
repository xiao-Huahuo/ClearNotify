<template>
  <section class="luminous-frame" :class="{ compact }" :style="{ '--accent-start': accentStart, '--accent-end': accentEnd }">
    <div class="frame-glow"></div>
    <svg class="frame-outline" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
      <path class="outline-base" pathLength="1000" d="M 1.5 7.5 L 7.5 1.5 L 88.5 1.5 L 98.5 11.5 L 98.5 92.5 L 92.5 98.5 L 11.5 98.5 L 1.5 88.5 Z" />
      <path class="outline-trace outline-trace-a" pathLength="1000" d="M 1.5 7.5 L 7.5 1.5 L 88.5 1.5 L 98.5 11.5 L 98.5 92.5 L 92.5 98.5 L 11.5 98.5 L 1.5 88.5 Z" />
      <path class="outline-trace outline-trace-b" pathLength="1000" d="M 1.5 7.5 L 7.5 1.5 L 88.5 1.5 L 98.5 11.5 L 98.5 92.5 L 92.5 98.5 L 11.5 98.5 L 1.5 88.5 Z" />
    </svg>
    <div class="frame-shell">
      <div class="frame-noise"></div>
      <FrameTitle v-if="title" :eyebrow="eyebrow" :title="title" :subtitle="subtitle" :accent-start="accentStart" :accent-end="accentEnd">
        <template v-if="$slots.actions" #right>
          <slot name="actions"></slot>
        </template>
      </FrameTitle>
      <div class="frame-body" :class="{ 'with-title': title }">
        <slot></slot>
      </div>
    </div>
  </section>
</template>

<script setup>
import FrameTitle from './FrameTitle.vue'

defineOptions({ name: 'LuminousFrame' })

defineProps({
  title: {
    type: String,
    default: '',
  },
  eyebrow: {
    type: String,
    default: '',
  },
  subtitle: {
    type: String,
    default: '',
  },
  accentStart: {
    type: String,
    default: '#ff8f7a',
  },
  accentEnd: {
    type: String,
    default: '#58cbff',
  },
  compact: {
    type: Boolean,
    default: false,
  },
})
</script>

<style scoped>
.luminous-frame {
  position: relative;
  display: flex;
  min-height: 0;
  height: 100%;
  overflow: hidden;
  isolation: isolate;
  filter:
    drop-shadow(0 18px 48px rgba(0, 0, 0, 0.35))
    drop-shadow(0 0 18px rgba(255, 143, 122, 0.12))
    drop-shadow(0 0 22px rgba(88, 203, 255, 0.1));
}

.frame-glow {
  position: absolute;
  inset: -30%;
  background:
    radial-gradient(circle at 20% 20%, rgba(255, 143, 122, 0.18), transparent 18%),
    radial-gradient(circle at 80% 0%, rgba(88, 203, 255, 0.16), transparent 22%),
    radial-gradient(circle at 50% 100%, rgba(128, 250, 176, 0.12), transparent 26%);
  animation: frame-glow-settle 4.2s ease-out 1 both;
  pointer-events: none;
}

.frame-shell {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  flex: 1;
  height: 100%;
  min-height: 0;
  isolation: isolate;
  padding: 18px 18px 16px;
  background:
    linear-gradient(180deg, rgba(12, 18, 29, 0.86), rgba(7, 10, 18, 0.96)),
    repeating-linear-gradient(
      180deg,
      rgba(255, 255, 255, 0.025) 0,
      rgba(255, 255, 255, 0.025) 1px,
      transparent 1px,
      transparent 6px
    );
  clip-path: polygon(0 6px, 6px 0, calc(100% - 10px) 0, 100% 10px, 100% calc(100% - 6px), calc(100% - 6px) 100%, 10px 100%, 0 calc(100% - 10px));
}

.frame-outline,
.frame-noise,
.frame-shell::after {
  position: absolute;
  pointer-events: none;
}

.frame-outline {
  inset: 0;
  z-index: 3;
  width: 100%;
  height: 100%;
  overflow: visible;
  mix-blend-mode: screen;
  filter:
    drop-shadow(0 0 10px color-mix(in srgb, var(--accent-start) 36%, transparent))
    drop-shadow(0 0 18px color-mix(in srgb, var(--accent-end) 32%, transparent));
}

.outline-base,
.outline-trace {
  fill: none;
  vector-effect: non-scaling-stroke;
  stroke-linejoin: round;
  stroke-linecap: round;
}

.outline-base {
  stroke: rgba(255, 255, 255, 0.08);
  stroke-width: 1.2;
}

.outline-trace {
  stroke-width: 2.1;
  opacity: 0.98;
}

.outline-trace-a {
  stroke: var(--accent-start);
  stroke-dasharray: 220 780;
  animation: outline-travel-a 8.2s linear infinite;
}

.outline-trace-b {
  stroke: var(--accent-end);
  stroke-dasharray: 180 820;
  animation: outline-travel-b 9.4s linear infinite;
}

.frame-noise {
  inset: 1px;
  clip-path: inherit;
  background:
    repeating-linear-gradient(
      180deg,
      rgba(255, 255, 255, 0.035) 0,
      rgba(255, 255, 255, 0.035) 1px,
      transparent 1px,
      transparent 6px
    ),
    repeating-linear-gradient(
      90deg,
      rgba(255, 255, 255, 0.02) 0,
      rgba(255, 255, 255, 0.02) 1px,
      transparent 1px,
      transparent 10px
    );
  opacity: 0.18;
}

.frame-shell::after {
  content: '';
  inset: 1px;
  z-index: 0;
  clip-path: polygon(0 6px, 6px 0, calc(100% - 10px) 0, 100% 10px, 100% calc(100% - 6px), calc(100% - 6px) 100%, 10px 100%, 0 calc(100% - 10px));
  border: 1px solid rgba(255, 255, 255, 0.06);
  box-shadow:
    inset 0 0 16px rgba(255, 143, 122, 0.08),
    inset 0 0 26px rgba(88, 203, 255, 0.06);
}

.frame-shell > :not(.frame-noise) {
  position: relative;
  z-index: 1;
}

.frame-body {
  position: relative;
  z-index: 1;
  display: flex;
  flex: 1;
  min-height: 0;
  flex-direction: column;
}

.frame-body.with-title {
  margin-top: 28px;
}

.luminous-frame.compact .frame-shell {
  padding: 16px 16px 14px;
}

.luminous-frame.compact .frame-body.with-title {
  margin-top: 24px;
}

@keyframes frame-glow-settle {
  0% {
    transform: translate3d(-18px, 12px, 0) scale(0.98);
    opacity: 0.84;
  }
  100% {
    transform: translate3d(0, 0, 0) scale(1);
    opacity: 1;
  }
}

@keyframes outline-travel-a {
  from {
    stroke-dashoffset: 0;
  }
  to {
    stroke-dashoffset: -1000;
  }
}

@keyframes outline-travel-b {
  from {
    stroke-dashoffset: 480;
  }
  to {
    stroke-dashoffset: -520;
  }
}

</style>
