<template>
  <div class="summary-ribbon">
    <div class="ribbon-track">
      <template v-for="repeat in 2" :key="repeat">
        <div v-for="item in items" :key="`${repeat}-${item.label}`" class="ribbon-chip">
          <span class="chip-label">{{ item.label }}</span>
          <strong class="chip-value">{{ item.value }}</strong>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
defineOptions({ name: 'SummaryRibbon' })

defineProps({
  items: {
    type: Array,
    default: () => [],
  },
})
</script>

<style scoped>
.summary-ribbon {
  position: relative;
  overflow: hidden;
  flex-shrink: 0;
  padding: 12px 0 4px;
}

.summary-ribbon::before,
.summary-ribbon::after {
  content: '';
  position: absolute;
  top: 0;
  bottom: 0;
  width: 120px;
  z-index: 1;
  pointer-events: none;
}

.summary-ribbon::before {
  left: 0;
  background: linear-gradient(90deg, rgba(8, 12, 20, 1), transparent);
}

.summary-ribbon::after {
  right: 0;
  background: linear-gradient(270deg, rgba(8, 12, 20, 1), transparent);
}

.ribbon-track {
  display: flex;
  gap: 14px;
  width: max-content;
  animation: ribbon-scroll 28s linear infinite;
}

.ribbon-chip {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  height: 42px;
  padding: 0 16px;
  background:
    linear-gradient(90deg, rgba(255, 143, 122, 0.08), rgba(88, 203, 255, 0.06)),
    rgba(255, 255, 255, 0.03);
  clip-path: polygon(0 8px, 8px 0, 100% 0, 100% calc(100% - 8px), calc(100% - 8px) 100%, 0 100%);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.chip-label {
  color: rgba(255, 255, 255, 0.56);
  font-size: 11px;
  letter-spacing: 0.12em;
}

.chip-value {
  color: #fff;
  font-family: 'Bahnschrift', 'DIN Alternate', sans-serif;
  font-size: 14px;
}

@keyframes ribbon-scroll {
  from { transform: translateX(0); }
  to { transform: translateX(-50%); }
}
</style>
