<template>
  <section class="luminous-frame" :class="{ compact }" :style="{ '--accent-start': accentStart, '--accent-end': accentEnd }">
    <div class="frame-glow"></div>
    <div class="frame-shell">
      <div class="frame-edge edge-top"></div>
      <div class="frame-edge edge-right"></div>
      <div class="frame-edge edge-bottom"></div>
      <div class="frame-edge edge-left"></div>
      <div class="frame-corner corner-tl"></div>
      <div class="frame-corner corner-tr"></div>
      <div class="frame-corner corner-br"></div>
      <div class="frame-corner corner-bl"></div>
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
  min-height: 0;
  overflow: hidden;
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
  animation: frame-glow-drift 8s ease-in-out infinite;
  pointer-events: none;
}

.frame-shell {
  position: relative;
  min-height: 100%;
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
  border: 1px solid rgba(255, 255, 255, 0.04);
  clip-path: polygon(0 12px, 12px 0, calc(100% - 22px) 0, 100% 22px, 100% calc(100% - 12px), calc(100% - 12px) 100%, 22px 100%, 0 calc(100% - 22px));
}

.frame-edge,
.frame-corner,
.frame-noise,
.frame-shell::after {
  position: absolute;
  pointer-events: none;
}

.frame-edge {
  z-index: 0;
  opacity: 0.96;
  mix-blend-mode: screen;
}

.edge-top,
.edge-bottom {
  height: 2px;
  background:
    linear-gradient(90deg, transparent 0%, var(--accent-start) 22%, rgba(255, 255, 255, 0.95) 44%, var(--accent-end) 66%, transparent 88%);
  background-size: 220% 100%;
  box-shadow:
    0 0 12px color-mix(in srgb, var(--accent-start) 38%, transparent),
    0 0 18px color-mix(in srgb, var(--accent-end) 34%, transparent);
}

.edge-top {
  top: 1px;
  left: 16px;
  right: 28px;
  animation: edge-flow-x 4.8s linear infinite;
}

.edge-bottom {
  bottom: 1px;
  left: 24px;
  right: 16px;
  animation: edge-flow-x-reverse 5.3s linear infinite;
}

.edge-left,
.edge-right {
  width: 2px;
  background:
    linear-gradient(180deg, transparent 0%, var(--accent-start) 20%, rgba(255, 255, 255, 0.95) 48%, var(--accent-end) 72%, transparent 100%);
  background-size: 100% 220%;
  box-shadow:
    0 0 12px color-mix(in srgb, var(--accent-start) 36%, transparent),
    0 0 18px color-mix(in srgb, var(--accent-end) 30%, transparent);
}

.edge-left {
  left: 1px;
  top: 16px;
  bottom: 28px;
  animation: edge-flow-y 5.2s linear infinite;
}

.edge-right {
  right: 1px;
  top: 24px;
  bottom: 16px;
  animation: edge-flow-y-reverse 4.9s linear infinite;
}

.frame-corner {
  z-index: 0;
  width: 24px;
  height: 24px;
  filter: blur(2px);
  opacity: 0.72;
}

.corner-tl {
  top: -2px;
  left: -2px;
  background: radial-gradient(circle at 70% 70%, var(--accent-start), transparent 72%);
}

.corner-tr {
  top: -2px;
  right: -2px;
  background: radial-gradient(circle at 30% 70%, var(--accent-end), transparent 72%);
}

.corner-br {
  right: -2px;
  bottom: -2px;
  background: radial-gradient(circle at 30% 30%, var(--accent-start), transparent 72%);
}

.corner-bl {
  left: -2px;
  bottom: -2px;
  background: radial-gradient(circle at 70% 30%, var(--accent-end), transparent 72%);
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
  opacity: 0.26;
  animation: frame-noise-shift 3.2s linear infinite;
}

.frame-shell::after {
  content: '';
  inset: 1px;
  clip-path: inherit;
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow:
    inset 0 0 26px rgba(255, 143, 122, 0.08),
    inset 0 0 34px rgba(88, 203, 255, 0.06);
}

.frame-shell > :not(.frame-edge):not(.frame-corner):not(.frame-noise) {
  position: relative;
  z-index: 1;
}

.frame-body {
  position: relative;
  z-index: 1;
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

@keyframes frame-glow-drift {
  0%,
  100% {
    transform: translate3d(0, 0, 0);
  }
  50% {
    transform: translate3d(10px, -8px, 0);
  }
}

@keyframes edge-flow-x {
  0% {
    background-position: 170% 50%;
  }
  100% {
    background-position: -70% 50%;
  }
}

@keyframes edge-flow-x-reverse {
  0% {
    background-position: -70% 50%;
  }
  100% {
    background-position: 170% 50%;
  }
}

@keyframes edge-flow-y {
  0% {
    background-position: 50% 170%;
  }
  100% {
    background-position: 50% -70%;
  }
}

@keyframes edge-flow-y-reverse {
  0% {
    background-position: 50% -70%;
  }
  100% {
    background-position: 50% 170%;
  }
}

@keyframes frame-noise-shift {
  0% {
    transform: translate3d(0, 0, 0);
  }
  50% {
    transform: translate3d(0, 2px, 0);
  }
  100% {
    transform: translate3d(0, 0, 0);
  }
}
</style>
