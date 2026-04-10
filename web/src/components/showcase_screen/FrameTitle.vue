<template>
  <div class="frame-title" :style="{ '--accent-start': accentStart, '--accent-end': accentEnd }">
    <div class="title-left">
      <span v-if="eyebrow" class="title-eyebrow">{{ eyebrow }}</span>
      <h3 class="title-text" :data-text="title">
        <span class="title-text-main">{{ title }}</span>
      </h3>
      <p v-if="subtitle" class="title-sub">{{ subtitle }}</p>
    </div>
    <div class="title-holder">
      <span class="holder-line left"></span>
      <span class="holder-core"></span>
      <span class="holder-line right"></span>
    </div>
    <div v-if="$slots.right" class="title-right">
      <slot name="right"></slot>
    </div>
  </div>
</template>

<script setup>
defineOptions({ name: 'FrameTitle' })

defineProps({
  eyebrow: {
    type: String,
    default: '',
  },
  title: {
    type: String,
    required: true,
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
})
</script>

<style scoped>
.frame-title {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: end;
  gap: 18px;
}

.title-left {
  min-width: 0;
}

.title-eyebrow {
  position: relative;
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.62);
  font-size: 10px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  overflow: hidden;
}

.title-eyebrow::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(110deg, transparent 0%, transparent 28%, rgba(255, 255, 255, 0.22) 48%, transparent 68%, transparent 100%);
  transform: translateX(-120%);
  animation: eyebrow-scan 5s linear infinite;
}

.title-text {
  position: relative;
  display: inline-flex;
  align-items: center;
  margin: 10px 0 6px;
  padding: 6px 18px 7px 10px;
  font-size: 20px;
  line-height: 1.2;
  color: #fff;
  letter-spacing: 0.04em;
  overflow: hidden;
  text-shadow:
    0 0 16px rgba(255, 143, 122, 0.24),
    0 0 20px rgba(88, 203, 255, 0.18);
}

.title-text::before {
  content: '';
  position: absolute;
  inset: 2px -18px 1px 0;
  background:
    linear-gradient(90deg, rgba(255, 255, 255, 0) 0%, rgba(255, 143, 122, 0.1) 20%, rgba(88, 203, 255, 0.12) 58%, rgba(255, 255, 255, 0) 100%);
  border: 1px solid rgba(255, 255, 255, 0.07);
  clip-path: polygon(0 0, calc(100% - 18px) 0, 100% 100%, 0 100%);
}

.title-text::after {
  content: attr(data-text);
  position: absolute;
  inset: 6px 18px 7px 10px;
  color: transparent;
  background: linear-gradient(
    110deg,
    transparent 0%,
    transparent 24%,
    rgba(255, 255, 255, 0.2) 34%,
    var(--accent-start) 43%,
    #ffffff 50%,
    var(--accent-end) 58%,
    transparent 70%,
    transparent 100%
  );
  background-size: 220% 100%;
  -webkit-background-clip: text;
  background-clip: text;
  animation: title-mask-sweep 4.8s ease-in-out infinite;
  pointer-events: none;
}

.title-text-main {
  position: relative;
  z-index: 1;
}

.title-sub {
  margin: 0;
  color: rgba(255, 255, 255, 0.56);
  font-size: 12px;
  line-height: 1.6;
}

.title-holder {
  position: absolute;
  left: 0;
  right: 0;
  bottom: -10px;
  display: flex;
  align-items: center;
  gap: 10px;
  pointer-events: none;
}

.holder-line {
  height: 1px;
  flex: 1;
  background: linear-gradient(90deg, transparent, var(--accent-start), var(--accent-end), transparent);
  opacity: 0.8;
}

.holder-core {
  width: 92px;
  height: 10px;
  border-radius: 999px;
  background:
    linear-gradient(90deg, rgba(255, 143, 122, 0.28), rgba(88, 203, 255, 0.3)),
    rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow:
    0 0 18px rgba(255, 143, 122, 0.18),
    0 0 26px rgba(88, 203, 255, 0.14);
}

.title-right {
  position: relative;
  z-index: 1;
}

@keyframes title-mask-sweep {
  0% {
    background-position: 160% 50%;
  }
  100% {
    background-position: -80% 50%;
  }
}

@keyframes eyebrow-scan {
  0% {
    transform: translateX(-120%);
  }
  100% {
    transform: translateX(120%);
  }
}
</style>
